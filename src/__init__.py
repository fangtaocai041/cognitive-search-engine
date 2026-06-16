"""cognitive-search-engine — 多源物种文献搜索验证引擎 (V/V1)"""

__version__ = "5.8.0"

from .adapter import CognitiveSearchAdapter
from .meso_agent import create_agent, MesoAgent
from .rule_engine import SearchRuleEngine
from .mcp_client import McpClient, get_client
from .world_model import WorldModel

__all__ = [
    "CognitiveSearchAdapter",
    "create_agent",
    "MesoAgent",
    "SearchRuleEngine",
    "McpClient",
    "get_client",
    "WorldModel",
    "__version__",
]
