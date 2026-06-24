"""
MesoAgent 配置与结果类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MesoConfig:
    """MesoAgent 运行配置."""
    mode: str = "http"               # http | direct (http 使用 MCP 工具; direct 用本地函数)
    max_tokens: int = 50000
    min_papers_satisfice: int = 8
    max_papers: int = 30
    timeout_s: int = 300
    enable_inference: bool = True     # 启用 P3 推理增强
    enable_evolution: bool = True     # 启用自进化
    enable_cross_validation: bool = True  # 启用跨项目验证
    enable_graph_update: bool = True  # 搜索后更新图谱
    verbose: bool = False


@dataclass
class MesoSearchResult:
    """MesoAgent.search() 的返回类型."""
    species_id: str = ""
    papers: List[Dict[str, Any]] = field(default_factory=list)
    new_papers: int = 0
    total_cost: int = 0          # token 消耗
    phase_count: int = 0
    stop_reason: str = ""
    errors: List[str] = field(default_factory=list)
    meso_log: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_s: float = 0.0
    mode_used: str = ""          # 实际使用的搜索模式
    volume_estimate: int = 0
    adaptations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "species_id": self.species_id,
            "papers": self.papers,
            "new_papers": self.new_papers,
            "total_cost": self.total_cost,
            "phase_count": self.phase_count,
            "stop_reason": self.stop_reason,
            "errors": self.errors,
            "elapsed_s": self.elapsed_s,
            "mode_used": self.mode_used,
            "volume_estimate": self.volume_estimate,
        }
