"""
MesoAgent — 中宇宙协调层 (Mesocosm Orchestrator) package.

BDI 认知架构入口：
  Belief  (信念)  → 加载物种图谱 + 文献量估算
  Desire  (欲望)  → 规划搜索策略 (自适应模式选择)
  Intention (意图) → 多阶段搜索执行 + 验证 + 评分 + 图谱回写

用法:
    from src.meso_agent import MesoAgent, create_agent

    agent = MesoAgent(MesoConfig(mode="http"))
    result = agent.search("Pseudaspius_hakonensis")
"""

from __future__ import annotations

from ._config import MesoConfig, MesoSearchResult
from ._agent import MesoAgent
from ._factory import create_agent
from ._utils import _extract_papers, _normalize_paper, _dedup_papers

__all__ = [
    "MesoAgent",
    "MesoConfig",
    "MesoSearchResult",
    "create_agent",
    "_extract_papers",
    "_normalize_paper",
    "_dedup_papers",
]
