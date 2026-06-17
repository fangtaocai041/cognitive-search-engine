"""MPCWorldModel — Model Predictive Control for search cost optimization.

Replaces heuristic D3 prediction with MPC:
  - Predict: estimate papers found + token cost for each engine combo
  - Optimize: minimize (cost × time) subject to coverage constraints
  - Replan: update prediction based on actual results

Usage:
    mpc = MPCWorldModel()
    engines, predicted = mpc.plan(query, available_engines, budget_tokens=5000)
    actual = search(engines)
    mpc.update(actual)  # Learn from error
"""

from dataclasses import dataclass, field
from typing import Dict, List
import json, os, logging

logger = logging.getLogger(__name__)


@dataclass
class EngineModel:
    papers_per_query: float = 10.0
    tokens_per_paper: float = 200.0
    success_rate: float = 0.9
    avg_latency_ms: float = 500.0

@dataclass
class MPCPlan:
    engines: List[str]
    predicted_papers: int
    predicted_tokens: int
    predicted_cost: float
    confidence: float


class MPCWorldModel:
    """Model Predictive Control for search planning."""

    def __init__(self, state_file: str = None):
        self._models: Dict[str, EngineModel] = {}
        self._state_file = state_file or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'mpc_state.json')
        self._load()

    def plan(self, query: str, available: List[str],
             max_papers: int = 50, budget_tokens: int = 5000) -> MPCPlan:
        """MPC optimization: select engines to maximize coverage within budget."""
        candidates = []
        for engine in available:
            model = self._models.get(engine, EngineModel())
            expected_papers = min(model.papers_per_query, max_papers)
            expected_tokens = expected_papers * model.tokens_per_paper
            efficiency = expected_papers / max(expected_tokens, 1) * model.success_rate
            candidates.append((engine, expected_papers, expected_tokens, efficiency))

        # Greedy selection within budget
        selected = []
        total_tokens = 0
        total_papers = 0
        for engine, papers, tokens, eff in sorted(candidates, key=lambda x: x[3], reverse=True):
            if total_tokens + tokens > budget_tokens:
                break
            selected.append(engine)
            total_tokens += int(tokens)
            total_papers += int(papers)

        return MPCPlan(
            engines=selected,
            predicted_papers=total_papers,
            predicted_tokens=total_tokens,
            predicted_cost=total_tokens * 0.0001,  # ~$0.0001/token
            confidence=0.7 + 0.05 * len(selected)
        )

    def update(self, engine: str, actual_papers: int, actual_tokens: int, success: bool):
        """Update engine model from actual results (learning)."""
        if engine not in self._models:
            self._models[engine] = EngineModel()

        m = self._models[engine]
        m.papers_per_query = m.papers_per_query * 0.8 + actual_papers * 0.2
        m.tokens_per_paper = m.tokens_per_paper * 0.8 + (actual_tokens / max(actual_papers, 1)) * 0.2
        m.success_rate = m.success_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self._save()

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            data = {e: {'ppq': m.papers_per_query, 'tpp': m.tokens_per_paper,
                        'sr': m.success_rate, 'lat': m.avg_latency_ms}
                    for e, m in self._models.items()}
            with open(self._state_file, 'w') as f:
                json.dump(data, f)
        except: pass

    def _load(self):
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file) as f:
                    data = json.load(f)
                for e, d in data.items():
                    self._models[e] = EngineModel(
                        papers_per_query=d.get('ppq', 10),
                        tokens_per_paper=d.get('tpp', 200),
                        success_rate=d.get('sr', 0.9))
        except: pass
