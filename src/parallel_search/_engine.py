from __future__ import annotations
from ._shared import _HEADERS, _TIMEOUT_S, logger, retry_call, ErrorTier, classify_error, get_engine_breaker

import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ._western import (
    _search_pubmed,
    _search_europe_pmc,
    _search_crossref,
    _search_openalex,
    _search_arxiv,
    _search_crossref_direct,
    _search_semantic_scholar,
    _search_biorxiv_medrxiv,
    _search_researchgate,
)
from ._chinese import (
    _search_cnki_web,
    _search_baidu_scholar,
    _search_wanfang_web,
)
from ._web import (
    _search_wikipedia,
    _search_duckduckgo,
    _search_gbif,
    _search_core,
)

# ═══════════════════════════════════════════════════════════════
# Provider registry
# ═══════════════════════════════════════════════════════════════

_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "pubmed": (_search_pubmed, 10),
    "europe_pmc": (_search_europe_pmc, 20),
    "crossref": (_search_crossref, 20),
    "openalex": (_search_openalex, 20),
    "arxiv": (_search_arxiv, 10),
    "crossref_direct": (_search_crossref_direct, 15),
    "semantic_scholar": (_search_semantic_scholar, 10),
    "biorxiv_medrxiv": (_search_biorxiv_medrxiv, 10),
    "researchgate": (_search_researchgate, 10),
    "wikipedia": (_search_wikipedia, 5),
    "duckduckgo": (_search_duckduckgo, 8),
    "gbif": (_search_gbif, 5),
    "core": (_search_core, 10),
}

# Chinese providers run separately with chinese_name
_CN_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "cnki_web": (_search_cnki_web, 10),
    "baidu_scholar": (_search_baidu_scholar, 10),
    "wanfang_web": (_search_wanfang_web, 10),
}


# ═══════════════════════════════════════════════════════════════
# Cache provider — species_graph 预计算查找 (0 token, <1ms)
# ═══════════════════════════════════════════════════════════════

def _search_species_graph_cache(query: str, max_results: int = 50) -> List[Dict]:
    """从 species_graph.yaml 缓存中查找已知论文 (0 token, 即时)."""
    try:
        from src.unified_search import _ensure_species_graph_loaded
        graph = _ensure_species_graph_loaded()
        if not graph:
            return []
        species_list = graph.get("graph", {}).get("species", [])
        query_lower = query.lower().strip()
        for species in species_list:
            name = (species.get("name") or "").lower()
            sci_name = (species.get("scientific_name") or "").lower()
            if query_lower in name or query_lower in sci_name:
                papers = species.get("papers", [])
                for p in papers:
                    p["source"] = "cache(species_graph)"
                    p["_cached"] = True
                return papers[:max_results]
    except Exception:
        pass
    return []


_CACHE_PROVIDER = ("cache", (_search_species_graph_cache, 100))


# ═══════════════════════════════════════════════════════════════
# Genus filter — 噪音论文过滤
# ═══════════════════════════════════════════════════════════════

def _extract_genus(query: str) -> Optional[str]:
    """从搜索查询中提取属名（首个拉丁单词，首字母大写）。"""
    query = query.strip()
    # 匹配合法学名：首字母大写的拉丁词
    m = re.match(r'([A-Z][a-z]+)', query)
    if m:
        return m.group(1).lower()
    return None


def _filter_by_genus(query: str, papers: List[Dict[str, Any]],
                     strict_sources: Optional[set] = None) -> List[Dict[str, Any]]:
    """按属名/物种名过滤论文，移除标题中不含目标属名的噪音条目。

    Args:
        query: 搜索查询（从中提取属名）
        papers: 论文列表
        strict_sources: 启用严格模式的源名集合
                        (arXiv/Crossref 噪音大，默认启用)

    Returns:
        过滤后的论文列表
    """
    if strict_sources is None:
        strict_sources = {"arxiv", "crossref"}

    genus = _extract_genus(query)
    if not genus:
        return papers  # 无法提取属名时不过滤

    filtered: List[Dict[str, Any]] = []
    for p in papers:
        source = p.get("source", "")
        title = (p.get("title") or "").lower()
        abstract = (p.get("abstract") or "")
        if isinstance(abstract, dict):
            abstract = str(abstract)
        abstract = abstract.lower()

        # 标题中包含属名 → 保留
        if genus in title:
            filtered.append(p)
            continue

        # arXiv: 严格模式 — 标题必须含属名
        if source in strict_sources:
            continue  # 跳过

        # 其他源: 标题或摘要含属名均可
        if genus in abstract:
            # 摘要匹配比标题匹配可信度低
            p["credibility_score"] = min(p.get("credibility_score", 50), 45)
            filtered.append(p)
            continue

        # 完全不相关
        logger.debug(f"Filtered out '{p.get('title', '')[:60]}' (genus={genus}, source={source})")

    return filtered


# ═══════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════

def _deduplicate(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by DOI (primary) then title (secondary)."""
    seen_dois: set = set()
    seen_titles: set = set()
    result: List[Dict[str, Any]] = []

    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()[:100]

        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)
        result.append(p)

    return result


# ═══════════════════════════════════════════════════════════════
# ParallelSearch
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchStats:
    total_raw: int = 0
    total_merged: int = 0
    new_papers: List[Dict[str, Any]] = field(default_factory=list)
    providers_succeeded: List[str] = field(default_factory=list)
    providers_failed: List[str] = field(default_factory=list)
    elapsed_s: float = 0.0


# ─── Thompson Sampling engine selector ────────────────────────────
_THOMPSON_SELECTOR = None  # Lazy init

def _get_engine_selector():
    """Get or create Thompson engine selector for adaptive engine selection."""
    global _THOMPSON_SELECTOR
    if _THOMPSON_SELECTOR is None:
        try:
            from src.thompson_selector import ThompsonEngineSelector
            _THOMPSON_SELECTOR = ThompsonEngineSelector()
        except ImportError:
            class _DummySelector:
                def select_engines(self, query, available, k=20, context=None):
                    return available
                def update(self, *args, **kwargs):
                    pass
            _THOMPSON_SELECTOR = _DummySelector()
    return _THOMPSON_SELECTOR


class ParallelSearch:
    """多源 HTTP 并行搜索。

    使用 ThreadPoolExecutor 同时查询多个学术搜索引擎。
    结果自动去重（DOI + 标题）。
    """

    def __init__(self, max_workers: int = 4,
                 providers: Optional[List[str]] = None,
                 use_thompson: bool = True):
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._providers = providers or list(_PROVIDERS.keys())
        self._use_thompson = use_thompson and len(self._providers) > 10

    def search(self, query: str, chinese_name: str = "",
               max_per_provider: int = 20) -> SearchStats:
        """并行搜索所有已配置的源.

        Args:
            query: 搜索关键词（通常是学名）
            chinese_name: 中文名，用于中文源
            max_per_provider: 每源最大结果数

        Returns:
            SearchStats with merged papers
        """
        t0 = time.perf_counter()
        all_papers: List[Dict[str, Any]] = []
        per_engine_results: List[List[Dict]] = []  # for RRF fusion
        succeeded: List[str] = []
        failed: List[str] = []
        futures = []

        # ── Cache-first: 0-token graph lookup (Semantic Scholar hybrid pattern) ──
        cache_name, (cache_fn, cache_max) = _CACHE_PROVIDER
        cache_results = cache_fn(query, max_per_provider)
        if cache_results:
            per_engine_results.append(cache_results)
            succeeded.append(f"{cache_name}({len(cache_results)})")
        else:
            per_engine_results.append([])
            failed.append(f"{cache_name}(empty)")

        # ── Thompson Sampling: select optimal provider subset ──
        active_providers = self._providers
        if self._use_thompson:
            selector = _get_engine_selector()
            selected = selector.select_engines(
                query, active_providers, k=min(12, len(active_providers)),
                context={"query": query}
            )
            # Always include core essential providers
            essential = {"pubmed", "crossref", "openalex"}
            for e in essential:
                if e in active_providers and e not in selected:
                    selected.append(e)
            active_providers = selected

        # 提交国际源 (带重试 + 熔断)
        for name in active_providers:
            fn, default_max = _PROVIDERS.get(name, (None, 0))
            if fn is None:
                continue
            # ── 熔断检查 ──
            breaker = get_engine_breaker(name)
            if not breaker.can_pass():
                failed.append(f"{name}(suspended)")
                per_engine_results.append([])
                continue
            limit = min(max_per_provider, default_max)
            futures.append((name, self._pool.submit(
                lambda f=fn, q=query, l=limit: retry_call(f, q, l, max_retries=2),  # noqa: E501
            )))

        # 提交中文源 (带重试 + 熔断)
        if chinese_name:
            for name, (fn_cn, default_max_cn) in _CN_PROVIDERS.items():
                breaker = get_engine_breaker(name)
                if not breaker.can_pass():
                    failed.append(f"{name}(suspended)")
                    per_engine_results.append([])
                    continue
                limit = min(max_per_provider, default_max_cn)
                futures.append((name, self._pool.submit(
                    lambda f=fn_cn, q=chinese_name, l=limit: retry_call(f, q, l, max_retries=2),  # noqa: E501
                )))

        # 收集结果 (带错误分类 + 熔断反馈)
        for name, future in futures:
            breaker = get_engine_breaker(name)
            try:
                result = future.result(timeout=_TIMEOUT_S + 10)
                if result:
                    all_papers.extend(result)
                    per_engine_results.append(result)
                    succeeded.append(name)
                    breaker.record_success()
                else:
                    failed.append(f"{name}(empty)")
                    per_engine_results.append([])
                    breaker.record_failure()
            except Exception as e:
                tier = classify_error(e)
                label = f"{name}({tier.value})"
                failed.append(label)
                per_engine_results.append([])
                if tier in (ErrorTier.SUSPEND, ErrorTier.FATAL):
                    breaker.record_failure()
                logger.debug("[%s] %s: %s", tier.value, name, e)

        # ── 结果融合 (RRF 默认, CombMNZ 可选) ──
        from ._shared import fuse_results
        fused = fuse_results(per_engine_results, method="rrf")

        # 属名校验 — 过滤标题不含目标属名的噪音论文
        filtered = _filter_by_genus(query, fused)

        # ── Thompson update: record engine performance ──
        if self._use_thompson:
            selector = _get_engine_selector()
            elapsed_s = time.perf_counter() - t0
            for name in active_providers:
                had_papers = name in succeeded and any(
                    p.get("source") == name for p in filtered
                )
                selector.update(name, success=had_papers, elapsed_ms=elapsed_s * 1000)

        return SearchStats(
            total_raw=len(all_papers),
            total_merged=len(filtered),
            new_papers=filtered,
            providers_succeeded=succeeded,
            providers_failed=failed,
            elapsed_s=time.perf_counter() - t0,
        )

    def search_all(self, queries: List[str],
                   max_per_query: int = 20) -> SearchStats:
        """对多个查询执行搜索，结果合并去重.

        Args:
            queries: 多个搜索词（学名变体 + 中文名）
            max_per_query: 每查询每源最大结果数

        Returns:
            SearchStats with merged papers from all queries
        """
        all_papers: List[Dict[str, Any]] = []
        all_succeeded: set = set()
        all_failed: set = set()

        for q in queries:
            # Detect if Chinese
            chinese_name = q if re.search(r'[\u4e00-\u9fff]', q) else ""
            search_query = q if not chinese_name else q
            stats = self.search(search_query, chinese_name=chinese_name,
                                max_per_provider=max_per_query)
            all_papers.extend(stats.new_papers)
            all_succeeded.update(stats.providers_succeeded)
            all_failed.update(stats.providers_failed)

        deduped = _deduplicate(all_papers)
        return SearchStats(
            total_raw=len(all_papers),
            total_merged=len(deduped),
            new_papers=deduped,
            providers_succeeded=list(all_succeeded),
            providers_failed=list(all_failed),
        )

    def close(self) -> None:
        """关闭线程池."""
        self._pool.shutdown(wait=False)

    def __enter__(self) -> "ParallelSearch":
        return self

    def __exit__(self, *args) -> None:
        self.close()


# ═══════════════════════════════════════════════════════════════
# Async Parallel Search (v2.0 — aiohttp-based, 3-5x faster)
# ═══════════════════════════════════════════════════════════════

try:
    import aiohttp
    import asyncio as _asyncio
    _HAS_AIOHTTP = True
except ImportError:
    _HAS_AIOHTTP = False


class AsyncParallelSearch:
    """Non-blocking parallel search using aiohttp.

    Usage:
        searcher = AsyncParallelSearch()
        results = await searcher.search("Coilia nasus", providers=["pubmed","crossref"])
    """

    def __init__(self):
        if not _HAS_AIOHTTP:
            raise ImportError("aiohttp required: pip install aiohttp")

    async def search(self, query: str, providers: list = None,
                     max_results: int = 10, timeout: int = 30) -> dict:
        """Execute parallel async search across providers."""
        providers = providers or ["pubmed", "crossref"]
        timeout_obj = _asyncio.timeout(timeout) if hasattr(_asyncio, 'timeout') else None

        async with aiohttp.ClientSession() as session:
            tasks = [self._search_provider(session, p, query, max_results) 
                     for p in providers]
            try:
                if timeout_obj:
                    results = await _asyncio.wait_for(
                        _asyncio.gather(*tasks, return_exceptions=True), timeout
                    )
                else:
                    results = await _asyncio.gather(*tasks, return_exceptions=True)
            except _asyncio.TimeoutError:
                results = [{"error": "timeout", "provider": p} for p in providers]

        return self._merge_results(results, providers)

    async def _search_provider(self, session, provider: str, query: str, limit: int) -> dict:
        """Search a single provider."""
        try:
            if provider == "pubmed":
                return await self._search_pubmed(session, query, limit)
            elif provider == "crossref":
                return await self._search_crossref(session, query, limit)
            elif provider == "openalex":
                return await self._search_openalex(session, query, limit)
            elif provider == "semantic_scholar":
                return await self._search_semantic_scholar(session, query, limit)
            else:
                return {"provider": provider, "error": "unsupported"}
        except Exception as e:
            return {"provider": provider, "error": str(e), "status": "failed"}

    async def _search_pubmed(self, session, query: str, limit: int) -> dict:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return {"provider": "pubmed", "count": len(data.get("esearchresult", {}).get("idlist", [])), "data": data}

    async def _search_crossref(self, session, query: str, limit: int) -> dict:
        url = "https://api.crossref.org/works"
        params = {"query": query, "rows": limit}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            items = data.get("message", {}).get("items", [])
            return {"provider": "crossref", "count": len(items), "data": data}

    async def _search_openalex(self, session, query: str, limit: int) -> dict:
        url = "https://api.openalex.org/works"
        params = {"search": query, "per_page": limit}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            items = data.get("results", [])
            return {"provider": "openalex", "count": len(items), "data": data}

    async def _search_semantic_scholar(self, session, query: str, limit: int) -> dict:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": query, "limit": limit}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            items = data.get("data", [])
            return {"provider": "semantic_scholar", "count": len(items), "data": data}

    def _merge_results(self, results: list, providers: list) -> dict:
        merged = {"total": 0, "providers": {}, "papers": []}
        for p, r in zip(providers, results):
            if isinstance(r, dict) and "error" not in r:
                merged["providers"][p] = r.get("count", 0)
                merged["total"] += r.get("count", 0)
            else:
                merged["providers"][p] = 0
        return merged


def search_async(query: str, providers: list = None, **kwargs) -> dict:
    """One-liner async search (convenience)."""
    if not _HAS_AIOHTTP:
        raise ImportError("aiohttp required")
    searcher = AsyncParallelSearch()
    return _asyncio.run(searcher.search(query, providers, **kwargs))
