"""
tool_schema — 16 搜索引擎的 LLM 工具描述

将现有的 16 个搜索引擎包装为 LLM function calling 可消费的格式。
每个引擎的描述包括：用途、适用场景、引擎特点。

结合 entity/ 模块（学者/机构/专利搜索），
LLM Agent 可获得完整的学术搜索工具箱。

使用示例:
    from src.tool_schema import ALL_TOOLS
    # ALL_TOOLS 可直接传入 LLM 的 tools 参数
"""

from __future__ import annotations
from typing import Any, Dict, List


# ═══════════════════════════════════════════════════════════════
# 论文搜索引擎 (16 个)
# ═══════════════════════════════════════════════════════════════

PAPER_SEARCH_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_papers",
            "description": "多引擎并行搜索学术论文。自动在 16 个搜索引擎中并行检索，"
                           "返回去重后的论文列表。支持多种搜索模式。"
                           "适用于：文献调研、物种知识查询、研究前沿追踪。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如 'Coilia nasus otolith'、'长江江豚 声学'"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "standard", "full", "chinese", "preprint", "species"],
                        "description": "搜索模式: quick=快速(3引擎), standard=标准(6引擎,默认), "
                                       "full=全面(19引擎), chinese=中文优先(7引擎), "
                                       "preprint=预印本(3引擎), species=物种百科(4引擎)"
                    }
                },
                "required": ["query"]
            }
        }
    },
]

# ═══════════════════════════════════════════════════════════════
# 各引擎详情清单（供参考/选择使用）
# ═══════════════════════════════════════════════════════════════

ENGINE_DETAILS: List[Dict[str, Any]] = [
    {"id": "pubmed", "name": "PubMed", "category": "国际学术", "coverage": "生物医学, 3000万+", "strength": "权威医学"},
    {"id": "europe_pmc", "name": "Europe PMC", "category": "国际学术", "coverage": "生物医学, 全文", "strength": "开放获取"},
    {"id": "crossref", "name": "Crossref", "category": "国际学术", "coverage": "多学科, 1.2亿+", "strength": "DOI 解析"},
    {"id": "openalex", "name": "OpenAlex", "category": "国际学术", "coverage": "全学科, 2.5亿+", "strength": "开放索引"},
    {"id": "arxiv", "name": "arXiv", "category": "预印本", "coverage": "数理化/CS", "strength": "最新预印本"},
    {"id": "semantic_scholar", "name": "Semantic Scholar", "category": "国际学术", "coverage": "全学科, AI筛选", "strength": "高影响论文"},
    {"id": "baidu_scholar", "name": "百度学术", "category": "中文", "coverage": "中文学术, 2亿+", "strength": "中文全覆盖"},
    {"id": "cnki_web", "name": "CNKI", "category": "中文", "coverage": "中文学术, 核心期刊", "strength": "中文权威"},
    {"id": "wanfang_web", "name": "万方", "category": "中文", "coverage": "中文学术", "strength": "学位论文"},
    {"id": "gbif", "name": "GBIF", "category": "物种", "coverage": "全球生物多样性", "strength": "物种分布"},
    {"id": "core", "name": "CORE", "category": "全文", "coverage": "开放获取全文", "strength": "全文下载"},
]

# ═══════════════════════════════════════════════════════════════
# 实体搜索工具 (借鉴 AMiner 设计)
# ═══════════════════════════════════════════════════════════════

# 从 entity 模块导入工具描述
try:
    from .entity.person import TOOL_DESCRIPTION as PERSON_TOOL
    from .entity.org import TOOL_DESCRIPTION as ORG_TOOL
    from .entity.patent import TOOL_DESCRIPTION as PATENT_TOOL
    ENTITY_TOOLS = [PERSON_TOOL, ORG_TOOL, PATENT_TOOL]
except ImportError:
    ENTITY_TOOLS = []

# ═══════════════════════════════════════════════════════════════
# 完整工具清单 — 直接传给 LLM
# ═══════════════════════════════════════════════════════════════

ALL_TOOLS: List[Dict[str, Any]] = PAPER_SEARCH_TOOLS + ENTITY_TOOLS

# ═══════════════════════════════════════════════════════════════
# 工具名 → 函数映射（供 Agent 路由使用）
# ═══════════════════════════════════════════════════════════════

TOOL_FUNCTIONS = {}

try:
    from .entity.person import search_person
    TOOL_FUNCTIONS["search_person"] = search_person
except ImportError:
    pass

try:
    from .entity.org import search_org
    TOOL_FUNCTIONS["search_org"] = search_org
except ImportError:
    pass

try:
    from .entity.patent import search_patent
    TOOL_FUNCTIONS["search_patent"] = search_patent
except ImportError:
    pass

try:
    from .search_coordinator import search as search_papers_fn
    TOOL_FUNCTIONS["search_papers"] = search_papers_fn
except ImportError:
    pass
