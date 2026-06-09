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
# KB-First 两阶段搜索入口 (f项目KB先查 → 询问 → c项目续搜)
# ═══════════════════════════════════════════════════════

def kb_first(species: str) -> "KbFirstSearchResult":
    """
    kb_first("珠星三块鱼") → KbFirstSearchResult (stage="kb_check")

    两阶段搜索 Stage 1: 先查 f项目 (fish-ecology-assistant) 知识库。
    返回 KbFirstSearchResult，调用方应呈现 ask_user_prompt() 给用户，
    然后根据用户选择决定是否调用 continue_full_search()。

    Usage:
      # Stage 1
      r = kb_first("珠星三块鱼")
      print(r.ask_user_prompt())
      # ... user says "continue" or "stay" ...

      # Stage 2 (only if user continues)
      r = continue_full_search(r, group="full")
      print(r.full_search.summary())
    """
    import sys
    mod = sys.modules.get("src.unified_search")
    if mod is not None:
        return mod.search_with_kb_first(species_name=species)
    from src.unified_search import search_with_kb_first
    return search_with_kb_first(species_name=species)


def continue_full_search(
    stage1_result: "KbFirstSearchResult",
    group: str = "full",
    limit: int = 10,
) -> "KbFirstSearchResult":
    """
    continue_full_search(stage1_result, group="full") → KbFirstSearchResult

    两阶段搜索 Stage 2: 在 KB 查询结果基础上，启动 c项目全量文献搜索。
    自动利用 KB 已知的异名/别名/变体来丰富搜索。

    Args:
        stage1_result: kb_first() 返回的 Stage 1 结果。
        group: 引擎组 ("quick"/"standard"/"full").
        limit: 每引擎最大结果数。

    Returns:
        同一 KbFirstSearchResult 对象，.stage 变为 "full_search"，
        .full_search 填充为 CoordinatedSearchResult。
    """
    import sys
    mod = sys.modules.get("src.unified_search")
    if mod is not None:
        return mod.continue_full_search(
            stage1_result=stage1_result, group=group, limit=limit)
    from src.unified_search import continue_full_search as cfs
    return cfs(stage1_result=stage1_result, group=group, limit=limit)


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
        KbFirstSearchResult,
    )
    return CoordinatedSearchResult, EngineResult, StreamEvent, SearchMode, KbFirstSearchResult


def __getattr__(name: str):
    """透明代理: 自动从 unified_search 导入缺失的属性。"""
    if name in ("CoordinatedSearchResult", "EngineResult", "StreamEvent", "SearchMode",
                "KbFirstSearchResult"):
        types = _get_result_types()
        idx = {"CoordinatedSearchResult": 0, "EngineResult": 1, "StreamEvent": 2,
               "SearchMode": 3, "KbFirstSearchResult": 4}
        return types[idx[name]]
    if name in ("kb_first", "continue_full_search"):
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
