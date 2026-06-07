"""
MesoAgent — 中宇宙式 Agent，宏观（BDI）与微观（工具调用）之间的协调层。

┌──────────────────────────────────────────────────────────────────┐
│                    Macro-cosmos (CognitiveAgent)                  │
│  意图形成 · 策略选择 · BDI 推理                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│           Meso-cosmos · 中宇宙 (MesoAgent)                        │
│   ┌────────────┐  ┌──────────────┐  ┌───────────────┐            │
│   │ WorldModel │  │ SearchRule   │  │ MemorySystem   │            │
│   │ (BDI)      │→ │ Engine       │→ │ (Context/Graph)│            │
│   └────────────┘  │ (Phases)     │  └───────┬───────┘            │
│                   └──────┬───────┘          │                    │
│                          │                  │                    │
│                   ┌──────▼───────┐   ┌──────▼───────┐            │
│                   │ GraphUpdater │   │ ZN/EN Rules  │            │
│                   │ (Persistence)│   │ (Language)   │            │
│                   └──────────────┘   └──────────────┘            │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    Micro-cosmos (Tools)                           │
│  PubMed E-utilities · Crossref · OpenAlex · MCP servers · HTTP    │
└──────────────────────────────────────────────────────────────────┘

Usage:
    from src.meso_agent import MesoAgent

    agent = MesoAgent(mode="http")
    result = agent.search("Ochetobius_elongatus")
    
    # Result contains:
    # - papers: list[Paper]
    # - stats: {total_papers, new_papers, total_cost, ig_final, ...}
    # - meso_log: list of phase execution records
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Conditional imports — each module can fail independently
try:
    from src.world_model import WorldModel
except ImportError:
    WorldModel = None

try:
    from src.memory_layer import MemorySystem
except ImportError:
    MemorySystem = None

try:
    from src.rule_engine import SearchRuleEngine
except ImportError:
    SearchRuleEngine = None

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger("meso_agent")


# ──── Data Classes ────


@dataclass
class MesoResult:
    """Structured result from a MesoAgent search."""
    species_id: str
    papers: list[dict] = field(default_factory=list)
    new_papers: int = 0
    total_cost: float = 0.0      # estimated token cost
    elapsed_sec: float = 0.0
    ig_final: float = 0.0         # information gain at end
    phase_count: int = 0
    stop_reason: str = ""
    meso_log: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "species_id": self.species_id,
            "papers": self.papers,
            "new_papers": self.new_papers,
            "total_cost": self.total_cost,
            "elapsed_sec": self.elapsed_sec,
            "ig_final": self.ig_final,
            "phase_count": self.phase_count,
            "stop_reason": self.stop_reason,
            "meso_log": self.meso_log,
            "errors": self.errors,
        }


@dataclass
class MesoConfig:
    """MesoAgent configuration."""
    mode: str = "http"                          # http / mcp / recorded / mock
    graph_path: str = "config/species_graph.yaml"
    rules_path: str = "config/search_rules.yaml"
    agent_config_path: str = "config/agent.yaml"

    # Energy budget
    max_tokens: int = 50000
    min_papers_satisfice: int = 8
    max_papers_exhaustive: int = 20

    # ZN/EN (中文/English)
    cn_auto_authors_zh: bool = True             # auto-fill authors_zh
    zn_en_dedup: bool = True                    # dedup ZN/EN dual versions
    cn_review_first: bool = True                # review-first for Chinese species
    
    # Self-evolution
    evolution_enabled: bool = True
    evolution_config_path: str = "config/evolution.yaml"


# ──── MesoAgent ────


class MesoAgent:
    """中宇宙式 Agent — the coordination layer.

    Wraps WorldModel (BDI), SearchRuleEngine (execution),
    MemorySystem (context), and GraphUpdater (persistence)
    into one coherent search pipeline.
    """

    def __init__(self, config: MesoConfig | None = None):
        self.config = config or MesoConfig()

        # Lazy-init sub-modules
        self._world: Any = None
        self._engine: Any = None
        self._memory: Any = None
        self._graph: dict | None = None

        # ZN/EN species registry (lazy-loaded from graph)
        self._species_map: dict[str, dict] = {}  # species_id → {name, chinese, family, ...}

    # ──── Public API ────

    def search(self, species_id: str, full_pipeline: bool | None = None) -> MesoResult:
        """Execute a full search for a species through the meso-cosmos pipeline.

        Pipeline:
          1. Load species info (ZN/EN detection)
          2. Initialize BDI belief (WorldModel.predict)
          3. Load known papers (MemorySystem / Graph)
          4. Execute search phases (SearchRuleEngine)
          5. Update graph with new papers (GraphUpdater)
          6. Report metrics (IG, cost, recall)
        """
        start = time.time()
        result = MesoResult(species_id=species_id)

        try:
            # ── Phase 0: Load graph & species info ──
            self._ensure_graph_loaded()
            species_info = self._species_map.get(species_id, {})
            is_chinese = bool(species_info.get("chinese", ""))

            # ── Phase 1: WorldModel BDI ──
            volume_estimate = self._estimate_volume(species_id)
            if full_pipeline is None:
                full_pipeline = self._decide_pipeline(species_id, volume_estimate, is_chinese)

            # Log meso decision
            result.meso_log.append({
                "phase": "bdi",
                "volume_estimate": volume_estimate,
                "full_pipeline": full_pipeline,
                "species_chinese": species_info.get("chinese", ""),
            })

            # ── Phase 2: Memory / Graph load ──
            known_papers = self._load_known(species_id)
            result.meso_log.append({
                "phase": "graph_load",
                "known_papers": len(known_papers),
            })

            # ── Phase 3: Execute search ──
            self._ensure_engine()
            if self._engine is None:
                result.errors.append("SearchRuleEngine not available")
            else:
                engine_result = self._engine.execute(species_id)

                raw_papers = engine_result.get("papers", [])
                # Normalize: Paper dataclass → dict
                result.papers = [
                    p.__dict__ if hasattr(p, '__dataclass_fields__') else p
                    for p in raw_papers
                ]
                stats = engine_result.get("stats", engine_result)

                result.phase_count = stats.get("phases_run", 0) or stats.get("phases_executed", 0)
                result.stop_reason = stats.get("stop_reason", "") or stats.get("stop_reason", "")
                result.total_cost = stats.get("total_cost", 0.0) or stats.get("tokens_spent", 0)
                ig = stats.get("ig_final", 0.0) or 0.0
                result.ig_final = ig

                result.meso_log.append({
                    "phase": "search",
                    "papers_found": len(result.papers),
                    "phases_run": result.phase_count,
                    "stop_reason": result.stop_reason,
                })

                # ── Phase 4: Graph update (with ZN/EN rules) ──
                new_count = self._update_graph(
                    species_id, result.papers, is_chinese
                )
                result.new_papers = new_count
                result.meso_log.append({
                    "phase": "graph_update",
                    "new_papers_added": new_count,
                })

        except Exception as e:
            logger.exception("MesoAgent.search failed")
            result.errors.append(f"{type(e).__name__}: {e}")

        result.elapsed_sec = round(time.time() - start, 3)
        return result

    def stats(self, species_id: str | None = None) -> dict:
        """Return graph statistics."""
        try:
            from src.graph_updater import get_graph_stats
            return get_graph_stats(species_id)
        except Exception:
            return {"papers": 0, "authors": 0, "journals": 0, "edges": 0}

    def get_papers(self, species_id: str) -> list[dict]:
        """Load known papers for a species from the graph."""
        try:
            from src.graph_updater import load_species_graph
            return load_species_graph(species_id)
        except Exception:
            return []

    # ──── ZN/EN helpers ────

    def _is_chinese_species(self, species_id: str) -> bool:
        """Check if a species has a Chinese common name (implies Chinese literature exists)."""
        self._ensure_graph_loaded()
        info = self._species_map.get(species_id, {})
        return bool(info.get("chinese", ""))

    def _decide_pipeline(self, species_id: str, volume: int, is_chinese: bool) -> bool:
        """Decide whether to run full pipeline or lightweight search.

        Rules:
          - Volume < 20 → exhaustive (full)
          - Volume 20-100 → classification mode (full)
          - Volume > 100 AND reviewed → lightweight
          - Chinese species → review-first strategy
        """
        if volume < 20:
            return True
        if volume < 100:
            return True
        # Large volume — check if reviews exist
        known = self._load_known(species_id)
        has_review = any(
            self._is_review(p.get("title", ""))
            for p in known
        )
        if not has_review:
            return True  # No review → need full search
        return False

    # ──── Internal ────

    def _ensure_engine(self):
        """Lazy-init SearchRuleEngine."""
        if self._engine is not None:
            return
        if SearchRuleEngine is None:
            return
        try:
            self._engine = SearchRuleEngine(self.config.rules_path, mode=self.config.mode)
        except Exception:
            pass

    def _ensure_graph_loaded(self):
        """Load species_graph.yaml into memory and build species map."""
        if self._graph is not None:
            return
        if yaml is None:
            self._graph = {"graph": {"species": [], "papers": [], "authors": [], "journals": []}}
            return
        path = Path(self.config.graph_path)
        if not path.exists():
            self._graph = {"graph": {"species": [], "papers": [], "authors": [], "journals": []}}
            return
        try:
            with open(path, encoding="utf-8") as f:
                self._graph = yaml.safe_load(f) or {"graph": {}}
        except Exception:
            self._graph = {"graph": {"species": [], "papers": [], "authors": [], "journals": []}}

        # Build species map
        for s in self._graph.get("graph", {}).get("species", []):
            sid = s.get("id", "")
            if sid:
                self._species_map[sid] = s

    def _estimate_volume(self, species_id: str) -> int:
        """Estimate literature volume using WorldModel or graph fallback."""
        if WorldModel is not None and self._world is None:
            try:
                from src.graph_updater import load_species_graph
                known = load_species_graph(species_id)
                self._world = WorldModel()
                self._world.init_belief(species_id, len(known))
                prediction = self._world.predict(species_id)
                return prediction.get("estimated_volume", len(known))
            except Exception:
                pass
        # Fallback: count known papers
        known = self._load_known(species_id)
        return max(len(known), 8)

    def _load_known(self, species_id: str) -> list[dict]:
        """Load known papers from graph."""
        try:
            from src.graph_updater import load_species_graph
            return load_species_graph(species_id)
        except Exception:
            return []

    def _update_graph(self, species_id: str, papers: list[dict], is_chinese: bool) -> int:
        """Update graph with ZN/EN-aware rules.

        Handles:
          - authors_zh auto-fill for Chinese journals
          - New author registration
          - New journal registration
          - ZN/EN dedup
        """
        try:
            from src.graph_updater import update_species_graph
            return update_species_graph(species_id, papers)
        except ImportError:
            return 0
        except Exception:
            return 0

    @staticmethod
    def _is_review(title: str) -> bool:
        """Check if a paper title suggests it's a review."""
        keywords = [
            "review", "survey", "overview", "进展", "综述",
            "status", "retrospective", "meta-analysis",
            "bibliometric", "研究进展", "展望",
        ]
        title_lower = title.lower()
        return any(kw in title_lower for kw in keywords)


# ──── Convenience ────

def create_agent(mode: str = "http") -> MesoAgent:
    """Factory: create a MesoAgent with default config."""
    return MesoAgent(MesoConfig(mode=mode))
