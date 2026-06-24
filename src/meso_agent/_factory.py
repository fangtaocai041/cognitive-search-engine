"""
MesoAgent 工厂函数。
"""

from __future__ import annotations

from typing import Any

from ._config import MesoConfig
from ._agent import MesoAgent


def create_agent(mode: str = "http", **kwargs) -> MesoAgent:
    """创建 MesoAgent 实例的工厂函数.

    Args:
        mode: "http" (使用 MCP 工具) 或 "direct" (使用本地搜索协调器)
        **kwargs: 传给 MesoConfig 的额外参数

    Returns:
        MesoAgent 实例
    """
    config = MesoConfig(mode=mode, **kwargs)
    return MesoAgent(config)
