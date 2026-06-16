"""
Search Rule Engine — Load search_rules.yaml and execute phases.

⚠️ DEPRECATED (v5.9+): Not used by the active search pipeline.
    MesoAgent.search() → ParallelSearch (direct HTTP) is the actual engine.
    SearchRuleEngine was the v4.x phase-based engine, superseded by the
    coordinated_search() + search_streaming() model in unified_search.py.
    KEPT for reference only — may be removed in v6.0.
"""

import yaml
from pathlib import Path
from typing import Any

# ===== Rule Engine =====

class SearchRuleEngine:
    """Load search_rules.yaml → execute phases → return papers."""

    def __init__(self, config_path: str = "config/search_rules.yaml"):
        with open(config_path) as f:
            self.rules = yaml.safe_load(f)
        self.phases = self.rules["phases"]
        self.stop_conditions = self.rules["stop_conditions"]["global"]
        self.adaptive = self.rules["adaptive_params"]
        self._all_papers: list[dict] = []
        self._tokens_spent: int = 0
        self._consecutive_zero: int = 0

    def execute(self, species_id: str) -> dict[str, Any]:
        """Execute all active phases, respecting stop conditions and budget."""
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

        return {
            "papers": self._all_papers,
            "tokens_spent": self._tokens_spent,
            "phases_executed": phases_executed,
            "efficiency": len(self._all_papers) / max(self._tokens_spent / 1000, 1),
        }

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
        """Execute a single phase. Stub — delegates to MCP tools in production."""
        fn = phase["function"]
        tools = phase.get("tools", [])
        # In production: call MCP tools, apply phase logic
        return {"phase": name, "function": fn, "tools_used": tools, "new_papers": []}

    def _builtins(self) -> dict:
        return {
            "len": len, "any": any, "max": max, "min": min, "filter": filter,
            "config": {
                "search": {"energy": {"min_papers_satisfice": 8, "max_total_tokens": 50000}}
            }
        }

    def get_adaptive_params(self) -> dict:
        """Return current adaptive parameter values."""
        return {k: v["value"] for k, v in self.adaptive.items()}


# ===== Usage =====
# engine = SearchRuleEngine("config/search_rules.yaml")
# result = engine.execute("Ochetobius_elongatus")
# → {"papers": [...], "tokens_spent": 2000, "phases_executed": ["graph_lookup","exact_search"], "efficiency": 4.0}
