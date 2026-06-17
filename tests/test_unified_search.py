"""Tests for unified_search — adaptive mode, incidental filtering, classification, CN/EN labeling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.unified_search import (
    estimate_mode, is_incidental, classify_paper, cn_en_label,
    SearchMode, PaperCategory,
)


# ── estimate_mode() ──────────────────────────────────────────

def test_estimate_mode_conservation_driven():
    """CR<20→EXHAUSTIVE(100), EN/VU<50→EXHAUSTIVE(50), 20-100→CLASSIFIED(40), >100→REVIEW_ANCHORED(30)."""
    d = estimate_mode("Ochetobius elongatus", "CR", 12)
    assert d.mode == SearchMode.EXHAUSTIVE and d.include_incidental and d.max_papers == 100

    d = estimate_mode("EN fish", "EN", 30)
    assert d.mode == SearchMode.EXHAUSTIVE and d.max_papers == 50

    d = estimate_mode("VU fish", "VU", 45)
    assert d.mode == SearchMode.EXHAUSTIVE

    d = estimate_mode("Medium", "NT", 60)
    assert d.mode == SearchMode.CLASSIFIED and not d.include_incidental and d.max_papers == 40

    d = estimate_mode("Common", "LC", 150)
    assert d.mode == SearchMode.REVIEW_ANCHORED and d.max_papers == 30


def test_estimate_mode_boundaries_and_hot_species():
    """Boundary values: 20/100→CLASSIFIED, 101→REVIEW_ANCHORED.
    Hot species (Cyprinus carpio) with >500→SATURATED."""
    assert estimate_mode("X", "LC", 20).mode == SearchMode.CLASSIFIED
    assert estimate_mode("X", "LC", 100).mode == SearchMode.CLASSIFIED
    assert estimate_mode("X", "LC", 101).mode == SearchMode.REVIEW_ANCHORED

    d = estimate_mode("Cyprinus carpio", "LC", 600)
    assert d.mode == SearchMode.SATURATED and not d.include_incidental
    # Hot species but low volume → NOT saturated
    assert estimate_mode("Cyprinus carpio", "LC", 400).mode != SearchMode.SATURATED


# ── is_incidental() ──────────────────────────────────────────

def test_is_incidental_core_vs_incidental():
    """Genetic keywords→core; feed/material keywords→incidental; short title→incidental."""
    inc, reason = is_incidental({"title": "Genetic diversity of Ochetobius elongatus"})
    assert not inc and "核心" in reason

    inc, reason = is_incidental({"title": "Growth performance of carp fed with hydrolysate"})
    assert inc and "附带" in reason

    inc, reason = is_incidental({"title": "Fish survey 2020"})
    assert inc and "标题过短" in reason

    # species_in_title flag overrides
    inc, reason = is_incidental({
        "title": "Some observation on fish behavior in Yangtze River",
        "species_in_title": True,
    })
    assert not inc

    # Default: no keywords, long title → core
    inc, _ = is_incidental({"title": "A comprehensive study of freshwater fish ecology in Asia"})
    assert not inc


# ── classify_paper() ─────────────────────────────────────────

def test_classify_paper_all_categories():
    """Each PaperCategory gets at least one keyword match; unmatched→ECOLOGY."""
    cases = [
        ("Population genetic structure and microsatellite analysis", PaperCategory.GENETICS),
        ("Chromosome-level genome assembly of a new species", PaperCategory.GENOMICS),
        ("Geometric morphometric analysis of body shape", PaperCategory.MORPHOLOGY),
        ("Fish resource abundance and CPUE trends", PaperCategory.ECOLOGY),
        ("Conservation strategies for endangered fish", PaperCategory.CONSERVATION),
        ("Heavy metal accumulation and pollution effects", PaperCategory.TOXICOLOGY),
        ("Larval rearing and hatchery techniques", PaperCategory.AQUACULTURE),
    ]
    for title, expected in cases:
        assert classify_paper({"title": title}) == expected, f"Failed: {title}"

    # Default
    assert classify_paper({"title": "A novel approach to data analysis"}) == PaperCategory.ECOLOGY
    # Abstract match
    assert classify_paper({"title": "Overview", "abstract": "microsatellite markers"}) == PaperCategory.GENETICS
    # First match wins
    assert classify_paper({"title": "genetic diversity and genome assembly"}) == PaperCategory.GENETICS


# ── cn_en_label() ────────────────────────────────────────────

def test_cn_en_label():
    assert cn_en_label({"journal": "水生生物学报"}) == ("CN", 25)
    assert cn_en_label({"journal": "Nature"}) == ("EN", 30)
    assert cn_en_label({"venue": "Science"}) == ("EN", 30)
    assert cn_en_label({"journal": "Unknown"}) == ("EN", 10)
