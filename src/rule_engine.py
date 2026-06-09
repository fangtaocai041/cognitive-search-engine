"""
Search Rule Engine — Load search_rules.yaml and execute phases.
Replaces natural-language Skill instructions with structured, machine-executable rules.

Execution modes:
  - MCP:    Connect to external MCP servers (scholar, article, tavily, exa)
  - HTTP:   Direct REST API calls (PubMed E-utilities, Crossref, OpenAlex)
  - RECORD: Load from pre-recorded search results (search_records/)
  - MOCK:   Deterministic test responses (for unit testing)

Usage:
  engine = SearchRuleEngine("config/search_rules.yaml", mode="http")
  result = engine.execute("Ochetobius_elongatus")
"""

import json
import logging
import time
import urllib.request
import urllib.error
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
import sys as _sys
# Ensure engine root is on sys.path so 'from src.xxx' imports work
_ENGINE_ROOT = str(Path(__file__).resolve().parent.parent)
if _ENGINE_ROOT not in _sys.path:
    _sys.path.insert(0, _ENGINE_ROOT)

logger = logging.getLogger("rule_engine")

from typing import Any, Optional
from urllib.parse import quote_plus

try:
    import yaml
except ImportError:
    yaml = None

# D₃ World Model
try:
    from src.world_model import WorldModel
except ImportError:
    WorldModel = None

# ──── Helpers ────

from src._utils import DotDict  # v5.7: de-duplicated from agent_core + rule_engine

# ──── Data Classes ────

@dataclass
class Paper:
    doi: str
    title: str
    title_zh: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    species: list[str] = field(default_factory=list)
    citations: int = 0
    pmid: Optional[str] = None
    trust: str = "pending"
    trust_score: int = 50
    source: str = ""
    note: str = ""
    abstract: str = ""

    @property
    def doi_key(self) -> str:
        """Normalized DOI or title-based fallback key for dedup."""
        if self.doi:
            doi = self.doi.lower().strip().rstrip(".")
            doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
            return doi if doi else self.title.lower().strip()[:80]
        return self.title.lower().strip()[:80]


# ──── Phase Function Registry ────

PHASE_FUNCTIONS: dict[str, str] = {}  # name → method name on SearchRuleEngine

def register_phase(name: str):
    """Decorator: register a phase function by its search_rules.yaml function name."""
    def decorator(method):
        PHASE_FUNCTIONS[name] = method.__name__
        return method
    return decorator


# ──── Rule Engine ────

class SearchRuleEngine:
    """Load search_rules.yaml → execute phases → return papers.

    Modes:
      mode="mcp"    → call external MCP servers via subprocess JSON-RPC
      mode="http"   → call REST APIs directly (PubMed, Crossref, OpenAlex)
      mode="record" → replay from search_records/*.json (deterministic)
      mode="mock"   → return deterministic test data (no network)
    """

    def __init__(self, config_path=None,
                 mode: str = "http", record_dir=None,
                 use_react: bool = True):
        if yaml is None:
            raise ImportError("PyYAML required: pip install pyyaml")
        # Resolve paths relative to engine root
        _engine_root = Path(__file__).resolve().parent.parent
        if config_path is None:
            config_path = str(_engine_root / "config" / "search_rules.yaml")
        if record_dir is None:
            record_dir = str(_engine_root / "search_records")
        with open(config_path, encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)
        self.phases = self.rules["phases"]
        self.stop_conditions = self.rules["stop_conditions"]["global"]
        self.adaptive_params = self.rules.get("adaptive_params", {})
        self.mode = mode
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(exist_ok=True)
        self.use_react = use_react

        # Reactive agent (lazy init)
        self._agent = None  # CognitiveAgent instance

        # Execution state
        self._all_papers: list[Paper] = []
        self._all_dois: set[str] = set()
        self._tokens_spent: int = 0
        self._consecutive_zero: int = 0
        self._ig_history: list[float] = []  # info gain per phase
        self._search_errors: list[str] = []  # visible error log

        # Timeout / retry config (v5.6: 缩减 — NCBI 500 不应阻塞全景流程)
        self._http_timeout_per_call: int = 8        # 单次 HTTP 请求超时 (15→8s)
        self._http_retry_max_s: int = 12            # 总重试窗口 (60→12s)
        self._http_retry_attempts: int = 2           # 最多重试 (5→2次)
        self._mcp_parallel_timeout_s: int = 180       # MCP 并行总超时 3min
        self._mcp_per_call_timeout_s: int = 30        # MCP 单次调用超时

        # D₃ World Model
        self._world_model = WorldModel() if WorldModel else None

    # ── Public API ──

    def execute(self, species_id: str) -> dict[str, Any]:
        """Execute all active phases. Returns consolidated search result.

        Two execution modes:
          - ReAct mode (use_react=True, default): delegates to CognitiveAgent
            for Think→Act→Observe→Reflect loop with BDI lifecycle.
          - Linear mode (use_react=False): flat sequential phase execution
            (backward-compatible, used for testing).
        """
        # Parse species_id → genus + species
        genus, sp_epithet = self._parse_species_id(species_id)
        graph_papers = self._load_graph_papers(species_id)
        chinese_name = self._get_chinese_name(species_id)

        # ── ReAct mode: delegate to CognitiveAgent ──
        if self.use_react:
            return self._execute_react(
                species_id, genus, sp_epithet, chinese_name, graph_papers
            )

        # ── Linear mode (legacy) ──
        species = sp_epithet  # backward-compatible variable name

        # D₃: Pre-search prediction
        prediction = None
        if self._world_model:
            prediction = self._world_model.predict(
                species_id, graph_known_count=len(graph_papers)
            )

        # Initialize context (includes engine state for stop conditions)
        ctx = {
            "species_id": species_id,
            "genus": genus,
            "species": species,
            "chinese_name": self._get_chinese_name(species_id),
            "all_papers": self._all_papers,
            "all_dois": self._all_dois,
            "graph_papers": graph_papers,
            "total_tokens": 0,
            "consecutive_zero_new": 0,
            "ig_history": [],
        }

        phases_executed = []
        new_papers_by_phase: dict[str, list[Paper]] = {}
        paper_counts: list[int] = []

        for name, phase in sorted(self.phases.items(),
                                   key=lambda x: x[1].get("priority", 99)):
            if not self._should_activate(phase, ctx):
                continue
            if self._should_stop_global(ctx):
                break

            phase_result = self._execute_phase(name, phase, ctx)
            phases_executed.append(name)

            budget = phase.get("budget", 0)
            self._tokens_spent += budget
            ctx["total_tokens"] = self._tokens_spent

            new_papers = phase_result.get("new_papers", [])
            if new_papers:
                self._merge_papers(new_papers)
                new_papers_by_phase[name] = new_papers
                self._consecutive_zero = 0
            else:
                self._consecutive_zero += 1

            # Sync ctx with latest engine state (for stop condition eval)
            paper_counts.append(len(self._all_papers))
            ctx["all_papers"] = self._all_papers
            ctx["all_dois"] = self._all_dois
            ctx["consecutive_zero_new"] = self._consecutive_zero
            ig = len(new_papers) / max(budget / 1000, 1)
            if budget > 0:
                self._ig_history.append(ig)
            ctx["ig_history"] = self._ig_history

        # Dedup & merge (final pass)
        merged = self._deduplicate(self._all_papers)
        # Augment: fill in authors/institutions/abstract from species_graph
        merged = self._augment_papers_from_graph(merged)

        # Auto-writeback: persist new papers to species_graph.yaml
        new_graph_count = self._auto_writeback(species_id, merged)

        result = {
            "papers": [p.__dict__ for p in merged],
            "paper_count": len(merged),
            "tokens_spent": self._tokens_spent,
            "phases_executed": phases_executed,
            "new_papers_by_phase": {
                k: [p.__dict__ for p in v] for k, v in new_papers_by_phase.items()
            },
            "efficiency": len(merged) / max(self._tokens_spent / 1000, 1),
            "stop_reason": self._stop_reason(),
            "ig_per_phase": self._ig_history,
            "new_to_graph": new_graph_count,  # papers auto-added to species_graph.yaml
        }

        # Save record
        if self.mode == "record":
            self._save_record(species_id, result)

        # D₃: Update World Model
        if prediction and self._world_model:
            self._world_model.update(prediction, len(merged), self._tokens_spent)
            result["world_model"] = {
                "predicted_volume": prediction.estimated_volume,
                "predicted_tokens": prediction.predicted_tokens,
                "actual_papers": len(merged),
                "actual_tokens": self._tokens_spent,
                "prediction_accuracy": round(self._world_model.prediction_accuracy, 2),
            }

        return result

    # ── Phase Execution ──

    def _execute_phase(self, name: str, phase: dict, ctx: dict) -> dict:
        """Dispatch phase by function name to the appropriate handler."""
        fn_name = phase["function"]
        handler_name = PHASE_FUNCTIONS.get(fn_name)

        if handler_name and hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return handler(phase, ctx)

        # Fallback: try method named after function
        method_name = f"_fn_{fn_name}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(phase, ctx)

        return {
            "phase": name,
            "function": fn_name,
            "warning": f"No handler registered for '{fn_name}'",
            "new_papers": [],
        }

    # ── Phase Handlers ──

    @register_phase("load_known_papers")
    def _fn_load_known_papers(self, phase: dict, ctx: dict) -> dict:
        """Phase 0: Load pre-computed papers from species_graph.yaml (FREE)."""
        graph_papers = ctx.get("graph_papers", [])
        papers = [self._dict_to_paper(p) for p in graph_papers]
        return {"new_papers": papers, "tokens_used": 0}

    @register_phase("search_scholar_article")
    def _fn_search_scholar_article(self, phase: dict, ctx: dict) -> dict:
        """Phase 1: Exact name search via configured search tools.

        Precision gate: Chinese-name queries on Crossref can return
        unrelated species sharing the same epithet (e.g. 'elongatus'
        matching Ophiodon, Dipterocarpus, etc.).  All results are
        filtered through _matches_species_context.

        v2.1: Increased n=50 to get comprehensive results for well-studied
        species (was 20, missing many papers).
        """
        species_id = ctx["species_id"]
        genus = ctx["genus"]
        sp = ctx["species"]

        queries = [f"{genus} {sp}"]
        # Add Chinese name if available
        if ctx.get("chinese_name"):
            queries.append(ctx["chinese_name"])

        papers = []
        for q in queries:
            raw_results = self._call_search_tools(q, phase.get("tools", []), ctx, n=50)
            for r in raw_results:
                # Crossref fuzzy search returns any species sharing the
                # same epithet (e.g. Ophiodon elongatus, Dipterocarpus
                # elongatus).  Filter to only keep papers plausibly about
                # the target genus.
                if r.source == "crossref":
                    if not self._matches_species_context(r, ctx, genus, sp):
                        continue
                # Chinese-name query: same filter on all sources
                elif q == ctx.get("chinese_name", ""):
                    if not self._matches_species_context(r, ctx, genus, sp):
                        continue
                papers.append(r)

        return {"new_papers": papers, "tokens_used": phase.get("budget", 500)}

    @register_phase("search_chinese_scholar")
    def _fn_search_chinese_scholar(self, phase: dict, ctx: dict) -> dict:
        """Phase 1.5: Chinese-specific search — v5.7 MCP 运行时双路径.

        MCP 模式 (Reasonix runtime):
          Layer 1: tavily_tavily_search (AI搜索，中文内容覆盖好)
          Layer 2: web_search (Reasonix 内置，浏览器级反爬)
          Layer 3: scholar_search_literature_graph (Google Scholar)
        HTTP 模式 (独立 Python):
          Layer 1: 中文原生引擎 (baidu_scholar/cnki_web/wanfang_web/cas_web)
          Layer 2: 学术引擎 (OpenAlex/Europe PMC/Crossref)
          Layer 3: Bing 语义搜索降级
        """
        chinese_name = ctx.get("chinese_name", "")
        genus = ctx.get("genus", "")
        species_ep = ctx.get("species", "")
        if not chinese_name:
            return {"new_papers": [], "tokens_used": 0}

        papers = []
        seen_dois: set[str] = set()

        # ── MCP 模式: 使用 MCP 工具搜中文 (Tavily/Web/Scholar 都支持中文) ──
        if self.mode == "mcp":
            mcp_tools = ["tavily_tavily_search", "web_search", "scholar_search_literature_graph"]
            for q in [chinese_name, f"{chinese_name} {genus} {species_ep}",
                       f"{chinese_name} 研究 OR 论文 OR 综述"]:
                try:
                    raw = self._call_search_tools(q, mcp_tools, ctx, n=15)
                    for r in raw:
                        if r.doi_key not in seen_dois:
                            if self._matches_species_context(r, ctx, genus, species_ep):
                                seen_dois.add(r.doi_key)
                                papers.append(r)
                except Exception:
                    continue
            return {"new_papers": papers, "tokens_used": 1500}

        # ── HTTP 模式: 使用 phase_tools ──
        phase_tools = phase.get("tools", [])

        # Layer 1: 中文原生引擎 + OpenAlex/Scholar 桥接
        try:
            raw = self._call_search_tools(chinese_name, phase_tools, ctx, n=15)
            for r in raw:
                if r.doi_key not in seen_dois:
                    if self._matches_species_context(r, ctx, genus, species_ep):
                        seen_dois.add(r.doi_key)
                        papers.append(r)
        except Exception:
            pass

        # Layer 2: 中文名 + 学名 → 学术引擎
        if len(papers) < 5:
            cn_en_queries = [
                f"{chinese_name} {genus} {species_ep}",
                f"{chinese_name} 鱼类 OR 鱼",
            ]
            for q in cn_en_queries:
                try:
                    raw = self._call_search_tools(q, phase_tools, ctx, n=10)
                    for r in raw:
                        if r.doi_key not in seen_dois:
                            if self._matches_species_context(r, ctx, genus, species_ep):
                                seen_dois.add(r.doi_key)
                                papers.append(r)
                except Exception:
                    continue

        # Layer 3: 语义搜索降级
        if len(papers) < 3 and self.mode in ("mcp", "http"):
            try:
                fallback_q = f"{chinese_name} {genus} 学术论文 研究"
                raw = self._call_search_tools(fallback_q, phase_tools, ctx, n=10)
                for r in raw:
                    if r.doi_key not in seen_dois:
                        if self._matches_species_context(r, ctx, genus, species_ep):
                            seen_dois.add(r.doi_key)
                            papers.append(r)
            except Exception:
                pass

        logger.info(f"Chinese search '{chinese_name}': {len(papers)} papers from {len(seen_dois)} unique DOIs")
        return {"new_papers": papers, "tokens_used": phase.get("budget", 500)}

    @register_phase("search_by_authors")
    def _fn_search_by_authors(self, phase: dict, ctx: dict) -> dict:
        """Phase 2: Cross-reference known authors' other publications."""
        graph_papers = ctx.get("graph_papers", [])
        authors = set()
        for p in graph_papers:
            for a in p.get("authors", []):
                authors.add(a)

        if not authors:
            return {"new_papers": [], "note": "No known authors in graph"}

        papers = []
        for author in list(authors)[:5]:  # Top 5 authors
            query = f'"{author}" fish'
            results = self._call_search_tools(query, phase.get("tools", []), ctx, n=10)
            # Only keep papers mentioning the target species
            for r in results:
                if self._species_in_title(r, ctx):
                    papers.append(r)

        return {"new_papers": papers, "tokens_used": phase.get("budget", 1500)}

    @register_phase("mine_review_references")
    def _fn_mine_review_references(self, phase: dict, ctx: dict) -> dict:
        """Phase 1.5: Mine reference lists from review papers."""
        existing = ctx.get("all_papers", [])
        reviews = [p for p in existing
                   if self._is_review(p.title or "")]

        if not reviews:
            return {"new_papers": [], "note": "No review papers found"}

        new_papers = []
        existing_dois = {p.doi_key for p in existing}

        for review in reviews[:3]:  # Top 3 reviews
            refs = self._get_references(review.doi, ctx)
            for ref in refs:
                if ref.doi_key not in existing_dois:
                    ref.source = f"via_review:{review.title[:60]}"
                    ref.trust = "tentative"
                    ref.trust_score = 50
                    new_papers.append(ref)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 500)}

    @register_phase("verify_references")
    def _fn_verify_references(self, phase: dict, ctx: dict) -> dict:
        """Phase 1.6: 5-level trust scoring for mined papers."""
        papers = ctx.get("all_papers", [])
        threshold = phase.get("params", {}).get("trust_threshold_verified", 80)

        verified = []
        params = phase.get("params", {})

        for p in papers:
            score = self._trust_score(p, ctx)
            p.trust_score = score
            if score >= params.get("trust_threshold_verified", 80):
                p.trust = "verified"
                verified.append(p)
            elif score >= params.get("trust_threshold_tentative", 50):
                p.trust = "tentative"
                verified.append(p)
            else:
                p.trust = "unverified"

        return {"new_papers": verified, "tokens_used": phase.get("budget", 1000)}

    @register_phase("traverse_citation_graph")
    def _fn_traverse_citation_graph(self, phase: dict, ctx: dict) -> dict:
        """Phase 5: Forward/backward citation traversal from known DOIs."""
        existing = ctx.get("all_papers", [])
        papers_with_doi = [p for p in existing if p.doi and p.doi.startswith("10.")]

        if len(papers_with_doi) < 3:
            return {"new_papers": [], "note": "Need ≥3 papers with DOIs"}

        max_depth = phase.get("params", {}).get("max_depth", 3)
        new_papers = []
        existing_dois = {p.doi_key for p in existing}

        for seed in papers_with_doi[:5]:
            # Forward: who cited this paper?
            citing = self._get_citing_papers(seed.doi, ctx)
            for c in citing:
                if c.doi_key not in existing_dois:
                    c.source = f"citing:{seed.doi}"
                    new_papers.append(c)

            # Backward: what did this paper cite?
            refs = self._get_references(seed.doi, ctx)
            for r in refs:
                if r.doi_key not in existing_dois:
                    r.source = f"reference:{seed.doi}"
                    new_papers.append(r)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 1000)}

    @register_phase("search_variants")
    def _fn_search_variants(self, phase: dict, ctx: dict) -> dict:
        """Phase 6: Search known spelling variants + OCR-generated variants.

        Precision gate: every variant search MUST include the genus prefix
        to avoid matching unrelated species (e.g. 'elongatum' matching
        Colydium, Thinopyrum, etc. instead of Ochetobius).
        """
        species_id = ctx["species_id"]
        genus = ctx["genus"]
        sp = ctx["species"]

        if not genus:
            return {"new_papers": [], "note": "No genus — cannot filter variants"}

        # Load variants from graph + auto-generate OCR variants
        variants = set(self._get_variants(species_id))
        try:
            from src.variant_generator import generate_variants
            variants.update(generate_variants(genus, sp))
        except ImportError:
            pass

        if not variants:
            return {"new_papers": [], "note": "No variants defined"}

        existing_dois = {p.doi_key for p in ctx.get("all_papers", [])}
        new_papers = []
        genus_lower = genus.lower()

        for variant in list(variants)[:8]:
            # Precision gate: if variant is a species-only fragment like
            # 'elongatum', wrap it with genus to avoid false matches
            if genus_lower not in variant.lower():
                query = f'"{genus} {variant}"'
            else:
                query = f'"{variant}"'
            results = self._call_search_tools(query, phase.get("tools", []), ctx, n=30)
            for r in results:
                if r.doi_key not in existing_dois:
                    # Double-check: reject papers whose title contains none
                    # of the target genus, Chinese name, or known variants
                    if not self._matches_species_context(r, ctx, genus, sp):
                        continue
                    r.source = f"variant:{variant}"
                    new_papers.append(r)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 2000)}

    @register_phase("search_phonetic")
    def _fn_search_phonetic(self, phase: dict, ctx: dict) -> dict:
        """Phase 8: Soundex/Metaphone phonetic search."""
        genus = ctx["genus"]
        if len(genus) <= 6:
            return {"new_papers": [], "note": "Genus too short for phonetic"}

        soundex_codes = self._soundex(genus)
        existing_dois = {p.doi_key for p in ctx.get("all_papers", [])}
        new_papers = []

        for code in soundex_codes:
            results = self._call_search_tools(code, phase.get("tools", []), ctx, n=10)
            for r in results:
                if r.doi_key not in existing_dois:
                    r.source = f"phonetic:{code}"
                    new_papers.append(r)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 800)}

    @register_phase("scan_target_journals")
    def _fn_scan_target_journals(self, phase: dict, ctx: dict) -> dict:
        """Phase 5/8: Scan known journals for species mentions."""
        species_id = ctx["species_id"]
        journals = self._get_journals(species_id)
        chinese_name = ctx.get("chinese_name", "")

        if not journals:
            return {"new_papers": [], "note": "No target journals"}

        existing_dois = {p.doi_key for p in ctx.get("all_papers", [])}
        new_papers = []

        for journal in journals[:5]:
            query = f'{chinese_name} site:{journal.lower().replace(" ", "")}'
            results = self._call_search_tools(query, phase.get("tools", []), ctx, n=10)
            for r in results:
                if r.doi_key not in existing_dois:
                    r.source = f"journal:{journal}"
                    new_papers.append(r)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 1200)}

    @register_phase("llm_query_expansion")
    def _fn_llm_query_expansion(self, phase: dict, ctx: dict) -> dict:
        """Phase 11: LLM-generated semantic query expansion (last resort)."""
        existing = ctx.get("all_papers", [])
        if len(existing) >= 5:
            return {"new_papers": [], "note": "Already ≥5 papers, skip LLM expansion"}

        genus, species = ctx["genus"], ctx["species"]
        chinese_name = ctx.get("chinese_name", "")

        # Generate semantic queries without using the species name
        semantic_queries = [
            f"endangered cyprinid Yangtze River China",
            f"freshwater fish conservation genetics East Asia",
            f"{genus} X-ray microtomography",
        ]
        if chinese_name:
            semantic_queries.append(f"{chinese_name} 资源 保护")

        existing_dois = {p.doi_key for p in existing}
        new_papers = []

        for q in semantic_queries:
            results = self._call_search_tools(q, phase.get("tools", []), ctx, n=15)
            for r in results:
                if r.doi_key not in existing_dois and self._species_in_title(r, ctx):
                    r.source = f"llm_expansion:{q[:40]}"
                    new_papers.append(r)

        return {"new_papers": new_papers, "tokens_used": phase.get("budget", 3000)}

    @register_phase("deduplicate_and_merge")
    def _fn_deduplicate_and_merge(self, phase: dict, ctx: dict) -> dict:
        """Phase 99: Final deduplication of all papers."""
        papers = ctx.get("all_papers", [])
        deduped = self._deduplicate(papers)
        return {"new_papers": deduped, "tokens_used": 0}

    # ── 重连/重试工具 ──

    def _http_retry(self, url_fn, label="http"):
        """带指数退避的 HTTP 重试包装器。

        Args:
            url_fn: 返回 (response_body: bytes) 的可调用对象
            label: 日志标签

        Returns:
            response_body: bytes

        Raises:
            urllib.error.URLError: 重试全部耗尽后抛出
        """
        deadline = time.monotonic() + self._http_retry_max_s
        last_error = None
        for attempt in range(self._http_retry_attempts):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                return url_fn()
            except (urllib.error.URLError, urllib.error.HTTPError,
                    TimeoutError, OSError) as e:
                last_error = e
                wait = min(2 ** attempt, remaining / 2, 15)  # 退避 ≤15s
                if wait > 0.5 and attempt < self._http_retry_attempts - 1:
                    logger.info(f"Retry {label} attempt {attempt+1}/{self._http_retry_attempts} "
                                f"after {wait:.1f}s ({type(e).__name__})")
                    time.sleep(wait)
        raise last_error or RuntimeError(f"{label}: retry exhausted")

    # ── Tool Calling ──

    def _call_search_tools(self, query: str, tools: list[str],
                           ctx: dict, n: int = 20) -> list[Paper]:
        """Dispatch search query to available tools based on mode."""
        if self.mode == "mock":
            return self._mock_search(query, n)
        elif self.mode == "record":
            return self._recorded_search(query, n)
        elif self.mode == "http":
            return self._http_search(query, tools, n)
        elif self.mode == "mcp":
            return self._mcp_search(query, tools, n)
        return []

    # ── Tool → API 映射（_http_search 用） ──
    _TOOLS_PUBMED = {"ncbi_ncbi_esearch", "article_search_literature"}
    _TOOLS_CROSSREF_OPENALEX = {
        "scholar_search_literature_graph", "article_search_literature",
        "scholar_search_google_scholar_key_words",
        "scholarly_research_search",
    }
    _TOOLS_WEB_ONLY = {
        "web_search", "tavily_tavily_search", "tavily_tavily_extract",
        "exa_web_search_exa", "exa_web_fetch_exa",
    }
    # v3.0: 中文原生引擎 — 通过 parallel_search HTTP provider 直调
    _TOOLS_CHINESE_NATIVE = {
        "baidu_scholar", "cnki_web", "wanfang_web", "cas_web", "chinese_sweep",
        "chinese_search", "duckduckgo_search",
    }
    # v3.0: 预印本引擎 — bioRxiv API + ResearchGate Bing
    _TOOLS_PREPRINT = {
        "biorxiv_api", "biorxiv_search", "researchgate_web",
    }
    # v3.0: 所有非 MCP 原生引擎 (HTTP fallback 可用)
    _TOOLS_NATIVE_HTTP = _TOOLS_PUBMED | _TOOLS_CROSSREF_OPENALEX | _TOOLS_CHINESE_NATIVE | _TOOLS_PREPRINT

    def _http_search(self, query: str, tools: list[str], n: int) -> list[Paper]:
        """HTTP-mode: call PubMed E-utilities, Crossref, OpenAlex, Chinese native, Preprint.

        v3.0 扩展: 支持中文原生引擎 (baidu_scholar/cnki_web/wanfang_web/cas_web) 
        和预印本引擎 (biorxiv_api/researchgate_web)，通过 parallel_search HTTP provider 直调。
        Web-only 工具 (web_search, tavily, exa) 在纯 HTTP 模式下不可用。
        """
        # ── Tools routing: determine which APIs to call ──
        tool_set = {t.lower() for t in tools}

        # Empty tools → backward-compatible: call all
        if not tool_set:
            call_pubmed = True
            call_crossref_openalex = True
            call_native = False
            call_preprint = False
        else:
            call_pubmed = bool(tool_set & self._TOOLS_PUBMED)
            call_crossref_openalex = bool(tool_set & self._TOOLS_CROSSREF_OPENALEX)
            call_native = bool(tool_set & self._TOOLS_CHINESE_NATIVE)
            call_preprint = bool(tool_set & self._TOOLS_PREPRINT)
            # If ALL tools are web-only → nothing available in HTTP mode
            if tool_set and tool_set.issubset(self._TOOLS_WEB_ONLY):
                logger.debug(f"HTTP mode has no web tools, skipping '{query[:40]}'")
                return []

        papers = []
        errors: list[str] = []

        # ── Parallel execution ──
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=5) as pool:  # v5.6: 3→5 (PubMed+Crossref+OpenAlex+Chinese+Preprint)
            futures = []

            # Task 1: PubMed (with Europe PMC fallback)
            if call_pubmed:
                def _task_pubmed():
                    from urllib.parse import quote as _q
                    local_papers: list[Paper] = []
                    source = "PubMed"
                    try:
                        def _fetch():
                            url = (
                                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                                f"db=pubmed&term={_q(query)}&retmax={n}&retmode=json"
                            )
                            with urllib.request.urlopen(url, timeout=self._http_timeout_per_call) as resp:
                                return resp.read()
                        body = self._http_retry(_fetch, label=f"PubMed esearch({query[:40]})")
                        data = json.loads(body)
                        id_list = data.get("esearchresult", {}).get("idlist", [])
                        if id_list:
                            ids = ",".join(id_list[:n])
                            efetch_url = (
                                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                                f"db=pubmed&id={ids}&retmode=xml"
                            )
                            local_papers.extend(self._parse_pubmed_xml(efetch_url))
                        logger.info(f"PubMed: {len(id_list)} hits for '{query}'")
                    except Exception as exc:
                        logger.warning(f"PubMed NCBI failed for '{query}': {exc}")
                        # v5.6: Europe PMC fallback — same data, different host, no API key
                        try:
                            from src.parallel_search import search_europe_pmc
                            raw = search_europe_pmc(query, n)
                            for item in raw:
                                p = Paper(
                                    doi=item.get("doi", ""),
                                    title=item.get("title", ""),
                                    year=item.get("year"),
                                    journal=item.get("journal", ""),
                                    authors=item.get("authors", []),
                                    source="europe_pmc",
                                    abstract=item.get("abstract", ""),
                                )
                                if p.doi_key:
                                    local_papers.append(p)
                            source = "Europe_PMC(fallback)"
                            logger.info(f"Europe PMC fallback: {len(local_papers)} hits for '{query[:40]}'")
                        except Exception as e2:
                            logger.warning(f"Europe PMC also failed: {e2}")
                            return local_papers, f"PubMed+EuropePMC(ERROR)"
                    return local_papers, source
                futures.append(pool.submit(_task_pubmed))

            # Task 2: Crossref
            if call_crossref_openalex:
                def _task_crossref():
                    from urllib.parse import quote as _q
                    local_papers: list[Paper] = []
                    try:
                        def _fetch():
                            url = f"https://api.crossref.org/works?query={_q(query)}&rows={n}"
                            with urllib.request.urlopen(url, timeout=self._http_timeout_per_call) as resp:
                                return resp.read()
                        body = self._http_retry(_fetch, label=f"Crossref({query[:40]})")
                        data = json.loads(body)
                        items = data.get("message", {}).get("items", [])
                        for item in items:
                            paper = self._crossref_to_paper(item)
                            if paper:
                                local_papers.append(paper)
                        logger.info(f"Crossref: {len(items)} items for '{query}'")
                    except Exception as exc:
                        logger.warning(f"Crossref failed for '{query}': {exc}")
                        raise exc
                    return local_papers, "Crossref"
                futures.append(pool.submit(_task_crossref))

            # Task 3: OpenAlex
            if call_crossref_openalex:
                def _task_openalex():
                    from urllib.parse import quote as _q
                    local_papers: list[Paper] = []
                    try:
                        def _fetch():
                            oa_query = _q(query, safe='')
                            url = f"https://api.openalex.org/works?search={oa_query}&per_page={min(n, 50)}"
                            req = urllib.request.Request(url, headers={
                                "User-Agent": "mailto:cognitive-search-engine@reasonix.local",
                                "Accept": "application/json",
                            })
                            with urllib.request.urlopen(req, timeout=self._http_timeout_per_call) as resp:
                                return resp.read()
                        body = self._http_retry(_fetch, label=f"OpenAlex({query[:40]})")
                        data = json.loads(body)
                        results = data.get("results", [])
                        for item in results:
                            paper = self._openalex_to_paper(item)
                            if paper:
                                local_papers.append(paper)
                        logger.info(f"OpenAlex: {len(results)} results for '{query}'")
                    except Exception as exc:
                        logger.warning(f"OpenAlex failed for '{query}': {exc}")
                        raise exc
                    return local_papers, "OpenAlex"
                futures.append(pool.submit(_task_openalex))

            # Task 4: Chinese native engines (v3.0) — baidu_scholar/cnki_web/wanfang_web/cas_web
            if call_native:
                def _task_native():
                    local_papers: list[Paper] = []
                    engines_called: list[str] = []
                    try:
                        # Lazy-load parallel_search providers
                        from src.parallel_search import SEARCH_PROVIDERS as _providers
                        # Map tool names → provider names (strip _web suffix where needed)
                        provider_map = {
                            "baidu_scholar": "baidu_scholar",
                            "cnki_web": "cnki_web",
                            "wanfang_web": "wanfang_web",
                            "cas_web": "cas_web",
                            "chinese_sweep": "chinese_search",
                            "chinese_search": "chinese_search",
                        "duckduckgo_search": "serpapi_duckduckgo",
                        }
                        for tool_name in tool_set & self._TOOLS_CHINESE_NATIVE:
                            prov_name = provider_map.get(tool_name, tool_name)
                            provider_fn = _providers.get(prov_name)
                            if provider_fn:
                                try:
                                    raw = provider_fn(query, n)
                                    engines_called.append(tool_name)
                                    for item in raw:
                                        p = Paper(
                                            doi=item.get("doi", ""),
                                            title=item.get("title", ""),
                                            year=item.get("year"),
                                            journal=item.get("journal", ""),
                                            authors=item.get("authors", []),
                                            source=f"native_http:{tool_name}",
                                            abstract=item.get("abstract", item.get("snippet", "")),
                                        )
                                        if p.doi_key:
                                            local_papers.append(p)
                                except Exception as pe:
                                    logger.warning(f"Native engine {tool_name} failed: {pe}")
                        logger.info(f"Chinese native ({','.join(engines_called)}): {len(local_papers)} papers for '{query[:40]}'")
                    except ImportError:
                        logger.debug("parallel_search providers not available, skipping Chinese native engines")
                    except Exception as exc:
                        logger.warning(f"Chinese native engines failed for '{query}': {exc}")
                    return local_papers, f"native({','.join(engines_called) if engines_called else 'none'})"
                futures.append(pool.submit(_task_native))

            # Task 5: Preprint engines (v3.0) — biorxiv_api/researchgate_web
            if call_preprint:
                def _task_preprint():
                    local_papers: list[Paper] = []
                    engines_called: list[str] = []
                    try:
                        from src.parallel_search import SEARCH_PROVIDERS as _providers
                        provider_map = {
                            "biorxiv_api": "biorxiv_search",
                            "biorxiv_search": "biorxiv_search",
                            "researchgate_web": "researchgate_web",
                        }
                        for tool_name in tool_set & self._TOOLS_PREPRINT:
                            prov_name = provider_map.get(tool_name, tool_name)
                            provider_fn = _providers.get(prov_name)
                            if provider_fn:
                                try:
                                    raw = provider_fn(query, n)
                                    engines_called.append(tool_name)
                                    for item in raw:
                                        p = Paper(
                                            doi=item.get("doi", ""),
                                            title=item.get("title", ""),
                                            year=item.get("year"),
                                            journal=item.get("journal", item.get("server", "")),
                                            authors=item.get("authors", []),
                                            source=f"preprint:{tool_name}",
                                            abstract=item.get("abstract", ""),
                                        )
                                        if p.doi_key:
                                            local_papers.append(p)
                                except Exception as pe:
                                    logger.warning(f"Preprint engine {tool_name} failed: {pe}")
                        logger.info(f"Preprint ({','.join(engines_called)}): {len(local_papers)} papers for '{query[:40]}'")
                    except ImportError:
                        logger.debug("parallel_search providers not available, skipping preprint engines")
                    except Exception as exc:
                        logger.warning(f"Preprint engines failed for '{query}': {exc}")
                    return local_papers, f"preprint({','.join(engines_called) if engines_called else 'none'})"
                futures.append(pool.submit(_task_preprint))

            # Collect results
            for fut in as_completed(futures):
                try:
                    result_papers, source = fut.result()
                    papers.extend(result_papers)
                except Exception as exc:
                    errors.append(f"{exc}")

        # Log errors once
        for err in errors:
            self._search_errors.append(str(err))

        return papers

    def _mcp_search(self, query: str, tools: list[str], n: int) -> list[Paper]:
        """MCP-mode: call external MCP servers via stdio JSON-RPC.

        并行启动所有工具，先完成先返回，后完成的后合并。
        B 引擎可在 A 引擎的结果上添加引用回溯。
        """
        # v5.7: 优先使用全局 MCP 工具 (Reasonix 运行时注入)
        mcp_fn = globals().get("tavily_tavily_search")
        if callable(mcp_fn):
            from dataclasses import fields as _dfields
            papers = []
            for tool_name in tools:
                try:
                    fn = globals().get(tool_name)
                    if not callable(fn):
                        continue
                    result = fn(query, n)
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict):
                                p = Paper(
                                    doi=item.get("doi", ""),
                                    title=item.get("title", item.get("name", "")),
                                    year=item.get("year", item.get("pubYear")),
                                    journal=item.get("journal", item.get("journalTitle", "")),
                                    authors=item.get("authors", []),
                                    source=f"mcp:{tool_name}",
                                    abstract=item.get("abstract", item.get("snippet", "")),
                                )
                                if p.doi_key:
                                    papers.append(p)
                            elif hasattr(item, '__dataclass_fields__'):
                                papers.append(item)
                except Exception:
                    continue
            return papers

        # Fallback: MCP client
        try:
            from src.mcp_client import McpClient
            client = McpClient()
            tool_calls = [
                (t, {"query": query, "max_results": n})
                for t in tools
            ]
            parallel_results = client.call_tools_parallel(
                tool_calls,
                timeout_s=self._mcp_parallel_timeout_s,
            )
            papers = []
            for tool_name, result_list in parallel_results:
                try:
                    papers.extend(self._mcp_result_to_papers(result_list, tool_name))
                except Exception:
                    continue
            return papers
        except ImportError:
            return []
            return papers

    def _call_mcp_tool(self, tool_name: str, args: dict) -> list[dict]:
        """Call a single MCP tool. Requires external MCP server process."""
        # This delegates to src/mcp_client.py when available
        try:
            from src.mcp_client import McpClient
            client = McpClient()
            return client.call_tool(tool_name, args)
        except ImportError:
            raise RuntimeError(
                "MCP mode requires src/mcp_client.py. "
                "Install MCP servers: npx -y scholar-mcp, article-mcp, etc."
            )

    def _mock_search(self, query: str, n: int) -> list[Paper]:
        """Mock-mode: return deterministic test papers (no network)."""
        return [
            Paper(
                doi=f"10.mock/{hash(query) % 100000}",
                title=f"Mock paper about {query[:50]}",
                year=2024,
                journal="Mock Journal",
                authors=["Mock Author"],
                species=["Ochetobius_elongatus"],
                source=f"mock:{query[:40]}",
            )
        ]

    def _recorded_search(self, query: str, n: int) -> list[Paper]:
        """Record-mode: replay saved search results."""
        record_path = self.record_dir / f"{hash(query) % 10000}.json"
        if record_path.exists():
            with open(record_path) as f:
                data = json.load(f)
            return [Paper(**p) for p in data.get("papers", [])]
        return []

    # ── Graph Interaction ──

    def _load_graph_papers(self, species_id: str) -> list[dict]:
        """Load papers from species_graph.yaml for the given species."""
        try:
            from src.graph_updater import load_species_graph
            return load_species_graph(species_id)
        except ImportError as exc:
            logger.debug(f"graph_updater not available: {exc}")

        # Fallback: resolve path relative to engine root — collect ALL matching papers
        papers = []
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                for p in graph.get("graph", {}).get("papers", []):
                    if species_id in p.get("species", []):
                        papers.append(p)
        except Exception as exc:
            logger.warning(f"Graph load failed: {exc}")
        return papers

    def _get_chinese_name(self, species_id: str) -> str:
        """Get Chinese name from species_graph.yaml."""
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                for s in graph.get("graph", {}).get("species", []):
                    if s["id"] == species_id:
                        return s.get("chinese", "")
        except Exception as exc:
            logger.warning(f"getName failed: {exc}")
        return ""

    def _get_variants(self, species_id: str) -> list[str]:
        """Get known spelling variants from graph."""
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                for s in graph.get("graph", {}).get("species", []):
                    if s["id"] == species_id:
                        return s.get("variants", [])
        except Exception:
            pass
        return []

    def _get_journals(self, species_id: str) -> list[str]:
        """Get target journals from graph."""
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                journals = []
                for j in graph.get("graph", {}).get("journals", []):
                    if species_id in j.get("species", []):
                        journals.append(j["name"])
                return journals
        except Exception:
            pass
        return []

    # ── Deduplication ──

    def _merge_papers(self, new_papers: list[Paper]):
        """Merge new papers into all_papers."""
        existing_dois = {p.doi_key for p in self._all_papers}
        for p in new_papers:
            if p.doi_key not in existing_dois:
                self._all_papers.append(p)
                existing_dois.add(p.doi_key)

    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Deduplicate by DOI (primary) and normalized title (secondary).

        DOI normalization: strip trailing dots, lowercase.
        Title normalization: strip trailing dots/HTML, squash whitespace,
        first 80 chars after normalization.
        """
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[Paper] = []

        for p in papers:
            # DOI key
            raw_doi = (p.doi or "").lower().strip().rstrip(".")
            key = raw_doi if raw_doi else ""
            # Title key: normalize aggressively
            raw_title = (p.title or "").lower().strip()
            # Remove HTML entities and trailing punctuation
            raw_title = raw_title.replace("&lt;i&gt;", "").replace("&lt;/i&gt;", "")
            raw_title = raw_title.replace("<i>", "").replace("</i>", "")
            raw_title = raw_title.rstrip(".").strip()
            # Squash multiple spaces
            while "  " in raw_title:
                raw_title = raw_title.replace("  ", " ")
            title_key = raw_title[:80]

            if key and key in seen_dois:
                continue
            if not key and title_key in seen_titles:
                continue

            if key:
                seen_dois.add(key)
            seen_titles.add(title_key)
            unique.append(p)

        return unique

    # ── Trust Score ──

    def _trust_score(self, paper: Paper, ctx: dict) -> int:
        """5-level trust scoring — delegates to src/validator.py.

        Uses the extracted validator module for independence from search logic.
        Falls back to inline scoring if validator is unavailable.
        """
        try:
            from src.validator import trust_score as validator_trust_score
            known_authors = self._get_all_known_authors()
            known_journals = self._get_all_known_journals()
            species_terms = [ctx.get("species", ""), ctx.get("chinese_name", "")]
            species_terms = [t for t in species_terms if t]
            return validator_trust_score(
                paper, known_authors=known_authors,
                known_journals=known_journals,
                species_terms=species_terms,
            )
        except ImportError:
            pass

        # Fallback: inline scoring (backward compatible)
        score = 50
        if paper.doi and paper.doi.startswith("10."):
            score += 20
        if paper.pmid:
            score += 15
        if self._species_in_title(paper, ctx):
            score += 10
        known_authors = {a.lower() for a in self._get_all_known_authors()}
        if any(a.lower() in known_authors for a in paper.authors):
            score += 10
        known_journals = self._get_all_known_journals()
        if paper.journal and paper.journal.lower() in [j.lower() for j in known_journals]:
            score += 5
        return min(100, score)

    def _get_all_known_authors(self) -> list[str]:
        """Get all known authors from graph."""
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                return [a["name"] for a in graph.get("graph", {}).get("authors", [])]
        except Exception:
            pass
        return []

    def _get_all_known_journals(self) -> list[str]:
        """Get all known journals from graph."""
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                return [j["name"] for j in graph.get("graph", {}).get("journals", [])]
        except Exception:
            pass
        return []

    # ── Activation / Stop Logic ──

    def _should_activate(self, phase: dict, ctx: dict) -> bool:
        condition = phase.get("activation")
        if condition is None:
            return True
        try:
            return eval(condition, {"__builtins__": {}}, {**ctx, **self._builtins()})
        except Exception:
            return False

    def _should_stop_global(self, ctx: dict) -> bool:
        for sc in self.stop_conditions:
            try:
                if eval(sc["condition"], {"__builtins__": {}}, {**ctx, **self._builtins()}):
                    return True
            except Exception:
                continue
        return False

    def _stop_reason(self) -> str:
        if self._consecutive_zero >= 3:
            return f"3 consecutive phases returned 0 new papers (diminishing returns)"
        if self._tokens_spent >= 50000:
            return f"Token budget exhausted ({self._tokens_spent} tokens)"
        return f"All phases exhausted ({len(self._all_papers)} papers, {self._tokens_spent} tokens)"

    def _builtins(self) -> dict:
        # Read satisfice_threshold from search_rules.yaml adaptive_params
        _sat_val = self.adaptive_params.get("satisfice_threshold", {}).get("value", 50)
        return {
            "len": len, "any": any, "max": max, "min": min,
            "filter": filter, "sum": sum,
            "config": DotDict({
                "search": {
                    "energy": {
                        "min_papers_satisfice": _sat_val,
                        "max_total_tokens": 50000,
                    }
                }
            })
        }

    # ── ReAct execution ──

    def _execute_react(self, species_id: str, genus: str,
                       sp_epithet: str, chinese_name: str,
                       graph_papers: list[dict]) -> dict[str, Any]:
        """Delegate search to CognitiveAgent (ReAct loop).

        Wires the rule_engine's phase executor into the agent,
        so that Think→Act→Observe→Reflect uses the same handlers.
        """
        # importlib with unique module name to avoid 'src' package conflicts
        # (porpoise-agent/src/ and coilia-agent/src/ also have __init__.py)
        import importlib.util as _iu
        import sys as _sys2
        _agent_path = Path(__file__).resolve().parent / "agent_core.py"
        _mod_name = f"cognitive.agent_core.{id(self)}"
        _spec = _iu.spec_from_file_location(_mod_name, str(_agent_path))
        if _spec and _spec.loader:
            _mod = _iu.module_from_spec(_spec)
            _sys2.modules[_mod_name] = _mod
            _spec.loader.exec_module(_mod)
            CognitiveAgent = _mod.CognitiveAgent
        else:
            raise ImportError(f"agent_core.py not found at {_agent_path}")

        agent = self._get_agent()

        # Wire phase executor: CognitiveAgent calls back to
        # RuleEngine._execute_phase for each ReAct cycle
        agent.set_executor(self._execute_phase)

        # Delegate search
        result = agent.search(
            species_id=species_id,
            genus=genus,
            species=sp_epithet,
            chinese_name=chinese_name,
            graph_papers=graph_papers,
        )

        # Augment: fill in authors/institutions from species_graph
        from dataclasses import fields
        paper_dicts = result.get("papers", [])
        if paper_dicts:
            # Convert from dict to Paper, augment, convert back
            papers = [self._dict_to_paper(p) for p in paper_dicts]
            augmented = self._augment_papers_from_graph(papers)
            result["papers"] = [p.__dict__ for p in augmented]
            result["paper_count"] = len(augmented)

        # Auto-writeback: persist new papers to graph
        try:
            papers_for_writeback = [self._dict_to_paper(p) for p in paper_dicts]
            result["new_to_graph"] = self._auto_writeback(species_id, papers_for_writeback)
        except Exception:
            result["new_to_graph"] = 0

        # Save record
        if self.mode == "record":
            self._save_record(species_id, result)

        return result

    def _auto_writeback(self, species_id: str, papers: list[Paper]) -> int:
        """Merge new papers back into species_graph.yaml for persistent knowledge.

        Returns number of papers added to graph. Non-critical — failures
        are silently swallowed (graph write is a best-effort side effect).
        """
        try:
            from src.graph_updater import update_species_graph, load_species_graph
            known_papers = load_species_graph(species_id)
            known_dois = {(p.get("doi") or "").lower().strip() for p in known_papers}
            truly_new = []
            for p in papers:
                key = (p.doi or "").lower().strip()
                if key and key not in known_dois and p.source != "graph":
                    truly_new.append({
                        "doi": p.doi,
                        "title": p.title or "",
                        "year": p.year,
                        "journal": p.journal or "",
                        "authors": p.authors,
                        "institutions": p.institutions,
                        "species": p.species,
                    })
            if truly_new:
                return update_species_graph(species_id, truly_new)
        except Exception:
            pass
        return 0

    def _get_agent(self):
        """Lazy-init the CognitiveAgent with phase specs from search_rules."""
        if self._agent is None:
            # importlib with unique module name (same as _execute_react)
            import importlib.util as _iu
            import sys as _sys2
            _agent_path = Path(__file__).resolve().parent / "agent_core.py"
            _mod_name = f"cognitive.agent_core.{id(self)}"
            _spec = _iu.spec_from_file_location(_mod_name, str(_agent_path))
            if _spec and _spec.loader:
                _mod = _iu.module_from_spec(_spec)
                _sys2.modules[_mod_name] = _mod
                _spec.loader.exec_module(_mod)
                CognitiveAgent = _mod.CognitiveAgent
            else:
                raise ImportError(f"agent_core.py not found at {_agent_path}")
            _rules_path = str(Path(__file__).resolve().parent.parent / "config" / "search_rules.yaml")
            self._agent = CognitiveAgent(mode=self.mode, rules_path=_rules_path)
        return self._agent

    # ── Helpers ──

    def _dict_to_paper(self, d) -> Paper:
        """Convert a species_graph.yaml paper dict to a Paper object."""
        # Normalize: Paper dataclass -> dict
        if not isinstance(d, dict):
            d = d.__dict__ if hasattr(d, "__dataclass_fields__") else {}
        return Paper(
            doi=d.get("doi", ""),
            title=d.get("title", ""),
            title_zh=d.get("title_zh"),
            year=d.get("year"),
            journal=d.get("journal", ""),
            authors=d.get("authors", []),
            institutions=d.get("institutions", []),
            species=d.get("species", []),
            citations=d.get("citations", 0),
            pmid=d.get("pmid"),
            trust="verified",
            trust_score=80,
            source="species_graph",
            note=d.get("note", ""),
            abstract=d.get("abstract", ""),
        )

    def _matches_species_context(self, paper: Paper, ctx: dict,
                                  genus: str, species: str) -> bool:
        """Check if paper is plausibly about the target species.

        Three-tier filter:
          Tier 1 — Reject: unrelated taxa sharing the epithet
          Tier 2 — Strong accept: genus+species in title or Chinese name
          Tier 3 — Weak accept: species epithet + fish/biological context
        """
        title_raw = paper.title or ""
        title_lower = title_raw.lower()
        genus_lower = genus.lower()
        sp_lower = species.lower()
        chinese = ctx.get("chinese_name", "")
        chinese_alt = ctx.get("chinese_alt", [])
        if isinstance(chinese_alt, str):
            chinese_alt = [chinese_alt]

        # ── Tier 1: Reject unrelated taxa that share the epithet ──
        reject_taxa = [
            "sulfolobus", "metallosphaera", "antrocephalus", "gryon",
        ]
        for rt in reject_taxa:
            if rt in title_lower[:80]:
                return False

        # ── Tier 2: Strong accept ──
        # Full binomial in title
        binomial = f"{genus_lower} {sp_lower}"
        if binomial in title_lower:
            return True
        # Genus match (strongest single signal)
        if genus_lower in title_lower:
            return True
        # Chinese name match
        if chinese and chinese in title_raw:
            return True
        for cn in chinese_alt:
            if cn and cn in title_raw:
                return True

        # ── Tier 3: Species epithet + biological context ──
        if sp_lower in title_lower:
            bio_kw = [
                "fish", "cyprinid", "dace", "redfin", "pisces",
                "freshwater", "anadromous", "teleost", "cypriniformes",
                "genetic", "genome", "morpholog", "phenotyp",
                "conservation", "endangered", "population",
                "mitochondrial", "dna", "sequence",
                "river", "lake", "yangtze", "sea of japan",
                "spawning", "migration", "otolith",
            ]
            if any(kw in title_lower for kw in bio_kw):
                return True
            # Also check first 200 chars of abstract
            abstract = (paper.abstract or "")[:200].lower()
            if any(kw in abstract for kw in bio_kw):
                return True

        return False

    def _augment_papers_from_graph(self, papers: list[Paper]) -> list[Paper]:
        """Complete paper metadata from species_graph.yaml.

        If a paper's DOI matches a graph entry, fill in missing fields
        (authors, institutions, Chinese title, abstract).
        """
        graph_papers = {}
        try:
            _root = Path(__file__).resolve().parent.parent
            graph_path = _root / "config" / "species_graph.yaml"
            if graph_path.exists():
                with open(graph_path) as f:
                    graph = yaml.safe_load(f)
                for p in graph.get("graph", {}).get("papers", []):
                    doi = p.get("doi", "").lower().strip()
                    if doi:
                        graph_papers[doi] = p
        except Exception:
            return papers

        for paper in papers:
            key = (paper.doi or "").lower().strip()
            if key and key in graph_papers:
                gp = graph_papers[key]
                if not paper.authors:
                    paper.authors = gp.get("authors", [])
                if not paper.institutions:
                    paper.institutions = gp.get("institutions", [])
                if not paper.title_zh:
                    paper.title_zh = gp.get("title_zh")
                if not paper.abstract:
                    paper.abstract = gp.get("abstract", "")
                if gp.get("note"):
                    paper.note = gp["note"]
                # Elevate trust for graph-verified papers
                if paper.trust == "pending":
                    paper.trust = "graph_verified"
                    paper.trust_score = 85
        return papers

    @staticmethod
    def _parse_species_id(species_id: str) -> tuple[str, str]:
        """'Ochetobius_elongatus' → ('Ochetobius', 'elongatus')"""
        parts = species_id.replace("-", "_").split("_")
        if len(parts) >= 2:
            return parts[0], "_".join(parts[1:])
        return parts[0], ""

    @staticmethod
    def _is_review(title: str) -> bool:
        pattern = r"(review|systematic\s*review|meta.?analysis|综述|研究进展|进展|概述)"
        return bool(re.search(pattern, title, re.IGNORECASE))

    @staticmethod
    def _species_in_title(paper: Paper, ctx: dict) -> bool:
        title_lower = (paper.title or "").lower()
        genus_lower = ctx.get("genus", "").lower()
        species_lower = ctx.get("species", "").replace("_", " ").lower()
        chinese = ctx.get("chinese_name", "")

        if genus_lower and genus_lower in title_lower:
            return True
        if species_lower and species_lower in title_lower:
            return True
        if chinese and chinese in (paper.title or ""):
            return True
        return False

    @staticmethod
    def _soundex(word: str) -> list[str]:
        """Generate Soundex code(s) for a word."""
        if not word:
            return []
        word = word.upper()
        mapping = {
            "B": "1", "F": "1", "P": "1", "V": "1",
            "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2",
            "S": "2", "X": "2", "Z": "2",
            "D": "3", "T": "3",
            "L": "4",
            "M": "5", "N": "5",
            "R": "6",
        }
        first = word[0]
        code = first
        prev = mapping.get(first, "")
        for ch in word[1:]:
            mapped = mapping.get(ch, "")
            if mapped and mapped != prev:
                code += mapped
                prev = mapped
        code = code[:4].ljust(4, "0")
        return [code]

    def _get_references(self, doi: str, ctx: dict) -> list[Paper]:
        """Get reference list of a paper by DOI."""
        if self.mode == "mock":
            return []
        try:
            import urllib.request
            url = f"https://api.crossref.org/works/{quote_plus(doi)}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            refs = []
            for ref in data.get("message", {}).get("reference", [])[:30]:
                paper = Paper(
                    doi=ref.get("DOI", ""),
                    title=ref.get("article-title", ""),
                    year=ref.get("year"),
                    journal=ref.get("journal-title", ""),
                    authors=[ref.get("author", "")] if ref.get("author") else [],
                    source=f"reference_of:{doi}",
                )
                refs.append(paper)
            return refs
        except Exception:
            return []

    def _get_citing_papers(self, doi: str, ctx: dict) -> list[Paper]:
        """Get papers that cite this paper."""
        if self.mode == "mock":
            return []
        try:
            import urllib.request
            url = f"https://api.crossref.org/works/{quote_plus(doi)}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            return [self._crossref_to_paper(data.get("message", {}))]
        except Exception:
            return []

    def _crossref_to_paper(self, item: dict) -> Optional[Paper]:
        """Convert Crossref API response item to Paper."""
        try:
            doi = item.get("DOI", "")
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                if given and family:
                    authors.append(f"{family} {given}")
                elif family:
                    authors.append(family)
            return Paper(
                doi=doi,
                title=title,
                year=int(item.get("published-print", {}).get("date-parts", [[0]])[0][0]
                         or item.get("published-online", {}).get("date-parts", [[0]])[0][0]
                         or 0),
                journal=item.get("container-title", [""])[0] if item.get("container-title") else "",
                authors=authors,
                citations=item.get("is-referenced-by-count", 0),
                source="crossref",
            )
        except Exception:
            return None


    def _openalex_to_paper(self, item: dict) -> Optional[Paper]:
        """Convert OpenAlex API response item to Paper."""
        try:
            doi = item.get("doi", "") or ""
            doi = doi.replace("https://doi.org/", "").strip()
            title = item.get("title", "")
            publication_date = item.get("publication_date", "")
            year = int(publication_date[:4]) if publication_date else None
            # Authors
            authors = []
            for a in item.get("authorships", []):
                author_obj = a.get("author", {})
                name = author_obj.get("display_name", "")
                if name:
                    authors.append(name)
            # Journal/venue
            journal = ""
            primary_location = item.get("primary_location", {})
            source = primary_location.get("source", {})
            journal = source.get("display_name", "") if source else ""
            if not journal:
                host = item.get("host_venue", {})
                journal = host.get("display_name", "") if host else ""
            # Citations
            citations = item.get("cited_by_count", 0) or 0
            return Paper(
                doi=doi,
                title=title or "",
                year=year,
                journal=journal,
                authors=authors,
                citations=citations,
                source="openalex",
                trust="tentative",
                trust_score=70,
            )
        except Exception:
            return None

    def _parse_pubmed_xml(self, url: str) -> list[Paper]:
        """Parse PubMed EFetch XML response."""
        papers = []
        try:
            import urllib.request
            import xml.etree.ElementTree as ET
            with urllib.request.urlopen(url, timeout=15) as resp:
                tree = ET.parse(resp)
            root = tree.getroot()
            for article in root.findall(".//PubmedArticle"):
                try:
                    medline = article.find(".//MedlineCitation")
                    article_data = medline.find(".//Article") if medline is not None else None
                    if article_data is None:
                        continue
                    title_el = article_data.find("ArticleTitle")
                    title = "".join(title_el.itertext()) if title_el is not None else ""
                    pmid_el = medline.find("./PMID") if medline is not None else None
                    pmid = pmid_el.text if pmid_el is not None else None
                    # Authors
                    authors = []
                    author_list = article_data.find(".//AuthorList")
                    if author_list is not None:
                        for auth in author_list.findall("Author"):
                            last = auth.find("LastName")
                            fore = auth.find("ForeName")
                            if last is not None and fore is not None:
                                authors.append(f"{last.text} {fore.text}")
                            elif last is not None:
                                authors.append(last.text or "")
                    # Journal
                    journal_el = article_data.find(".//Journal/Title")
                    journal = journal_el.text if journal_el is not None else ""
                    # Year
                    year_el = article_data.find(".//Journal/JournalIssue/PubDate/Year")
                    year = int(year_el.text) if year_el is not None else None
                    # DOI (from ArticleIdList) — handle namespaced XML
                    doi = ""
                    # Try both namespaced and plain searches
                    id_list = article.findall(".//ArticleId")
                    if not id_list:
                        id_list = article.findall(".//{http://www.ncbi.nlm.nih.gov}ArticleId")
                    if not id_list:
                        id_list = article.findall(".//*[local-name()='ArticleId']")
                    for aid in id_list:
                        idtype = aid.get("IdType") or aid.get("{http://www.w3.org/1999/xlink}IdType")
                        if idtype == "doi":
                            doi = aid.text or ""
                            break
                    # Fallback: ELocationID
                    if not doi:
                        eloc_list = article.findall(".//ELocationID")
                        if not eloc_list:
                            eloc_list = article.findall(".//*[local-name()='ELocationID']")
                        for eloc in eloc_list:
                            if (eloc.get("EIdType") or eloc.get("EidType", "")
                                ) in ("doi", "DOI"):
                                doi = eloc.text or ""
                                break
                    papers.append(Paper(
                        doi=doi, title=title, year=year, journal=journal,
                        authors=authors, pmid=pmid, source="pubmed",
                    ))
                except Exception:
                    continue
        except Exception as exc:
            logger.warning(f"Graph load failed: {exc}")
        return papers

    def _save_record(self, species_id: str, result: dict):
        """Save search result as a replayable record."""
        record_path = self.record_dir / f"{species_id}.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def get_adaptive_params(self) -> dict:
        """Return current adaptive parameter values."""
        return {k: v.get("value") if isinstance(v, dict) else v
                for k, v in self.adaptive_params.items()}

