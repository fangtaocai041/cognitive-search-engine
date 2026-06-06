"""
Search Rule Engine — Load search_rules.yaml and execute phases.
Replaces natural-language Skill instructions with structured, machine-executable rules.
"""

import yaml
from pathlib import Path
from typing import Any

# ===== D₃ World Model import =====
try:
    from src.world_model import WorldModel
except ImportError:
    WorldModel = None  # graceful fallback

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
