"""
Memory Layer — Short-term + Long-term memory for the cognitive search engine.

Implements the formal memory transition function:

    M_{t+1} = Φ(M_t, O_t, A_t)

where:
  M_t   = current memory state (context + graph)
  O_t   = observation from last action (new papers, IG, errors)
  A_t   = action taken (phase name, query, tool call)
  Φ     = memory update function

Two subsystems:
  1. ContextTracker — short-term memory (LLM context window analog)
     - Current search state: species_id, papers found, tokens consumed
     - IG trajectory per phase
     - Error log & correction history
     - BDI belief snapshot (for Reflection)

  2. GraphMemory — long-term memory (RAG / vector DB analog)
     - Persistent paper index via species_graph.yaml
     - Author → paper reverse index
     - Journal → paper reverse index
     - Keyword / species name → paper forward index
     - Extensible to vector embeddings (reserved API)

Usage:
  from memory_layer import ContextTracker, GraphMemory, MemorySystem

  mem = MemorySystem()
  mem.start_search("Ochetobius_elongatus")
  mem.track_phase("exact_search", papers=5, tokens=500, ig=0.01)
  mem.commit_to_long_term()  # persist new papers to graph
"""

import json
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# ═══════════════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PhaseTrace:
    """Record of a single phase execution."""
    phase_name: str
    papers_found: int
    tokens_used: int
    ig: float                     # information gain (papers / (tokens/1000))
    error: str = ""
    timestamp: str = ""           # ISO-8601 or sequence number
    query: str = ""               # search query used
    source: str = ""              # "graph" | "pubmed" | "crossref" | "mcp"


@dataclass
class SearchContext:
    """Short-term memory snapshot for the current search session.

    Analogous to the LLM context window — tracks what the agent
    "remembers" about the current task.
    """
    species_id: str = ""
    started_at: str = ""           # ISO-8601 or empty
    phases: list[PhaseTrace] = field(default_factory=list)
    total_papers: int = 0
    total_tokens: int = 0
    active: bool = True
    error_count: int = 0
    correction_count: int = 0      # successful error recoveries

    @property
    def ig_trajectory(self) -> list[float]:
        return [p.ig for p in self.phases]

    @property
    def consecutive_zeros(self) -> int:
        count = 0
        for p in reversed(self.phases):
            if p.papers_found == 0:
                count += 1
            else:
                break
        return count

    @property
    def diminishing(self) -> bool:
        ig = self.ig_trajectory
        return len(ig) >= 3 and ig[-1] < ig[-2] < ig[-3]

    def to_dict(self) -> dict:
        return {
            "species_id": self.species_id,
            "phases": [p.__dict__ for p in self.phases],
            "total_papers": self.total_papers,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "correction_count": self.correction_count,
        }


# ═══════════════════════════════════════════════════════════════════════
# Context Tracker — Short-term Memory
# ═══════════════════════════════════════════════════════════════════════

class ContextTracker:
    """Manages the current search session's short-term memory.

    Tracks: phase execution history, paper/token counts, IG trajectory,
    error signals, and BDI belief snapshots.

    Memory transition: M_{t+1} = Φ(M_t, O_t, A_t)
      - M_t = current PhaseTrace list + paper/token counts
      - O_t = (new_papers, tokens, ig, error)
      - A_t = (phase_name, query)
      - Φ = append PhaseTrace, update accumulators
    """

    def __init__(self):
        self._ctx: Optional[SearchContext] = None
        self._history: list[SearchContext] = []  # past searches (meta-memory)

    def start_search(self, species_id: str) -> SearchContext:
        """Initialize a new search session."""
        self._ctx = SearchContext(species_id=species_id, active=True)
        return self._ctx

    def track_phase(self, phase_name: str, papers_found: int,
                    tokens_used: int, query: str = "",
                    error: str = "", source: str = "") -> PhaseTrace:
        """Record the outcome of a phase execution.

        This is the Φ function: append observation, update accumulators.
        """
        if self._ctx is None:
            self._ctx = SearchContext()

        ig = papers_found / max(tokens_used / 1000, 1)

        trace = PhaseTrace(
            phase_name=phase_name,
            papers_found=papers_found,
            tokens_used=tokens_used,
            ig=round(ig, 4),
            error=error,
            query=query,
            source=source,
        )
        self._ctx.phases.append(trace)
        self._ctx.total_papers += papers_found
        self._ctx.total_tokens += tokens_used

        if error:
            self._ctx.error_count += 1
        if error and papers_found > 0:
            self._ctx.correction_count += 1

        return trace

    @property
    def context(self) -> SearchContext:
        if self._ctx is None:
            self._ctx = SearchContext()
        return self._ctx

    def finish_search(self):
        """Archive current context to history and deactivate."""
        if self._ctx:
            self._ctx.active = False
            self._history.append(self._ctx)
            self._ctx = None

    def recall_last(self) -> Optional[SearchContext]:
        """Retrieve the most recent completed search (meta-memory)."""
        return self._history[-1] if self._history else None


# ═══════════════════════════════════════════════════════════════════════
# Graph Memory — Long-term Memory
# ═══════════════════════════════════════════════════════════════════════

class GraphMemory:
    """Long-term persistent memory backed by species_graph.yaml.

    Provides:
      - Paper lookup by species, author, journal, DOI
      - Reverse indexes (author → papers, journal → papers)
      - Auto-merging of new search results into the graph
      - Reserved vector-index API for future RAG integration

    This is the long-term component of M in the Memory transition function.
    """

    GRAPH_PATH = Path("config/species_graph.yaml")

    def __init__(self):
        self._graph: dict[str, Any] = {}
        self._paper_index: dict[str, dict] = {}       # doi → paper
        self._author_index: dict[str, set[str]] = defaultdict(set)  # author → dois
        self._journal_index: dict[str, set[str]] = defaultdict(set) # journal → dois
        self._species_index: dict[str, set[str]] = defaultdict(set) # species → dois
        self._loaded = False

    # ── Load ──

    def load(self) -> bool:
        """Load graph from disk and build in-memory indexes."""
        if yaml is None:
            return False
        try:
            if self.GRAPH_PATH.exists():
                with open(self.GRAPH_PATH, encoding="utf-8") as f:
                    self._graph = yaml.safe_load(f) or {}
                self._build_indexes()
                self._loaded = True
                return True
        except Exception:
            pass
        return False

    def _build_indexes(self):
        """Rebuild all reverse indexes from graph data."""
        self._paper_index.clear()
        self._author_index.clear()
        self._journal_index.clear()
        self._species_index.clear()

        papers = self._graph.get("graph", {}).get("papers", [])
        for p in papers:
            doi = (p.get("doi", "") or "").lower().strip()
            if doi:
                self._paper_index[doi] = p

            for author in p.get("authors", []):
                self._author_index[author.lower()].add(doi)

            journal = (p.get("journal", "") or "").lower()
            if journal:
                self._journal_index[journal].add(doi)

            for sp in p.get("species", []):
                self._species_index[sp].add(doi)

    def ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ── Query ──

    def get_papers_by_species(self, species_id: str) -> list[dict]:
        """Retrieve all papers for a given species."""
        self.ensure_loaded()
        dois = self._species_index.get(species_id, set())
        return [self._paper_index[d] for d in dois if d in self._paper_index]

    def get_papers_by_author(self, author: str) -> list[dict]:
        """Retrieve all papers by a given author (case-insensitive)."""
        self.ensure_loaded()
        dois = self._author_index.get(author.lower(), set())
        return [self._paper_index[d] for d in dois if d in self._paper_index]

    def get_papers_by_journal(self, journal: str) -> list[dict]:
        """Retrieve all papers from a given journal."""
        self.ensure_loaded()
        dois = self._journal_index.get(journal.lower(), set())
        return [self._paper_index[d] for d in dois if d in self._paper_index]

    def get_paper_by_doi(self, doi: str) -> Optional[dict]:
        """Look up a single paper by DOI."""
        self.ensure_loaded()
        return self._paper_index.get(doi.lower().strip())

    def get_authors(self) -> list[dict]:
        """Return all author nodes."""
        self.ensure_loaded()
        return self._graph.get("graph", {}).get("authors", [])

    def get_journals(self) -> list[str]:
        """Return all journal names."""
        self.ensure_loaded()
        return list(self._journal_index.keys())

    def get_species(self) -> list[dict]:
        """Return all species nodes."""
        self.ensure_loaded()
        return self._graph.get("graph", {}).get("species", [])

    # ── Mutation ──

    def add_paper(self, paper: dict, species_id: str) -> bool:
        """Add a single paper to the graph.  Returns True if new."""
        self.ensure_loaded()
        # Normalize Paper dataclass to dict
        if not isinstance(paper, dict):
            paper = paper.__dict__ if hasattr(paper, "__dataclass_fields__") else dict(paper)
        doi = (paper.get("doi", "") or "").lower().strip()
        if not doi or doi in self._paper_index:
            return False

        entry = {
            "doi": paper.get("doi", ""),
            "title": paper.get("title", ""),
            "year": paper.get("year"),
            "journal": paper.get("journal", ""),
            "authors": paper.get("authors", []),
            "species": [species_id],
            "source": "auto_ingest",
        }
        if paper.get("title_zh"):
            entry["title_zh"] = paper["title_zh"]
        if paper.get("institutions"):
            entry["institutions"] = paper["institutions"]
        if paper.get("abstract"):
            entry["abstract"] = paper["abstract"]

        self._graph.setdefault("graph", {}).setdefault("papers", []).append(entry)
        self._paper_index[doi] = entry
        self._species_index[species_id].add(doi)

        for author in entry.get("authors", []):
            self._author_index[author.lower()].add(doi)
        journal = (entry.get("journal", "") or "").lower()
        if journal:
            self._journal_index[journal].add(doi)

        return True

    def add_papers_batch(self, papers: list[dict], species_id: str) -> int:
        """Add multiple papers.  Returns count of newly added papers."""
        count = 0
        for p in papers:
            if self.add_paper(p, species_id):
                count += 1
        return count

    def save(self) -> bool:
        """Persist graph back to YAML file."""
        if yaml is None or not self._graph:
            return False
        try:
            with open(self.GRAPH_PATH, "w", encoding="utf-8") as f:
                yaml.dump(self._graph, f, allow_unicode=True,
                          default_flow_style=False, sort_keys=False)
            return True
        except Exception:
            return False

    # ── Stats ──

    @property
    def stats(self) -> dict:
        self.ensure_loaded()
        papers = self._graph.get("graph", {}).get("papers", [])
        return {
            "total_papers": len(papers),
            "unique_authors": len(self._author_index),
            "unique_journals": len(self._journal_index),
            "species_count": len(self._species_index),
            "edges": len(self._graph.get("graph", {}).get("edges", [])),
        }

    # ── Reserved: Vector Index API (future RAG integration) ──

    def embed_paper(self, doi: str) -> Optional[list[float]]:
        """Placeholder for vector embedding of paper abstract.

        Future: use sentence-transformers to generate an embedding,
        store in a vector DB (e.g., Chroma, Qdrant), return the vector.
        """
        paper = self.get_paper_by_doi(doi)
        if paper is None:
            return None
        # Placeholder — would call embedding model
        text = paper.get("abstract") or paper.get("title", "")
        return _placeholder_embed(text)

    def search_similar(self, query: str, top_k: int = 5) -> list[dict]:
        """Placeholder for vector similarity search.

        Future: encode query → search vector DB → return top_k papers.
        """
        _ = query, top_k
        return []


def _placeholder_embed(text: str) -> list[float]:
    """Deterministic placeholder for vector embedding (hash-based)."""
    h = hashlib.sha256(text.encode()).digest()
    return [float(b) / 255.0 for b in h[:64]]  # 64-dim pseudo-embedding


# ═══════════════════════════════════════════════════════════════════════
# Unified Memory System
# ═══════════════════════════════════════════════════════════════════════

class MemorySystem:
    """Combined short-term + long-term memory for the cognitive agent.

    Usage pattern during a search:
      1. mem.start_search(species_id)        → init short-term context
      2. mem.track_phase(name, papers, ...)  → update per phase
      3. mem.commit_to_long_term()           → persist new papers to graph
      4. mem.finish_search()                 → archive context

    Memory transition formula:
      M_{t+1} = Φ(M_t, O_t, A_t)
        - Short-term: append PhaseTrace to context
        - Long-term:  add new papers to graph if they persist across searches
    """

    def __init__(self):
        self.short_term = ContextTracker()
        self.long_term = GraphMemory()
        self._pending_papers: list[dict] = []
        self._species_id: str = ""

    def start_search(self, species_id: str, load_graph: bool = True):
        """Initialize both memory systems for a new search."""
        self._species_id = species_id
        self._pending_papers.clear()
        self.short_term.start_search(species_id)
        if load_graph:
            self.long_term.ensure_loaded()

    def track_phase(self, phase_name: str, papers_found: int,
                    tokens_used: int, query: str = "",
                    error: str = "", source: str = "",
                    new_papers: list[dict] = None) -> PhaseTrace:
        """Record a phase execution and queue new papers for long-term storage."""
        trace = self.short_term.track_phase(
            phase_name, papers_found, tokens_used,
            query=query, error=error, source=source,
        )
        if new_papers:
            self._pending_papers.extend(new_papers)
        return trace

    def commit_to_long_term(self) -> int:
        """Persist queued new papers to the graph."""
        if not self._pending_papers:
            return 0
        count = self.long_term.add_papers_batch(
            self._pending_papers, self._species_id
        )
        if count > 0:
            self.long_term.save()
        self._pending_papers.clear()
        return count

    def finish_search(self):
        """Archive context and persist any remaining papers."""
        self.commit_to_long_term()
        self.short_term.finish_search()

    @property
    def context(self) -> SearchContext:
        return self.short_term.context

    @property
    def graph_stats(self) -> dict:
        return self.long_term.stats

    @property
    def memory_state(self) -> dict:
        """Full memory state snapshot (for BDI Belief update)."""
        ctx = self.context
        return {
            "short_term": {
                "species_id": ctx.species_id,
                "phases_count": len(ctx.phases),
                "total_papers": ctx.total_papers,
                "total_tokens": ctx.total_tokens,
                "ig_trajectory": ctx.ig_trajectory,
                "consecutive_zeros": ctx.consecutive_zeros,
                "diminishing": ctx.diminishing,
            },
            "long_term": self.long_term.stats,
            "pending": len(self._pending_papers),
        }
