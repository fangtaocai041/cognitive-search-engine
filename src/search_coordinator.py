"""
SearchCoordinator — 统一物种搜索协调器

整合全项目规则:
  unified_search.py:  自适应模式 + 分类学检查 + 流式并行
  ZN_EN_RULES.md:    CN/EN通道 + 附带过滤 + 学科分类
  species_graph.yaml: 物种变体 + 保护等级
  unified-species-search.md: 7+引擎并行策略

工作流:
  输入: "珠星三块鱼"
  1. check_taxonomy() → ["Pseudaspius", "Tribolodon", "Leuciscus"]
  2. estimate_mode("LC", 50) → EXHAUSTIVE
  3. search_streaming(variants, group="full") → 7引擎并行
  4. cn_en_label() + is_incidental() + classify_paper()
  5. 江汉大学论文优先 → 输出

用法 (在本会话中直接使用):
  from src.search_coordinator import search
  result = search("鳤")  # 或 "Ochetobius elongatus"
  print(result.summary())
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# 导入 unified_search 的规则引擎
# ═══════════════════════════════════════════════════════

try:
    from src.unified_search import (
        check_taxonomy, estimate_mode, is_incidental, classify_paper,
        cn_en_label, SearchMode, SearchDecision, SearchReport,
        ENGINE_REGISTRY, ENGINE_GROUPS, EngineResult,
        _ensure_species_graph_loaded,
    )
    _HAVE_RULES = True
except ImportError:
    _HAVE_RULES = False
    ENGINE_REGISTRY = {}
    ENGINE_GROUPS = {"quick": [], "standard": [], "full": [], "chinese": []}


# ═══════════════════════════════════════════════════════
# 江汉大学课题组 — 论文优先级标记
# ═══════════════════════════════════════════════════════

# 本课题组作者列表 (按字母排序)
JHU_AUTHORS = {
    # 导师组
    "fei xiong", "熊飞",
    "hongyan liu", "刘红艳",
    "ying wang", "王莹",
    # 学生/成员
    "fangtao cai", "蔡方陶",
    "dongdong zhai", "翟东东",
    "ziyue xu", "徐子悦",
    "ming xia", "夏明",
    "min zhou", "周敏",
    "wen zheng", "郑雯",
    "yuanyuan chen", "陈媛媛",
    # 合作者 (江汉大学)
    "xinbin duan", "段辛斌",
    "huiwu tian", "田辉伍",
}

# 中文期刊白名单 (引用自 ZN_EN_RULES.md)
CN_JOURNALS = {
    "水生生物学报", "acta hydrobiologica sinica",
    "生物多样性", "biodiversity science",
    "中国水产科学", "journal of fishery sciences of china",
    "水产学报", "journal of fisheries of china",
    "湖泊科学", "journal of lake sciences",
    "南方水产科学", "south china fisheries science",
    "生态学报", "acta ecologica sinica",
    "生态科学", "ecological science",
}


# ═══════════════════════════════════════════════════════
# 搜索结果数据结构
# ═══════════════════════════════════════════════════════

@dataclass
class Paper:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    channel: str = ""           # CN | EN
    category: str = ""          # 学科分类
    is_incidental: bool = False
    is_jhu: bool = False        # 江汉大学论文
    jhu_authors: List[str] = field(default_factory=list)  # 本课题组人员


@dataclass
class SearchResult:
    species_name: str           # 搜索名
    all_variants: List[str]    # 所有变体
    mode: str                   # exhaustive | classified | review_anchored
    papers: List[Paper]         # 去重后的论文
    categories: Dict[str, List[Paper]]  # 分类索引
    accidental_count: int       # 附带论文数
    jhu_count: int              # 江汉大学论文数
    engine_stats: Dict[str, int]  # 引擎统计
    elapsed_ms: float           # 总耗时
    error: str = ""             # 错误信息
    emergence_signals: list = field(default_factory=list)  # v8.0: 涌现检测信号

    def summary(self) -> str:
        """生成分类概览 — 按需展开"""
        lines = [
            f"📊 {self.species_name} — 搜索结果",
            f"模式: {self.mode} | 总计: {len(self.papers)}篇",
        ]
        if self.jhu_count:
            lines.append(f"🏠 江汉大学: {self.jhu_count}篇 (已置顶)")
        if self.accidental_count:
            lines.append(f"📎 附带: {self.accidental_count}篇")
        total_engines = sum(self.engine_stats.values())
        ok = self.engine_stats.get("ok", 0)
        lines.append(f"引擎: {ok}/{total_engines} OK ({self.elapsed_ms:.0f}ms)")
        # v8.0: 涌现信号
        if self.emergence_signals:
            lines.append("")
            lines.append("🔮 涌现检测:")
            for sig in self.emergence_signals:
                desc = sig.get("description", str(sig))
                conf = sig.get("confidence", 0)
                icon = "🔴" if conf > 0.7 else "🟡" if conf > 0.4 else "🟢"
                lines.append(f"  {icon} {desc} (置信度: {conf:.0%})")
        lines.append("")
        for cat, papers in self.categories.items():
            if papers:
                latest = max(p.year for p in papers)
                jhu = sum(1 for p in papers if p.is_jhu)
                tag = f" 🏠x{jhu}" if jhu else ""
                lines.append(f"  {cat}: {len(papers)}篇 (最新: {latest}){tag}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# 核心搜索函数
# ═══════════════════════════════════════════════════════

# ── Cross-lingual helper: auto-resolve Chinese↔Latin ──

def _resolve_species_name(name: str) -> List[str]:
    """Resolve a species name to all search forms (CN + Latin + variants).

    Input can be Chinese (刀鲚) or Latin (Coilia nasus).
    Returns all name forms for comprehensive search.
    """
    names = [name]
    try:
        graph = _ensure_species_graph_loaded()
        if not graph:
            return names
        
        name_lower = name.lower().replace(" ", "_")
        
        # Search by scientific name
        for s in graph:
            sid = s.get("id", "").lower()
            if name_lower == sid or name_lower == s.get("name", "").lower():
                cn = s.get("chinese", "")
                if cn and cn not in names:
                    names.append(cn)
                for v in s.get("variants", []):
                    if v not in names:
                        names.append(v)
                break
        
        # Search by Chinese name
        for s in graph:
            cn = s.get("chinese", "")
            if cn and name == cn:
                sci = s.get("name", "")
                if sci and sci not in names:
                    names.append(sci)
                break
    except Exception as _e:
                logger.warning(f"Suppressed in search_coordinator.py: {type(_e).__name__}: {_e}")
    return names


# ── Adaptive engine pruning ──

# Engines to use for different habitat types
_HABITAT_ENGINES = {
    "freshwater": ["scholar_graph", "scholar_keywords", "ncbi_esearch", "crossref_article",
                    "crossref_direct", "semantic_scholar", "cnki_web", "baidu_scholar",
                    "wanfang_web", "tavily_search", "exa_search", "web_search"],
    "marine": ["scholar_graph", "scholar_keywords", "ncbi_esearch", "crossref_article",
                 "crossref_direct", "semantic_scholar", "tavily_search", "exa_search", "web_search"],
    "diadromous": ["scholar_graph", "scholar_keywords", "ncbi_esearch", "crossref_article",
                     "crossref_direct", "semantic_scholar", "cnki_web", "baidu_scholar",
                     "wanfang_web", "tavily_search", "exa_search", "web_search"],
}

def _prune_engines(family: str, group: List[str]) -> List[str]:
    """Prune irrelevant engines based on species family/habitat.

    Marine families skip Chinese freshwater-focused engines.
    """
    family_lower = family.lower() if family else ""
    
    # Marine/estuarine families
    marine_families = {"tetraodontidae", "cynoglossidae", "mugilidae", "engraulidae",
                       "clupeidae", "polynemidae", "callionymidae", "soleidae"}
    
    if family_lower in marine_families:
        # Keep only essential engines for marine species
        return [e for e in group if e not in ("cnki_web", "baidu_scholar", "wanfang_web")]
    
    # Freshwater default: keep all
    return group


def search(species: str, group: str = "full", limit: int = 10) -> SearchResult:
    """
    search("鳤") → SearchResult
    search("鳤") → SearchResult

    统一入口: 分类学检查 → 模式决策 → 多引擎并行 → 规则分类 → 课题组优先
    """
    t0 = time.perf_counter()

    # 0. 跨语种名称解析 (中英双向)
    all_names = _resolve_species_name(species)
    if len(all_names) > 1:
        logger.info(f"Cross-lingual resolved: {species} -> {all_names}")
    species_for_search = all_names[0]
    
    # 1. 分类学变更检查 (unified_search §7)
    try:
        variants = check_taxonomy(species_for_search)
    except Exception:
        # check_taxonomy 不可用时, 优先用 species_graph.yaml
        variants = _fallback_check_taxonomy(species)
    if not variants:
        variants = [species]

    # 2. 自适应模式决策 (unified_search §1)
    try:
        # 从 species_graph 获取保护等级
        conservation = _get_conservation(variants[0])
        mode = estimate_mode(variants[0], conservation, 50)
        search_mode = mode.mode.value
    except Exception:
        search_mode = "exhaustive"

    # 2b. 自适应引擎裁剪
    # 获取物种的科信息，裁剪不相关引擎
    pruned_group = group
    try:
        graph = _ensure_species_graph_loaded()
        if graph:
            species_lower = species_for_search.lower()
            for s in graph:
                if s.get("name", "").lower() == species_lower or s.get("chinese", "") == species:
                    family = s.get("family", "")
                    full_group = ENGINE_GROUPS.get(group, ENGINE_GROUPS.get("full", []))
                    pruned_group = _prune_engines(family, full_group)
                    if len(pruned_group) < len(full_group):
                        logger.info(f"Adaptive pruning: {len(full_group)} -> {len(pruned_group)} engines")
                    break
    except Exception as _e:
                logger.warning(f"Suppressed in search_coordinator.py: {type(_e).__name__}: {_e}")
    
    # 3. 多引擎并行搜索 — 直接调用 MCP 工具 (本会话可用)
    engine_results = _run_real_search(variants, pruned_group, limit)

    # 4. 合并 + 去重 (从 EngineResult 列表提取论文)
    all_papers = []
    engine_stats: Dict[str, int] = {}
    for er in engine_results:
        engine_stats[er.status] = engine_stats.get(er.status, 0) + 1
        if er.results:
            all_papers.extend(er.results)

    # 5. 规则分类 (unified_search §2-4)
    classified_papers = []
    for p in all_papers:
        paper_data = _extract_paper_data(p)
        paper_data.channel = cn_en_label(p)[0] if callable(cn_en_label) else "EN"
        paper_data.category = classify_paper(p).value if callable(classify_paper) else "🌊 生态与资源"
        paper_data.is_incidental = is_incidental(p)[0] if callable(is_incidental) else False
        paper_data.is_jhu, paper_data.jhu_authors = _is_jhu_paper(p)
        classified_papers.append(paper_data)

    # 6. 课题组优先排序
    jhu_first = []
    others = []
    for p in classified_papers:
        if p.is_jhu:
            jhu_first.append(p)
        else:
            others.append(p)
    sorted_papers = jhu_first + others

    # 7. 分类索引
    categories = {}
    jhu_count = 0
    accidental_count = 0
    for p in sorted_papers:
        if p.is_jhu:
            jhu_count += 1
        if p.is_incidental:
            accidental_count += 1
        cat = p.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    elapsed = (time.perf_counter() - t0) * 1000

    # 8. 反幻觉验证: 对搜索结果进行可信度评分
    #    自动运行 credibility_scorer + 交叉引用检查
    #    只为非附属论文做标记 (附属论文已有特殊处理)
    verification_tags = []
    try:
        from src.credibility_scorer import CredibilityScorer as _CS
        _scorer = _CS()
        for _p in sorted_papers:
            _score = _scorer.score({
                "source": _p.channel,
                "cross_ref_count": sum(1 for q in sorted_papers if q.doi and q.doi == _p.doi),
            })
            # 只标记低可信度论文
            try:
                _s = int(_score) if isinstance(_score, (int, float)) else 0
                if _s < 40:
                    verification_tags.append(f"[low-confidence: {_s}]")
            except (TypeError, ValueError):
                pass  # 非数字类型，跳过低可信度标记
    except Exception:
        pass  # credential scorer is non-critical

    # ── 涌现检测钩子 (v8.0) — 搜索完成后自动检测研究趋势涌现 ──
    emergence_signals = _record_emergence(species, sorted_papers, categories, engine_stats, search_mode)

    return SearchResult(
        species_name=species,
        all_variants=variants,
        mode=search_mode,
        papers=sorted_papers,
        categories=categories,
        jhu_count=jhu_count,
        accidental_count=accidental_count,
        engine_stats=engine_stats,
        elapsed_ms=elapsed,
        emergence_signals=emergence_signals,
    )


# ═══════════════════════════════════════════════════════
# 涌现检测钩子 (v8.0)
# ═══════════════════════════════════════════════════════

def _record_emergence(
    species: str,
    papers: list,
    categories: dict,
    engine_stats: dict,
    search_mode: str,
) -> list:
    """搜索后自动记录指标到涌现检测引擎，返回检测到的涌现信号。"""
    signals = []
    try:
        from unified_emergence import EmergenceMonitor, DimensionalLevel

        monitor = EmergenceMonitor(emergence_threshold_sigma=2.5, min_sources=2)

        # 记录论文总量
        monitor.record(
            metric=f"papers:{species}",
            value=len(papers),
            source="search_coordinator",
            level=DimensionalLevel.D1,
        )

        # 记录各分类论文数（检测研究热点转移）
        for cat, count in (categories or {}).items():
            if count > 0:
                monitor.record(
                    metric=f"category:{species}:{cat}",
                    value=count,
                    source="search_coordinator",
                    level=DimensionalLevel.D1,
                )

        # 记录搜索引擎成功率（检测数据源退化）
        for engine, stats in (engine_stats or {}).items():
            if isinstance(stats, dict) and stats.get("count", 0) > 0:
                monitor.record(
                    metric=f"engine:{engine}:success",
                    value=stats["count"],
                    source="search_coordinator",
                    level=DimensionalLevel.D0,
                )

        # 检测涌现
        signals = monitor.check_emergence()
        if signals:
            import logging
            logger = logging.getLogger(__name__)
            for sig in signals:
                logger.info(
                    f"[emergence] {species}: {sig.get('description', str(sig))} "
                    f"(confidence={sig.get('confidence', 0):.2f})"
                )
        return signals or []
    except ImportError:
        return []
    except Exception:
        return []


# ═══════════════════════════════════════════════════════
# 内部辅助函数
# ═══════════════════════════════════════════════════════

def _run_real_search(variants: List[str], group, limit: int) -> List[EngineResult]:
    """实际调用搜索引擎执行搜索。

    优先级:
      1. MCP 工具函数 (在 Reasonix 会话中)
      2. MesoAgent (BDI 管线, 支持 HTTP 直连)
      3. ParallelSearch (纯 HTTP 并行搜索)

    Args:
        variants: 搜索变体列表
        group: 引擎组名 (str) 或引擎 ID 列表 (List[str])
        limit: 每引擎最大结果数
    """
    if isinstance(group, list):
        engines = group  # 已剪枝的引擎列表
    else:
        engines = ENGINE_GROUPS.get(group, ENGINE_GROUPS["full"])
    results = []

    # ── 尝试 MCP 工具 ──
    mcp_available = any(
        globals().get(ENGINE_REGISTRY[e].get("tool", ""))
        for e in engines if e in ENGINE_REGISTRY
    )
    if not mcp_available:
        try:
            mcp_available = any(
                getattr(__builtins__, ENGINE_REGISTRY[e].get("tool", ""), None)
                for e in engines if e in ENGINE_REGISTRY
            )
        except Exception:
            mcp_available = False

    if mcp_available:
        for variant in variants[:3]:
            for engine_id in engines:
                info = ENGINE_REGISTRY.get(engine_id, {})
                tool_name = info.get("tool", "")
                if not tool_name:
                    continue
                t0 = time.perf_counter()
                er = EngineResult(engine=engine_id, query=variant, tool=tool_name)
                fn = globals().get(tool_name)
                if fn is None:
                    try:
                        fn = getattr(__builtins__, tool_name, None)
                    except Exception:
                        fn = None
                if fn is None:
                    er.status = "degraded"
                    er.error = f"MCP {tool_name}: not available"
                else:
                    try:
                        result = _call_mcp(fn, variant, limit)
                        if isinstance(result, list):
                            er.results = result
                        elif isinstance(result, dict):
                            er.results = result.get("results", result.get("papers", [result]))
                        else:
                            er.results = [result]
                        er.status = "ok"
                    except Exception as e:
                        er.status = "error"
                        er.error = str(e)[:200]
                er.elapsed_ms = (time.perf_counter() - t0) * 1000
                results.append(er)
        return results

    # ── Fallback: MesoAgent (BDI 管线 + HTTP 直连) ──
    try:
        from src.meso_agent import MesoAgent, MesoConfig
        agent = MesoAgent(MesoConfig(mode="http"))
        for variant in variants[:2]:
            t0 = time.perf_counter()
            er = EngineResult(engine="meso_agent", query=variant, tool="MesoAgent.search")
            try:
                r = agent.search(variant.replace(" ", "_"))
                papers = getattr(r, "papers", r.get("papers", [])) if isinstance(r, dict) else getattr(r, "papers", [])
                er.results = papers[:limit]
                er.status = "ok" if papers else "degraded"
                er.error = "" if papers else "MesosAgent returned 0 papers"
            except Exception as e:
                er.status = "error"
                er.error = str(e)[:200]
            er.elapsed_ms = (time.perf_counter() - t0) * 1000
            results.append(er)
        if results:
            return results
    except Exception as e:
        logger.debug("MesoAgent fallback failed: %s", e)

    # ── Last resort: ParallelSearch (纯 HTTP) ──
    try:
        from src.parallel_search import ParallelSearch
        searcher = ParallelSearch(max_workers=4)
        for variant in variants[:2]:
            t0 = time.perf_counter()
            er = EngineResult(engine="parallel_search", query=variant, tool="ParallelSearch.search")
            try:
                stats = searcher.search(variant)
                er.results = stats.new_papers[:limit]
                er.status = "ok" if stats.new_papers else "degraded"
            except Exception as e:
                er.status = "error"
                er.error = str(e)[:200]
            er.elapsed_ms = (time.perf_counter() - t0) * 1000
            results.append(er)
        searcher.close()
    except Exception as e:
        logger.debug("ParallelSearch fallback failed: %s", e)

    return results


def _call_mcp(fn: Callable, query: str, limit: int) -> Any:
    """调用MCP工具并返回结果。"""
    name = getattr(fn, "__name__", str(fn))

    if "scholar" in name and "graph" in name:
        return fn(query=query, limit=limit)
    elif "ncbi_esearch" in name:
        return fn(query=query, maxResults=limit)
    elif "article_search" in name:
        return fn(keyword=query, max_results=limit)
    elif "tavily" in name:
        return fn(query=query, max_results=min(limit, 20))
    elif "web_search" in name:
        return fn(query=query, topK=min(limit, 10))
    elif "exa" in name:
        return fn(query=query, numResults=min(limit, 20))
    else:
        return fn(query=query)


def _extract_paper_data(p: Dict) -> Paper:
    """从原始结果提取 Paper 数据。"""
    return Paper(
        title=p.get("title", p.get("name", "")),
        authors=[a.get("name", "") for a in p.get("authors", []) if isinstance(a, dict)],
        year=p.get("year", 0),
        journal=p.get("venue", p.get("journal", "")),
        doi=p.get("doi", ""),
        pmid=p.get("pmid", p.get("externalIds", {}).get("pmid", "")),
    )


def _is_jhu_paper(p: Dict) -> Tuple[bool, List[str]]:
    """判断论文是否为江汉大学课题组论文。"""
    authors = []
    for a in p.get("authors", []):
        if isinstance(a, dict):
            name = (a.get("name") or "").strip().lower()
            authors.append(name)

    matched = [a for a in authors if a in JHU_AUTHORS]
    return len(matched) > 0, matched


def _get_conservation(species_name: str) -> str:
    """从 species_graph 获取保护等级。"""
    import yaml
    from pathlib import Path
    config = Path(__file__).resolve().parent.parent / "config" / "species_graph.yaml"
    if not config.exists():
        return "DD"
    with open(config) as f:
        graph = yaml.safe_load(f)
    name_lower = species_name.lower()
    for s in graph.get("graph", {}).get("species", []):
        if s.get("name", "").lower() == name_lower:
            return s.get("conservation", "DD")
    return "DD"


def _fallback_check_taxonomy(species_name: str) -> List[str]:
    """离线分类学检查。"""
    try:
        return check_taxonomy(species_name)
    except Exception as _e:
                logger.warning(f"Suppressed in search_coordinator.py: {type(_e).__name__}: {_e}")
    import yaml
    from pathlib import Path
    config = Path(__file__).resolve().parent.parent / "config" / "species_graph.yaml"
    if not config.exists():
        return [species_name]
    with open(config) as f:
        graph = yaml.safe_load(f)
    name_lower = species_name.lower()
    for s in graph.get("graph", {}).get("species", []):
        all_names = [s.get("name", "").lower()] + [v.lower() for v in s.get("variants", [])]
        if name_lower in all_names:
            return [s.get("name", species_name)] + s.get("variants", [])
    return [species_name]


# ═══════════════════════════════════════════════════════
# KB-First 两阶段搜索 (f项目知识库 → 全量搜索)
# ═══════════════════════════════════════════════════════

@dataclass
class KbFirstSearchResult:
    """Result from kb_first() — wraps both stages.

    Stage 1 (kb_check): KB lookup result from f项目.
    Stage 2 (full_search): Only populated if user chose to continue.
    """
    stage: str                              # "kb_check" | "full_search"
    species_name: str                       # Original query
    kb_found: bool                          # Whether species found in f项目 KB
    kb_summary: str = ""                    # Human-readable KB result summary
    kb_recommendation: str = ""             # "stay_in_kb" | "continue_to_c"
    kb_data: Dict[str, Any] = field(default_factory=dict)  # Raw KB data
    full_search: Optional[SearchResult] = None  # Stage 2 result
    suggested_next: str = ""                # "ask_user" | "done"
    all_candidates: List[Dict[str, Any]] = field(default_factory=list)

    def ask_user_prompt(self) -> str:
        """Generate the user-facing prompt asking whether to continue."""
        if self.kb_found:
            return (
                f"📚 f项目知识库已收录「{self.species_name}」。\n\n"
                f"{self.kb_summary}\n\n"
                f"───\n"
                f"**是否继续？**\n"
                f"- **留步**：仅使用知识库数据（已足够）\n"
                f"- **继续搜索**：启动 c项目全量文献搜索（多引擎并行 + 引用回溯 + 变体安全网）"
            )
        else:
            candidates = ""
            if self.all_candidates:
                top = self.all_candidates[:3]
                candidates = "\n可能近缘种: " + ", ".join(
                    f"{c['chinese']}({c['scientific']})" for c in top
                )
            return (
                f"🔍 f项目知识库未收录「{self.species_name}」。{candidates}\n\n"
                f"**是否启动 c项目全量文献搜索？** (多引擎并行 + 引用回溯 + 变体安全网)"
            )


def _load_fish_kb() -> Any:
    """Lazy-load FishEcologyOrchestrator from fish-ecology-assistant.

    Returns the orchestrator instance, or None if the f项目 is unavailable.
    Uses cross-project import path: fish-ecology-assistant/src/orchestrator.py.
    """
    try:
        from pathlib import Path

        # Find fish-ecology-assistant root relative to cognitive-search-engine
        cognitive_root = Path(__file__).resolve().parent.parent
        fish_root = cognitive_root.parent / "fish-ecology-assistant"
        fish_src = fish_root / "src"

        if not fish_src.is_dir():
            logger.debug("fish-ecology-assistant not found at %s", fish_root)
            return None

        import sys
        fish_str = str(fish_root)
        if fish_str not in sys.path:
            sys.path.insert(0, fish_str)

        import importlib
        import importlib.util
        _mod_name = f"_fish_orch_{id(fish_str).__abs__() % 10000}"
        spec = importlib.util.spec_from_file_location(
            _mod_name, str(fish_src / "orchestrator.py"))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[_mod_name] = mod
            spec.loader.exec_module(mod)
            factory = getattr(mod, "get_orchestrator", None)
            if factory:
                return factory()
        return None
    except Exception as exc:
        logger.warning("Failed to load fish KB: %s", exc)
        return None


def kb_first(
    species_name: str,
    group: str = "standard",
    limit: int = 10,
) -> KbFirstSearchResult:
    """KB-First 两阶段搜索 — 先查 f项目知识库，再决定是否启动全量搜索。

    This is the RECOMMENDED entry point for species literature search.
    It implements the two-stage workflow:

      Stage 1 (kb_check): Query fish-ecology-assistant knowledge base.
        → Returns KbFirstSearchResult with stage="kb_check".
        → Caller presents ask_user_prompt() to user.

      Stage 2 (full_search): If user says "continue", call
        continue_full_search() → runs search() for full coordinated search.

    Usage:
      # Stage 1: KB check
      result = kb_first("珠星三块鱼")
      if result.stage == "kb_check":
          print(result.ask_user_prompt())
          # ... wait for user input ...

      # Stage 2: Full search (only if user says continue)
      result = continue_full_search(result, group="full")

    Args:
        species_name: Chinese name or scientific name.
        group: Engine group for full search ("quick"/"standard"/"full").
        limit: Max results per engine.

    Returns:
        KbFirstSearchResult with stage="kb_check" (first call) or "full_search".
    """
    # Stage 1: Query fish-ecology-assistant KB
    orch = _load_fish_kb()
    if orch is None:
        # f项目不可用 → 直接跳到全量搜索
        logger.info("fish KB unavailable, running full search directly")
        full = search(species_name, group=group, limit=limit)
        return KbFirstSearchResult(
            stage="full_search",
            species_name=species_name,
            kb_found=False,
            kb_summary="⚠️ f项目知识库不可用，已直接启动全量搜索。",
            kb_recommendation="continue_to_c",
            full_search=full,
            suggested_next="done",
        )

    try:
        kb = orch.kb_first_lookup(query=species_name)
    except Exception as exc:
        # KB lookup failed → fall through to full search
        logger.warning("KB lookup failed: %s, running full search", exc)
        full = search(species_name, group=group, limit=limit)
        return KbFirstSearchResult(
            stage="full_search",
            species_name=species_name,
            kb_found=False,
            kb_summary="⚠️ KB查询失败，已直接启动全量搜索。",
            kb_recommendation="continue_to_c",
            full_search=full,
            suggested_next="done",
        )

    # KB lookup succeeded — build result for user decision
    kb_data = {
        "found": getattr(kb, "found", False),
        "scientific_name": getattr(kb, "scientific_name", ""),
        "chinese_name": getattr(kb, "chinese_name", ""),
        "aliases": getattr(kb, "aliases", []),
        "synonyms": getattr(kb, "synonyms", []),
        "family": getattr(kb, "family", ""),
        "conservation": getattr(kb, "conservation", ""),
        "ecology": getattr(kb, "ecology", ""),
        "distribution": getattr(kb, "distribution", ""),
        "summary_text": getattr(kb, "summary_text", ""),
        "search_recommendation": getattr(kb, "search_recommendation", "continue_to_c"),
        "all_candidates": getattr(kb, "all_candidates", []),
    }

    return KbFirstSearchResult(
        stage="kb_check",
        species_name=species_name,
        kb_found=getattr(kb, "found", False),
        kb_summary=getattr(kb, "summary_text", ""),
        kb_recommendation=getattr(kb, "search_recommendation", "continue_to_c"),
        kb_data=kb_data,
        all_candidates=getattr(kb, "all_candidates", []),
        suggested_next="ask_user",
    )


def continue_full_search(
    stage1_result: KbFirstSearchResult,
    group: str = "full",
    limit: int = 10,
) -> KbFirstSearchResult:
    """Stage 2: Continue to full search with c项目, enriched by KB data.

    Takes the Stage 1 result (kb_check), enriches the search with KB-known
    synonyms/aliases/variants, and runs search() from search_coordinator.

    Args:
        stage1_result: Result from kb_first() Stage 1.
        group: Engine group ("quick"/"standard"/"full").
        limit: Max results per engine.

    Returns:
        KbFirstSearchResult with stage="full_search" and populated full_search.
    """
    # Build enriched species name: prefer KB scientific name
    kb = stage1_result.kb_data
    search_name = kb.get("scientific_name", "") or stage1_result.species_name

    # Run full coordinated search
    full = search(
        species_name=search_name,
        group=group,
        limit=limit,
    )

    stage1_result.stage = "full_search"
    stage1_result.full_search = full
    stage1_result.suggested_next = "done"

    return stage1_result

# ═══════════════════════════════════════════════════════
# Graph Traversal + Write-back helpers
# ═══════════════════════════════════════════════════════

def _load_species_graph() -> List[Dict[str, Any]]:
    """Load species graph from YAML."""
    try:
        import yaml
        path = Path(__file__).resolve().parent.parent / "config" / "species_graph.yaml"
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data.get("graph", {}).get("species", [])
    except Exception as e:
        logger.debug(f"Can't load species graph: {e}")
    return []


def _write_back_to_fish_kb(result: KbFirstSearchResult) -> bool:
    """Write search results back to fish-ecology-assistant knowledge base.

    This implements the V(cognitive)->S(fish) feedback loop:
      - New papers found by C project -> append to fish KB
      - Topology info (related species, family) -> update species graph

    Args:
        result: Completed KbFirstSearchResult with full_search populated.

    Returns:
        True if write succeeded, False otherwise.
    """
    if not result.full_search or not result.full_search.papers:
        return False

    try:
        new_papers = result.full_search
        species_name = result.species_name

        # Path to fish KB species file
        fish_kb_dir = Path(__file__).resolve().parent.parent.parent /             "fish-ecology-assistant" / "data" / "knowledge_base" / "species"
        fish_kb_dir.mkdir(parents=True, exist_ok=True)
        
        kb_file = fish_kb_dir / f"{species_name.replace(chr(32), "_").lower()}.md"

        if not kb_file.is_file():
            # Create new KB entry
            content = [
                f"# {species_name} — 物种知识库",
                f"",
                f"## 基本信息",
                f"- 物种: {species_name}",
                f"- 来源: 认知搜索引擎 v5.8 全量搜索",
                f"- 搜索时间: {time.strftime('%Y-%m-%d %H:%M')}",
                f"- 引擎组: full (15引擎)",
                f"",
                f"## 文献列表 ({len(new_papers.papers)} 篇)",
            ]
            for i, p in enumerate(new_papers.papers[:50], 1):
                title = p.get("title", "").strip()
                if title:
                    doi = p.get("doi", "")
                    doi_str = f" DOI:{doi}" if doi else ""
                    authors = p.get("authors", [])
                    author_str = f", {chr(44).join(authors[:3])}" if authors else ""
                    year = p.get("year", "")
                    journal = p.get("journal", "")
                    content.append(f"  {i}. {title}{author_str} ({year}) {journal}{doi_str}")
            content.append("")
            content.append("## 图谱拓扑")
            content.append("- 同科近缘种: 见 species_graph.yaml")
            kb_file.write_text(chr(10).join(content), encoding="utf-8")
        else:
            # Append new papers to existing KB
            existing = kb_file.read_text(encoding="utf-8")
            new_lines = []
            for p in new_papers.papers[:30]:
                title = p.get("title", "").strip()
                if title and title not in existing:
                    doi = p.get("doi", "")
                    doi_str = f" DOI:{doi}" if doi else ""
                    new_lines.append(f"  - {title}{doi_str}")
            if new_lines:
                with open(kb_file, "a", encoding="utf-8") as f:
                    f.write(chr(10).join(["", "## 认知引擎补充文献", *new_lines, ""]))

        logger.info(f"Written {len(new_papers.papers)} papers to fish KB: {kb_file}")
        return True
    except Exception as e:
        logger.error(f"Write-back to fish KB failed: {e}")
        return False