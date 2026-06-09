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
    validation: dict = field(default_factory=dict)   # cross-project validation result
    evolution: dict = field(default_factory=dict)    # evolution adaptations

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

            # ── Phase 1: WorldModel BDI + Contradiction Analysis ──
            volume_estimate = self._estimate_volume(species_id)

            # Contradiction-driven strategy selection
            known = self._load_known(species_id)
            contradiction = self._analyze_contradiction(
                species_id, volume_estimate, known, is_chinese
            )
            if full_pipeline is None:
                override = contradiction.get("strategy_override", {})
                full_pipeline = override.get("full_pipeline",
                    self._decide_pipeline(species_id, volume_estimate, is_chinese))

            # Log meso decision
            result.meso_log.append({
                "phase": "bdi",
                "volume_estimate": volume_estimate,
                "full_pipeline": full_pipeline,
                "species_chinese": species_info.get("chinese", ""),
                "contradiction": {
                    "primary": contradiction["primary_contradiction"],
                    "type": contradiction["contradiction_type"],
                    "budget_multiplier": contradiction["budget_multiplier"],
                },
            })

            # ── Phase 2: Memory / Graph load ──
            known_papers = self._load_known(species_id)
            result.meso_log.append({
                "phase": "graph_load",
                "known_papers": len(known_papers),
            })

            # ── Phase 3: Execute search (with contradiction strategy overrides) ──
            self._ensure_engine()
            if self._engine is None:
                result.errors.append("SearchRuleEngine not available")
            else:
                # Apply contradiction strategy overrides to engine parameters
                strategy = contradiction.get("strategy_override", {})
                if strategy:
                    if strategy.get("trust_threshold_boost"):
                        # Raise trust threshold to filter noise
                        self._engine.adaptive_params["trust_score_threshold"] = {
                            "value": 50 + strategy["trust_threshold_boost"]
                        }
                    if strategy.get("max_papers_satisfice"):
                        self.config.min_papers_satisfice = strategy["max_papers_satisfice"]
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

                # ── Phase 4.5: Cross-Project Validation ──
                try:
                    from src.validator import validate_papers as validate
                    validation = validate(
                        result.papers,
                        min_sources=3,
                        min_projects=2,
                    )
                    result.meso_log.append({
                        "phase": "cross_validation",
                        "independence_passed": validation.stats["independence_passed"],
                        "verified": validation.stats["verified_count"],
                        "unique_projects": validation.stats["unique_projects"],
                        "violations": len(validation.independence_violations),
                    })
                    result.validation = validation.stats
                    if validation.independence_violations:
                        result.errors.extend(
                            v["violation"] for v in validation.independence_violations
                        )
                    # Tag papers with credibility scores
                    self._score_credibility(result.papers)
                except ImportError:
                    # Fallback: still score credibility even if validator unavailable
                    self._score_credibility(result.papers)

                # ── Phase 4.6: Evolution Feedback ──
                try:
                    from src.evolution_executor import EvolutionExecutor
                    evo_path = self.config.evolution_config_path
                    if not Path(evo_path).exists():
                        import os as _os
                        base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
                        evo_path = _os.path.join(base, "config", "evolution.yaml")
                    executor = EvolutionExecutor(evo_path)
                    metrics = {
                        "pipeline_success_rate": 1.0 if not result.errors else 0.5,
                        "recall_rate": len(result.papers) / max(volume_estimate, 1),
                        "avg_tokens_per_query": result.total_cost,
                        "contradiction_rate": (
                            0.0 if contradiction["contradiction_type"] != "antagonistic"
                            else 0.4
                        ),
                    }
                    actions = executor.evaluate_and_adapt(metrics)
                    result.evolution = {"adaptations": len(actions), "triggered": [a.trigger_name for a in actions]}
                    if actions:
                        result.meso_log.append({
                            "phase": "evolution",
                            "adaptations": [
                                {"param": a.param, "old": a.old_value, "new": a.new_value}
                                for a in actions if a.param
                            ],
                        })
                except ImportError:
                    pass

        except Exception as e:
            logger.exception("MesoAgent.search failed")
            result.errors.append(f"{type(e).__name__}: {e}")

        # ── Post-search: Inference Engine (P3) ──
        try:
            from src.inference_engine import InferenceEngine
            ie = InferenceEngine()
            inference = ie.infer(result.papers, species_id)
            result.meso_log.append({
                "phase": "inference",
                "gaps_found": len(inference.knowledge_gaps),
                "followup_queries": len(inference.followup_queries),
                "contradictions": inference.contradictions_found,
            })
            if inference.knowledge_gaps:
                result.meso_log[-1]["gaps"] = inference.knowledge_gaps[:3]
            if inference.followup_queries:
                result.meso_log[-1]["queries"] = inference.followup_queries[:3]
        except ImportError:
            pass

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

    def _analyze_contradiction(self, species_id: str, volume: int,
                                known_papers: list[dict],
                                is_chinese: bool) -> dict:
        """Contradiction-driven search strategy analysis.

        Identifies the PRIMARY contradiction for a species search and
        routes resources accordingly.  Follows the same pattern as
        porpoise-agent's orchestrator.ContradictionSignal.

        Contradiction types:
          - DATA_SCARCITY:    < 20 papers known → exhaustive mode, expand all variants
          - DATA_NOISE:       many papers but low quality → tighten trust threshold
          - CHINESE_GAP:      Chinese species, Western DB blind spot → CN-first strategy
          - NEW_EMERGENCE:    recent papers detected → forward-citation traversal
          - TAXONOMIC_CONFUSION: name variants / OCR errors → variant-first strategy

        Returns:
            {
                "primary_contradiction": str,
                "contradiction_type": "antagonistic" | "non_antagonistic" | "structural",
                "budget_multiplier": float,
                "strategy_override": dict | None,
            }
        """
        result = {
            "primary_contradiction": "DATA_SCARCITY",
            "contradiction_type": "structural",
            "budget_multiplier": 1.0,
            "strategy_override": None,
        }

        # ── Contradiction 1: Data scarcity (< 20 papers) ──
        if volume < 20:
            result["primary_contradiction"] = "DATA_SCARCITY"
            result["contradiction_type"] = "antagonistic"
            result["budget_multiplier"] = 2.5  # 2.5x resources
            result["strategy_override"] = {
                "full_pipeline": True,
                "variant_expansion": "aggressive",  # generate ALL OCR variants
                "citation_traversal_depth": 3,
                "author_backward_search": True,
                "chinese_sources": is_chinese,
            }
            return result

        # ── Contradiction 2: Chinese database gap (v5.6: 不限 volume) ──
        # 中文物种在西方数据库 (PubMed/Crossref) 中搜索量≠中文文献量
        # 中国知网/万方/百度学术/CAS 的中文文献是独立的，无法被西方 DB 覆盖
        if is_chinese:
            result["primary_contradiction"] = "CHINESE_GAP"
            result["contradiction_type"] = "non_antagonistic"
            result["budget_multiplier"] = 2.0
            result["strategy_override"] = {
                "full_pipeline": True,
                "chinese_priority": True,    # CNKI/万方/百度学术/CAS first
                "review_mining_first": True,  # mine Chinese reviews
            }
            return result

        # ── Contradiction 3: Data noise (large volume, mixed quality) ──
        if volume > 200:
            result["primary_contradiction"] = "DATA_NOISE"
            result["contradiction_type"] = "structural"
            result["budget_multiplier"] = 0.5  # conserve tokens
            result["strategy_override"] = {
                "full_pipeline": False,
                "trust_threshold_boost": 10,    # raise trust threshold
                "max_papers_satisfice": 12,
            }
            return result

        # ── Contradiction 4: New emergence ──
        current_year = __import__("datetime").datetime.now().year
        recent_papers = [
            p for p in known_papers
            if p.get("year") and p.get("year", 0) >= current_year - 1
        ]
        if len(recent_papers) >= 3 and len(recent_papers) / max(volume, 1) > 0.3:
            result["primary_contradiction"] = "NEW_EMERGENCE"
            result["contradiction_type"] = "phasic"
            result["budget_multiplier"] = 1.8
            result["strategy_override"] = {
                "full_pipeline": True,
                "forward_citation_priority": True,  # who cited these new papers?
                "new_paper_detection": True,
            }
            return result

        # ── Contradiction 5: Taxonomic confusion (known OCR variants) ──
        species_info = self._species_map.get(species_id, {})
        variants = species_info.get("variants", [])
        if len(variants) >= 3:
            result["primary_contradiction"] = "TAXONOMIC_CONFUSION"
            result["contradiction_type"] = "non_antagonistic"
            result["budget_multiplier"] = 1.5
            result["strategy_override"] = {
                "full_pipeline": True,
                "variant_first": True,       # search variants before exact name
                "phonetic_search": True,      # Soundex/Metaphone
            }
            return result

        # Default: moderate search
        result["budget_multiplier"] = 1.0
        result["strategy_override"] = {"full_pipeline": volume < 100}
        return result

    # ──── Internal ────

    def _ensure_engine(self):
        """Lazy-init SearchRuleEngine."""
        if self._engine is not None:
            return
        if SearchRuleEngine is None:
            return
        try:
            self._engine = SearchRuleEngine(self.config.rules_path, mode=self.config.mode)
        except (FileNotFoundError, Exception):
            # Fallback: try absolute path derived from this file's location
            try:
                import os
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                abs_rules = os.path.join(base, "config", "search_rules.yaml")
                self._engine = SearchRuleEngine(abs_rules, mode=self.config.mode)
                self.config.rules_path = abs_rules  # update for future calls
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
        """Estimate literature volume using multi-source (PubMed/Scholar/Web) or graph fallback.

        Implements fuzzy-species-search-rule v5.0:
          ncbi_esearch(scientific_name) → total_count
          scholar_search_literature_graph(scientific_name, limit=5) → rough_estimate
          web_search(chinese_name + " 论文 OR 综述", topK=5) → chinese_hits
          RETURN MAX(pubmed_count, scholar_count, chinese_hits * 0.5)
        """
        # ── Primary: WorldModel prediction ──
        if WorldModel is not None and self._world is None:
            try:
                from src.graph_updater import load_species_graph as lgs
                known = lgs(species_id)
                self._world = WorldModel()
                self._world.init_belief(species_id, len(known))
                prediction = self._world.predict(species_id)
                wm_volume = prediction.get("estimated_volume", len(known))
                if wm_volume > len(known):
                    return wm_volume
            except Exception:
                pass

        # ── Secondary: Multi-source HTTP estimation ──
        multi = self._estimate_literature_volume_multi(species_id)
        if multi > 0:
            return multi

        # ── Fallback: count known papers from graph ──
        known = self._load_known(species_id)
        return max(len(known), 8)

    def _estimate_literature_volume_multi(self, species_id: str) -> int:
        """Multi-source literature volume estimation via HTTP REST APIs.

        Uses PubMed E-utilities (esearch), Crossref, and Chinese web search
        to estimate total literature volume for adaptive search strategy.

        Returns:
            Estimated volume as MAX(pubmed_count, scholar_count, chinese_hits * 0.5).
            Returns 0 if all sources fail.
        """
        self._ensure_graph_loaded()
        species_info = self._species_map.get(species_id, {})
        scientific_name = species_info.get("name", species_id.replace("_", " "))
        chinese_name = species_info.get("chinese", "")

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from urllib.parse import quote as _url_quote
        import urllib.request as _urlreq
        import json as _json

        pubmed_count: int = 0
        scholar_count: int = 0
        chinese_hits: int = 0

        def _fetch_pubmed():
            nonlocal pubmed_count
            # v5.6: Europe PMC primary (fast, live), NCBI E-utilities as fallback
            try:
                epmc_url = (
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
                    f"query={_url_quote(scientific_name)}&resultType=lite&pageSize=1&format=json"
                )
                req = _urlreq.Request(epmc_url, headers={
                    "User-Agent": "CognitiveSearchEngine/5.6",
                    "Accept": "application/json",
                })
                with _urlreq.urlopen(req, timeout=5) as resp:
                    epmc_data = _json.loads(resp.read())
                pubmed_count = int(epmc_data.get("hitCount", 0) or 0)
            except Exception:
                # NCBI fallback (often 500, skips fast)
                try:
                    url = (
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                        f"db=pubmed&term={_url_quote(scientific_name)}&retmax=0&retmode=json"
                    )
                    with _urlreq.urlopen(url, timeout=3) as resp:
                        data = _json.loads(resp.read())
                    pubmed_count = int(data.get("esearchresult", {}).get("count", "0") or "0")
                except Exception:
                    pass

        def _fetch_crossref():
            nonlocal scholar_count
            try:
                url = (
                    "https://api.crossref.org/works?"
                    f"query={_url_quote(scientific_name)}&rows=0"
                )
                with _urlreq.urlopen(url, timeout=5) as resp:
                    data = _json.loads(resp.read())
                scholar_count = int(data.get("message", {}).get("total-results", 0) or 0)
            except Exception:
                pass

        def _fetch_chinese():
            nonlocal chinese_hits
            if not chinese_name:
                return
            try:
                # Use Bing web search for Chinese literature presence estimate
                bing_url = (
                    "https://www.bing.com/search?"
                    f"q={_url_quote(chinese_name + ' 论文 OR 综述')}&count=5"
                )
                req = _urlreq.Request(bing_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Reasonix/1.0)",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                })
                with _urlreq.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                # Count search result blocks as rough estimate.
                # NOTE: Fragile — depends on Bing's HTML class names.
                # If Bing changes markup, chinese_hits stays 0 (safe fallback).
                import re
                blocks = re.findall(r'<li class="b_algo"', html)
                chinese_hits = len(blocks) * 3  # each Bing result ≈ 3 papers
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = [pool.submit(f) for f in (_fetch_pubmed, _fetch_crossref, _fetch_chinese)]
            for fut in as_completed(futs):
                try:
                    fut.result(timeout=12)
                except Exception:
                    pass

        return max(pubmed_count, scholar_count, int(chinese_hits * 0.5))

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

    @staticmethod
    def _score_credibility(papers: list[dict]):
        """Ensure every paper dict has a credibility_score via validator module.

        Uses the SCI/CSCD/preprint-aware scoring from src/validator.credibility_score().
        Papers already scored are left untouched; unscored papers get a computed score.
        """
        try:
            from src.validator import credibility_score, Paper as ValPaper
        except ImportError:
            return

        for p in papers:
            if "credibility_score" in p:
                continue
            try:
                vp = ValPaper(
                    doi=p.get("doi", ""),
                    title=p.get("title", ""),
                    year=p.get("year"),
                    journal=p.get("journal", ""),
                    authors=p.get("authors", []),
                    citations=p.get("citations", 0),
                    pmid=p.get("pmid"),
                    pmcid=p.get("pmcid"),
                )
                cs = credibility_score(vp)
                p["credibility_score"] = max(0, cs) if cs >= 0 else 0
                p["trust"] = p.get("trust", (
                    "verified" if cs >= 80 else
                    "tentative" if cs >= 50 else
                    "rejected" if cs >= 0 else
                    "retracted"
                ))
            except Exception:
                p["credibility_score"] = 50  # neutral default


# ──── Convenience ────

def create_agent(mode: str = "http") -> MesoAgent:
    """Factory: create a MesoAgent with default config."""
    return MesoAgent(MesoConfig(mode=mode))
