"""
Search Streaming — Per-engine dual-path parallel search.

v5.8 从 unified_search.py 抽离，独立模块。
每个引擎 MCP → HTTP 自动降级。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import concurrent.futures
import time


@dataclass
class EngineResult:
    engine: str
    query: str
    tool: str = ""
    status: str = "pending"
    results: List[Dict] = field(default_factory=list)
    error: str = ""
    retries: int = 0
    elapsed_ms: float = 0.0


@dataclass
class StreamEvent:
    """流式结果 — 引擎完成后立即输出"""
    engine: str
    status: str
    paper_count: int
    elapsed_ms: float
    is_last: bool = False


# 原生 HTTP 引擎 (始终 HTTP，不走 MCP)
_NATIVE_HTTP_TOOLS = {
    "baidu_scholar", "cnki_web", "wanfang_web", "cas_web",
    "chinese_search", "chinese_sweep",
    "biorxiv_search", "researchgate_web", "europe_pmc_search",
    "web_search",
}


def _mcp_available() -> bool:
    """Check if MCP tools are injected (Reasonix runtime)."""
    return callable(globals().get("scholar_search_literature_graph"))


def _call_mcp_tool(tool_name: str, query: str, limit: int) -> List[Dict]:
    """
    _call_mcp_tool(tool_name, query, limit) → [papers]

    Calls the actual MCP search tool injected by Reasonix runtime.
    Tools are injected as Python callables, not through import.
    """
    fn = globals().get(tool_name)
    if callable(fn):
        result = fn(query, limit)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "results" in result:
            return result["results"]
    raise ImportError(f"MCP tool '{tool_name}' not available")


def search_streaming(
    queries: List[str],
    engines: List[str] = None,
    group: str = "standard",
    limit: int = 10,
    max_retries: int = 3,
    per_engine_timeout_s: float = 120.0,
    on_result: Optional[Callable] = None,
    engine_registry: Optional[Dict[str, Dict]] = None,
    engine_groups: Optional[Dict[str, List[str]]] = None,
) -> List[EngineResult]:
    """
    search_streaming(queries, group="standard") → [EngineResult]

    v5.6 双路径架构: 每个引擎 MCP → HTTP 自动降级。
    - MCP 可用 → 优先 MCP 调用
    - MCP 不可用/失败 → 自动 HTTP fallback
    - 中文/预印本原生引擎 → 始终走 HTTP
    """
    from src.unified_search import ENGINE_GROUPS as _DEFAULT_GROUPS
    from src.unified_search import ENGINE_REGISTRY as _DEFAULT_REGISTRY

    groups = engine_groups or _DEFAULT_GROUPS
    registry = engine_registry or _DEFAULT_REGISTRY

    if engines is None:
        engines = groups.get(group, groups.get("standard", []))

    results: List[EngineResult] = []

    # ── Detect MCP availability ──
    _mcp_ok = _mcp_available()
    if not _mcp_ok:
        _mcp_start = time.monotonic()
        while time.monotonic() - _mcp_start < 2.0:
            time.sleep(0.5)
            if _mcp_available():
                _mcp_ok = True
                break

    # ── Lazy-load HTTP fallback registry ──
    try:
        from src.parallel_search import MCP_HTTP_FALLBACK as _hfb
    except ImportError:
        _hfb = {}

    def _search_one_dual(engine_id: str, query: str) -> EngineResult:
        """Per-engine dual-path: MCP first → HTTP fallback."""
        t0 = time.perf_counter()
        info = registry.get(engine_id, {"tool": engine_id, "category": "unknown", "priority": 9})
        tool = info.get("tool", engine_id)
        result = EngineResult(engine=engine_id, query=query, tool=tool)

        is_native_http = tool in _NATIVE_HTTP_TOOLS
        http_fn = _hfb.get(tool) if _hfb else None

        # ── Path A: Native HTTP engines ──
        if is_native_http:
            if http_fn:
                try:
                    result.results = http_fn(query, limit)
                    result.status = "ok"
                except Exception as e:
                    result.status = "error"
                    result.error = str(e)[:200]
            else:
                result.status = "degraded"
                result.error = f"{tool}: native HTTP provider not found"
            result.elapsed_ms = (time.perf_counter() - t0) * 1000
            return result

        # ── Path B: MCP first ──
        if _mcp_ok:
            for attempt in range(max_retries):
                try:
                    result.results = _call_mcp_tool(tool, query, limit)
                    result.status = "ok"
                    result.elapsed_ms = (time.perf_counter() - t0) * 1000
                    return result
                except ImportError:
                    break
                except Exception as e:
                    result.retries = attempt + 1
                    if attempt < max_retries - 1:
                        time.sleep(min(1.0 * (2 ** attempt), 8))
                        continue
                    break

        # ── Path C: HTTP fallback ──
        if http_fn:
            try:
                result.results = http_fn(query, limit)
                result.status = "ok(fallback)"
                result.tool = f"{tool}→HTTP"
            except Exception as e:
                result.status = "error"
                result.error = str(e)[:200]
        else:
            result.status = "degraded" if not _mcp_ok else "error"
            result.error = f"{tool}: MCP {'unavailable' if not _mcp_ok else 'failed'} + no HTTP fallback"

        result.elapsed_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── Parallel fan-out ──
    total = len(engines) * len(queries)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 12)) as ex:
        futures = {}
        for engine_id in engines:
            for query in queries:
                future = ex.submit(_search_one_dual, engine_id, query)
                futures[future] = (engine_id, query)

        for future in concurrent.futures.as_completed(futures):
            engine_id, query = futures[future]
            try:
                result = future.result(timeout=per_engine_timeout_s)
                results.append(result)
                completed += 1
                if on_result:
                    on_result(StreamEvent(
                        engine=result.engine,
                        status=result.status,
                        paper_count=len(result.results),
                        elapsed_ms=result.elapsed_ms,
                        is_last=(completed == total),
                    ))
            except concurrent.futures.TimeoutError:
                results.append(EngineResult(
                    engine=engine_id, query=query,
                    status="error", error=f"timeout ({per_engine_timeout_s}s)"
                ))
                completed += 1

    return results, []
