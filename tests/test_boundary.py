"""test_boundary.py — boundary tests as pytest"""
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, _root)
sys.path.insert(0, str(Path(_root).parent))

from _bayesian import BetaBelief
from fangtao_fishlab import query_library, get_adapter, health_check_all
from _shared.pipeline import Pipeline, PipelineStep
from _shared.errors import safe_call


def test_beta_zero_params():
    b = BetaBelief(0, 0)
    assert 0 <= b.mean() <= 1

def test_beta_zero_update():
    b = BetaBelief(0, 0)
    b.update(successes=0, trials=0)

def test_query_library_missing_lib():
    r = query_library("nonexistent")
    assert r == []

def test_get_adapter_unknown():
    try:
        get_adapter("nonexistent")
        assert False, "should raise"
    except (ValueError, ImportError):
        pass

def test_get_adapter_cse():
    a = get_adapter("cognitive-search-engine")
    assert a.project_name == "cognitive-search-engine"

def test_pipeline_empty():
    p = Pipeline("t", [])
    r = p.run("q")
    assert isinstance(r, dict)

def test_health_check_runs():
    r = health_check_all()
    assert isinstance(r, dict)
    assert len(r) >= 5

def test_safe_call_retry():
    count = [0]
    def flaky():
        count[0] += 1
        if count[0] < 3:
            raise ConnectionError("t")
        return "ok"
    r = safe_call(flaky, error_type="transient")
    assert r == "ok"
    assert count[0] == 3

def test_safe_call_fatal():
    count = [0]
    def fatal():
        count[0] += 1
        raise RuntimeError("fatal")
    try:
        safe_call(fatal, error_type="fatal")
        assert False, "should raise"
    except Exception:  # safe_call wraps in AdapterError
        assert count[0] == 1  # no retry
