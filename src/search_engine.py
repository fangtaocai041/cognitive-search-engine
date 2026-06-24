"""CognitiveSearchEngine — 多源并行搜索编排器。

⚠️ DEPRECATED (v5.9+): 此模块为早期 stub，实际搜索功能已迁移至
   search_coordinator.py + unified_search.py + parallel_search.py。
   保留此文件仅因为 meso_agent.py 和测试中存在向后兼容引用。
   计划 v6.0 移除。
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """单个搜索结果."""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    abstract: str = ""
    credibility_score: int = 0
    source: str = ""  # google_scholar / cnki / pubmed / crossref
    url: str = ""


class CognitiveSearchEngine:
    """多源并行搜索引擎 — ⚠️ STUB (已废弃).

    Features:
      - Google Scholar 优先搜索
      - 中文期刊 (CNKI/CQVIP) 补充
      - PubMed/Crossref 国际文献
      - 可信度评分与去重
    """

    def __init__(self) -> None:
        warnings.warn(
            "CognitiveSearchEngine is DEPRECATED. "
            "Use search_coordinator.search() or unified_search instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._initialized = True

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """⚠️ STUB: 始终返回空列表。

        实际搜索请使用: from src.search_coordinator import search
        """
        warnings.warn(
            "CognitiveSearchEngine.search() is a STUB that always returns []. "
            "Use search_coordinator.search(species=..., group=..., limit=...) instead.",
            FutureWarning,
            stacklevel=2,
        )
        logger.warning(
            f"CognitiveSearchEngine.search() called but is a STUB. "
            f"Query: {query} — returning empty list."
        )
        return []

    def health(self) -> Dict[str, Any]:
        return {"project": "cognitive-search-engine", "status": "HEALTHY"}

    def info(self) -> Dict[str, Any]:
        return {
            "project": "cognitive-search-engine",
            "version": "3.2.0",
            "capabilities": {
                "multi_source_search": True,
                "credibility_scoring": True,
                "fulltext_retrieval": True,
            },
        }
