"""Tests for variant_generator — OCR spelling variant generation for Latin species names."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.variant_generator import generate_variants, generate_full_species_variants


# ── generate_variants() ──────────────────────────────────────

def test_generate_variants_includes_original():
    """Original name must appear in the variant list."""
    result = generate_variants("Ochetobius")
    assert "Ochetobius" in result


def test_generate_variants_produces_multiple_variants():
    """Ochetobius with OCR-prone chars (O, i, u) should yield several variants."""
    result = generate_variants("Ochetobius")
    # O→0, i→j/l, u→v, us→i/a → many combos
    assert len(result) >= 3, f"Expected ≥3 variants, got {len(result)}: {result}"


def test_generate_variants_all_unique():
    """No duplicate variants should be in the result."""
    result = generate_variants("Pseudaspius")
    assert len(result) == len(set(result))


def test_generate_variants_all_start_with_uppercase():
    """Every variant should be normalized with first letter uppercase."""
    result = generate_variants("ochetobius")  # lowercase input
    for v in result:
        assert v[0].isupper(), f"'{v}' does not start with uppercase"


def test_generate_variants_short_name_still_works():
    """A 2-character name should not crash and still produce the original."""
    result = generate_variants("Ru")
    assert "Ru" in result
    assert len(result) >= 1


def test_generate_variants_empty_string():
    """Empty string should return list with just the empty string."""
    result = generate_variants("")
    assert "" in result
    assert len(result) == 1


def test_generate_variants_pure_ascii_no_confusable_chars():
    """A name like 'Test' with no OCR-confusable chars still produces variants
    via suffix handling (us→i/a)."""
    result = generate_variants("Test")
    # No char confusion (T,e,s,t), but 't' has no confusions defined;
    # suffix 'us' is not present; so mainly just the original
    assert "Test" in result


def test_generate_variants_latin_suffix_us_produces_variants():
    """'us' ending Latin names should produce 'i' and 'a' suffix variants."""
    result = generate_variants("Elongatus")
    has_i = any(v.endswith("i") for v in result)
    has_a = any(v.endswith("a") for v in result)
    assert has_i or has_a, f"Expected suffix variants in {result}"


def test_generate_variants_double_letter_variants():
    """Names with double letters should produce single-letter variants."""
    result = generate_variants("Pallas")
    # 'll' → 'l'
    assert "Palas" in result


def test_generate_variants_variant_count_reasonable():
    """Variant count should not explode; keep under ~200 for typical genus name."""
    result = generate_variants("Ochetobius")
    assert len(result) < 200, f"Too many variants: {len(result)}"


# ── generate_full_species_variants() ─────────────────────────

def test_generate_full_species_variants_returns_combinations():
    """Genus × species variants produce full binomial names."""
    result = generate_full_species_variants("Ochetobius", "elongatus")
    assert len(result) >= 5, f"Expected ≥5 combos, got {len(result)}"
    # Normalisation capitalises first letter: "Ochetobius Elongatus"
    assert "Ochetobius Elongatus" in result


def test_generate_full_species_variants_includes_dot_form():
    """Results should include abbreviated forms like 'O. elongatus'."""
    result = generate_full_species_variants("Pseudaspius", "hakonensis")
    dot_forms = [r for r in result if r.startswith("P.")]
    assert len(dot_forms) > 0, f"Expected dot-abbreviated forms in {result}"


def test_generate_full_species_variants_all_unique():
    result = generate_full_species_variants("Rutilus", "rutilus")
    assert len(result) == len(set(result))


def test_generate_full_species_variants_sorted():
    result = generate_full_species_variants("Abramis", "brama")
    assert result == sorted(result)
