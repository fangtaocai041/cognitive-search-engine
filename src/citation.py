"""
citation — 引用导出工具

通过 CrossRef API 获取 BibTeX/EndNote 格式的引用数据。
不依赖 SciSpace，纯 CrossRef 开放接口。

用法:
    from src.citation import export_bibtex, export_endnote

    # 单篇 DOI
    bib = export_bibtex("10.1007/s10641-020-00986-1")

    # 批量导出
    papers = search("Coilia nasus")["papers"]
    bibtex_str = export_bibtex_batch([p["doi"] for p in papers if p.get("doi")])
"""

from __future__ import annotations
from parallel_search._shared import _HEADERS, _TIMEOUT_S, logger

import json
import re
import urllib.request
from typing import Any, Dict, List, Optional


def export_bibtex(doi: str) -> str:
    """通过 CrossRef 获取 BibTeX 格式引用

    Args:
        doi: DOI 标识符 (如 "10.1007/s10641-020-00986-1")

    Returns:
        BibTeX 格式字符串，失败返回空字符串
    """
    if not doi or not isinstance(doi, str):
        return ""
    doi = doi.strip()
    if not doi:
        return ""

    try:
        url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
        req = urllib.request.Request(url, headers={
            **_HEADERS,
            "Accept": "application/x-bibtex",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception as e:
        logger.debug(f"BibTeX export failed for {doi}: {e}")
        return ""


def export_endnote(doi: str) -> str:
    """通过 CrossRef 获取 EndNote 格式引用

    Args:
        doi: DOI 标识符

    Returns:
        EndNote 格式字符串
    """
    if not doi or not isinstance(doi, str):
        return ""
    doi = doi.strip()
    if not doi:
        return ""

    try:
        url = f"https://api.crossref.org/works/{doi}/transform/application/x-endnote"
        req = urllib.request.Request(url, headers={
            **_HEADERS,
            "Accept": "application/x-endnote",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception as e:
        logger.debug(f"EndNote export failed for {doi}: {e}")
        return ""


def export_bibtex_batch(dois: List[str]) -> str:
    """批量导出 BibTeX

    Args:
        dois: DOI 列表

    Returns:
        合并的 BibTeX 字符串，每篇用空行分隔
    """
    entries = []
    for doi in dois:
        bib = export_bibtex(doi)
        if bib:
            entries.append(bib)
    return "\n\n".join(entries)


def export_bibtex_from_papers(papers: List[Dict[str, Any]]) -> str:
    """从论文列表中导出 BibTeX

    Args:
        papers: 论文列表（每项需含 doi 字段）

    Returns:
        合并的 BibTeX 字符串
    """
    dois = [p.get("doi", "") for p in papers if p.get("doi")]
    return export_bibtex_batch(dois)
