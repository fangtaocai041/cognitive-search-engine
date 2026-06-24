# ⚠ DEPRECATED: This module has been split into the `parallel_search` package.
# Importing from here still works for backward compatibility, but new code
# should import directly from `src.parallel_search`.
#
# Usage (new):
#     from src.parallel_search import ParallelSearch
#
# This file is kept as a thin re-export shim.

from __future__ import annotations

from src.parallel_search import (
    ParallelSearch,
    AsyncParallelSearch,
    SearchStats,
    search_async,
    _search_pubmed,
    _search_europe_pmc,
    _search_crossref,
    _search_openalex,
    _search_arxiv,
    _search_crossref_direct,
    _search_semantic_scholar,
    _search_biorxiv_medrxiv,
    _search_researchgate,
    _search_cnki_web,
    _search_baidu_scholar,
    _search_wanfang_web,
    _search_wikipedia,
    _search_duckduckgo,
    _search_gbif,
    _search_core,
)
