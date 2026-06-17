"""Tests for credibility_scorer — journal tier scoring, citation bonuses, formatting."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.credibility_scorer import (
    score_paper,
    score_papers,
    detect_journal_tier,
    is_predatory,
    format_credibility,
    JOURNAL_TIERS,
)


# ── score_paper() ────────────────────────────────────────────

def test_score_paper_top_sci_journal_gets_50_base():
    """Nature/Science should score 50 base (top tier)."""
    paper = {"journal": "Nature", "citation_count": 0}
    assert score_paper(paper) == 50


def test_score_paper_cscd_chinese_core_gets_25_base():
    """CSCD Chinese core journals like 水生生物学报 should score 25 base."""
    paper = {"journal": "水生生物学报", "citation_count": 0}
    assert score_paper(paper) == 25


def test_score_paper_unknown_journal_gets_10_base():
    """Unknown journal defaults to base score 10."""
    paper = {"journal": "Unknown Quarterly Review", "citation_count": 0}
    assert score_paper(paper) == 10


def test_score_paper_citation_gt_50_adds_5():
    """Citations > 50 add +5 to base score."""
    paper = {"journal": "Nature", "citation_count": 51}
    assert score_paper(paper) == 55  # 50 + 5


def test_score_paper_citation_gt_20_adds_3():
    """Citations > 20 and ≤ 50 add +3 to base score."""
    paper = {"journal": "PLOS ONE", "citation_count": 25}
    assert score_paper(paper) == 33  # 30 + 3


def test_score_paper_citation_gt_5_adds_1():
    """Citations > 5 and ≤ 20 add +1 to base score."""
    paper = {"journal": "Science", "citation_count": 10}
    assert score_paper(paper) == 51  # 50 + 1


def test_score_paper_citation_boundary_5_adds_nothing():
    """Exactly 5 citations → no bonus."""
    paper = {"journal": "Science", "citation_count": 5}
    assert score_paper(paper) == 50


def test_score_paper_citation_boundary_20_adds_1():
    """Exactly 20 citations → +1 (citations > 5 but ≤ 20)."""
    paper = {"journal": "Science", "citation_count": 20}
    assert score_paper(paper) == 51


def test_score_paper_citation_boundary_50_adds_3():
    """Exactly 50 citations → +3 (citations > 20 but ≤ 50)."""
    paper = {"journal": "Science", "citation_count": 50}
    assert score_paper(paper) == 53


def test_score_paper_capped_at_100():
    """Score must never exceed 100."""
    paper = {"journal": "Nature", "citation_count": 200}
    assert score_paper(paper) == 55  # 50 + 5, well under 100


def test_score_paper_missing_journal_defaults_unknown():
    """Paper with no journal field gets base 10."""
    paper = {"citation_count": 0}
    assert score_paper(paper) == 10


# ── score_papers() ───────────────────────────────────────────

def test_score_papers_adds_credibility_and_sorts_desc():
    """score_papers adds credibility_score key and sorts descending."""
    papers = [
        {"journal": "Unknown", "citation_count": 0},
        {"journal": "Science", "citation_count": 100},
        {"journal": "水生生物学报", "citation_count": 0},
    ]
    result = score_papers(papers)
    assert result[0]["credibility_score"] == 55  # Science + citations
    assert result[1]["credibility_score"] == 25  # 水生生物学报
    assert result[2]["credibility_score"] == 10  # Unknown
    # Original list items mutated
    assert papers[0].get("credibility_score") is not None


def test_score_papers_empty_list():
    """Empty list should return empty list."""
    assert score_papers([]) == []


# ── detect_journal_tier() ────────────────────────────────────

def test_detect_journal_tier_top():
    assert detect_journal_tier("Science") == "top"
    assert detect_journal_tier("Nature") == "top"


def test_detect_journal_tier_core():
    assert detect_journal_tier("水生生物学报") == "core"
    assert detect_journal_tier("水产学报") == "core"


def test_detect_journal_tier_unknown():
    assert detect_journal_tier("Random Journal") == "unknown"
    assert detect_journal_tier("") == "unknown"


# ── is_predatory() ───────────────────────────────────────────

def test_is_predatory_detects_known_patterns():
    assert is_predatory("waset journal of engineering") is True
    assert is_predatory("World Academy of Science Proceedings") is True


def test_is_predatory_negative():
    assert is_predatory("Nature") is False
    assert is_predatory("PLOS ONE") is False


# ── format_credibility() ─────────────────────────────────────

def test_format_credibility_top():
    assert "极高" in format_credibility(45)
    assert "⭐⭐⭐⭐⭐" in format_credibility(45)


def test_format_credibility_high():
    label = format_credibility(35)
    assert "高" in label
    assert "⭐⭐⭐⭐" in label


def test_format_credibility_medium():
    label = format_credibility(25)
    assert "中等" in label
    assert "⭐⭐⭐" in label


def test_format_credibility_low():
    label = format_credibility(15)
    assert "低" in label
    assert "⭐⭐" in label


def test_format_credibility_unverified():
    label = format_credibility(5)
    assert "待验证" in label
    assert "⭐" in label
