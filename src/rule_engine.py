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
        return self._safe_eval(condition, {**ctx, **self._builtins()})

    def _should_stop_global(self, ctx: dict) -> bool:
        """Check global stop conditions."""
        for sc in self.stop_conditions:
            if self._safe_eval(sc["condition"], {**ctx, **self._builtins()}):
                return True
        return False

    def _safe_eval(self, expr: str, namespace: dict) -> bool:
        """Safely evaluate a condition expression using AST whitelist.

        Only allows: Compare, BoolOp, UnaryOp(Not), Name, Constant,
        Call(to whitelisted functions), and safe operators.
        No attribute access, no comprehensions, no imports.
        """
        import ast

        # Whitelisted function names
        _SAFE_FUNCS = {"len", "any", "max", "min", "filter"}

        # Whitelisted operator types
        _SAFE_OPS = {
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Is, ast.IsNot, ast.In, ast.NotIn,
            ast.And, ast.Or,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
            ast.Not, ast.USub,
        }

        try:
            tree = ast.parse(expr.strip(), mode="eval")
        except SyntaxError:
            import logging
            logging.getLogger("cognitive.rule_engine").warning(
                "Invalid condition syntax: %s", expr
            )
            return False

        def _check(node):
            """Recursively validate AST node against whitelist."""
            if isinstance(node, ast.Expression):
                return _check(node.body)
            if isinstance(node, ast.Constant):
                return True
            if isinstance(node, ast.Name):
                return True
            if isinstance(node, ast.BoolOp):
                return all(_check(v) for v in node.values)
            if isinstance(node, ast.Compare):
                return _check(node.left) and all(_check(c) for c in node.comparators)
            if isinstance(node, ast.UnaryOp):
                if type(node.op) not in _SAFE_OPS:
                    return False
                return _check(node.operand)
            if isinstance(node, ast.BinOp):
                if type(node.op) not in _SAFE_OPS:
                    return False
                return _check(node.left) and _check(node.right)
            if isinstance(node, ast.Call):
                # Only allow calls to whitelisted function names
                if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
                    return all(_check(a) for a in node.args)
                return False
            if isinstance(node, ast.Subscript):
                # Allow dict access: config["key"]
                return True
            if isinstance(node, ast.Index):
                return _check(node.value)  # py<3.9 compat
            # Reject: Attribute, ListComp, DictComp, Lambda, etc.
            return False

        if not _check(tree):
            import logging
            logging.getLogger("cognitive.rule_engine").warning(
                "Unsafe condition rejected: %s", expr
            )
            return False

        # Now safe to eval with empty builtins + provided namespace
        try:
            return bool(eval(expr, {"__builtins__": {}}, namespace))
        except Exception:
            import logging
            logging.getLogger("cognitive.rule_engine").debug(
                "Condition evaluation failed: %s", expr, exc_info=True
            )
            return False

    def _execute_phase(self, name: str, phase: dict, ctx: dict) -> dict:
        """Execute a single phase. Stub — delegates to MCP tools in production."""
        fn = phase["function"]
        tools = phase.get("tools", [])
        # In production: call MCP tools, apply phase logic
        return {"phase": name, "function": fn, "tools_used": tools, "new_papers": []}

    def _builtins(self) -> dict:
        # Dynamic budget: read from workspace token_budget system
        try:
            from workspace import get_token_budget
            _budget = get_token_budget()
        except Exception:
            _budget = 150000  # fallback
        return {
            "len": len, "any": any, "max": max, "min": min, "filter": filter,
            "config": {
                "search": {"energy": {"min_papers_satisfice": 15, "max_total_tokens": _budget}}
            }
        }

    def get_adaptive_params(self) -> dict:
        """Return current adaptive parameter values."""
        return {k: v["value"] for k, v in self.adaptive.items()}


# ===== Usage =====
# engine = SearchRuleEngine("config/search_rules.yaml")
# result = engine.execute("Ochetobius_elongatus")
# → {"papers": [...], "tokens_spent": 2000, "phases_executed": ["graph_lookup","exact_search"], "efficiency": 4.0}
