"""
Validator — Independent verification engine for cognitive-search-engine.

Extracted from rule_engine.py (Step 2 of architecture refactoring).
Provides:
  1. trust_score()           — 5-level trust scoring (from rule_engine._trust_score)
  2. credibility_score()     — Full authority scoring with SCI/CSCD/preprint detection
  3. enforce_independence()  — Cross-project source independence check (min 2 different sources)
  4. validate_papers()       — Batch validation with independence enforcement

Design: This module is SEPARATE from search logic (rule_engine.py).
        It can be imported independently by any project in the S-T-V triangle.

Usage:
    from src.validator import validate_papers, credibility_score, enforce_independence

    papers = [...]
    result = validate_papers(papers, known_authors=[], known_journals=[],
                             species_id="Ochetobius_elongatus")
    # result.verified, result.pending, result.rejected
    # result.independence_violations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


# ═══════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════

@dataclass
class Paper:
    """Minimal paper representation for validation (avoids circular import)."""
    doi: str = ""
    title: str = ""
    year: Optional[int] = None
    journal: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    citations: int = 0
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    trust: str = "pending"
    trust_score: int = 50
    source: str = ""
    source_project: str = ""  # "pubmed" | "crossref" | "openalex" | "scholar" | "cnki" | etc.


@dataclass
class ValidationResult:
    """Structured validation output."""
    papers: list[dict] = field(default_factory=list)
    verified: list[dict] = field(default_factory=list)       # score >= 80
    tentative: list[dict] = field(default_factory=list)      # 50 <= score < 80
    rejected: list[dict] = field(default_factory=list)       # score < 40
    independence_violations: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# Journal Authority Whitelists
# ═══════════════════════════════════════════════════════════════

# SCI-indexed journals (subset — extend via config)
SCI_JOURNALS: set[str] = {
    "scientific data", "scientific reports", "animals", "gene",
    "mitochondrial dna", "conserv genet resour", "plos one",
    "nature", "science", "pnas", "cell", "current biology",
    "molecular ecology", "ecology letters", "journal of animal ecology",
    "global change biology", "frontiers in marine science",
    "marine biology", "marine ecology progress series",
    "journal of fish biology", "environmental biology of fishes",
    "reviews in fish biology and fisheries",
}

# CSCD 核心 / 北大核心 Chinese journals
CSCD_JOURNALS: set[str] = {
    "水生生物学报", "中国水产科学", "水产学报",
    "生物多样性", "湖泊科学", "南方水产科学",
    "生态学报",
}

# 中国科技核心
CSTPCD_JOURNALS: set[str] = {
    "生态科学",
}

# Known preprint servers (no peer review)
PREPRINT_SERVERS: set[str] = {
    "biorxiv", "medrxiv", "research square", "arxiv",
    "ssrn", "preprints.org", "researchgate",
}

# Known predatory / self-published patterns
PREDATORY_PATTERNS: list[str] = [
    "omics", "academic journals", "david publishing",
    "scirp", "hindawi",  # Note: some Hindawi journals are legit; flag for review
]

# Sources and their project mapping
SOURCE_PROJECT_MAP: dict[str, str] = {
    "pubmed": "ncbi",
    "crossref": "crossref",
    "openalex": "openalex",
    "scholar": "google_scholar",
    "cnki": "cnki",
    "wanfang": "wanfang",
    "baidu_scholar": "baidu_scholar",
    "cas": "cas",
    "tavily": "tavily",
    "exa": "exa",
    "mcp:scholar": "google_scholar",
    "mcp:article": "crossref",
    "mcp:tavily": "tavily",
    "via_review": "review_mining",
    "citing": "citation_graph",
    "reference": "citation_graph",
    "variant": "variant_search",
    "mcp_fallback": "mcp",
}


# ═══════════════════════════════════════════════════════════════
# Core Scoring Functions
# ═══════════════════════════════════════════════════════════════

def trust_score(paper: Paper,
                known_authors: list[str] | None = None,
                known_journals: list[str] | None = None,
                species_terms: list[str] | None = None) -> int:
    """5-level trust scoring — extracted from rule_engine._trust_score.

    Levels:
      L1: DOI resolves (+20)
      L2: PMID exists (+15)
      L3: Title/species match (+10)
      L4: Known author (+10)
      L5: Known journal (+5)
    """
    score = 50
    known_authors = known_authors or []
    known_journals = known_journals or []
    species_terms = species_terms or []

    # L1: DOI
    if paper.doi and paper.doi.startswith("10."):
        score += 20

    # L2: PMID
    if paper.pmid:
        score += 15

    # L3: Species terms in title
    title_lower = (paper.title or "").lower()
    if any(term.lower() in title_lower for term in species_terms):
        score += 10

    # L4: Known author
    known_lower = {a.lower() for a in known_authors}
    if any(a.lower() in known_lower for a in (paper.authors or [])):
        score += 10

    # L5: Known journal
    journal_lower = {j.lower() for j in known_journals}
    if paper.journal and paper.journal.lower() in journal_lower:
        score += 5

    return min(100, score)


def credibility_score(paper: Paper) -> int:
    """Full authority credibility scoring (0-100).

    Formula (from species-search rule v5.0):
      baseline = 50
      +30 if SCI/SSCI indexed journal
      +25 if 北大核心 or CSCD 核心
      +20 if 中国科技核心
      +10 if OTHER peer-reviewed journal
      +10 if has DOI
      +10 if has PMID
      +5  if has PMCID (open access)
      +5  if citations >= 10
      +10 if citations >= 50
      -30 if preprint WITHOUT peer review
      -20 if non-core Chinese journal
      -10 if conference abstract only
      -40 if predatory journal or self-published
      -100 if retracted (exclude entirely)

    Returns score clamped to [0, 100].
    Special: returns -1 for retracted papers (should be excluded).
    """
    score = 50
    journal_lower = (paper.journal or "").lower()

    # ── Retraction check (absolute exclusion) ──
    if "retracted" in journal_lower or "retraction" in (paper.title or "").lower():
        return -1

    # ── Journal authority ──
    is_sci = any(sci_j in journal_lower for sci_j in SCI_JOURNALS)
    is_cscd = any(cscd_j in journal_lower for cscd_j in CSCD_JOURNALS)
    is_cstpcd = any(cstpcd_j in journal_lower for cstpcd_j in CSTPCD_JOURNALS)

    if is_sci:
        score += 30
    elif is_cscd:
        score += 25
    elif is_cstpcd:
        score += 20
    elif paper.journal:
        score += 10  # Other peer-reviewed

    # ── Identifier bonuses ──
    if paper.doi and paper.doi.startswith("10."):
        score += 10
    if paper.pmid:
        score += 10
    if paper.pmcid:
        score += 5

    # ── Citation bonuses ──
    if paper.citations >= 50:
        score += 10
    elif paper.citations >= 10:
        score += 5

    # ── Penalties ──
    # Preprint detection
    is_preprint = any(srv in journal_lower for srv in PREPRINT_SERVERS)
    if is_preprint:
        score -= 30

    # Predatory detection
    is_predatory = any(pat in journal_lower for pat in PREDATORY_PATTERNS)
    if is_predatory:
        score -= 40

    # Conference abstract
    if paper.journal and ("conference" in journal_lower or "abstract" in journal_lower):
        score -= 10

    return max(0, min(100, score))


def resolve_source_project(source: str) -> str:
    """Map a source string to its project namespace.

    >>> resolve_source_project("pubmed")
    'ncbi'
    >>> resolve_source_project("mcp:scholar")
    'google_scholar'
    """
    return SOURCE_PROJECT_MAP.get(source, source)


def enforce_independence(papers: list[Paper | dict],
                          min_sources: int = 3,
                          min_projects: int = 2) -> tuple[bool, list[str], dict]:
    """Enforce cross-project source independence for triangulation.

    Requirements (from S-T-V triangle protocol):
      - Core claims MUST have >= min_sources (default 3) independent sources
      - At least min_projects (default 2) DIFFERENT projects/databases
      - Same project counted once regardless of how many papers from it

    Args:
        papers: List of Paper objects or dicts with 'source' key
        min_sources: Minimum total independent sources
        min_projects: Minimum distinct project namespaces

    Returns:
        (passed, violations, stats)
        - passed: True if independence requirement met
        - violations: list of violation descriptions
        - stats: {unique_sources, unique_projects, source_counts, project_counts}
    """
    from collections import Counter

    # Normalize to source strings
    sources = []
    for p in papers:
        if isinstance(p, dict):
            s = p.get("source", p.get("source_project", ""))
        else:
            s = getattr(p, "source", "") or getattr(p, "source_project", "")
        if s:
            sources.append(s)

    # Map to projects
    projects = [resolve_source_project(s) for s in sources]

    source_counts = Counter(sources)
    project_counts = Counter(projects)

    unique_sources = len(source_counts)
    unique_projects = len(project_counts)

    stats = {
        "unique_sources": unique_sources,
        "unique_projects": unique_projects,
        "source_counts": dict(source_counts),
        "project_counts": dict(project_counts),
        "min_sources_required": min_sources,
        "min_projects_required": min_projects,
    }

    violations = []

    # Check 1: minimum source count
    if unique_sources < min_sources:
        violations.append(
            f"INSUFFICIENT_SOURCES: {unique_sources} unique sources < {min_sources} required. "
            f"Sources found: {list(source_counts.keys())}"
        )

    # Check 2: cross-project independence
    if unique_projects < min_projects:
        violations.append(
            f"DEPENDENCY_RISK: {unique_projects} project(s) < {min_projects} required. "
            f"All papers from: {list(project_counts.keys())}. "
            f"Triangulation requires at least {min_projects} independent projects."
        )

    passed = len(violations) == 0
    return passed, violations, stats


def validate_papers(papers: list[Paper | dict],
                    known_authors: list[str] | None = None,
                    known_journals: list[str] | None = None,
                    species_terms: list[str] | None = None,
                    min_sources: int = 3,
                    min_projects: int = 2,
                    trust_threshold_verified: int = 80,
                    trust_threshold_tentative: int = 50) -> ValidationResult:
    """Full validation pipeline: score each paper + enforce independence.

    Returns structured ValidationResult with:
      - verified:   papers with score >= trust_threshold_verified
      - tentative:  papers with trust_threshold_tentative <= score < trust_threshold_verified
      - rejected:   papers with score < 40 OR retracted
      - independence_violations: cross-project source violations
    """
    result = ValidationResult()

    scored_papers = []
    verified = []
    tentative = []
    rejected = []

    for p in papers:
        if isinstance(p, dict):
            # Build minimal Paper for scoring
            paper_obj = Paper(
                doi=p.get("doi", ""),
                title=p.get("title", ""),
                year=p.get("year"),
                journal=p.get("journal"),
                authors=p.get("authors", []),
                citations=p.get("citations", 0),
                pmid=p.get("pmid"),
                pmcid=p.get("pmcid"),
                source=p.get("source", ""),
                source_project=p.get("source_project", ""),
            )
        else:
            paper_obj = p

        # Compute both scores
        ts = trust_score(paper_obj, known_authors, known_journals, species_terms)
        cs = credibility_score(paper_obj)

        # Use credibility_score as primary; fall back to trust_score
        final_score = cs if cs >= 0 else -1
        trust_label = "verified" if final_score >= trust_threshold_verified else \
                      "tentative" if final_score >= trust_threshold_tentative else \
                      "rejected"

        if isinstance(p, dict):
            p["trust_score"] = final_score if final_score >= 0 else 0
            p["credibility_score"] = cs
            p["trust"] = trust_label if final_score >= 0 else "retracted"
        else:
            paper_obj.trust_score = final_score if final_score >= 0 else 0
            paper_obj.trust = trust_label if final_score >= 0 else "retracted"

        paper_dict = p if isinstance(p, dict) else {
            "doi": paper_obj.doi, "title": paper_obj.title,
            "year": paper_obj.year, "journal": paper_obj.journal,
            "authors": paper_obj.authors, "citations": paper_obj.citations,
            "pmid": paper_obj.pmid, "trust_score": paper_obj.trust_score,
            "trust": paper_obj.trust, "source": paper_obj.source,
            "source_project": resolve_source_project(paper_obj.source),
        }

        scored_papers.append(paper_dict)

        if final_score < 0:
            rejected.append(paper_dict)
        elif final_score >= trust_threshold_verified:
            verified.append(paper_dict)
        elif final_score >= trust_threshold_tentative:
            tentative.append(paper_dict)
        else:
            rejected.append(paper_dict)

    # Enforce cross-project independence
    passed, violations, independence_stats = enforce_independence(
        scored_papers, min_sources=min_sources, min_projects=min_projects
    )

    result.papers = scored_papers
    result.verified = verified
    result.tentative = tentative
    result.rejected = rejected
    result.independence_violations = [
        {"violation": v, "severity": "BLOCK" if "INSUFFICIENT" in v else "WARN"}
        for v in violations
    ]
    result.stats = {
        "total": len(scored_papers),
        "verified_count": len(verified),
        "tentative_count": len(tentative),
        "rejected_count": len(rejected),
        "independence_passed": passed,
        **independence_stats,
    }

    return result


# ═══════════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════════

def quick_validate(papers: list[dict]) -> dict:
    """One-liner: validate a list of paper dicts, return summary."""
    result = validate_papers(papers)
    return {
        "passed": result.stats["independence_passed"],
        "verified": result.stats["verified_count"],
        "tentative": result.stats["tentative_count"],
        "rejected": result.stats["rejected_count"],
        "violations": [v["violation"] for v in result.independence_violations],
        "unique_sources": result.stats["unique_sources"],
        "unique_projects": result.stats["unique_projects"],
    }
