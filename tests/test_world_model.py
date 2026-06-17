"""Tests for world_model — D₃ pre-search simulation, prediction, and adaptive learning."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.world_model import WorldModel, SearchPrediction


# ── WorldModel.predict() — depth switching ───────────────────

def test_predict_depth_switching_by_volume():
    """0/5/13→exhaustive, 20→classified, 200/300/500→satisficing."""
    wm = WorldModel()

    assert wm.predict("X", 0).predicted_depth == "exhaustive"
    assert wm.predict("X", 5).predicted_depth == "exhaustive"
    assert wm.predict("X", 13).predicted_depth == "exhaustive"
    assert wm.predict("X", 20).predicted_depth == "classified"
    assert wm.predict("X", 200).predicted_depth == "satisficing"
    assert wm.predict("X", 300).predicted_depth == "satisficing"
    assert wm.predict("X", 500).predicted_depth == "satisficing"

    # estimated_volume math check
    pred = wm.predict("Rare", 5)
    assert pred.estimated_volume == 7  # max(5, int(5/0.7))

    pred = wm.predict("Busy", 200)
    assert pred.estimated_volume > 200  # max(200, 285)


def test_predict_returns_valid_dataclass():
    wm = WorldModel()
    pred = wm.predict("Test", graph_known_count=10)
    assert isinstance(pred, SearchPrediction)
    assert 0.0 <= pred.confidence <= 1.0
    assert pred.predicted_tokens > 0
    assert pred.predicted_new_papers >= 0


# ── WorldModel.update() — adaptive parameter learning ────────

def test_update_discovery_rate_adapts():
    """Underestimated→increase; overestimated→decrease; clamped [0.05, 0.8]."""
    wm = WorldModel(); wm.discovery_rate = 0.3
    pred = wm.predict("T", 10)
    orig = wm.discovery_rate
    wm.update(pred, actual_papers=pred.predicted_new_papers * 3, actual_tokens=5000)
    assert wm.discovery_rate > orig  # ×1.1

    wm.discovery_rate = 0.3
    pred = wm.predict("T", 10)
    wm.update(pred, actual_papers=0, actual_tokens=0)
    assert wm.discovery_rate < 0.3  # ×0.95

    wm.discovery_rate = 0.06
    pred = wm.predict("T", 10)
    wm.update(pred, 0, 0)
    assert wm.discovery_rate >= 0.05  # lower clamp

    wm.discovery_rate = 0.79
    pred = wm.predict("T", 10)
    wm.update(pred, pred.predicted_new_papers * 100, 5000)
    assert wm.discovery_rate <= 0.8  # upper clamp


def test_update_token_per_paper_blends_and_no_div0():
    wm = WorldModel(); wm.token_per_paper = 250.0
    pred = wm.predict("T", 10)
    old = wm.token_per_paper
    wm.update(pred, actual_papers=5, actual_tokens=1000)
    expected = 0.7 * old + 0.3 * (1000 / 5)
    assert abs(wm.token_per_paper - expected) < 0.01

    wm.token_per_paper = 250.0
    pred = wm.predict("T", 10)
    wm.update(pred, 0, 0)
    assert wm.token_per_paper == 250.0  # unchanged


# ── prediction_accuracy — rolling accuracy ───────────────────

def test_prediction_accuracy():
    wm = WorldModel()
    assert wm.prediction_accuracy == 1.0  # no errors yet

    wm._prediction_errors = [0.5, 0.3]
    assert wm.prediction_accuracy < 1.0  # errors reduce accuracy

    wm._prediction_errors = [0.0, 0.0, 0.0]
    assert wm.prediction_accuracy == 1.0  # perfect predictions

    # Rolling window: only last 10 count
    wm._prediction_errors = [0.9] * 15
    assert abs(wm.prediction_accuracy - 0.1) < 0.01


def test_full_predict_update_cycle():
    """End-to-end: predict → update → error recorded."""
    wm = WorldModel()
    pred = wm.predict("Ochetobius_elongatus", graph_known_count=8)
    assert pred.predicted_depth == "exhaustive"
    wm.update(pred, actual_papers=pred.predicted_new_papers + 2,
              actual_tokens=pred.predicted_tokens)
    assert len(wm._prediction_errors) == 1
    assert 0.0 <= wm.prediction_accuracy <= 1.0
