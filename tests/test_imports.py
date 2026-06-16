"""Import validation — verify all c项目 modules can be imported."""

import sys
import importlib


def test_all_modules_importable():
    """Every public module in src/ must import without errors."""
    modules = [
        "src._utils",
        "src.adapter",
        "src.agent_core",
        "src.mcp_client",
        "src.meso_agent",
        "src.parallel_search",
        "src.rule_engine",
        "src.search_coordinator",
        "src.unified_search",
        "src.validator",
        "src.variant_generator",
        "src.world_model",
        "src.credibility_scorer",
        "src.report_formatter",
        "src.evolution_executor",
        "src.inference_engine",
    ]
    failed = []
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            failed.append((mod_name, str(e)))
    assert not failed, f"Import failures:\n" + "\n".join(
        f"  ❌ {m}: {e}" for m, e in failed
    )


def test_dotdict_works():
    """DotDict attribute access must work."""
    from src._utils import DotDict

    d = DotDict({"a": {"b": {"c": 8}}})
    assert d.a.b.c == 8
    assert d["a"]["b"]["c"] == 8
    d.new_attr = 42
    assert d["new_attr"] == 42


def test_engine_registry_count():
    """ENGINE_REGISTRY must have ≥20 engines."""
    from src.unified_search import ENGINE_REGISTRY

    assert len(ENGINE_REGISTRY) >= 20, (
        f"Only {len(ENGINE_REGISTRY)} engines, expected ≥20"
    )


def test_engine_groups_have_chinese():
    """ENGINE_GROUPS must have chinese and preprint groups."""
    from src.unified_search import ENGINE_GROUPS

    assert "chinese" in ENGINE_GROUPS, "Missing chinese engine group"
    assert "preprint" in ENGINE_GROUPS, "Missing preprint engine group"


def test_kb_first_result():
    """KbFirstSearchResult must be constructable."""
    from src.search_coordinator import KbFirstSearchResult

    r = KbFirstSearchResult(stage="kb_check", species_name="test", kb_found=False)
    assert r.stage == "kb_check"
    assert "f项目" in r.ask_user_prompt()
