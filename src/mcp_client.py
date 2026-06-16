"""
McpClient — MCP Server Client Manager

Manages multiple MCP server subprocesses (scholar, article, tavily, exa, etc.),
handles JSON-RPC communication over stdin/stdout, and provides both
single-call and parallel-call interfaces.

Config source: config/mcp_servers.yaml
Protocol: JSON-RPC 2.0 over stdio (compatible with @modelcontextprotocol/sdk)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class McpClient:
    """Manages MCP server processes and provides JSON-RPC tool calling."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._servers: Dict[str, dict] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._request_id: int = 0
        self._load_config(config_path)

    # ── Configuration ──────────────────────────────────────────────

    def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load MCP server definitions from YAML config."""
        if config_path is None:
            base = Path(__file__).resolve().parent.parent  # cognitive-search-engine root
            config_path = str(base / "config" / "mcp_servers.yaml")

        path = Path(config_path)
        if not path.exists():
            logger.warning(f"MCP config not found at {config_path}; using empty server list")
            self._servers = {}
            return

        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            logger.warning("PyYAML not installed; cannot load MCP config")
            self._servers = {}
            return

        raw = data.get("servers", data) if isinstance(data, dict) else {}
        self._servers = {}
        for name, cfg in raw.items():
            if isinstance(cfg, dict) and "command" in cfg:
                self._servers[name] = {
                    "command": cfg["command"],
                    "args": cfg.get("args", []),
                    "description": cfg.get("description", ""),
                }

        logger.info(
            f"McpClient loaded {len(self._servers)} servers: "
            f"{', '.join(self._servers.keys())}"
        )

    def list_servers(self) -> List[str]:
        """Return names of all configured servers."""
        return list(self._servers.keys())

    def server_info(self, name: str) -> Optional[dict]:
        """Return config dict for a server."""
        return self._servers.get(name)

    # ── Process management ────────────────────────────────────────

    def _get_or_start_process(self, server_name: str,
                              retry_max_s: int = 60) -> Optional[subprocess.Popen]:
        """Return the running process for a server, starting it if needed."""
        if server_name in self._processes:
            proc = self._processes[server_name]
            if proc.poll() is None:  # still running
                return proc
            # Restart if dead
            logger.info(f"MCP {server_name} process died, restarting...")
            del self._processes[server_name]

        server = self._servers.get(server_name)
        if server is None:
            logger.warning(f"MCP server '{server_name}' not configured")
            return None

        deadline = time.monotonic() + retry_max_s
        last_error: Optional[Exception] = None

        for attempt in range(5):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                proc = subprocess.Popen(
                    [server["command"]] + server["args"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    text=False,  # binary mode for JSON-RPC
                )
                self._processes[server_name] = proc
                return proc
            except (FileNotFoundError, OSError) as e:
                last_error = e
                wait = min(2 ** attempt, remaining / 2, 10)
                if wait > 0.5:
                    time.sleep(wait)
                continue

        logger.warning(f"MCP {server_name} failed after retry: {last_error}")
        return None

    def stop_server(self, server_name: str) -> None:
        """Terminate a specific MCP server process."""
        proc = self._processes.pop(server_name, None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

    def stop_all(self) -> None:
        """Terminate all managed MCP server processes."""
        for name in list(self._processes.keys()):
            self.stop_server(name)

    def __del__(self) -> None:
        self.stop_all()

    # ── JSON-RPC communication ────────────────────────────────────

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _send_request(self, proc: subprocess.Popen, method: str,
                      params: dict) -> Optional[dict]:
        """Send a JSON-RPC request and read the response."""
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
        request_bytes = (json.dumps(req) + "\n").encode("utf-8")
        if proc.stdin is None:
            return None

        try:
            proc.stdin.write(request_bytes)
            proc.stdin.flush()
        except BrokenPipeError:
            return None

        # Read response: look for a line containing our id
        if proc.stdout is None:
            return None

        deadline = time.monotonic() + 30
        buffer = b""
        while time.monotonic() < deadline:
            try:
                chunk = proc.stdout.read1(65536)
                if not chunk:
                    break
                buffer += chunk
                # Try to parse complete JSON objects from buffer
                text = buffer.decode("utf-8", errors="replace")
                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        resp = json.loads(line)
                        if isinstance(resp, dict) and resp.get("id") == req["id"]:
                            return resp
                    except json.JSONDecodeError:
                        continue
            except Exception:
                break

        # Fallback: try to parse any complete JSON from accumulated buffer
        try:
            text = buffer.decode("utf-8", errors="replace")
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    resp = json.loads(line)
                    if isinstance(resp, dict) and resp.get("id") == req["id"]:
                        return resp
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        return None

    # ── Tool calling ──────────────────────────────────────────────

    def call_tool(self, server_name: str,
                  arguments: Optional[dict] = None) -> List[dict]:
        """Call a tool on an MCP server.

        Args:
            server_name: Tool name in form "server_name" or "server_name/tool_name".
                         If no slash, tool name = server name.
            arguments: Tool arguments dict.

        Returns:
            List of content items from the tool response.
        """
        proc = self._get_or_start_process(server_name)
        if proc is None:
            return [{"error": f"Server '{server_name}' not available", "source": "mcp"}]

        # Split into server_name and tool_name
        parts = server_name.split("/", 1)
        if len(parts) > 1:
            tool_name = parts[1]
        else:
            tool_name = server_name  # same as server name

        # Step 1: Initialize session
        init_resp = self._send_request(proc, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "cognitive-search-engine", "version": "5.8.0"},
        })
        if init_resp is None:
            return [{"error": "MCP initialization failed", "source": "mcp"}]

        # Step 2: List tools (optional, get tool schema)
        tools_resp = self._send_request(proc, "tools/list", {})
        if tools_resp is None:
            return [{"error": "MCP tools/list failed", "source": "mcp"}]

        # Step 3: Call the tool
        call_resp = self._send_request(proc, "tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        })
        if call_resp is None:
            return [{"error": f"MCP tool call '{tool_name}' failed", "source": "mcp"}]

        if "error" in call_resp:
            err = call_resp["error"]
            return [{
                "error": err.get("message", str(err)),
                "code": err.get("code"),
                "source": "mcp",
            }]

        result = call_resp.get("result", {})
        if isinstance(result, dict):
            content = result.get("content", [])
            if isinstance(content, list):
                return content
            return [{"text": str(result), "source": tool_name}]
        return [{"text": str(result), "source": tool_name}]

    def call_tools_parallel(
        self,
        tool_calls: List[Tuple[str, dict]],
        timeout_s: int = 180,
        on_result: Optional[Callable[[str, List[dict]], None]] = None,
    ) -> List[Tuple[str, List[dict]]]:
        """并行调用多个 MCP 工具，先完成先返回。

        Args:
            tool_calls: [(tool_name, args), ...] 列表
            timeout_s: 总超时 (默认 180s = 3min)
            on_result: 可选回调, 每完成一个调用即调用 on_result(tool_name, results)

        Returns:
            [(tool_name, results), ...] — 按完成顺序排列
        """
        import concurrent.futures

        results: List[Tuple[str, List[dict]]] = []
        deadline = time.monotonic() + timeout_s

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(tool_calls), 7)
        ) as executor:
            future_map = {
                executor.submit(self.call_tool, name, args): name
                for name, args in tool_calls
            }

            for future in concurrent.futures.as_completed(future_map, timeout=timeout_s):
                name = future_map[future]
                try:
                    remaining = deadline - time.monotonic()
                    per_timeout = min(remaining, 30)
                    if per_timeout <= 0:
                        per_timeout = 5
                    call_results = future.result(timeout=per_timeout)
                    results.append((name, call_results))
                    if on_result:
                        on_result(name, call_results)
                except concurrent.futures.TimeoutError:
                    results.append((name, [{"note": f"timeout > {timeout_s}s", "source": "mcp_timeout"}]))
                    if on_result:
                        on_result(name, [])
                except Exception as e:
                    results.append((name, [{"note": f"error: {e}", "source": "mcp_error"}]))
                    if on_result:
                        on_result(name, [])

        return results

    # ── Convenience: search-specific adapters ─────────────────────

    def search_scholar(self, query: str, limit: int = 10) -> List[dict]:
        """Search via scholar-mcp."""
        return self.call_tool("scholar", {
            "query": query,
            "limit": limit,
        })

    def search_article(self, keyword: str, max_results: int = 10) -> List[dict]:
        """Search via article-mcp."""
        return self.call_tool("article", {
            "keyword": keyword,
            "max_results": max_results,
            "search_type": "comprehensive",
        })

    def search_tavily(self, query: str, max_results: int = 5) -> List[dict]:
        """Search via tavily-mcp."""
        return self.call_tool("tavily", {
            "query": query,
            "max_results": max_results,
        })

    def search_exa(self, query: str, num_results: int = 5) -> List[dict]:
        """Search via exa-mcp."""
        return self.call_tool("exa", {
            "query": query,
            "numResults": num_results,
        })


# ── Module-level convenience ──────────────────────────────────────

_default_client: Optional[McpClient] = None


def get_client() -> McpClient:
    """Return (or create) the default singleton McpClient."""
    global _default_client
    if _default_client is None:
        _default_client = McpClient()
    return _default_client
