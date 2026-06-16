"""cognitive-search-engine — 多源物种文献搜索验证引擎 (V/V1)"""

__version__ = "5.8.0"

from .adapter import CognitiveSearchAdapter
from .meso_agent import create_agent, MesoAgent
from .unified_search import coordinated_search
from .agent_core import CognitiveAgent
from .rule_engine import SearchRuleEngine
from .mcp_client import McpClient
from .world_model import WorldModel
from .variant_generator import generate_variants

__all__ = [
    "CognitiveSearchAdapter",
    "create_agent",
    "MesoAgent",
    "coordinated_search",
    "CognitiveAgent",
    "SearchRuleEngine",
    "McpClient",
    "WorldModel",
    "generate_variants",
    "__version__",
]
