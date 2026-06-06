"""
Search Rule Engine — Load search_rules.yaml and execute phases.
Replaces natural-language Skill instructions with structured, machine-executable rules.

v4.1: +7-engine tool registry (ncbi+scholar+article+scholarly+tavily+exa+web_search)
"""

import yaml
from pathlib import Path
from typing import Any

# ===== D₃ World Model import =====
try:
    from src.world_model import WorldModel
except ImportError:
    WorldModel = None  # graceful fallback

# ===== 7-Engine Tool Registry (v4.1) =====
TOOL_REGISTRY: dict[str, dict] = {
    # 免费学术引擎
    "ncbi": {
        "server": "ncbi",
        "tools": ["ncbi_ncbi_esearch", "ncbi_ncbi_esummary", "ncbi_ncbi_efetch"],
        "requires_api_key": False,
        "category": "academic",
    },
    "scholar": {
        "server": "scholar",
        "tools": ["scholar_search_literature_graph", "scholar_search_google_scholar_key_words"],
        "requires_api_key": False,
        "category": "academic",
    },
    "article": {
        "server": "article",
        "tools": ["article_search_literature", "article_get_article_details", "article_get_references"],
        "requires_api_key": False,
        "category": "academic",
    },
    "scholarly": {
        "server": "scholarly",
        "tools": ["scholarly_search"],
        "requires_api_key": False,
        "category": "academic",
    },
    # 付费网络搜索
    "tavily": {
        "server": "tavily",
        "tools": ["tavily_search", "tavily_extract"],
        "requires_api_key": True,
        "category": "web",
        "env_var": "TAVILY_API_KEY",
    },
    "exa": {
        "server": "exa",
        "tools": ["exa_web_search"],
        "requires_api_key": True,
        "category": "web",
        "env_var": "EXA_API_KEY",
    },
    # 内置引擎
    "web_search": {
        "server": "reasonix_builtin",
        "tools": ["web_search", "web_fetch"],
        "requires_api_key": False,
        "category": "builtin",
    },
}

# Flattened list of all search tool names for availability checks
ALL_SEARCH_TOOLS = [tool for engine in TOOL_REGISTRY.values() for tool in engine["tools"]]

# Free vs paid classification
FREE_SEARCH_TOOLS = [tool for engine in TOOL_REGISTRY.values() if not engine["requires_api_key"] for tool in engine["tools"]]
PAID_SEARCH_TOOLS = [tool for engine in TOOL_REGISTRY.values() if engine["requires_api_key"] for tool in engine["tools"]]

# Fallback chain by priority
FALLBACK_CHAIN_ACADEMIC = ["scholar", "article", "scholarly", "ncbi", "web_search"]
FALLBACK_CHAIN_WEB = ["tavily", "exa", "web_search"]

# ===== Rule Engine =====

class SearchRuleEngine:
    """Load search_rules.yaml → execute phases → return papers.

    v4.1: 7-engine parallel with TOOL_REGISTRY for tool discovery and fallback.
    """

    def __init__(self, config_path: str = "config/search_rules.yaml"):
        with open(config_path) as f:
            self.rules = yaml.safe_load(f)
        self.phases = self.rules["phases"]
        self.stop_conditions = self.rules["stop_conditions"]["global"]
        self.adaptive = self.rules["adaptive_params"]
        self._all_papers: list[dict] = []
        self._tokens_spent: int = 0
        self._consecutive_zero: int = 0
        # ===== D₃ World Model =====
        self._world_model = WorldModel() if WorldModel else None

    def execute(self, species_id: str) -> dict[str, Any]:
        """Execute all active phases, respecting stop conditions and budget."""
        # ===== D₃: Pre-search World Model prediction =====
        prediction = None
        if self._world_model:
            prediction = self._world_model.predict(species_id, graph_known_count=0)

        context = {"species_id": species_id, "all_papers": self._all_papers}
        phases_executed = []

        for name, phase in sorted(self.phases.items(), key=lambda x: x[1]["priority"]):
            if not self._should_activate(phase, context):
                continue
            if self._should_stop_global(context):
                break

            result = self._execute_phase(name, phase, context)
            phases_executed.append(name)
            self._tokens_spent += phase.get("budget", 0)

            if result.get("new_papers"):
                self._all_papers.extend(result["new_papers"])
                self._consecutive_zero = 0
            else:
                self._consecutive_zero += 1

        result = {
            "papers": self._all_papers,
            "tokens_spent": self._tokens_spent,
            "phases_executed": phases_executed,
            "efficiency": len(self._all_papers) / max(self._tokens_spent / 1000, 1),
        }

        # ===== D₃: Update World Model with actual results =====
        if prediction and self._world_model:
            self._world_model.update(prediction, len(self._all_papers), self._tokens_spent)
            result["world_model"] = {
                "predicted_volume": prediction.estimated_volume,
                "predicted_tokens": prediction.predicted_tokens,
                "accuracy": round(self._world_model.prediction_accuracy, 2),
            }

        return result

    def _should_activate(self, phase: dict, ctx: dict) -> bool:
        """Check activation condition. None = always active."""
        condition = phase.get("activation")
        if condition is None:
            return True
        return eval(condition, {"__builtins__": {}}, {**ctx, **self._builtins()})

    def _should_stop_global(self, ctx: dict) -> bool:
        """Check global stop conditions."""
        for sc in self.stop_conditions:
            if eval(sc["condition"], {"__builtins__": {}}, {**ctx, **self._builtins()}):
                return True
        return False

    def _execute_phase(self, name: str, phase: dict, ctx: dict) -> dict:
        """Execute a single phase. Stub — delegates to MCP tools in production.

        v4.1: Resolves tool names via TOOL_REGISTRY. In production, calls the
        actual MCP tools; here returns stub for testing.
        """
        fn = phase["function"]
        tools = phase.get("tools", [])
        # Resolve which engines provide these tools
        resolved_engines = []
        for tool_name in tools:
            for engine_name, engine_spec in TOOL_REGISTRY.items():
                if tool_name in engine_spec["tools"]:
                    resolved_engines.append(engine_name)
                    break
        resolved_engines = list(dict.fromkeys(resolved_engines))  # dedup preserve order
        # In production: call MCP tools, apply phase logic
        return {
            "phase": name,
            "function": fn,
            "tools_used": tools,
            "engines_used": resolved_engines,
            "new_papers": [],
        }

    def get_available_engines(self, api_keys: dict[str, bool]) -> dict[str, list[str]]:
        """Check which engines are available given API key status.

        api_keys: {"TAVILY_API_KEY": True, "EXA_API_KEY": True} etc.
        Returns: {"free": [...], "paid": [...], "all": [...]}
        """
        free = [name for name, spec in TOOL_REGISTRY.items()
                if not spec["requires_api_key"]]
        paid = [name for name, spec in TOOL_REGISTRY.items()
                if spec["requires_api_key"] and api_keys.get(spec.get("env_var", ""), False)]
        return {"free": free, "paid": paid, "all": free + paid}

    def _builtins(self) -> dict:
        return {
            "len": len, "any": any, "max": max, "min": min, "filter": filter,
            "config": {
                "search": {
                    "energy": {"min_papers_satisfice": 8, "max_total_tokens": 50000},
                    "engines": {
                        "free": FREE_SEARCH_TOOLS,
                        "paid": PAID_SEARCH_TOOLS,
                        "all": ALL_SEARCH_TOOLS,
                    },
                }
            },
        }

    def get_adaptive_params(self) -> dict:
        """Return current adaptive parameter values."""
        return {k: v["value"] for k, v in self.adaptive.items()}


# ===== Usage v4.1 =====
# engine = SearchRuleEngine("config/search_rules.yaml")
# result = engine.execute("Ochetobius_elongatus")
# → {
#     "papers": [...],
#     "tokens_spent": 2000,
#     "phases_executed": ["graph_lookup","exact_search","variant_search"],
#     "efficiency": 4.0,
#     "world_model": {"predicted_volume": 8, "predicted_tokens": 3000, "accuracy": 0.85},
#   }
#
# # Check engine availability:
# engine.get_available_engines({"TAVILY_API_KEY": True})
# → {"free": ["ncbi","scholar","article","scholarly","web_search"], "paid": ["tavily"], "all": [...]}
