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
        # 涌现状态追踪 (per-species)
        self._emergence_signals: Dict[str, list[dict]] = {}
        self._emergence_mode: Dict[str, str] = {}  # "normal" | "surge" | "stalled"

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
            except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        # ── Secondary: Multi-source HTTP estimation ──
        multi = self._estimate_literature_volume_multi(species_id)
        if multi > 0:
            return multi

        # ── Fallback: count known papers from graph ──
        known = self._load_known(species_id)
        return max(len(known), 8)

    def _estimate_literature_volume_multi(self, species_id: str) -> int:
        """Multi-source literature volume estimation via HTTP REST APIs (并行, 6s 超时).

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
        openalex_count: int = 0

        def _fetch_pubmed():
            nonlocal pubmed_count
            try:
                url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                       f"db=pubmed&term={_url_quote(scientific_name)}&retmax=0&retmode=json")
                with _urlreq.urlopen(url, timeout=6) as resp:
                    data = _json.loads(resp.read())
                pubmed_count = int(data.get("esearchresult", {}).get("count", "0") or "0")
            except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        def _fetch_crossref():
            nonlocal scholar_count
            try:
                url = f"https://api.crossref.org/works?query={_url_quote(scientific_name)}&rows=0"
                with _urlreq.urlopen(url, timeout=6) as resp:
                    data = _json.loads(resp.read())
                scholar_count = int(data.get("message", {}).get("total-results", 0) or 0)
            except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        def _fetch_openalex():
            nonlocal openalex_count
            try:
                url = f"https://api.openalex.org/works?filter=title.search:{_url_quote(scientific_name)}&per_page=0"
                with _urlreq.urlopen(url, timeout=6) as resp:
                    data = _json.loads(resp.read())
                openalex_count = int(data.get("meta", {}).get("count", 0) or 0)
            except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = [pool.submit(f) for f in (_fetch_pubmed, _fetch_crossref, _fetch_openalex)]
            for fut in as_completed(futs):
                try:
                    fut.result(timeout=8)
                except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        return max(pubmed_count, scholar_count, openalex_count, 0)

    # ── BDI: Desire — search strategy planning ────────────────────

    def _plan_search(self, species_id: str, volume: int) -> Dict[str, Any]:
        """基于文献量估算 + 涌现信号规划搜索策略 (Desire 阶段)."""
        self._ensure_graph_loaded()
        species_info = self._species_map.get(species_id, {})
        conservation = species_info.get("conservation", "LC")

        # 检查该物种是否有涌现信号
        signals = self._emergence_signals.get(species_id, [])
        emergence_adjust = self._emergence_mode.get(species_id, "normal")

        # 模式选择 (基础)
        if volume <= 30:
            mode = "exhaustive"
            full_pipeline = True
        elif volume <= 200:
            mode = "classified"
            full_pipeline = True
        else:
            mode = "review_anchored"
            full_pipeline = True

        # 涌现信号调整策略
        if signals:
            if any(s.get("type", "") in ("new_paper_surge", "emergence", "trend_change") for s in signals):
                mode = "exhaustive"
                full_pipeline = True
                emergence_adjust = "surge"
            elif any(s.get("type", "") in ("stagnation", "diminishing_return", "saturation") for s in signals):
                if mode != "exhaustive":
                    mode = "classified"
                emergence_adjust = "stalled"

        # 受保护物种 → 更全面搜索
        if conservation in ("CR", "EN") and emergence_adjust != "surge":
            mode = "exhaustive"
            full_pipeline = True

        self._emergence_mode[species_id] = emergence_adjust

        return dict(
            mode=mode,
            full_pipeline=full_pipeline,
            volume_estimate=volume,
            conservation=conservation,
            emergence_adjust=emergence_adjust,
            emergence_signals=len(signals),
        )

    # ── BDI: Intention — search execution ─────────────────────────

    def _execute_search_http(self, species_id: str, plan: Dict[str, Any]
                             ) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """HTTP 直连搜索（parallel_search）— 通用方案，不依赖 MCP/npx。

        使用 PubMed E-utilities + Crossref + Europe PMC + OpenAlex + arXiv + Bing
        并行搜索，所有源通过标准 HTTP API 访问。
        """
        papers: List[Dict[str, Any]] = []
        total_cost = 0
        errors: List[str] = []
        species_info = self._species_map.get(species_id, {})
        scientific_name = species_info.get("name", species_id.replace("_", " "))
        chinese_name = species_info.get("chinese", "")
        variants = species_info.get("variants", [])
        min_satisfice = self.config.min_papers_satisfice

        # Phase 1: Graph lookup (FREE)
        known = self._load_known(species_id)
        for k in known:
            k["_phase"] = "graph_lookup"
            papers.append(k)

        # Phase 2: HTTP parallel search
        try:
            from src.parallel_search import ParallelSearch
            search_queries = [scientific_name]
            search_queries.extend(variants[:2])
            if chinese_name:
                search_queries.append(chinese_name)

            with ParallelSearch(max_workers=4) as ps:
                stats = ps.search_all(search_queries, max_per_query=15)

            for p in stats.new_papers:
                p["_phase"] = "http_search"
                papers.append(p)

            total_cost += len(stats.new_papers) * 50
            logger.info(f"HTTP search: {stats.total_raw} raw → {stats.total_merged} merged "
                        f"({stats.providers_succeeded}/{stats.providers_succeeded + stats.providers_failed} providers)")
        except Exception as e:
            errors.append(f"HTTP search failed: {e}")

        papers = _dedup_papers(papers)
        return papers[:self.config.max_papers], total_cost, errors

    def _execute_search_mcp(self, species_id: str, plan: Dict[str, Any],
                            mcp: Any) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """MCP 子进程搜索 — 使用 subprocess 启动 npx MCP 服务器。

        在 Reasonix Desktop 中 MCP 工具已注入，此模式用于 CLI/standalone。
        如果 McpClient 无法启动，自动回退到 HTTP 搜索。
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

        # Phase 1: Graph lookup (FREE)
        known = self._load_known(species_id)
        for k in known:
            k["_phase"] = "graph_lookup"
            papers.append(k)

        if len(papers) >= min_satisfice and mode != "exhaustive":
            return papers[:self.config.max_papers], total_cost, errors

        # Phase 2: Exact search via MCP tools
        if mcp and len(papers) < min_satisfice:
            try:
                sr = mcp.search_scholar(scientific_name, limit=10)
                for item in _extract_papers(sr, "scholar"):
                    item["_phase"] = "exact_search"
                    papers.append(item)
                total_cost += 300
            except Exception as e:
                errors.append(f"scholar: {e}")

            try:
                ar = mcp.search_article(scientific_name, max_results=10)
                for item in _extract_papers(ar, "article"):
                    item["_phase"] = "exact_search"
                    papers.append(item)
                total_cost += 300
            except Exception as e:
                errors.append(f"article: {e}")

            try:
                if chinese_name:
                    tv = mcp.search_tavily(f"{chinese_name} {scientific_name} 鱼类 研究 论文", max_results=5)
                    for item in _extract_papers(tv, "tavily"):
                        item["_phase"] = "exact_search"
                        papers.append(item)
                    total_cost += 200
            except Exception as e:
                errors.append(f"tavily: {e}")

        papers = _dedup_papers(papers)
        if len(papers) >= min_satisfice:
            return papers[:self.config.max_papers], total_cost, errors

        # Phase 3: Variant search
        if mcp and variants and len(papers) < min_satisfice:
            for variant in variants[:3]:
                try:
                    vr = mcp.search_scholar(variant, limit=5)
                    for item in _extract_papers(vr, "scholar_variant"):
                        item["_phase"] = "variant_search"
                        papers.append(item)
                    total_cost += 150
                except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

        papers = _dedup_papers(papers)
        return papers[:self.config.max_papers], total_cost, errors

    def _execute_search(self, species_id: str, plan: Dict[str, Any],
                        mcp: Any) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """执行多阶段搜索 — 自动选择 MCP 或 HTTP 通道。

        优先级:
          1. MCP 子进程 (如果有 npx+node 环境)
          2. HTTP 并行搜索 (parallel_search, 通用方案)
        """
        papers, cost, errors = self._execute_search_mcp(species_id, plan, mcp)

        # 如果 MCP 只找到很少的论文 (说明 MCP 进程可能不可用)，用 HTTP 补充
        if len(papers) < self.config.min_papers_satisfice:
            http_papers, http_cost, http_errors = self._execute_search_http(species_id, plan)
            # Merge: HTTP 结果 + MCP 结果
            all_papers = papers + http_papers
            merged = _dedup_papers(all_papers)
            if len(merged) > len(papers):
                logger.info(f"HTTP search added {len(merged) - len(papers)} papers")
                papers = merged
                cost += http_cost
                errors.extend(http_errors)

        return papers[:self.config.max_papers], cost, errors

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
                except Exception as _e:
                logger.warning(f"Suppressed in meso_agent.py: {type(_e).__name__}: {_e}")

    def _detect_new_papers(self, papers: List[Dict[str, Any]]) -> int:
        """统计新论文 (来自 graph_lookup 以外的阶段)."""
        new_count = 0
        for p in papers:
            phase = p.get("_phase", "")
            if phase and phase != "graph_lookup":
                new_count += 1
        return new_count

    # ── Runtime detection ─────────────────────────────────────────

    @staticmethod
    def _probe_mcp_available() -> bool:
        """快速检测当前环境 MCP 子进程是否可用.

        检查 npx (npm) 和 node 是否在 PATH 中。
        Reasonix Desktop 中的 MCP 工具直接注入到 AI 模型，
        此检测仅决定 Python 子进程是否要尝试启动额外 MCP 进程。

        Returns:
            True 如果 npx 或 node 可用
        """
        import shutil
        npx_path = shutil.which("npx")
        node_path = shutil.which("node")
        uvx_path = shutil.which("uvx")
        available = bool(npx_path or node_path or uvx_path)
        if not available:
            import logging as _lg
            _lg.getLogger(__name__).info(
                "MCP subprocess unavailable (npx/node/uvx not found) — using HTTP search"
            )
        return available

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
            # 快速检测 MCP 是否可用 (npx/uvx 是否存在)
            mcp_available = self._probe_mcp_available()
            if mcp_available:
                try:
                    mcp = self._get_mcp()
                except Exception as e:
                    result.errors.append(f"MCP init: {e}")
                    mcp_available = False
            else:
                result.meso_log.append({
                    "phase": "mcp_check",
                    "available": False,
                    "note": "MCP 子进程不可用 (npx/node 未找到)，使用 HTTP 直连",
                })

            # Execute search phases (自动 fallback MCP→HTTP)
            papers, total_cost, exec_errors = self._execute_search(
                species_id, plan, mcp if mcp_available else None
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

        # ── Evolution + 涌现检测 ──
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

                # 提取涌现信号，存下来影响下一次搜索
                emergence_actions = [a for a in actions if getattr(a, "param", "") == "emergence_signals"]
                if emergence_actions:
                    self._emergence_signals[species_id] = [
                        {"type": "emergence", "severity": 0.5, "metric": "evolution"}
                    ]
                else:
                    self._emergence_signals.pop(species_id, None)

                result.adaptations = actions
                result.meso_log.append({
                    "phase": "evolution",
                    "adaptations": actions,
                    "emergence_signals": len(self._emergence_signals.get(species_id, [])),
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
    """从 MCP 工具返回的结果中提取结构化论文数据.

    支持格式:
      1. MCP tools/call JSON results (text 字段包含 JSON)
      2. scholar-mcp: {"results": [{title, doi, authors, year, venue}, ...]}
      3. article-mcp: {"articles": [{title, doi, ...}]}
      4. ncbi: {"papers": [{title, doi, ...}]}
      5. Raw dict with title/doi fields
    """
    papers: List[Dict[str, Any]] = []

    for item in mcp_results:
        if not isinstance(item, dict):
            continue

        text = item.get("text", "")
        if text and isinstance(text, str) and len(text) > 10:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    # scholar-mcp: {"results": [...], "query": ...}
                    results = (parsed.get("results") or parsed.get("papers")
                               or parsed.get("articles") or parsed.get("items")
                               or [])
                    if isinstance(results, list):
                        for p in results:
                            if isinstance(p, dict) and (p.get("title") or p.get("doi")):
                                _normalize_paper(p, source)
                                papers.append(p)
                    else:
                        _normalize_paper(parsed, source)
                        papers.append(parsed)
                elif isinstance(parsed, list):
                    for p in parsed:
                        if isinstance(p, dict) and (p.get("title") or p.get("doi")):
                            _normalize_paper(p, source)
                            papers.append(p)
            except (json.JSONDecodeError, TypeError):
                # Plain text — create an entry
                lines = text.strip().split("\n")
                title_guess = lines[0][:200] if lines else text[:200]
                papers.append({
                    "title": title_guess,
                    "source": source,
                    "_raw": text[:500],
                })
        elif item.get("title") or item.get("doi"):
            _normalize_paper(item, source)
            papers.append(item)

    return papers


def _normalize_paper(paper: dict, source: str) -> None:
    """Normalize a paper dict to canonical field names."""
    paper.setdefault("source", source)
    # Map common field names
    field_map = {
        "volume": "journal",    # Some APIs return journal in "volume"
        "venue": "journal",     # scholar-mcp uses "venue"
        "container-title": "journal",  # Crossref
        "publication": "journal",
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
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()[:100]

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
