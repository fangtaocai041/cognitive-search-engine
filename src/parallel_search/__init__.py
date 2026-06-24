"""
ParallelSearch — 多源 HTTP 并行搜索模块 (package)

替代 MCP 无法使用时的 HTTP 直连搜索。
支持 PubMed E-utilities、Europe PMC、Crossref、OpenAlex、CNKI/Bing。
在 Reasonix 外部 CLI 环境中也可独立运行。

用法:
    from src.parallel_search import ParallelSearch

    searcher = ParallelSearch(max_workers=4)
    papers = searcher.search("Ochetobius elongatus")
    searcher.close()

返回统一的论文 dict 格式:
    { "doi", "title", "authors": [], "year", "journal", "abstract",
      "source", "pmid", "pmcid", "url", "credibility_score" }
"""

from __future__ import annotations

from ._engine import (
    ParallelSearch,
    AsyncParallelSearch,
    SearchStats,
    search_async,
)

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

__all__ = [
    "ParallelSearch",
    "AsyncParallelSearch",
    "SearchStats",
    "search_async",
    "_search_pubmed",
    "_search_europe_pmc",
    "_search_crossref",
    "_search_openalex",
    "_search_arxiv",
    "_search_crossref_direct",
    "_search_semantic_scholar",
    "_search_biorxiv_medrxiv",
    "_search_researchgate",
    "_search_cnki_web",
    "_search_baidu_scholar",
    "_search_wanfang_web",
    "_search_wikipedia",
    "_search_duckduckgo",
    "_search_gbif",
    "_search_core",
]
