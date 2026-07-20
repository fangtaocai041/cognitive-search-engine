"""
学者搜索 — AMiner 学术档案

借鉴 AMiner 的 search_person 与 get_person_* 设计，
补足现有系统"只能搜论文、不能搜学者"的能力缺口。

生态学场景:
  - 查某位鱼类学家的近期成果 ("曹文宣")
  - 查某机构有哪些学者 ("水生所 鱼类学")
  - 查合作者网络
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

# 运行时按需导入，避免模块级依赖 MCP 包
_search_person_fn = None
_get_detail_fn = None
_get_papers_fn = None


def _lazy_import():
    global _search_person_fn, _get_detail_fn, _get_papers_fn
    if _search_person_fn is None:
        from ..parallel_search._aminer import (
            search_aminer_person,
            _call_aminer_tool,
        )
        _search_person_fn = search_aminer_person
        _get_detail_fn = lambda pid: _call_aminer_tool("get_person_detail", {"id": pid})
        _get_papers_fn = lambda pid, limit=20: _call_aminer_tool(
            "get_person_papers", {"id": pid, "offset": 0, "size": limit}
        )


# ── 工具描述（供 LLM function calling 使用） ──

TOOL_DESCRIPTION = {
    "type": "function",
    "function": {
        "name": "search_person",
        "description": "搜索学者。按姓名查找学者的学术档案，包括所在机构、H-index、论文数等。"
                       "适用于：查某位研究者的背景、找某领域的学者、查合作者。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "学者姓名，中英文均可，如 '曹文宣'、'Yi Li'"
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


def search_person(name: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """搜索学者 — 按姓名查找学术档案

    参数:
        name: 学者姓名（中英文均可）
        max_results: 最大结果数

    返回:
        学者信息列表，每项含:
        - name: 姓名
        - org: 所在机构
        - h_index: H-index
        - paper_count: 论文数
        - citation_count: 总引用
        - tags: 研究方向标签
    """
    _lazy_import()
    return _search_person_fn(name, max_results)


def get_person_detail(person_id: str) -> Dict[str, Any]:
    """获取学者详情 — 按 AMiner ID 获取完整档案

    参数:
        person_id: AMiner 学者 ID

    返回:
        学者完整档案信息
    """
    _lazy_import()
    results = _get_detail_fn(person_id)
    return results[0] if results else {}


def get_person_papers(person_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """获取学者的论文列表

    参数:
        person_id: AMiner 学者 ID
        max_results: 最大论文数

    返回:
        论文列表
    """
    _lazy_import()
    return _get_papers_fn(person_id, max_results)
