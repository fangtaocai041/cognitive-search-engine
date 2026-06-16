"""Paper credibility scoring based on journal whitelist and citation metrics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Unified journal credibility whitelist
JOURNAL_TIERS: Dict[str, int] = {
    # Q1 / 顶级
    "Nature": 50, "Science": 50, "PNAS": 45,
    "Current Biology": 40, "Molecular Ecology": 40,
    "Ecology Letters": 40, "Global Change Biology": 40,
    # Q2 / 优秀
    "BMC Biology": 30, "Scientific Data": 30,
    "Scientific Reports": 30, "PLOS ONE": 30,
    "Genes": 30, "Gene": 30, "Animals": 30,
    "Mitochondrial DNA": 30, "Conserv Genet Resour": 30,
    # 中文核心
    "水生生物学报": 25, "中国水产科学": 25,
    "水产学报": 25, "生物多样性": 25,
    "湖泊科学": 25, "生态学报": 25,
}


def score_paper(paper: Dict[str, Any]) -> int:
    """Score a single paper's credibility."""
    journal = paper.get("journal", "")
    base = JOURNAL_TIERS.get(journal, 10)
    citations = paper.get("citation_count", 0)
    if citations > 50:
        base += 5
    elif citations > 20:
        base += 3
    elif citations > 5:
        base += 1
    return min(base, 100)


def score_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Score a list of papers and return sorted by credibility."""
    for p in papers:
        p["credibility_score"] = score_paper(p)
    return sorted(papers, key=lambda x: x.get("credibility_score", 0), reverse=True)


def detect_journal_tier(journal: str) -> str:
    """Detect journal tier based on whitelist."""
    score = JOURNAL_TIERS.get(journal, 0)
    if score >= 40:
        return "top"
    elif score >= 25:
        return "core"
    elif score >= 15:
        return "standard"
    return "unknown"


def is_predatory(journal: str) -> bool:
    """Basic heuristic check for potentially predatory journals."""
    predatory_indicators = [
        "waset", "world academy of science",
        "journal of applied sciences",
        "academic research international",
    ]
    return any(ind in journal.lower() for ind in predatory_indicators)


def format_credibility(score: int) -> str:
    """Format credibility score as human-readable label."""
    if score >= 40:
        return "⭐⭐⭐⭐⭐ 极高"
    elif score >= 30:
        return "⭐⭐⭐⭐ 高"
    elif score >= 20:
        return "⭐⭐⭐ 中等"
    elif score >= 10:
        return "⭐⭐ 低"
    return "⭐ 待验证"
