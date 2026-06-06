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
import subprocess
import sys
from pathlib import Path
from typing import Any

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

    def __init__(self, config_path: str = "config/mcp_servers.yaml"):
        self._config_path = Path(config_path)
        self._servers: dict[str, dict] = {}
        self._processes: dict[str, subprocess.Popen] = {}
        self._tool_to_server: dict[str, str] = {}
        self._load_config()

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

            # Read from stdout (one JSON-RPC response line)
            line = process.stdout.readline()
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

    def _get_or_start_process(self, server_name: str) -> subprocess.Popen | None:
        """Return the running process for a server, starting it if needed."""
        if server_name in self._processes:
            proc = self._processes[server_name]
            if proc.poll() is None:  # still running
                return proc
            # Restart if dead
            del self._processes[server_name]

        server = self._servers[server_name]
        try:
            proc = subprocess.Popen(
                [server["command"]] + server["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # binary mode for JSON-RPC
            )
            self._processes[server_name] = proc
            return proc
        except (FileNotFoundError, OSError):
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
