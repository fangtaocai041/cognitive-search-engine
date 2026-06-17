"""Tests for validator — trust scoring, credibility scoring, independence enforcement."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.validator import (
    Paper,
    trust_score,
    credibility_score,
    enforce_independence,
    validate_papers,
    quick_validate,
    resolve_source_project,
)


def make_paper(doi="", pmid=None, pmcid=None, title="", journal=None,
               authors=None, citations=0, source=""):
    return Paper(doi=doi, pmid=pmid, pmcid=pmcid, title=title, journal=journal,
                 authors=authors or [], citations=citations, source=source)


# ── trust_score() ────────────────────────────────────────────

def test_trust_score_levels_stack_and_cap():
    """L1 DOI(+20), L2 PMID(+15), L3 species(+10), L4 author(+10), L5 journal(+5)."""
    empty = make_paper()
    assert trust_score(empty) == 50

    assert trust_score(make_paper(doi="10.1000/x")) == 70  # +20
    assert trust_score(make_paper(doi="11.1000/x")) == 50  # invalid prefix
    assert trust_score(make_paper(pmid="12345")) == 65     # +15
    assert trust_score(make_paper(doi="10.1000/x", pmid="12345")) == 85

    p = make_paper(title="Genetics of Ochetobius elongatus")
    assert trust_score(p, species_terms=["Ochetobius"]) == 60

    p = make_paper(authors=["Zhang Wei"])
    assert trust_score(p, known_authors=["Zhang Wei"]) == 60

    p = make_paper(journal="Nature")
    assert trust_score(p, known_journals=["Nature"]) == 55

    # Cap at 100: all bonuses (50+20+15+10+10+5=110)
    p = make_paper(doi="10.1000/x", pmid="12345", title="Ochetobius review",
                   authors=["Zhang Wei"], journal="Nature")
    assert trust_score(p, known_authors=["Zhang Wei"],
                       known_journals=["Nature"],
                       species_terms=["Ochetobius"]) == 100


# ── credibility_score() ─────────────────────────────────────

def test_credibility_score_journal_tiers():
    assert credibility_score(make_paper()) == 50                         # baseline
    assert credibility_score(make_paper(journal="Scientific Data")) == 80  # SCI +30
    assert credibility_score(make_paper(journal="水生生物学报")) == 75     # CSCD +25
    assert credibility_score(make_paper(journal="生态科学")) == 70         # CSTPCD +20
    assert credibility_score(make_paper(journal="Some Journal")) == 60     # other +10
    assert credibility_score(make_paper(doi="10.1000/x")) == 60           # DOI only


def test_credibility_score_identifiers_and_citations():
    assert credibility_score(make_paper(pmid="123", pmcid="PMC456")) == 65  # +10+5
    assert credibility_score(make_paper(citations=60)) == 60                # +10
    assert credibility_score(make_paper(citations=25)) == 55                # +5


def test_credibility_score_penalties_and_specials():
    # Preprint: journal exists +10, then -30
    assert credibility_score(make_paper(journal="bioRxiv")) == 30
    # Predatory: journal exists +10, then -40
    assert credibility_score(make_paper(journal="OMICS Publishing Group")) == 20
    # Conference: journal exists +10, then -10
    assert credibility_score(make_paper(journal="Conference on Fish Biology")) == 50
    # Retracted: returns -1 (exclusion)
    assert credibility_score(make_paper(title="retraction notice: some paper")) == -1
    assert credibility_score(make_paper(journal="Retracted Studies Quarterly")) == -1
    # Multiple penalties still clamped to [0,100] or -1
    s = credibility_score(make_paper(journal="omics predatory biorxiv"))
    assert 0 <= s <= 100 or s == -1


# ── enforce_independence() ───────────────────────────────────

def test_enforce_independence_scenarios():
    # Single source → fail
    p1 = [{"source": "pubmed"}, {"source": "pubmed"}, {"source": "pubmed"}]
    passed, v, s = enforce_independence(p1, min_sources=3)
    assert not passed and s["unique_sources"] == 1
    assert any("INSUFFICIENT_SOURCES" in x for x in v)

    # Three projects → pass
    p2 = [{"source": "pubmed"}, {"source": "crossref"}, {"source": "cnki"}]
    passed, v, s = enforce_independence(p2, min_sources=3, min_projects=2)
    assert passed and s["unique_projects"] == 3

    # Also accepts Paper objects
    p3 = [Paper(doi="10.1000/1", source="pubmed"),
          Paper(doi="10.1000/2", source="crossref"),
          Paper(doi="10.1000/3", source="cnki")]
    passed, _, _ = enforce_independence(p3, min_sources=3, min_projects=2)
    assert passed


# ── validate_papers() + quick_validate() ─────────────────────

def test_validate_papers_full_pipeline():
    papers = [
        {"doi": "10.1000/test", "title": "Fish study", "journal": "Nature",
         "source": "pubmed", "citations": 100, "pmid": "12345"},
        {"doi": "", "title": "Other", "journal": "bioRxiv", "source": "crossref"},
        {"doi": "", "title": "retraction of ...", "journal": "", "source": "openalex"},
    ]
    r = validate_papers(papers, min_sources=3, min_projects=2,
                        trust_threshold_verified=80, trust_threshold_tentative=50)
    assert r.stats["total"] == 3
    assert len(r.verified) >= 1
    assert len(r.rejected) >= 1
    assert any(p["trust"] == "retracted" for p in r.papers)
    # 3 papers from 3 sources → independence should pass
    assert r.stats["independence_passed"] is True


def test_quick_validate_empty_and_populated():
    assert quick_validate([])["verified"] == 0
    summary = quick_validate([
        {"doi": "10.1000/1", "title": "P1", "journal": "Nature",
         "source": "pubmed", "citations": 100},
    ])
    for k in ("passed", "verified", "tentative", "rejected",
              "unique_sources", "unique_projects"):
        assert k in summary


# ── resolve_source_project() ─────────────────────────────────

def test_resolve_source_project():
    assert resolve_source_project("pubmed") == "ncbi"
    assert resolve_source_project("cnki") == "cnki"
    assert resolve_source_project("mcp:scholar") == "google_scholar"
    assert resolve_source_project("custom") == "custom"
