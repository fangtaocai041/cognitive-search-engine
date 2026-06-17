"""测试骨架 — cognitive-search-engine 核心模块。"""

import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ))


def test_version():
    from src import __version__
    assert __version__ >= "5.0.0"


def test_graph_loads():
    import yaml
    graph = yaml.safe_load(open(PROJ / "config" / "species_graph.yaml", encoding="utf-8"))
    assert "graph" in graph
    assert "species" in graph["graph"]
    assert len(graph["graph"]["species"]) >= 80


def test_search_rules_loads():
    import yaml
    rules = yaml.safe_load(open(PROJ / "config" / "search_rules.yaml", encoding="utf-8"))
    assert "phases" in rules
