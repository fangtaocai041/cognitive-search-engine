"""cognitive-search-engine — 多源物种文献搜索验证引擎 (V/V1)"""

import os
import sys as _sys
from pathlib import Path
from typing import Optional as _Optional

# ── Ensure self-imports resolve correctly when imported cross-project ──
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in _sys.path:
    _sys.path.insert(0, _PROJECT_ROOT)

# ── .env auto-loader ──────────────────────────────────────────
# Loads .env into os.environ before any MCP subprocess is spawned.
# MCP servers (scholar, article, exa, etc.) inherit os.environ,
# so their API keys must be in the environment at process start.


def _load_dotenv(path: _Optional[str] = None) -> None:
    """Minimal .env loader — no extra dependency.

    Rules:
      - Lines starting with # are comments.
      - Lines without = are skipped.
      - Only sets keys that aren't already in os.environ.
      - Cascades: project .env → parent .env (D:\\Reasonix\\.env)
    """
    if path is None:
        here = Path(__file__).resolve().parent.parent  # cognitive-search-engine/
        paths = [str(here / ".env"), str(here.parent / ".env")]  # cascade
    else:
        paths = [path]

    for p in paths:
        env_file = Path(p)
        if not env_file.exists():
            continue
        try:
            with open(env_file, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key and key not in os.environ and val and val != f"your_{key.lower()}_here":
                        os.environ[key] = val
        except OSError:
            pass


_load_dotenv()

__version__ = "5.9.0"

from .adapter import CognitiveSearchAdapter
from .meso_agent import create_agent, MesoAgent
from .mcp_client import McpClient, get_client
from .world_model import WorldModel
from .unified_search import check_taxonomy, detect_taxonomy_discrepancy, estimate_mode, classify_paper
# v5.9+: 死代码复活 — 导出新接入模块
from .agent_judge import AgentJudge
from .mpc_world import MPCWorldModel, MPCPlan
from .catalog_loader import load_catalog, graph_route, score_domains, record_search_result, compare_routing
from .report_formatter import generate_quick_report, classify_papers, format_report
from .search_engine import CognitiveSearchEngine
from .rcca_core import SelfModelEngine, EmotionEngine, TranspositionLayer, ReflectionLoop

__all__ = [
    "CognitiveSearchAdapter",
    "create_agent",
    "MesoAgent",
    "McpClient",
    "get_client",
    "WorldModel",
    "check_taxonomy",
    "detect_taxonomy_discrepancy",
    "estimate_mode",
    "classify_paper",
    # v5.9+: 死代码复活
    "AgentJudge",
    "MPCWorldModel",
    "MPCPlan",
    "load_catalog",
    "graph_route",
    "score_domains",
    "record_search_result",
    "compare_routing",
    "generate_quick_report",
    "classify_papers",
    "format_report",
    "CognitiveSearchEngine",
    "SelfModelEngine",
    "EmotionEngine",
    "TranspositionLayer",
    "ReflectionLoop",
    "__version__",
]
