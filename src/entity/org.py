"""
机构搜索 — AMiner 学术机构

借鉴 AMiner 的 search_organization / get_organization_* 设计，
按机构名称查找学术产出。

生态学场景:
  - 查某研究所的鱼类学团队 ("中国科学院水生生物研究所")
  - 查某高校的生态学论文产出
  - 机构间合作分析
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

_search_org_fn = None
_get_papers_fn = None
_get_persons_fn = None


def _lazy_import():
    global _search_org_fn, _get_papers_fn, _get_persons_fn
    if _search_org_fn is None:
        from ..parallel_search._aminer import (
            search_aminer_organization,
            _call_aminer_tool,
        )
        _search_org_fn = search_aminer_organization
        _get_papers_fn = lambda oid, limit=20: _call_aminer_tool(
            "get_organization_papers", {"ids": oid, "offset": 0, "size": limit}
        )
        _get_persons_fn = lambda oid, limit=20: _call_aminer_tool(
            "get_organization_persons", {"ids": oid, "offset": 0, "size": limit}
        )


# ── 工具描述（供 LLM function calling 使用） ──

TOOL_DESCRIPTION = {
    "type": "function",
    "function": {
        "name": "search_org",
        "description": "搜索学术机构。按名称查找机构的基本信息、论文产出、学者规模等。"
                       "适用于：查某个研究机构、比较不同机构的学术产出。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "机构名称，如 '中国科学院水生生物研究所'、'Tsinghua University'"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回数 (1-50)",
                    "default": 10
                }
            },
            "required": ["name"]
        }
    }
}


def search_org(name: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """搜索机构 — 按名称查找学术机构

    参数:
        name: 机构名称
        max_results: 最大结果数

    返回:
        机构信息列表，每项含:
        - name: 机构名称
        - country: 国家
        - paper_count: 论文总数
        - person_count: 学者数
    """
    _lazy_import()
    return _search_org_fn(name, max_results)


def get_org_papers(org_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """获取机构的论文列表

    参数:
        org_id: AMiner 机构 ID
        max_results: 最大论文数

    返回:
        论文列表
    """
    _lazy_import()
    return _get_papers_fn(org_id, max_results)


def get_org_persons(org_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """获取机构的学者列表

    参数:
        org_id: AMiner 机构 ID
        max_results: 最大学者数

    返回:
        学者列表
    """
    _lazy_import()
    return _get_persons_fn(org_id, max_results)
