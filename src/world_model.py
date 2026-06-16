"""
D₃ World Model — Pre-search simulation engine.
Gemini D₃: "Agent 在发出控制指令前，先在内部的体模型中进行仿真物理推演"
Predicts search outcome before execution, compares prediction vs actual, adapts.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchPrediction:
    estimated_volume: int
    predicted_depth: str          # "exhaustive" | "classified" | "satisficing"
    predicted_tokens: int
    predicted_new_papers: int
    confidence: float = 0.8       # 0.0-1.0


class WorldModel:
    """D₃ Body: Predicts search outcomes before execution, learns from errors."""

    def __init__(self):
        self.discovery_rate: float = 0.3     # avg new papers / known papers
        self.token_per_paper: float = 250    # avg tokens per paper found
        self._prediction_errors: list[float] = []

    def predict(self, species_id: str, graph_known_count: int,
                mode: str = "adaptive") -> SearchPrediction:
        """Predict search outcome before execution.

        Args:
            species_id: e.g. "Ochetobius_elongatus"
            graph_known_count: papers already in species_graph
            mode: adaptive | exhaustive | classified | satisficing

        Returns:
            SearchPrediction with estimated volume, depth, tokens, new papers
        """
        estimated_volume = max(
            graph_known_count,
            int(graph_known_count / (1 - self.discovery_rate))
        )

        if estimated_volume < 20:
            depth = "exhaustive"
            active_layers = 11
        elif estimated_volume <= 200:
            depth = "classified"
            active_layers = 6
        else:
            depth = "satisficing"
            active_layers = 4

        predicted_tokens = graph_known_count * self.token_per_paper * active_layers
        predicted_new = int(graph_known_count * self.discovery_rate * active_layers)

        return SearchPrediction(
            estimated_volume=estimated_volume,
            predicted_depth=depth,
            predicted_tokens=predicted_tokens,
            predicted_new_papers=predicted_new,
        )

    def update(self, prediction: SearchPrediction, actual_papers: int,
               actual_tokens: int):
        """Update world model parameters based on prediction error.

        Adaptive learning: discovery_rate and token_per_paper adjust
        based on the gap between predicted and actual.
        """
        paper_error = abs(prediction.predicted_new_papers - actual_papers)
        paper_error_rate = paper_error / max(prediction.predicted_new_papers, 1)
        self._prediction_errors.append(paper_error_rate)

        # Adaptive: adjust discovery_rate toward actual
        if actual_papers > prediction.predicted_new_papers:
            self.discovery_rate *= 1.1  # underestimated → increase
        else:
            self.discovery_rate *= 0.95  # overestimated → decrease
        self.discovery_rate = max(0.05, min(0.8, self.discovery_rate))

        # Adjust token_per_paper
        if actual_papers > 0:
            actual_token_rate = actual_tokens / actual_papers
            self.token_per_paper = 0.7 * self.token_per_paper + 0.3 * actual_token_rate

    @property
    def prediction_accuracy(self) -> float:
        """Rolling accuracy of last 10 predictions."""
        if not self._prediction_errors:
            return 1.0
        recent = self._prediction_errors[-10:]
        return 1.0 - sum(recent) / len(recent)


# Usage:
# wm = WorldModel()
# pred = wm.predict("Ochetobius_elongatus", graph_known_count=8)
# → SearchPrediction(estimated_volume=11, depth="exhaustive", tokens=22000, new=26)
# wm.update(pred, actual_papers=8, actual_tokens=18000)
# → discovery_rate adjusted from 0.3 → 0.285
