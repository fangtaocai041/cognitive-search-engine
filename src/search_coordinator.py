"""
SearchCoordinator — 统一物种搜索协调器 (委托层)

⚠️ 2026-06-09 重构: 所有核心搜索逻辑已迁移至 unified_search.coordinated_search()。
   此文件现为薄委托层，保留 JHU_AUTHORS / CN_JOURNALS 常量供外部引用。

架构:
  search_coordinator.search()
    → unified_search.coordinated_search()
      → check_taxonomy() → estimate_mode() → search_streaming()
      → aggregate_results() → classify + CN/EN + JHU → CoordinatedSearchResult

用法 (在本会话中直接使用):
  from src.search_coordinator import search
  result = search("鳤")  # 或 "Ochetobius elongatus" 或 "珠星三块鱼"
  print(result.summary())
"""

from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# 江汉大学课题组 — 论文优先级标记
# ═══════════════════════════════════════════════════════

JHU_AUTHORS = {
    "fei xiong", "熊飞",
    "hongyan liu", "刘红艳",
    "ying wang", "王莹",
    "fangtao cai", "蔡方陶",
    "dongdong zhai", "翟东东",
    "ziyue xu", "徐子悦",
    "ming xia", "夏明",
    "min zhou", "周敏",
    "wen zheng", "郑雯",
    "yuanyuan chen", "陈媛媛",
    "xinbin duan", "段辛斌",
    "huiwu tian", "田辉伍",
}

# 中文期刊白名单 (引用自 ZN_EN_RULES.md)
CN_JOURNALS = {
    "水生生物学报", "acta hydrobiologica sinica",
    "生物多样性", "biodiversity science",
    "中国水产科学", "journal of fishery sciences of china",
    "水产学报", "journal of fisheries of china",
    "湖泊科学", "journal of lake sciences",
    "南方水产科学", "south china fisheries science",
    "生态学报", "acta ecologica sinica",
    "生态科学", "ecological science",
}


# ═══════════════════════════════════════════════════════
# 搜索入口 — 委托给 unified_search.coordinated_search()
# ═══════════════════════════════════════════════════════

def search(species: str, group: str = "full", limit: int = 10):
    """
    search("鳤") → CoordinatedSearchResult

    委托给 unified_search.coordinated_search() — 单一入口点。
    支持中文名 ("珠星三块鱼") 和学名 ("Ochetobius elongatus")。

    优先使用 workspace.py 预加载的模块 (避免多项目 src/ 命名空间冲突)。
    """
    # 优先使用已注册的模块 (workspace.py 的预加载)
    import sys
    mod = sys.modules.get("src.unified_search")
    if mod is not None:
        return mod.coordinated_search(species_name=species, group=group, limit=limit)
    # 兜底: 标准 import (仅当单独在 cognitive-search-engine 目录运行时)
    from src.unified_search import coordinated_search
    return coordinated_search(species_name=species, group=group, limit=limit)


# ═══════════════════════════════════════════════════════
# 向后兼容: 保留旧数据类引用 (从 unified_search 重新导出)
# ═══════════════════════════════════════════════════════

def _get_result_types():
    """懒加载: 避免导入时的循环依赖。"""
    from src.unified_search import (
        CoordinatedSearchResult,
        EngineResult,
        StreamEvent,
        SearchMode,
    )
    return CoordinatedSearchResult, EngineResult, StreamEvent, SearchMode


def __getattr__(name: str):
    """透明代理: 自动从 unified_search 导入缺失的属性。"""
    if name in ("CoordinatedSearchResult", "EngineResult", "StreamEvent", "SearchMode"):
        types = _get_result_types()
        idx = {"CoordinatedSearchResult": 0, "EngineResult": 1, "StreamEvent": 2, "SearchMode": 3}
        return types[idx[name]]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
