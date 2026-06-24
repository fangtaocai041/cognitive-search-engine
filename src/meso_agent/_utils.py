"""
MesoAgent 独立工具函数 — 论文提取、规范化、去重。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _extract_papers(mcp_results: List[dict], source: str) -> List[Dict[str, Any]]:
    """从 MCP 工具返回的结果中提取结构化论文数据.

    支持格式:
      1. MCP tools/call JSON results (text 字段包含 JSON)
      2. scholar-mcp: {"results": [{title, doi, authors, year, venue}, ...]}
      3. article-mcp: {"articles": [{title, doi, ...}]}
      4. ncbi: {"papers": [{title, doi, ...}]}
      5. Raw dict with title/doi fields
    """
    papers: List[Dict[str, Any]] = []

    for item in mcp_results:
        if not isinstance(item, dict):
            continue

        text = item.get("text", "")
        if text and isinstance(text, str) and len(text) > 10:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    # scholar-mcp: {"results": [...], "query": ...}
                    results = (parsed.get("results") or parsed.get("papers")
                               or parsed.get("articles") or parsed.get("items")
                               or [])
                    if isinstance(results, list):
                        for p in results:
                            if isinstance(p, dict) and (p.get("title") or p.get("doi")):
                                _normalize_paper(p, source)
                                papers.append(p)
                    else:
                        _normalize_paper(parsed, source)
                        papers.append(parsed)
                elif isinstance(parsed, list):
                    for p in parsed:
                        if isinstance(p, dict) and (p.get("title") or p.get("doi")):
                            _normalize_paper(p, source)
                            papers.append(p)
            except (json.JSONDecodeError, TypeError):
                # Plain text — create an entry
                lines = text.strip().split("\n")
                title_guess = lines[0][:200] if lines else text[:200]
                papers.append({
                    "title": title_guess,
                    "source": source,
                    "_raw": text[:500],
                })
        elif item.get("title") or item.get("doi"):
            _normalize_paper(item, source)
            papers.append(item)

    return papers


def _normalize_paper(paper: dict, source: str) -> None:
    """Normalize a paper dict to canonical field names."""
    paper.setdefault("source", source)
    # Map common field names
    field_map = {
        "volume": "journal",    # Some APIs return journal in "volume"
        "venue": "journal",     # scholar-mcp uses "venue"
        "container-title": "journal",  # Crossref
        "publication": "journal",
    }
    for old, new in field_map.items():
        if old in paper and new not in paper:
            paper[new] = paper[old]

    # Ensure authors is a list
    authors = paper.get("authors", paper.get("author", []))
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.replace(";", ",").split(",")]
    paper["authors"] = authors if isinstance(authors, list) else []

    # Ensure numeric year
    year = paper.get("year", 0)
    if isinstance(year, str):
        year = int(year[:4]) if year[:4].isdigit() else 0
    paper["year"] = year


def _dedup_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate papers by DOI (primary) then title similarity."""
    seen_dois: set = set()
    seen_titles: set = set()
    deduped: List[Dict[str, Any]] = []

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

        deduped.append(p)

    return deduped
