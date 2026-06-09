"""
Graph Updater — Auto-update species_graph.yaml with new search results.

After each search, discovered papers, authors, institutions, and citation edges
are merged back into the knowledge graph, enabling:
  - Persistent paper index (no re-searching known papers)
  - Growing author & institution network
  - Automatic citation edge generation
  - Graph-based cold-start for future searches

v2.0 — ZN/EN-aware dynamic update:
  - Chinese journal papers get authors_zh auto-filled
  - New authors auto-registered in authors list
  - New journals auto-registered in journals list
  - Chinese-English duplicate detection before insert

Usage:
  from graph_updater import load_species_graph, update_species_graph

import sys as _sys
from pathlib import Path
_SRC_ROOT = str(Path(__file__).resolve().parent)
if _SRC_ROOT not in _sys.path:
    _sys.path.insert(0, _SRC_ROOT)


  papers = load_species_graph("Ochetobius_elongatus")
  update_species_graph(species_id, new_papers)
"""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


GRAPH_PATH = Path("config/species_graph.yaml")

# ──── Chinese journal name patterns ────
# Journals containing any of these substrings are treated as Chinese-language journals.
_CHINESE_JOURNAL_PATTERNS = [
    "生物", "水产", "湖泊", "生态", "海洋", "渔业",
    "动物", "植物", "遗传", "水生", "南方", "中国",
    "应用", "环境", "资源", "学报", "研究", "通报",
    "科学", "天然", "实验", "分类",
]
# English-only journals that should NEVER get authors_zh even if they match patterns
_ENGLISH_ONLY_JOURNALS = {
    "Scientific Data", "Scientific Reports", "Animals",
    "Gene", "PLOS ONE", "PLoS One", "PloS one",
    "Mitochondrial DNA", "Mitochondrial DNA Part A",
    "Conservation Genetics Resources", "Conserv Genet Resour",
    "Marine pollution bulletin", "Marine Pollution Bulletin",
    "Environmental science & technology", "Environmental Science & Technology",
}


def load_species_graph(species_id: str) -> list[dict]:
    """Load all known papers for a species from the knowledge graph.

    Returns list of paper dicts with keys: doi, title, title_zh, year,
    journal, authors, authors_zh, institutions, species, citations, type, note.
    """
    graph = _read_graph()
    if graph is None:
        return []

    papers = []
    for p in graph.get("graph", {}).get("papers", []):
        if species_id in p.get("species", []):
            papers.append(dict(p))
    return papers


def update_species_graph(species_id: str, new_papers: list[dict]) -> int:
    """Merge newly discovered papers into the species graph.

    v2.0 enhancements:
      - Chinese journal papers get authors_zh auto-filled
      - New authors + journals auto-registered
      - ZN/EN duplicate detection before insert

    Args:
        species_id: e.g. "Ochetobius_elongatus"
        new_papers: list of dicts with keys matching paper schema

    Returns:
        Number of new papers added.
    """
    graph = _read_graph()
    if graph is None:
        return 0

    # Build index of existing DOIs and Chinese titles
    existing_dois: set[str] = set()
    existing_titles_zh: set[str] = set()
    for p in graph.get("graph", {}).get("papers", []):
        doi = (p.get("doi", "") or "").lower().strip()
        if doi:
            existing_dois.add(doi)
        tzh = (p.get("title_zh", "") or "").strip()
        if tzh:
            existing_titles_zh.add(tzh)

    new_count = 0
    registered_authors = set()
    # Pre-load existing author names for quick lookup
    for a in graph.get("graph", {}).get("authors", []):
        registered_authors.add(a.get("name", ""))

    registered_journals = set()
    for j in graph.get("graph", {}).get("journals", []):
        registered_journals.add(j.get("name", ""))

    for np in new_papers:
        doi = (np.get("doi", "") or "").lower().strip()
        title_zh = (np.get("title_zh", "") or "").strip()

        # ── Skip: no DOI and no Chinese title → can't deduplicate ──
        if not doi and not title_zh:
            continue

        # ── Dedup by DOI ──
        if doi and doi in existing_dois:
            continue

        # ── Dedup by Chinese title (ZN/EN duplicate detection) ──
        if title_zh and title_zh in existing_titles_zh:
            continue

        # ── Detect journal language ──
        journal = np.get("journal", "") or ""
        is_cn = _is_chinese_journal(journal)

        # ── Build a graph-compatible paper entry ──
        entry: dict[str, Any] = {
            "doi": np.get("doi", ""),
            "title": np.get("title", ""),
            "year": np.get("year"),
            "journal": journal,
            "authors": np.get("authors", []),
            "species": [species_id],
        }

        if title_zh:
            entry["title_zh"] = title_zh

        # ── Auto-fill authors_zh for Chinese journal papers ──
        if is_cn and np.get("authors_zh"):
            entry["authors_zh"] = np["authors_zh"]
        elif is_cn and not np.get("authors_zh"):
            # Attempt auto-lookup from existing author registry
            entry["authors_zh"] = _resolve_authors_zh(
                graph, np.get("authors", []), species_id
            )

        if np.get("institutions"):
            entry["institutions"] = np["institutions"]
        if np.get("citations"):
            entry["citations"] = np["citations"]
        if np.get("abstract"):
            entry["abstract"] = np["abstract"]
        if np.get("type"):
            entry["type"] = np["type"]
        if np.get("note"):
            entry["note"] = np["note"]
        entry["source"] = "auto_ingest"

        graph["graph"]["papers"].append(entry)

        # ── Auto-register new authors ──
        _auto_update_authors(graph, np.get("authors", []),
                             np.get("authors_zh", []),
                             np.get("institutions", []),
                             species_id, registered_authors)

        # ── Auto-register new journals ──
        _auto_update_journals(graph, journal, species_id, registered_journals)

        # Update dedup indices
        if doi:
            existing_dois.add(doi)
        if title_zh:
            existing_titles_zh.add(title_zh)
        new_count += 1

    # Save
    if new_count > 0:
        _write_graph(graph)

    return new_count


def get_graph_stats(species_id: str | None = None) -> dict:
    """Return graph statistics: paper count, author count, journal count."""
    graph = _read_graph()
    if graph is None:
        return {"papers": 0, "authors": 0, "journals": 0, "edges": 0}

    papers = graph.get("graph", {}).get("papers", [])
    authors = graph.get("graph", {}).get("authors", [])
    journals = graph.get("graph", {}).get("journals", [])
    edges = graph.get("graph", {}).get("edges", [])

    if species_id:
        papers = [p for p in papers if species_id in p.get("species", [])]

    return {
        "papers": len(papers),
        "authors": len(authors),
        "journals": len(journals),
        "edges": len(edges),
    }


# ──── ZN/EN helpers ────


def _is_chinese_journal(journal_name: str) -> bool:
    """Determine if a journal is Chinese-language.

    Detection rules:
      1. If journal_name contains Chinese characters → YES
      2. If journal_name is in ENGLISH_ONLY_JOURNALS override set → NO
      3. If journal_name matches any _CHINESE_JOURNAL_PATTERNS → YES
      4. Otherwise → NO (conservative default: treat as English)
    """
    name = journal_name.strip()

    # ── Rule 1: Contains Chinese characters → Chinese journal ──
    if any("\u4e00" <= ch <= "\u9fff" for ch in name):
        # Check English-only override
        base = name.split("(")[0].strip()
        if base in _ENGLISH_ONLY_JOURNALS:
            return False
        return True

    # ── Rule 2: Explicit English-only override ──
    if name in _ENGLISH_ONLY_JOURNALS:
        return False

    # ── Rule 3: Pattern match on Chinese journal name patterns ──
    for pat in _CHINESE_JOURNAL_PATTERNS:
        if pat in name:
            return True

    # ── Rule 4: Default to English ──
    return False


def _resolve_authors_zh(graph: dict, author_names: list[str],
                         species_id: str) -> list[str]:
    """Look up Chinese names from the author registry for a list of English names.

    Returns a list parallel to author_names, with empty strings for
    authors not found in the registry.
    """
    registry: dict[str, str] = {}
    for a in graph.get("graph", {}).get("authors", []):
        en = a.get("name", "")
        cn = a.get("chinese", "")
        if en and cn:
            registry[en.lower()] = cn

    result: list[str] = []
    for name in author_names:
        cn = registry.get(name.lower().strip(), "")
        result.append(cn)
    return result


def _auto_update_authors(graph: dict, author_names: list[str],
                          author_names_zh: list[str],
                          institutions: list[str],
                          species_id: str,
                          registered_authors: set[str]):
    """Auto-register new authors into the graph's authors list.

    Only adds authors whose English name is not already in the registry.
    Uses Chinese names from author_names_zh parallel list.
    """
    if not author_names:
        return

    authors_section = graph["graph"].setdefault("authors", [])
    insts = institutions or []

    for i, en_name in enumerate(author_names):
        en_name = en_name.strip()
        if not en_name:
            continue

        # Skip if already registered
        if en_name.lower() in {a.lower() for a in registered_authors}:
            continue

        # Get Chinese name if available
        cn_name = (author_names_zh[i] if i < len(author_names_zh)
                   and author_names_zh[i] else "")

        entry: dict[str, Any] = {
            "name": en_name,
            "institutions": insts,
            "species": [species_id],
        }
        if cn_name:
            entry["chinese"] = cn_name

        authors_section.append(entry)
        registered_authors.add(en_name)


def _auto_update_journals(graph: dict, journal_name: str,
                           species_id: str,
                           registered_journals: set[str]):
    """Auto-register a new journal into the graph's journals list."""
    if not journal_name or journal_name == "待确认":
        return

    if journal_name.lower() in {j.lower() for j in registered_journals}:
        return

    journals_section = graph["graph"].setdefault("journals", [])
    journals_section.append({
        "name": journal_name,
        "species": [species_id],
    })
    registered_journals.add(journal_name)


# ──── Internal file I/O ────


def _read_graph() -> dict | None:
    if yaml is None:
        return None
    try:
        if GRAPH_PATH.exists():
            with open(GRAPH_PATH, encoding="utf-8") as f:
                return yaml.safe_load(f)
    except Exception:
        pass
    return None


def _write_graph(graph: dict):
    """Write graph back to YAML."""
    if yaml is None:
        return
    try:
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            yaml.dump(graph, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False)
    except Exception:
        pass
