"""
MesoAgent — 中宇宙协调层 (Mesocosm Orchestrator)

Cognitive-search-engine 的 BDI 认知架构入口：
  Belief  (信念)  → 加载物种图谱 + 文献量估算
  Desire  (欲望)  → 规划搜索策略 (自适应模式选择)
  Intention (意图) → 多阶段搜索执行 + 验证 + 评分 + 图谱回写

用法:
    from src.meso_agent import MesoAgent, create_agent

    agent = MesoAgent(MesoConfig(mode="http"))
    result = agent.search("Pseudaspius_hakonensis")
    # result.papers, result.new_papers, result.total_cost, ...
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════

@dataclass
class MesoConfig:
    """MesoAgent 运行配置."""
    mode: str = "http"               # http | direct (http 使用 MCP 工具; direct 用本地函数)
    max_tokens: int = 50000
    min_papers_satisfice: int = 8
    max_papers: int = 30
    timeout_s: int = 300
    enable_inference: bool = True     # 启用 P3 推理增强
    enable_evolution: bool = True     # 启用自进化
    enable_cross_validation: bool = True  # 启用跨项目验证
    enable_graph_update: bool = True  # 搜索后更新图谱
    verbose: bool = False


# ═══════════════════════════════════════════════════════════
# Result type
# ═══════════════════════════════════════════════════════════

@dataclass
class MesoSearchResult:
    """MesoAgent.search() 的返回类型."""
    species_id: str = ""
    papers: List[Dict[str, Any]] = field(default_factory=list)
    new_papers: int = 0
    total_cost: int = 0          # token 消耗
    phase_count: int = 0
    stop_reason: str = ""
    errors: List[str] = field(default_factory=list)
    meso_log: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_s: float = 0.0
    mode_used: str = ""          # 实际使用的搜索模式
    volume_estimate: int = 0
    adaptations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "species_id": self.species_id,
            "papers": self.papers,
            "new_papers": self.new_papers,
            "total_cost": self.total_cost,
            "phase_count": self.phase_count,
            "stop_reason": self.stop_reason,
            "errors": self.errors,
            "elapsed_s": self.elapsed_s,
            "mode_used": self.mode_used,
            "volume_estimate": self.volume_estimate,
        }


# ═══════════════════════════════════════════════════════════
# MesoAgent
# ═══════════════════════════════════════════════════════════

class MesoAgent:
    """中宇宙 Agent — BDI 搜索循环的核心协调器。

    BDI Cycle:
      1. Belief  — 加载物种图谱、估算文献量、初始化 WorldModel
      2. Desire  — 根据估算选择搜索策略（自适应/穷举/分类/综述锚定）
      3. Intention — 执行多阶段搜索 → 验证 → 评分 → 图谱回写
    """

    def __init__(self, config: Optional[MesoConfig] = None) -> None:
        self.config = config or MesoConfig()
        self._engine_root: Path = Path(__file__).resolve().parent.parent
        self._species_map: Dict[str, dict] = {}
        self._world: Any = None  # WorldModel instance (lazy)
        self._mcp: Any = None    # McpClient instance (lazy)

        # 导入依赖 (延迟加载)
        self._WorldModel: Any = None
        self._SearchCoordinator: Any = None
        self._Validator: Any = None
        self._CredibilityScorer: Any = None
        self._EvolutionExecutor: Any = None
        self._InferenceEngine: Any = None

    # ── Lazy imports ──────────────────────────────────────────────

    def _ensure_deps(self) -> None:
        """Lazy-import all dependent modules."""
        try:
            from src.world_model import WorldModel as _WM
            self._WorldModel = _WM
        except ImportError:
            pass

        try:
            from src.search_coordinator import search as _sc_search
            from src.search_coordinator import SearchResult as _SCR
            self._SearchCoordinator = (_sc_search, _SCR)
        except ImportError:
            pass

        try:
            from src.validator import validate_papers as _vp
            self._Validator = _vp
        except ImportError:
            pass

        try:
            from src.credibility_scorer import score_paper as _sp
            self._CredibilityScorer = _sp
        except ImportError:
            pass

        try:
            from src.evolution_executor import EvolutionExecutor as _EE
            self._EvolutionExecutor = _EE
        except ImportError:
            pass

        try:
            from src.inference_engine import InferenceEngine as _IE
            self._InferenceEngine = _IE
        except ImportError:
            pass

    def _get_mcp(self) -> Any:
        """Lazy-init McpClient."""
        if self._mcp is None:
            try:
                from src.mcp_client import McpClient
                self._mcp = McpClient()
            except ImportError:
                pass
        return self._mcp

    # ── Graph loading ─────────────────────────────────────────────

    def _ensure_graph_loaded(self) -> None:
        """Load species graph into self._species_map."""
        if self._species_map:
            return

        graph_path = self._engine_root / "config" / "species_graph.yaml"
        if not graph_path.exists():
            logger.warning(f"Species graph not found at {graph_path}")
            return

        try:
            import yaml
            with open(graph_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            species_list = data.get("graph", {}).get("species", []) if isinstance(data, dict) else []
            for sp in species_list:
                sid = sp.get("id", "")
                if sid:
                    self._species_map[sid] = sp
            logger.info(f"Loaded {len(self._species_map)} species from graph")
        except Exception as e:
            logger.warning(f"Failed to load species graph: {e}")

    def _load_known(self, species_id: str) -> List[Dict[str, Any]]:
        """Load known papers for a species from the graph."""
        self._ensure_graph_loaded()
        species_info = self._species_map.get(species_id, {})
        # If we had a full graph DB, query it; fallback to config data
        papers: List[Dict[str, Any]] = []
        if species_info:
            papers.append({
                "species_id": species_id,
                "name": species_info.get("name", ""),
                "chinese": species_info.get("chinese", ""),
                "family": species_info.get("family", ""),
                "conservation": species_info.get("conservation", ""),
                "aliases": species_info.get("aliases", []),
                "variants": species_info.get("variants", []),
                "source": "graph",
            })
        return papers

    # ── BDI: Belief — literature volume estimation ────────────────

    def _estimate_volume(self, species_id: str) -> int:
        """Estimate literature volume using multi-source (PubMed/Scholar/Web) or graph fallback.

        Implements fuzzy-species-search-rule v5.0:
          ncbi_esearch(scientific_name) → total_count
          scholar_search_literature_graph(scientific_name, limit=5) → rough_estimate
          web_search(chinese_name + " 论文 OR 综述", topK=5) → chinese_hits
          RETURN MAX(pubmed_count, scholar_count, chinese_hits * 0.5)
        """
        # ── Primary: WorldModel prediction ──
        if self._WorldModel is not None and self._world is None:
            try:
                known = self._load_known(species_id)
                self._world = self._WorldModel()
                prediction = self._world.predict(species_id, len(known))
                wm_volume = prediction.estimated_volume if hasattr(prediction, "estimated_volume") else len(known)
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
            try:
                url = (
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                    f"db=pubmed&term={_url_quote(scientific_name)}&retmax=0&retmode=json"
                )
                with _urlreq.urlopen(url, timeout=10) as resp:
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
                with _urlreq.urlopen(url, timeout=10) as resp:
                    data = _json.loads(resp.read())
                scholar_count = int(data.get("message", {}).get("total-results", 0) or 0)
            except Exception:
                pass

        def _fetch_chinese():
            nonlocal chinese_hits
            if not chinese_name:
                return
            try:
                import re
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
                blocks = re.findall(r'<li class="b_algo"', html)
                chinese_hits = len(blocks) * 3
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

    # ── BDI: Desire — search strategy planning ────────────────────

    def _plan_search(self, species_id: str, volume: int) -> Dict[str, Any]:
        """基于文献量估算规划搜索策略 (Desire 阶段)."""
        self._ensure_graph_loaded()
        species_info = self._species_map.get(species_id, {})
        conservation = species_info.get("conservation", "LC")

        # 模式选择
        if volume <= 30:
            mode = "exhaustive"
            full_pipeline = True
        elif volume <= 200:
            mode = "classified"
            full_pipeline = True
        else:
            mode = "review_anchored"
            full_pipeline = True

        # 受保护物种 → 更全面搜索
        if conservation in ("CR", "EN"):
            if mode != "exhaustive":
                mode = "exhaustive"
                full_pipeline = True

        return {
            "mode": mode,
            "full_pipeline": full_pipeline,
            "volume_estimate": volume,
            "conservation": conservation,
        }

    # ── BDI: Intention — search execution ─────────────────────────

    def _execute_search(self, species_id: str, plan: Dict[str, Any],
                        mcp: Any) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """执行多阶段搜索 (Intention 阶段).

        Returns:
            (papers, total_cost, errors)
        """
        papers: List[Dict[str, Any]] = []
        total_cost = 0
        errors: List[str] = []
        mode = plan.get("mode", "exhaustive")
        species_info = self._species_map.get(species_id, {})
        scientific_name = species_info.get("name", species_id.replace("_", " "))
        chinese_name = species_info.get("chinese", "")
        variants = species_info.get("variants", [])
        min_satisfice = self.config.min_papers_satisfice

        # ── Phase 1: Graph lookup (FREE) ──
        known = self._load_known(species_id)
        for k in known:
            k["_phase"] = "graph_lookup"
            papers.append(k)
        logger.info(f"Phase 1 graph_lookup: {len(known)} known items")

        if len(papers) >= min_satisfice and mode != "exhaustive":
            return papers[:self.config.max_papers], total_cost, errors

        # ── Phase 2: Exact search via MCP ──
        if mcp and len(papers) < min_satisfice:
            try:
                # 2a. Scholar search (scientific name)
                scholar_results = mcp.search_scholar(scientific_name, limit=10)
                for item in _extract_papers(scholar_results, "scholar"):
                    item["_phase"] = "exact_search"
                    papers.append(item)
                total_cost += 500

                # 2b. Article search (scientific name)
                article_results = mcp.search_article(scientific_name, max_results=10)
                for item in _extract_papers(article_results, "article"):
                    item["_phase"] = "exact_search"
                    papers.append(item)
                total_cost += 500

                # 2c. Tavily web search
                if chinese_name:
                    tavily_results = mcp.search_tavily(
                        f"{chinese_name} {scientific_name} 鱼类 研究 论文",
                        max_results=5,
                    )
                    for item in _extract_papers(tavily_results, "tavily"):
                        item["_phase"] = "exact_search"
                        papers.append(item)
                    total_cost += 300
            except Exception as e:
                errors.append(f"Phase 2 exact_search: {e}")

        papers = _dedup_papers(papers)
        if len(papers) >= min_satisfice and mode != "exhaustive":
            return papers[:self.config.max_papers], total_cost, errors

        # ── Phase 3: Variant search ──
        if mcp and variants and len(papers) < min_satisfice:
            try:
                for variant in variants:
                    vr = mcp.search_scholar(variant, limit=5)
                    for item in _extract_papers(vr, "scholar_variant"):
                        item["_phase"] = "variant_search"
                        papers.append(item)
                    total_cost += 200
            except Exception as e:
                errors.append(f"Phase 3 variant_search: {e}")

        papers = _dedup_papers(papers)
        if len(papers) >= min_satisfice:
            return papers[:self.config.max_papers], total_cost, errors

        # ── Phase 4: Citation traversal (if we have DOIs) ──
        papers_with_doi = [p for p in papers if p.get("doi")]
        if mcp and len(papers_with_doi) >= 3 and len(papers) < min_satisfice:
            try:
                for p in papers_with_doi[:3]:
                    refs = mcp.call_tool("article", {
                        "identifier": p["doi"],
                        "id_type": "doi",
                        "max_results": 10,
                        "sources": ["crossref", "pubmed"],
                    })
                    for item in _extract_papers(refs, "citation"):
                        item["_phase"] = "citation_traversal"
                        papers.append(item)
                    total_cost += 300
            except Exception as e:
                errors.append(f"Phase 4 citation_traversal: {e}")

        papers = _dedup_papers(papers)

        # ── Phase 5: Author cross-reference ──
        if len(papers) < min_satisfice and len(papers) >= 2:
            try:
                known_authors = set()
                for p in papers:
                    for a in p.get("authors", []):
                        if isinstance(a, str) and len(a) > 3:
                            known_authors.add(a)
                # Search by top authors via Tavily/Exa
                top_authors = list(known_authors)[:5]
                if top_authors and mcp:
                    author_query = f"{' '.join(top_authors[:3])} {scientific_name}"
                    ar = mcp.search_tavily(author_query, max_results=5)
                    for item in _extract_papers(ar, "author_crossref"):
                        item["_phase"] = "author_crossref"
                        papers.append(item)
                    total_cost += 500
            except Exception as e:
                errors.append(f"Phase 5 author_crossref: {e}")

        papers = _dedup_papers(papers)

        # ── Phase 6: Chinese journal search ──
        if chinese_name and len(papers) < min_satisfice and mcp:
            try:
                # Search in Chinese via Tavily
                cn_results = mcp.search_tavily(
                    f"{chinese_name} 研究 论文 期刊 水产 生物",
                    max_results=5,
                )
                for item in _extract_papers(cn_results, "chinese_journal"):
                    item["_phase"] = "journal_scan"
                    item["_channel"] = "CN"
                    papers.append(item)
                total_cost += 400
            except Exception as e:
                errors.append(f"Phase 6 journal_scan: {e}")

        papers = _dedup_papers(papers)
        return papers[:self.config.max_papers], total_cost, errors

    # ── Post-processing ───────────────────────────────────────────

    def _validate_papers(self, papers: List[Dict[str, Any]],
                         species_id: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """应用验证引擎对论文评分."""
        validation_errors: List[str] = []
        if self._Validator:
            try:
                result = self._Validator(
                    papers,
                    known_authors=[],
                    known_journals=[],
                    species_id=species_id,
                )
                if hasattr(result, "verified") and hasattr(result, "rejected"):
                    # Filter out rejected papers
                    verified_ids = {id(p) for p in result.verified}
                    papers = [p for p in papers if id(p) in verified_ids]
                    validation_errors = [
                        str(e) for e in getattr(result, "errors", [])
                    ]
            except Exception as e:
                validation_errors.append(f"Validation error: {e}")

        return papers, validation_errors

    def _score_papers(self, papers: List[Dict[str, Any]]) -> None:
        """为每篇论文添加可信度评分."""
        if self._CredibilityScorer:
            for p in papers:
                try:
                    self._CredibilityScorer(p)
                except Exception:
                    pass

    def _detect_new_papers(self, papers: List[Dict[str, Any]]) -> int:
        """统计新论文 (来自 graph_lookup 以外的阶段)."""
        new_count = 0
        for p in papers:
            phase = p.get("_phase", "")
            if phase and phase != "graph_lookup":
                new_count += 1
        return new_count

    # ── Main entry ────────────────────────────────────────────────

    def search(self, species_id: str) -> MesoSearchResult:
        """执行 BDI 搜索循环.

        Args:
            species_id: e.g. "Pseudaspius_hakonensis" 或 "Ochetobius_elongatus"

        Returns:
            MesoSearchResult 包含论文列表、统计、日志
        """
        self._ensure_deps()
        start_time = time.time()

        result = MesoSearchResult(species_id=species_id)
        mcp = None

        # ── Phase B: Belief — 加载图谱 + 估算文献量 ──
        self._ensure_graph_loaded()
        volume = self._estimate_volume(species_id)

        result.meso_log.append({
            "phase": "bdi",
            "volume_estimate": volume,
            "full_pipeline": True,
        })

        # ── Phase D: Desire — 规划搜索策略 ──
        plan = self._plan_search(species_id, volume)
        result.mode_used = plan["mode"]
        result.volume_estimate = volume

        # ── Phase I: Intention — 执行搜索 ──
        if self.config.mode == "http" or plan.get("full_pipeline"):
            # Try MCP mode first
            try:
                mcp = self._get_mcp()
            except Exception as e:
                result.errors.append(f"MCP init: {e}")

            # Execute search phases
            papers, total_cost, exec_errors = self._execute_search(
                species_id, plan, mcp
            )
            result.papers = papers
            result.total_cost = total_cost
            result.errors.extend(exec_errors)
            result.meso_log.append({
                "phase": "search",
                "papers_found": len(papers),
                "phases_run": 6 if exec_errors else 6,
                "mode": result.mode_used,
            })
        else:
            # Direct mode: use SearchCoordinator
            if self._SearchCoordinator:
                try:
                    search_fn, _ = self._SearchCoordinator
                    s_result = search_fn(species_id)
                    if hasattr(s_result, "papers"):
                        result.papers = [
                            p.__dict__ if hasattr(p, "__dict__") else p
                            for p in s_result.papers
                        ]
                    result.meso_log.append({
                        "phase": "search",
                        "papers_found": len(result.papers),
                        "phases_run": 1,
                    })
                except Exception as e:
                    result.errors.append(f"Direct search: {e}")
            else:
                result.errors.append("SearchCoordinator not available")
                result.stop_reason = "no_engine"

        # ── Post-search: 验证 + 评分 ──
        if result.papers:
            result.papers, validation_errors = self._validate_papers(
                result.papers, species_id
            )
            result.errors.extend(validation_errors)

            self._score_papers(result.papers)

            result.new_papers = self._detect_new_papers(result.papers)

        # ── Inference (P3) ──
        if self.config.enable_inference and self._InferenceEngine and result.papers:
            try:
                ie = self._InferenceEngine()
                inference_result = ie.infer(result.papers, species_id=species_id)
                result.meso_log.append({
                    "phase": "inference",
                    "gaps_found": getattr(inference_result, "gaps_found", 0) if hasattr(inference_result, "gaps_found") else 0,
                    "followup_queries": getattr(inference_result, "followup_queries", 0) if hasattr(inference_result, "followup_queries") else 0,
                })
            except Exception as e:
                result.errors.append(f"Inference: {e}")

        # ── Evolution ──
        if self.config.enable_evolution and self._EvolutionExecutor:
            try:
                metrics = {
                    "pipeline_success_rate": 1.0 if not result.errors else 0.5,
                    "recall_rate": min(1.0, len(result.papers) / max(volume, 1)),
                    "new_papers_rate": result.new_papers / max(len(result.papers), 1),
                    "token_efficiency": len(result.papers) / max(result.total_cost / 1000, 1),
                }
                executor = self._EvolutionExecutor(
                    str(self._engine_root / "config" / "evolution.yaml")
                )
                actions = executor.evaluate_and_adapt(metrics)
                result.adaptations = actions
                result.meso_log.append({
                    "phase": "evolution",
                    "adaptations": actions,
                })
            except Exception as e:
                pass

        # ── Stop reason ──
        if not result.stop_reason:
            if len(result.papers) >= self.config.min_papers_satisfice:
                result.stop_reason = f"satisfice ({len(result.papers)} >= {self.config.min_papers_satisfice})"
            elif result.errors:
                result.stop_reason = f"errors ({len(result.errors)})"
            else:
                result.stop_reason = "all_phases_completed"

        result.phase_count = len(result.meso_log)
        result.elapsed_s = time.time() - start_time

        # ── Cleanup internal fields ──
        for p in result.papers:
            p.pop("_phase", None)

        return result


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _extract_papers(mcp_results: List[dict], source: str) -> List[Dict[str, Any]]:
    """从 MCP 工具返回的结果中提取结构化论文数据."""
    papers: List[Dict[str, Any]] = []

    for item in mcp_results:
        if not isinstance(item, dict):
            continue

        text = item.get("text", "")
        if text and isinstance(text, str) and len(text) > 20:
            # Try JSON parse
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    for p in parsed:
                        if isinstance(p, dict):
                            _normalize_paper(p, source)
                            papers.append(p)
                elif isinstance(parsed, dict):
                    _normalize_paper(parsed, source)
                    papers.append(parsed)
                continue
            except (json.JSONDecodeError, TypeError):
                # Treat as plain text entry
                papers.append({
                    "title": text[:200],
                    "source": source,
                    "_raw": text[:500],
                })
            continue

        # Direct metadata
        if item.get("title") or item.get("doi"):
            _normalize_paper(item, source)
            papers.append(item)

    return papers


def _normalize_paper(paper: dict, source: str) -> None:
    """Normalize a paper dict to canonical field names."""
    paper.setdefault("source", source)
    # Map common field names
    field_map = {
        "volume": "journal",  # Some APIs return journal in "volume"
    }
    for old, new in field_map.items():
        if old in paper and new not in paper:
            paper[new] = paper[old]

    # Ensure authors is a list
    authors = paper.get("authors", paper.get("author", []))
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.replace(";", ",").split(",")]
    paper["authors"] = authors if isinstance(authors, list) else []

    # Ensure numeric year
    year = paper.get("year", 0)
    if isinstance(year, str):
        year = int(year[:4]) if year[:4].isdigit() else 0
    paper["year"] = year


def _dedup_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate papers by DOI (primary) then title similarity."""
    seen_dois: set = set()
    seen_titles: set = set()
    deduped: List[Dict[str, Any]] = []

    for p in papers:
        doi = p.get("doi", "").strip().lower()
        title = p.get("title", "").strip().lower()[:100]

        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)

        deduped.append(p)

    return deduped


# ═══════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════

def create_agent(mode: str = "http", **kwargs) -> MesoAgent:
    """创建 MesoAgent 实例的工厂函数.

    Args:
        mode: "http" (使用 MCP 工具) 或 "direct" (使用本地搜索协调器)
        **kwargs: 传给 MesoConfig 的额外参数

    Returns:
        MesoAgent 实例
    """
    config = MesoConfig(mode=mode, **kwargs)
    return MesoAgent(config)
