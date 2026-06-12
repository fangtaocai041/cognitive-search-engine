"""
MCP Client — Model Context Protocol client for calling external search servers.

Implements the MCP stdio transport: spawns a subprocess for each MCP server
configured in config/mcp_servers.yaml, communicates via JSON-RPC 2.0 over
stdin/stdout.

Supported servers (configured in config/mcp_servers.yaml):
  - scholar-mcp     → Google Scholar via MCP
  - article-mcp     → Europe PMC + PubMed + Crossref
  - scholarly-mcp   → OpenAlex + Semantic Scholar
  - tavily-mcp      → Tavily AI web search
  - exa-mcp         → Exa semantic search

Usage:
  from mcp_client import McpClient
  client = McpClient()
  results = client.call_tool("scholar_search_literature_graph",
                             {"query": "Ochetobius elongatus", "limit": 10})
"""

import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# ──── JSON-RPC 2.0 primitives ────

_MSG_ID = 0


def _next_id() -> int:
    global _MSG_ID
    _MSG_ID += 1
    return _MSG_ID


def _rpc_request(method: str, params: dict) -> dict:
    return {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params}


# ──── McpClient ────

class McpClient:
    """MCP stdio client that manages subprocess connections to search servers.

    Each tool call maps to a specific MCP server.  The client starts the server
    process on first call and reuses it (process stays alive for the session).
    """

    def __init__(self, config_path: str = None,
                 prewarm: bool = True):
        if config_path is None:
            # 默认相对 mcp_client.py 所在路径
            config_path = str(Path(__file__).resolve().parent.parent / "config" / "mcp_servers.yaml")
        self._config_path = Path(config_path)
        self._servers: dict[str, dict] = {}
        self._processes: dict[str, subprocess.Popen] = {}
        self._tool_to_server: dict[str, str] = {}
        self._healthy_servers: set[str] = set()   # 已通过健康检查的
        self._prewarm_done: bool = False
        self._logger = logging.getLogger("mcp_client")
        self._env_cache: dict[str, str] = {}       # 从 .env 加载的密钥
        self._load_config()
        self._load_dotenv()                         # 加载 .env 密钥

        # 后台预热: 不阻塞 __init__, 首次 call_tool 前自动完成
        if prewarm and self._servers:
            t = threading.Thread(target=self._prewarm_background, daemon=True)
            t.start()

    def _prewarm_background(self):
        """后台线程: 并行启动所有 MCP 服务器 + 健康探测。"""
        self._logger.info(f"Prewarming {len(self._servers)} MCP servers...")
        import concurrent.futures

        def _start_one(name: str):
            proc = self._get_or_start_process(name, retry_max_s=30)
            if proc and self._health_check(name, timeout_s=10):
                self._healthy_servers.add(name)
                return True
            return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self._servers)) as ex:
            futs = {ex.submit(_start_one, name): name for name in self._servers}
            for fut in concurrent.futures.as_completed(futs, timeout=60):
                name = futs[fut]
                try:
                    ok = fut.result()
                    self._logger.info(f"MCP {name}: {'✅ healthy' if ok else '❌ unhealthy'}")
                except Exception as e:
                    self._logger.warning(f"MCP {name}: ❌ {e}")

        self._prewarm_done = True
        healthy = len(self._healthy_servers)
        self._logger.info(f"MCP prewarm complete: {healthy}/{len(self._servers)} healthy")

    def _health_check(self, server_name: str, timeout_s: int = 10) -> bool:
        """JSON-RPC 健康探测: 发送 tools/list 等待响应。

        Returns:
            True if server responds within timeout_s
        """
        proc = self._processes.get(server_name)
        if not proc or proc.poll() is not None:
            return False
        try:
            request = _rpc_request("tools/list", {})
            payload = (json.dumps(request) + "\n").encode("utf-8")
            proc.stdin.write(payload)
            proc.stdin.flush()

            line: Optional[bytes] = None
            def _read():
                nonlocal line
                try:
                    line = proc.stdout.readline()
                except Exception:
                    pass
            reader = threading.Thread(target=_read, daemon=True)
            reader.start()
            reader.join(timeout=timeout_s)
            if reader.is_alive():
                return False
            if not line:
                return False
            resp = json.loads(line.decode("utf-8"))
            return "result" in resp
        except Exception:
            return False

    def _load_config(self):
        """Parse mcp_servers.yaml and build tool→server mapping."""
        if yaml is None:
            return
        try:
            if self._config_path.exists():
                with open(self._config_path) as f:
                    config = yaml.safe_load(f)
                for name, server in (config.get("servers", {}) or {}).items():
                    self._servers[name] = {
                        "command": server.get("command", "npx"),
                        "args": server.get("args", []),
                        "env": server.get("env", {}),
                    }
        except Exception:
            pass

        # Tool → server mapping (extensible; populated as tools are discovered)
        # Default heuristic: any tool with "scholar" in name → scholar server
        self._tool_to_server = {
            "scholar_search_literature_graph": "scholar",
            "scholar_search_google_scholar_key_words": "scholar",
            "scholar_search_google_scholar_advanced": "scholar",
            "article_search_literature": "article",
            "article_get_article_details": "article",
            "article_get_references": "article",
            "article_get_literature_relations": "article",
            "scholarly_research_search": "scholarly",
            "tavily_tavily_search": "tavily",
            "exa_web_search_exa": "exa",
        }

    def _load_dotenv(self, dotenv_path: str = None):
        """加载 .env 文件到 _env_cache。

        搜索路径优先级：
          1. 显式传入 path
          2. 引擎根目录 .env
          3. 工作空间根目录 .env
        """
        candidates = []
        if dotenv_path:
            candidates.append(Path(dotenv_path))
        # 引擎根: mcp_client.py 的上上层
        candidates.append(Path(__file__).resolve().parent.parent / ".env")
        # 工作空间根
        candidates.append(Path(__file__).resolve().parent.parent.parent / ".env")

        for path in candidates:
            if path and path.exists():
                try:
                    with open(path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#") or "=" not in line:
                                continue
                            key, _, val = line.partition("=")
                            key = key.strip()
                            val = val.strip().strip("\"'").strip()
                            if key:
                                self._env_cache[key] = val
                    self._logger.info(f"Loaded {len(self._env_cache)} env vars from {path}")
                    return
                except Exception as e:
                    self._logger.warning(f"Failed to load {path}: {e}")
        self._logger.info("No .env found, using system env only")

    def _resolve_env(self, server_name: str) -> dict:
        """解析 MCP 服务器需要的环境变量。

        从 _env_cache (+ os.environ) 中读取
        mcp_servers.yaml 中声明的 env 字段。
        """
        server = self._servers.get(server_name, {})
        declared = server.get("env", {})
        resolved = dict(os.environ)  # 继承父进程全部环境变量
        for key, template in declared.items():
            # 支持 ${VAR} 和 $VAR 两种语法
            match = re.match(r"\$\{?(\w+)\}?", str(template))
            if match:
                var_name = match.group(1)
                # 优先 .env_cache，其次 os.environ
                val = self._env_cache.get(var_name)
                if not val:
                    val = os.environ.get(var_name)
                if val:
                    resolved[key] = val
                    self._logger.info(f"MCP {server_name}: {key}={val[:12]}...")
                else:
                    self._logger.warning(f"MCP {server_name}: {var_name} not found in .env or os.environ (cache keys: {list(self._env_cache.keys())[:5]})")
        return resolved

    def call_tool(self, tool_name: str, args: dict) -> list[dict]:
        """Call an MCP tool and return the parsed result list.

        Args:
            tool_name: MCP tool name (e.g. "scholar_search_literature_graph")
            args: Tool arguments dict (e.g. {"query": "...", "limit": 10})

        Returns:
            List of result dicts (paper records).
        """
        server_name = self._resolve_server(tool_name)

        if server_name not in self._servers:
            return self._mock_response(tool_name, args)

        process = self._get_or_start_process(server_name)
        if process is None:
            return self._mock_response(tool_name, args)

        try:
            # Build JSON-RPC call
            request = _rpc_request("tools/call", {
                "name": tool_name,
                "arguments": args,
            })
            payload = (json.dumps(request) + "\n").encode("utf-8")

            # Write to stdin
            process.stdin.write(payload)
            process.stdin.flush()

            # Read from stdout with timeout (prevents infinite block)
            line: Optional[bytes] = None
            def _readline():
                nonlocal line
                try:
                    line = process.stdout.readline()
                except Exception:
                    pass

            reader = threading.Thread(target=_readline, daemon=True)
            reader.start()
            reader.join(timeout=15.0)  # 15-second timeout
            if reader.is_alive():
                # Timeout — close stdin to signal the process
                try:
                    process.stdin.close()
                except Exception:
                    pass
                return []  # Return empty on timeout

            if not line:
                return []

            response = json.loads(line.decode("utf-8"))
            if "error" in response:
                return []

            # Unwrap MCP result
            result = response.get("result", {})
            content = result.get("content", [])
            if isinstance(content, list):
                return content
            return [content] if content else []

        except (BrokenPipeError, OSError, json.JSONDecodeError):
            return []

    def close(self):
        """Terminate all MCP server subprocesses."""
        for name, proc in self._processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    # ── Internal ──

    def _resolve_server(self, tool_name: str) -> str | None:
        """Map a tool name to the server that provides it."""
        if tool_name in self._tool_to_server:
            return self._tool_to_server[tool_name]
        # Heuristic: match by prefix
        for prefix, server in [
            ("scholar_", "scholar"),
            ("article_", "article"),
            ("scholarly_", "scholarly"),
            ("tavily_", "tavily"),
            ("exa_", "exa"),
        ]:
            if tool_name.startswith(prefix):
                return server
        return None

    def call_tools_parallel(self, tool_calls: list[tuple[str, dict]],
                            timeout_s: int = 180,
                            on_result: callable = None) -> list[tuple[str, list[dict]]]:
        """并行调用多个 MCP 工具，先完成先返回。

        Args:
            tool_calls: [(tool_name, args), ...] 列表
            timeout_s: 总超时 (默认 180s = 3min)
            on_result: 可选回调, 每完成一个调用即调用 on_result(tool_name, results)

        Returns:
            [(tool_name, results), ...] — 按完成顺序排列
        """
        import concurrent.futures
        import time

        results: list[tuple[str, list[dict]]] = []
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
                    per_timeout = min(remaining, 120)
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

    def _get_or_start_process(self, server_name: str,
                              retry_max_s: int = 60) -> subprocess.Popen | None:
        """Return the running process for a server, starting it if needed."""
        if server_name in self._processes:
            proc = self._processes[server_name]
            if proc.poll() is None:  # still running
                return proc
            # Restart if dead (带重试)
            logger = logging.getLogger("mcp_client")
            logger.info(f"MCP {server_name} process died, restarting...")
            del self._processes[server_name]

        server = self._servers[server_name]
        server_env = self._resolve_env(server_name)
        deadline = time.monotonic() + retry_max_s
        last_error = None

        for attempt in range(5):  # 最多 5 次重试
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                proc = subprocess.Popen(
                    [server["command"]] + server["args"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False,  # binary mode for JSON-RPC
                    env=server_env,
                )
                self._processes[server_name] = proc
                return proc
            except (FileNotFoundError, OSError) as e:
                last_error = e
                wait = min(2 ** attempt, remaining / 2, 10)
                if wait > 0.5:
                    import time as _time
                    _time.sleep(wait)
                continue

        logger = logging.getLogger("mcp_client")
        logger.warning(f"MCP {server_name} failed after retry: {last_error}")
        return None

    @staticmethod
    def _mock_response(tool_name: str, args: dict) -> list[dict]:
        """Fallback response when MCP server is unavailable."""
        query = args.get("query", "")
        return [
            {
                "doi": "10.mock/fallback",
                "title": f"[MCP unavailable] {query[:60]}",
                "note": f"MCP server for {tool_name} not running. "
                        "Install: npx -y scholar-mcp / article-mcp / scholarly-mcp",
                "year": None,
                "authors": [],
                "source": f"mcp_fallback:{tool_name}",
            }
        ]


# ──── Convenience API ────

# Module-level client (lazy init)
_client: McpClient | None = None


def call_mcp_tool(tool_name: str, args: dict) -> list[dict]:
    """Convenience function: call an MCP tool via the module-level client."""
    global _client
    if _client is None:
        _client = McpClient()
    return _client.call_tool(tool_name, args)


def call_mcp_tools_parallel(tool_calls: list[tuple[str, dict]],
                            timeout_s: int = 180) -> list[tuple[str, list[dict]]]:
    """并行调用多个 MCP 工具（模块级便捷函数）。

    Args:
        tool_calls: [(tool_name, args), ...]
        timeout_s: 总超时 (默认 180s)

    Returns:
        [(tool_name, results), ...] — 按完成顺序
    """
    global _client
    if _client is None:
        _client = McpClient()
    return _client.call_tools_parallel(tool_calls, timeout_s=timeout_s)


def prewarm_mcp(timeout_s: int = 60) -> int:
    """预热所有 MCP 服务器（阻塞直到全部启动或超时）。

    Args:
        timeout_s: 总超时

    Returns:
        健康检查通过的服务器数量
    """
    global _client
    if _client is None:
        _client = McpClient(prewarm=False)
    # 手动触发预热，等待完成
    deadline = time.monotonic() + timeout_s
    _client._prewarm_background()
    remaining = deadline - time.monotonic()
    if remaining > 0:
        time.sleep(min(remaining, 5))
    return len(_client._healthy_servers)
