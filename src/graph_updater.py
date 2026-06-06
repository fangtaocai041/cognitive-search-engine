"""
Graph Updater — Auto-update species_graph.yaml with new search results.

After each search, discovered papers, authors, institutions, and citation edges
are merged back into the knowledge graph, enabling:
  - Persistent paper index (no re-searching known papers)
  - Growing author & institution network
  - Automatic citation edge generation
  - Graph-based cold-start for future searches

Usage:
  from graph_updater import load_species_graph, update_species_graph

  # Load papers for a species from the graph (used by rule_engine)
  papers = load_species_graph("Ochetobius_elongatus")

  # After search, merge new findings back into the graph
  update_species_graph(species_id, new_papers)
"""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


GRAPH_PATH = Path("config/species_graph.yaml")


def load_species_graph(species_id: str) -> list[dict]:
    """Load all known papers for a species from the knowledge graph.

    Returns list of paper dicts with keys: doi, title, title_zh, year,
    journal, authors, institutions, species, citations, type, note.
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

    Args:
        species_id: e.g. "Ochetobius_elongatus"
        new_papers: list of dicts with keys matching species_graph.yaml paper schema

    Returns:
        Number of new papers added (papers that were not already in the graph).
    """
    graph = _read_graph()
    if graph is None:
        return 0

    existing_dois = set()
    for p in graph.get("graph", {}).get("papers", []):
        doi = (p.get("doi", "") or "").lower().strip()
        if doi:
            existing_dois.add(doi)

    new_count = 0
    for np in new_papers:
        doi = (np.get("doi", "") or "").lower().strip()
        if not doi or doi in existing_dois:
            continue

        # Build a graph-compatible paper entry
        entry = {
            "doi": np.get("doi", ""),
            "title": np.get("title", ""),
            "year": np.get("year"),
            "journal": np.get("journal", ""),
            "authors": np.get("authors", []),
            "species": [species_id],
        }

        if np.get("title_zh"):
            entry["title_zh"] = np["title_zh"]
        if np.get("institutions"):
            entry["institutions"] = np["institutions"]
        if np.get("citations"):
            entry["citations"] = np["citations"]
        if np.get("abstract"):
            entry["abstract"] = np["abstract"]
        entry["source"] = "auto_ingest"

        graph["graph"]["papers"].append(entry)
        existing_dois.add(doi)
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


# ──── Internal helpers ────

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
    """Write graph back to YAML with preserved formatting where possible."""
    if yaml is None:
        return
    try:
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            yaml.dump(graph, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False)
    except Exception:
        pass
