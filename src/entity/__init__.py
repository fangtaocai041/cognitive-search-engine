"""
entity — AMiner 实体搜索层

借鉴 AMiner MCP 的按实体类型搜索设计，提供学者/机构/专利/期刊搜索。

每个模块的特性：
- 函数可直接被 LLM 调用的格式（输入/输出/描述）
- 通过 `_aminer.py` 的 MCP 连接与 AMiner 通信
- 与现有 16 引擎论文搜索互补

使用示例:
    from src.entity import search_person, search_org, search_patent

    scholars = search_person("曹文宣", max_results=5)
    orgs = search_org("中国科学院水生生物研究所")
    patents = search_patent("鱼类增殖放流")
"""
from __future__ import annotations

from .person import search_person, get_person_detail, get_person_papers
from .org import search_org, get_org_papers, get_org_persons
from .patent import search_patent

__all__ = [
    "search_person", "get_person_detail", "get_person_papers",
    "search_org", "get_org_papers", "get_org_persons",
    "search_patent",
]
