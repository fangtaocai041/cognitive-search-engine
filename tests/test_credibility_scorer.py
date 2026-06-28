"""Tests for credibility_scorer — v5.4+ authority-tier scoring (0-100), journal tier detection, predatory check, format."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.credibility_scorer import (
    score_paper,
    score_papers,
    detect_journal_tier,
    is_predatory,
    format_credibility,
)


# ── score_paper() — v5.4+ authority-tier scoring ─────────────

def test_score_paper_nature_gets_94_base():
    """Nature journal → base score 94 (top peer-reviewed tier)."""
    paper = {"journal": "Nature", "citation_count": 0}
    assert score_paper(paper) == 94


def test_score_paper_science_gets_94_base():
    """Science journal → base score 94."""
    paper = {"journal": "Science", "citation_count": 0}
    assert score_paper(paper) == 94


def test_score_paper_chinese_core_gets_72_base():
    """Chinese core journal 水生生物学报 → base score 72."""
    paper = {"journal": "水生生物学报", "citation_count": 0}
    assert score_paper(paper) == 72


def test_score_paper_plos_one_gets_78_base():
    """PLOS ONE → base score 78 (standard SCI tier)."""
    paper = {"journal": "PLOS ONE", "citation_count": 0}
    assert score_paper(paper) == 78


def test_score_paper_unknown_journal_gets_30_base():
    """Unknown journal defaults to base score 30."""
    paper = {"journal": "Unknown Quarterly Review", "citation_count": 0}
    assert score_paper(paper) == 30


def test_score_paper_missing_journal_defaults_30():
    """Paper with no journal field gets base 30."""
    paper = {"citation_count": 0}
    assert score_paper(paper) == 30


# ── Citation bonuses (only applied when base >= 65) ──────────

def test_score_paper_citation_gt_100_adds_5():
    """Citations > 100 add +5 for qualified journals (base >= 65)."""
    paper = {"journal": "Nature", "citation_count": 101}
    assert score_paper(paper) == 99  # 94 + 5


def test_score_paper_citation_gt_50_adds_3():
    """Citations > 50 and ≤ 100 add +3 for qualified journals."""
    paper = {"journal": "Nature", "citation_count": 51}
    assert score_paper(paper) == 97  # 94 + 3


def test_score_paper_citation_gt_20_adds_2():
    """Citations > 20 and ≤ 50 add +2 for qualified journals."""
    paper = {"journal": "Science", "citation_count": 25}
    assert score_paper(paper) == 96  # 94 + 2


def test_score_paper_citation_gt_5_adds_1():
    """Citations > 5 and ≤ 20 add +1 for qualified journals."""
    paper = {"journal": "Science", "citation_count": 10}
    assert score_paper(paper) == 95  # 94 + 1


def test_score_paper_citation_boundary_5_adds_nothing():
    """Exactly 5 citations → no bonus (not strictly > 5)."""
    paper = {"journal": "Science", "citation_count": 5}
    assert score_paper(paper) == 94  # no bonus


def test_score_paper_citation_boundary_20_adds_1():
    """Exactly 20 citations → +1 (> 5 but not > 20)."""
    paper = {"journal": "Science", "citation_count": 20}
    assert score_paper(paper) == 95  # 94 + 1


def test_score_paper_citation_boundary_50_adds_2():
    """Exactly 50 citations → +2 (> 20 but not > 50)."""
    paper = {"journal": "Science", "citation_count": 50}
    assert score_paper(paper) == 96  # 94 + 2


def test_score_paper_citation_boundary_100_adds_3():
    """Exactly 100 citations → +3 (> 50 but not > 100)."""
    paper = {"journal": "Science", "citation_count": 100}
    assert score_paper(paper) == 97  # 94 + 3


def test_score_paper_low_tier_no_citation_bonus():
    """Journals with base < 65 don't get citation bonuses."""
    paper = {"journal": "Unknown", "citation_count": 200}
    assert score_paper(paper) == 30  # base 30, citations ignored


def test_score_paper_capped_at_100():
    """Score must never exceed 100 (capped by min(base, 100))."""
    paper = {"journal": "Nature", "citation_count": 200}
    assert score_paper(paper) == 99  # 94 + 5 = 99, under 100


# ── score_papers() ───────────────────────────────────────────

def test_score_papers_adds_credibility_and_sorts_desc():
    """score_papers adds credibility_score key and sorts descending."""
    papers = [
        {"journal": "Unknown", "citation_count": 0},
        {"journal": "Science", "citation_count": 100},
        {"journal": "水生生物学报", "citation_count": 0},
    ]
    result = score_papers(papers)
    # Science 94 + 3(citations 100) = 97, 水生 72, Unknown 30
    assert result[0]["credibility_score"] == 97
    assert result[1]["credibility_score"] == 72
    assert result[2]["credibility_score"] == 30
    # Original list items mutated
    assert papers[0].get("credibility_score") is not None


def test_score_papers_empty_list():
    """Empty list should return empty list."""
    assert score_papers([]) == []


# ── detect_journal_tier() ────────────────────────────────────

def test_detect_journal_tier_excellent():
    """Nature/Science are 'excellent' tier (85-94), not 'top' (95+ reserved for IUCN/FAO)."""
    assert detect_journal_tier("Science") == "excellent"
    assert detect_journal_tier("Nature") == "excellent"


def test_detect_journal_tier_core_cn():
    """Chinese core journals map to 'core_cn' tier."""
    assert detect_journal_tier("水生生物学报") == "core_cn"
    assert detect_journal_tier("水产学报") == "core_cn"


def test_detect_journal_tier_unknown():
    """Unknown journals return 'unknown'."""
    assert detect_journal_tier("Random Journal") == "unknown"
    assert detect_journal_tier("") == "unknown"


# ── is_predatory() ───────────────────────────────────────────

def test_is_predatory_detects_known_patterns():
    assert is_predatory("waset journal of engineering") is True
    assert is_predatory("World Academy of Science Proceedings") is True


def test_is_predatory_negative():
    assert is_predatory("Nature") is False
    assert is_predatory("PLOS ONE") is False


# ── format_credibility() — v5.4+ bracket-symbol format ───────

def test_format_credibility_top():
    """Score 95+ → [顶] 国际权威."""
    label = format_credibility(95)
    assert "[顶]" in label
    assert "国际权威" in label


def test_format_credibility_excellent():
    """Score 85-94 → [优] 顶级期刊."""
    label = format_credibility(90)
    assert "[优]" in label
    assert "顶级期刊" in label


def test_format_credibility_good():
    """Score 75-84 → [良] SCI期刊."""
    label = format_credibility(80)
    assert "[良]" in label
    assert "SCI期刊" in label


def test_format_credibility_core():
    """Score 65-74 → [核] 中文核心."""
    label = format_credibility(70)
    assert "[核]" in label
    assert "中文核心" in label


def test_format_credibility_standard():
    """Score 50-64 → [标] 一般学术."""
    label = format_credibility(55)
    assert "[标]" in label
    assert "一般学术" in label


def test_format_credibility_news():
    """Score 20-49 → [闻] 新闻报道."""
    label = format_credibility(30)
    assert "[闻]" in label
    assert "新闻报道" in label


def test_format_credibility_unverified():
    """Score < 20 → [--] 未验证."""
    label = format_credibility(5)
    assert "[--]" in label
    assert "未验证" in label
