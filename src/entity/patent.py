"""
专利搜索 — AMiner 专利数据库

借鉴 AMiner 的 search_patent / get_patent_detail 设计，
补足现有系统完全没有专利搜索能力的缺口。

生态学场景:
  - 查鱼类养殖相关专利
  - 查保护技术专利
  - 查某机构的专利布局
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

_search_patent_fn = None


def _lazy_import():
    global _search_patent_fn
    if _search_patent_fn is None:
        from ..parallel_search._aminer import search_aminer_patent
        _search_patent_fn = search_aminer_patent


# ── 工具描述（供 LLM function calling 使用） ──

TOOL_DESCRIPTION = {
    "type": "function",
    "function": {
        "name": "search_patent",
        "description": "搜索专利。按关键词搜索学术专利，返回专利标题、摘要、发明人、状态等。"
                       "适用于：查某项技术的专利情况、查某物种相关专利。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如 '鱼类增殖放流'、'aquaculture feed'"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回数 (1-50)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
}


def search_patent(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """搜索专利 — 按关键词搜索学术专利

    参数:
        query: 搜索关键词
        max_results: 最大结果数

    返回:
        专利信息列表，每项含:
        - title: 专利标题
        - abstract: 摘要
        - inventors: 发明人
        - patent_number: 专利号
        - status: 状态
    """
    _lazy_import()
    return _search_patent_fn(query, max_results)
