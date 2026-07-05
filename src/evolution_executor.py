"""
Evolution Executor — Unified trigger detection and parameter adaptation engine.

Unifies the 7 evolution triggers across the Triangle Core (fish+cognitive+eon-core).
Reads per-project evolution.yaml configs, evaluates trigger conditions,
and writes back adapted parameters.

Triggers (from THREE_PROJECTS_EVOLUTION.md §5.1):
  T1: pipeline_failure     — single pipeline success rate < 60%
  T2: contradiction        — triangulation contradiction rate > 30%
  T3: emergence_noise      — new paper emergence rate > 35%
  T4: recall_drop          — recall rate < 85%
  T5: token_exceed         — token consumption > 10000/query (tuned for DeepSeek)
  T6: dead_end             — 3 consecutive routing failures
  T7: health_check_failure — project health check fails 2 consecutive times

Usage:
    from src.evolution_executor import EvolutionExecutor

    executor = EvolutionExecutor("config/evolution.yaml")
    metrics = {"pipeline_success_rate": 0.45, "recall_rate": 0.72, ...}
    actions = executor.evaluate_and_adapt(metrics)
    # actions: [{"trigger": "recall_drop", "action": "increase min_sources", ...}]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 涌现检测集成
try:
    import sys
    _eon_core_path = str(Path(__file__).resolve().parent.parent.parent / "eon-core" / "src")
    if _eon_core_path not in sys.path:
        sys.path.insert(0, _eon_core_path)
    from unified_emergence import EmergenceMonitor, DimensionalLevel
    _EMERGENCE_AVAILABLE = True
except ImportError:
    _EMERGENCE_AVAILABLE = False
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# ═══════════════════════════════════════════════════════════════
# Trigger Registry — All 7 quantified conditions
# ═══════════════════════════════════════════════════════════════

@dataclass
class Trigger:
    """A quantified evolution trigger."""
    id: str
    name: str
    condition: str                          # Human-readable condition
    metric_key: str                         # Which metric to check
    threshold: float                        # Threshold value
    comparator: str                         # "<" | ">" | "<=" | ">="
    consecutive_required: int = 3           # Consecutive sessions
    action: str = ""                        # What to do when triggered
    param_to_adjust: str = ""               # Which config parameter
    adjust_direction: str = "increase"      # "increase" | "decrease"
    adjust_amount: float = 1.0              # How much to adjust


# All 7 triggers with quantified conditions
TRIGGERS: list[Trigger] = [
    Trigger(
        id="T1", name="pipeline_failure",
        condition="pipeline_success_rate < 0.60 for 3 consecutive sessions",
        metric_key="pipeline_success_rate",
        threshold=0.60, comparator="<", consecutive_required=3,
        action="increase max_retry by 1",
        param_to_adjust="max_retry", adjust_direction="increase", adjust_amount=1,
    ),
    Trigger(
        id="T2", name="contradiction",
        condition="contradiction_rate > 0.30 for 3 consecutive sessions",
        metric_key="contradiction_rate",
        threshold=0.30, comparator=">", consecutive_required=3,
        action="increase contradiction_budget_multiplier by 0.5",
        param_to_adjust="contradiction_budget_multiplier",
        adjust_direction="increase", adjust_amount=0.5,
    ),
    Trigger(
        id="T3", name="emergence_noise",
        condition="new_paper_emergence_rate > 0.35 for 3 consecutive sessions",
        metric_key="new_paper_emergence_rate",
        threshold=0.35, comparator=">", consecutive_required=3,
        action="decrease emergence_threshold by 1 (raise bar)",
        param_to_adjust="emergence_threshold",
        adjust_direction="increase", adjust_amount=1,  # increase threshold = stricter
    ),
    Trigger(
        id="T4", name="recall_drop",
        condition="recall_rate < 0.85 for 3 consecutive sessions",
        metric_key="recall_rate",
        threshold=0.85, comparator="<", consecutive_required=3,
        action="increase verification_min_sources by 1",
        param_to_adjust="verification_min_sources",
        adjust_direction="increase", adjust_amount=1,
    ),
    Trigger(
        id="T5", name="token_exceed",
        condition="avg_tokens_per_query > 10000 for 3 consecutive sessions",
        metric_key="avg_tokens_per_query",
        threshold=10000, comparator=">", consecutive_required=3,
        action="decrease max_revision_rounds by 1",
        param_to_adjust="max_revision_rounds",
        adjust_direction="decrease", adjust_amount=1,
    ),
    Trigger(
        id="T6", name="dead_end",
        condition="consecutive_routing_failures >= 3",
        metric_key="consecutive_routing_failures",
        threshold=3, comparator=">=", consecutive_required=1,
        action="decrease dead_end_retreat_threshold by 1 (retreat earlier)",
        param_to_adjust="dead_end_retreat_threshold",
        adjust_direction="decrease", adjust_amount=1,
    ),
    Trigger(
        id="T7", name="health_check_failure",
        condition="health_check_failure_count >= 2 for consecutive checks",
        metric_key="health_check_failure_count",
        threshold=2, comparator=">=", consecutive_required=1,
        action="log CRITICAL alert + suggest project restart",
        param_to_adjust="",  # Manual action required
        adjust_direction="", adjust_amount=0,
    ),
]


# ═══════════════════════════════════════════════════════════════
# Evolution Executor
# ═══════════════════════════════════════════════════════════════

@dataclass
class AdaptationAction:
    """Record of a parameter adaptation."""
    trigger_id: str
    trigger_name: str
    param: str
    old_value: float
    new_value: float
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EvolutionExecutor:
    """Load evolution.yaml, evaluate triggers, adapt parameters, persist."""

    def __init__(self, config_path: str = "config/evolution.yaml"):
        self.config_path = Path(config_path)
        self.config: dict = {}
        self._history: list[dict] = []  # rolling metric history
        self._load_config()

    def _load_config(self):
        """Load evolution config from YAML."""
        if yaml is None:
            self.config = {}
            return
        if not self.config_path.exists():
            self.config = {}
            return
        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            self.config = {}

    def _feed_emergence(self, metrics: dict) -> None:
        """将搜索指标送入涌现检测引擎."""
        if not _EMERGENCE_AVAILABLE:
            return
        try:
            mon = EmergenceMonitor()
            for key, val in metrics.items():
                if isinstance(val, (int, float)):
                    mon.record(f"c_{key}", val, DimensionalLevel.D1)
            signals = mon.check_emergence()
            if signals:
                logger.info(f"涌现信号: {len(signals)} 个")
        except Exception:
            pass

    def evaluate_and_adapt(self, metrics: dict) -> list[AdaptationAction]:
        """Evaluate all 7 triggers against current metrics and adapt parameters.

        Args:
            metrics: dict with keys matching Trigger.metric_key, e.g.:
                {"pipeline_success_rate": 0.45, "recall_rate": 0.72, ...}

        Returns:
            List of AdaptationAction records for triggered adaptations.
        """
        if not self.config.get("evolution", {}).get("enabled", False):
            return []

        # Record this session's metrics
        self._history.append({"timestamp": datetime.now().isoformat(), **metrics})
        if len(self._history) > 20:  # keep rolling window
            self._history = self._history[-20:]

        actions = []

        for trigger in TRIGGERS:
            if trigger.param_to_adjust == "":
                # T7: health check failure — manual action, log only
                if self._evaluate_trigger(trigger):
                    actions.append(AdaptationAction(
                        trigger_id=trigger.id,
                        trigger_name=trigger.name,
                        param="",
                        old_value=0,
                        new_value=0,
                        reason=f"CRITICAL: {trigger.condition} — manual intervention required",
                    ))
                continue

            if self._evaluate_trigger(trigger):
                action = self._adapt_parameter(trigger)
                if action:
                    actions.append(action)

        # Feed metrics to emergence engine
        self._feed_emergence(metrics)

        # Persist changes
        if actions:
            self._persist_config()

        return actions

    def _evaluate_trigger(self, trigger: Trigger) -> bool:
        """Check if a trigger condition is met over the required consecutive window."""
        if len(self._history) < trigger.consecutive_required:
            return False

        # Check the last N sessions
        recent = self._history[-trigger.consecutive_required:]
        values = [s.get(trigger.metric_key) for s in recent]
        if any(v is None for v in values):
            return False

        for v in values:
            if trigger.comparator == "<" and not (v < trigger.threshold):
                return False
            elif trigger.comparator == ">" and not (v > trigger.threshold):
                return False
            elif trigger.comparator == "<=" and not (v <= trigger.threshold):
                return False
            elif trigger.comparator == ">=" and not (v >= trigger.threshold):
                return False

        return True  # All N consecutive sessions met the condition

    def _adapt_parameter(self, trigger: Trigger) -> Optional[AdaptationAction]:
        """Apply the parameter adaptation from a triggered condition."""
        adaptive_params = (
            self.config.get("evolution", {})
            .get("adaptive_params", {})
        )

        if trigger.param_to_adjust not in adaptive_params:
            # Try alternative path (fish/porpoise use different config structure)
            adaptive_params = self.config.get("evolution", {}).get("adaptive_params", {})
            if trigger.param_to_adjust not in adaptive_params:
                return None

        param_config = adaptive_params[trigger.param_to_adjust]
        old_value = param_config.get("current", param_config.get("value", 0))
        param_range = param_config.get("range", [0, 100])

        # Calculate new value
        if trigger.adjust_direction == "increase":
            new_value = old_value + trigger.adjust_amount
        elif trigger.adjust_direction == "decrease":
            new_value = old_value - trigger.adjust_amount
        else:
            return None

        # Clamp to range
        new_value = max(param_range[0], min(param_range[1], new_value))

        if new_value == old_value:
            return None  # No change

        # Update in memory
        if "current" in param_config:
            param_config["current"] = new_value
        else:
            param_config["value"] = new_value
        param_config["last_adjusted"] = datetime.now().isoformat()

        return AdaptationAction(
            trigger_id=trigger.id,
            trigger_name=trigger.name,
            param=trigger.param_to_adjust,
            old_value=old_value,
            new_value=new_value,
            reason=f"{trigger.condition} → {trigger.action}",
        )

    def _persist_config(self):
        """Write adapted parameters back to evolution.yaml."""
        if yaml is None:
            return
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            pass  # Non-critical — adaptation still in memory

    def get_trigger_status(self, metrics: dict) -> list[dict]:
        """Get the current status of all 7 triggers without adapting."""
        status = []
        for trigger in TRIGGERS:
            value = metrics.get(trigger.metric_key)
            triggered = self._evaluate_trigger(trigger) if value is not None else None
            status.append({
                "id": trigger.id,
                "name": trigger.name,
                "current_value": value,
                "threshold": trigger.threshold,
                "comparator": trigger.comparator,
                "triggered": triggered,
                "consecutive_checked": min(len(self._history), trigger.consecutive_required),
            })
        return status


# ═══════════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════════

def check_all_triggers(evolution_config_path: str, metrics: dict) -> dict:
    """One-liner: load config, evaluate triggers, return summary.

    Returns:
        {"triggered": ["recall_drop", "token_exceed"],
         "adaptations": [{"param": "min_sources", "old": 3, "new": 4}, ...],
         "all_clear": False}
    """
    executor = EvolutionExecutor(evolution_config_path)
    actions = executor.evaluate_and_adapt(metrics)
    return {
        "triggered": [a.trigger_name for a in actions],
        "adaptations": [
            {"param": a.param, "old": a.old_value, "new": a.new_value}
            for a in actions if a.param
        ],
        "all_clear": len(actions) == 0,
        "alerts": [
            a.reason for a in actions if not a.param
        ],
    }
