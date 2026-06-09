"""
统一物种搜索 — 自适应模式 + 附带过滤 + CN/EN双通道 + 分类学变更检查

工程语言化所有搜索规则:
  1. estimate_literature_volume() → 自适应模式决策
  2. check_taxonomy() → 分类学变更检查 (⚠️ 防止属名变更遗漏)
  3. is_incidental() → 附带论文判定
  4. classify_paper() → 学科分类
  5. cn_en_label() → CN/EN通道标注

用法:
  from src.unified_search import estimate_mode, check_taxonomy
  mode = estimate_mode("Ochetobius elongatus", "CR", 16)
  variants = check_taxonomy("Tribolodon hakonensis")
  # → ["Tribolodon hakonensis", "Pseudaspius hakonensis", "Leuciscus hakonensis"]

⚠️ 教训: 2026.3 徐子悦论文因只用 Tribolodon 搜索遗漏了 Pseudaspius 属名
   现在 check_taxonomy() 强制检查 species_graph.yaml 的 variants 字段
"""

from __future__ import annotations
import os

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════════════════

class SearchMode(str, Enum):
    EXHAUSTIVE = "exhaustive"          # 穷举: 精确+宽网+变体+引用+附带
    CLASSIFIED = "classified"           # 分类: 专题全量, 附带过滤
    REVIEW_ANCHORED = "review_anchored" # 综述锚定: 先搜综述, 精选5-8篇
    SATURATED = "saturated"             # 饱和: 附带=噪音, 全部过滤


class Conservation(str, Enum):
    CR = "CR"  # 极危
    EN = "EN"  # 濒危
    VU = "VU"  # 易危
    NT = "NT"  # 近危
    LC = "LC"  # 无危


class PaperCategory(str, Enum):
    GENETICS = "🧬 遗传与分子"
    GENOMICS = "🧪 基因组学"
    MORPHOLOGY = "📐 形态与表型"
    DIET_PHYSIOLOGY = "🍽️ 食性与生理"
    ECOLOGY = "🌊 生态与资源"
    CONSERVATION = "📢 保护政策"
    TOXICOLOGY = "☣️ 毒理与环境"
    AQUACULTURE = "🐟 养殖与繁育"
    LOW_CREDIBILITY = "⚠️ 低可信度/变体"


@dataclass
class SearchDecision:
    mode: SearchMode
    include_incidental: bool
    max_papers: int
    reason: str


# ═══════════════════════════════════════════════════════
# §1 自适应模式决策
# ═══════════════════════════════════════════════════════

def estimate_mode(
    species_name: str,
    conservation: str,
    estimated_volume: int,
) -> SearchDecision:
    """
    estimate_mode(species, conservation, volume) → SearchDecision

    决策矩阵:
      CR + <20篇    → EXHAUSTIVE      (附带=珍贵, 全部保留)
      EN/VU + <50   → EXHAUSTIVE      (附带仅列不展开)
      20-100篇      → CLASSIFIED      (附带标注过滤)
      >100篇        → REVIEW_ANCHORED (附带=噪音, 全部跳过)

    热门物种 (鲤/鲫/草鱼等 LC且>500):
      → SATURATED (附带=噪音, 全部过滤)
    """

    # 热门物种: 附带 = 噪音
    HOT_SPECIES = {
        "cyprinus carpio", "carassius auratus", "ctenopharyngodon idella",
        "hypophthalmichthys molitrix", "aristichthys nobilis",
        "mylopharyngodon piceus", "parabramis pekinensis",
        # 中文别名
        "鲤鱼", "鲫鱼", "草鱼", "鲢鱼", "鳙鱼", "青鱼", "鳊鱼",
        "鲤", "鲫", "草", "鲢", "鳙", "青", "鳊",
    }
    name_lower = species_name.lower()
    if (name_lower in HOT_SPECIES or
        any(hot in name_lower for hot in ["cyprinus carpio", "鲤鱼", "鲤"])) \
        and estimated_volume > 500:
        return SearchDecision(
            mode=SearchMode.SATURATED,
            include_incidental=False,
            max_papers=30,
            reason="热门物种: 附带论文=噪音, 全部过滤",
        )

    # CR: 每条记录珍贵
    if conservation in ("CR",) and estimated_volume < 20:
        return SearchDecision(
            mode=SearchMode.EXHAUSTIVE,
            include_incidental=True,
            max_papers=100,
            reason=f"CR+{estimated_volume}篇: 穷举模式, 附带全部保留",
        )

    # EN/VU: 附带仅列不展开
    if conservation in ("EN", "VU") and estimated_volume < 50:
        return SearchDecision(
            mode=SearchMode.EXHAUSTIVE,
            include_incidental=True,
            max_papers=50,
            reason=f"{conservation}+{estimated_volume}篇: 穷举, 附带仅列",
        )

    # 中等文献量
    if 20 <= estimated_volume <= 100:
        return SearchDecision(
            mode=SearchMode.CLASSIFIED,
            include_incidental=False,
            max_papers=40,
            reason=f"{estimated_volume}篇: 分类模式, 附带过滤",
        )

    # 大量文献
    return SearchDecision(
        mode=SearchMode.REVIEW_ANCHORED,
        include_incidental=False,
        max_papers=30,
        reason=f"{estimated_volume}篇: 综述锚定, 附带全部跳过",
    )


# ═══════════════════════════════════════════════════════
# §2 附带论文判定
# ═══════════════════════════════════════════════════════

# 核心研究关键词: 论文主题=该物种本身
_CORE_KEYWORDS = [
    "genetic", "genome", "chromosome", "mitochondrial", "SNP", "microsatellite",
    "morpholog", "phenotypic", "geometric morphometric",
    "diet", "feeding", "digestive", "gut content", "intestinal",
    "population", "demographic", "diversity", "community",
    "conservation", "endangered", "protected", "fishing ban",
    "migration", "spawning", "habitat", "otolith",
    "transcriptome", "assembly", "sequencing",
]

# 附带标记关键词: 该物种仅作为实验材料出现
_INCIDENTAL_KEYWORDS = [
    "protein hydrolysate", "enzymatic hydrolysis", "papain",
    "collagen", "chondroitin", "gelatin",
    "blood biochemistry", "serum", "hematolog",
    "stocking density", "growth performance", "feed",
    "fatty acid", "amino acid", "nutritional",
    "heavy metal", "pollutant", "contamination",
]


def is_incidental(paper: Dict[str, Any]) -> Tuple[bool, str]:
    """
    is_incidental(paper) → (is_incidental: bool, reason: str)

    判定逻辑:
      1. 论文标题/摘要是否以该物种本身为研究对象?
      2. 该物种是否仅作为实验材料/商业原料出现?
      3. 该物种是否仅在调查名录中被提及?

    不是附带 (专题):
      - 论文直接研究该物种的生物学/保护/威胁
      - 该物种是主要研究对象

    是附带:
      - 该物种仅作为实验材料 (如"用中华鲟蛋白做水解实验")
      - 该物种仅作为商业原料 (如"中华鲟软骨提取物")
      - 该物种仅出现在调查名录中 (如"本次调查发现120种鱼类, 包括...")
    """
    title = (paper.get("title") or "").lower()
    abstract = (paper.get("abstract") or "").lower()

    # 检查核心关键词: 如果标题含核心词 → 专题
    for kw in _CORE_KEYWORDS:
        if kw in title:
            return False, f"核心研究: 标题含 '{kw}'"

    # 检查附带关键词: 如果标题含附带词 → 附带
    for kw in _INCIDENTAL_KEYWORDS:
        if kw in title:
            return True, f"附带: 标题含 '{kw}' (实验材料/商业原料)"

    # 标题太短 → 可能是调查名录中的附带记录
    if len(title) < 30:
        return True, "附带: 标题过短, 可能为调查名录记录"

    # 默认: 如果标题明确包含物种学名 → 专题
    species_in_title = paper.get("species_in_title", False)
    if species_in_title:
        return False, "专题: 标题含物种学名"

    return False, "默认: 专题"


# ═══════════════════════════════════════════════════════
# §3 学科分类
# ═══════════════════════════════════════════════════════

_CATEGORY_RULES = [
    (PaperCategory.GENETICS, [
        "genetic diversity", "population genetic", "microsatellite", "SNP",
        "mitochondrial dna", "mtdna", "haplotype", "phylogen", "phylogeograph",
        "molecular marker", "RAD-seq", "GBS", "genotyping",
    ]),
    (PaperCategory.GENOMICS, [
        "genome assembly", "chromosome-level", "whole genome", "sequencing",
        "transcriptome", "annotation", "BUSCO", "pseudochromosome",
    ]),
    (PaperCategory.MORPHOLOGY, [
        "morpholog", "geometric morphometric", "phenotyp", "landmark",
        "body shape", "meristic", "osteolog",
    ]),
    (PaperCategory.DIET_PHYSIOLOGY, [
        "diet", "feeding", "digestive", "gut content", "intestinal",
        "stomach", "food habit", "trophic", "prey",
    ]),
    (PaperCategory.ECOLOGY, [
        "population dynamic", "abundance", "distribution", "community",
        "diversity survey", "fish resource", "CPUE", "catch",
        "habitat", "migration", "spawning ground",
    ]),
    (PaperCategory.CONSERVATION, [
        "conservation", "endangered", "protected", "fishing ban",
        "recovery", "restoration", "management", "red list",
        "biodiversity decline", "IUCN",
    ]),
    (PaperCategory.TOXICOLOGY, [
        "toxic", "pollution", "contaminant", "heavy metal",
        "TPT", "PFC", "PFAS", "pesticide", "endocrine",
        "malformation", "deformity",
    ]),
    (PaperCategory.AQUACULTURE, [
        "aquaculture", "hatchery", "stocking", "larval",
        "juvenile growth", "feed", "nutrition", "disease",
        "immune", "stress response",
    ]),
]


def classify_paper(paper: Dict[str, Any]) -> PaperCategory:
    """
    classify_paper(paper) → PaperCategory

    根据标题+摘要的关键词匹配, 将论文分入最匹配的学科分类。
    匹配第一个命中的分类。
    """
    title = (paper.get("title") or "").lower()
    abstract = (paper.get("abstract") or "").lower()
    text = title + " " + abstract

    for category, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return category

    # 默认: 生态与资源
    return PaperCategory.ECOLOGY


# ═══════════════════════════════════════════════════════
# §4 CN/EN 通道标注
# ═══════════════════════════════════════════════════════

# 中文期刊列表 (期刊名 → 可信度加分)
_CHINESE_JOURNALS: Dict[str, int] = {
    "水生生物学报": 25,
    "acta hydrobiologica sinica": 25,
    "生物多样性": 25,
    "biodiversity science": 25,
    "中国水产科学": 25,
    "journal of fishery sciences of china": 25,
    "水产学报": 25,
    "journal of fisheries of china": 25,
    "湖泊科学": 25,
    "journal of lake sciences": 25,
    "南方水产科学": 25,
    "south china fisheries science": 25,
    "生态学报": 25,
    "acta ecologica sinica": 25,
    "生态科学": 20,
    "ecological science": 20,
    "动物学报": 20,
    "acta zoologica sinica": 20,
    "江西科学": 10,
}

# 英文期刊 (SCI收录)
_SCI_JOURNALS = {
    "animals", "scientific data", "scientific reports", "gene",
    "conservation genetics resources", "mitochondrial dna",
    "plos one", "pnas", "environmental science", "science",
    "nature", "fish physiology", "comparative biochemistry",
    "theriogenology", "environmental biology of fishes",
    "journal of fish biology", "national science review",
}


def cn_en_label(paper: Dict[str, Any]) -> Tuple[str, int]:
    """
    cn_en_label(paper) → (channel: "CN"|"EN", credibility_bonus: int)

    规则:
      CN通道: 期刊在中文期刊列表中 → 中文署名, credibility +25
      EN通道: 期刊在SCI列表中 → 英文署名, credibility +30
      其他:    可信度基线 = 50
    """
    venue = (paper.get("venue") or paper.get("journal") or "").lower().strip()

    # 检查中文期刊
    for cn_name, bonus in _CHINESE_JOURNALS.items():
        if cn_name in venue:
            return "CN", bonus

    # 检查英文SCI期刊
    for sci_name in _SCI_JOURNALS:
        if sci_name in venue:
            return "EN", 30

    # 默认
    return "EN", 10


# ═══════════════════════════════════════════════════════
# §5 多引擎搜索协调
# ═══════════════════════════════════════════════════════

@dataclass
class SearchStep:
    name: str
    engines: List[str]
    queries: List[str]
    limit: int
    optional: bool = False


def build_search_plan(
    species_name: str,
    chinese_name: str,
    variants: List[str],
    decision: SearchDecision,
) -> List[SearchStep]:
    """
    build_search_plan(species, cn_name, variants, decision) → [SearchStep]

    根据搜索模式生成多步骤搜索计划。
    """
    steps = []

    # Step 1: 精确名搜索 (必须)
    steps.append(SearchStep(
        name="精确名搜索",
        engines=["scholar", "ncbi", "web_search"],
        queries=[species_name, chinese_name],
        limit=15 if decision.mode == SearchMode.EXHAUSTIVE else 10,
    ))

    # Step 2: 宽网搜索 (穷举/分类模式)
    if decision.mode in (SearchMode.EXHAUSTIVE, SearchMode.CLASSIFIED):
        steps.append(SearchStep(
            name="宽网补漏",
            engines=["web_search", "scholar"],
            queries=[
                f"{species_name} conservation fishing ban recovery 2024 2025 2026",
                f"{chinese_name} 保护 禁渔 恢复 2024 2025",
            ],
            limit=5,
            optional=False,
        ))

    # Step 3: OCR变体 (所有模式)
    if variants:
        steps.append(SearchStep(
            name="OCR变体安全网",
            engines=["scholar"],
            queries=variants[:5],
            limit=3,
            optional=False,
        ))

    # Step 4: 附带论文搜索 (仅穷举模式)
    if decision.include_incidental:
        steps.append(SearchStep(
            name="附带论文",
            engines=["scholar", "web_search"],
            queries=[
                f"{species_name} survey diversity community",
                f"{chinese_name} 鱼类调查 资源调查 物种名录",
            ],
            limit=10,
            optional=True,
        ))

    # Step 5: 综述搜索 (综述锚定模式)
    if decision.mode == SearchMode.REVIEW_ANCHORED:
        steps.insert(1, SearchStep(
            name="综述优先",
            engines=["scholar"],
            queries=[f"{species_name} review"],
            limit=5,
            optional=False,
        ))

    return steps


# ═══════════════════════════════════════════════════════
# §6 全量搜索引擎注册表 + 流式并行搜索
# ═══════════════════════════════════════════════════════

# 可用搜索引擎全量清单 (按优先级) — v5.6 扩展
ENGINE_REGISTRY = {
    # 学术搜索 (Priority 1-3)
    "scholar_graph":    {"tool": "scholar_search_literature_graph", "category": "academic", "priority": 1},
    "scholar_keywords": {"tool": "scholar_search_google_scholar_key_words", "category": "academic", "priority": 1},
    "scholar_advanced": {"tool": "scholar_search_google_scholar_advanced", "category": "academic", "priority": 2},
    "ncbi_esearch":     {"tool": "ncbi_ncbi_esearch", "category": "academic", "priority": 1},
    "europe_pmc":       {"tool": "europe_pmc_search", "category": "academic", "priority": 1},  # v5.6: NCBI 500→Europe PMC failover
    "crossref_article": {"tool": "article_search_literature", "category": "academic", "priority": 2},
    "scholarly_multi":  {"tool": "scholarly_research_search", "category": "academic", "priority": 3},
    # 中文搜索 (Priority 1.5 — 中文物种优先) ⭐ v5.6 新增
    "baidu_scholar":    {"tool": "baidu_scholar", "category": "chinese_academic", "priority": 1},
    "cnki_web":         {"tool": "cnki_web", "category": "chinese_academic", "priority": 1},
    "wanfang_web":      {"tool": "wanfang_web", "category": "chinese_academic", "priority": 2},
    "cas_web":          {"tool": "cas_web", "category": "chinese_academic", "priority": 2},
    "chinese_sweep":    {"tool": "chinese_search", "category": "chinese_academic", "priority": 3},
    "duckduckgo_search": {"tool": "duckduckgo_search", "category": "chinese_academic", "priority": 2},
    # 语义/深度搜索 (Priority 4-5)
    "tavily_search":    {"tool": "tavily_tavily_search", "category": "semantic", "priority": 4},
    "tavily_research":  {"tool": "tavily_tavily_research", "category": "semantic", "priority": 5},
    "exa_search":       {"tool": "exa_web_search_exa", "category": "semantic", "priority": 4},
    # 预印本 (Priority 3.5) ⭐ v5.6 新增
    "biorxiv_api":      {"tool": "biorxiv_search", "category": "preprint", "priority": 3},
    "researchgate_web": {"tool": "researchgate_web", "category": "preprint", "priority": 3},
    # 内置搜索 (Priority 6)
    "web_search":       {"tool": "web_search", "category": "web", "priority": 6},
    # 引用/关系 (Priority 7)
    "references":       {"tool": "article_get_references", "category": "graph", "priority": 7},
    "relations":        {"tool": "article_get_literature_relations", "category": "graph", "priority": 7},
}

# 默认搜索引擎组 (按场景) — v5.6 扩组
ENGINE_GROUPS = {
    # 快速验证 (3引擎, ~10s)
    "quick":    ["scholar_graph", "ncbi_esearch", "web_search"],
    # 标准搜索 (5引擎, ~20s)
    "standard": ["scholar_graph", "ncbi_esearch", "crossref_article", "web_search", "tavily_search"],
    # 全量搜索 (9引擎, ~40s) ⭐ v5.6: +中文+预印本
    "full":     ["scholar_graph", "ncbi_esearch", "crossref_article", "scholarly_multi",
                 "baidu_scholar", "tavily_search", "exa_search", "biorxiv_api", "web_search"],
    # 中文优先 (7引擎, ~25s) ⭐ v5.6: 中文数据库全覆盖
    "chinese":  ["baidu_scholar", "cnki_web", "wanfang_web", "cas_web",
                 "scholar_graph", "ncbi_esearch", "chinese_sweep"],
    # 预印本速递 (3引擎, ~15s) ⭐ v5.6 新增
    "preprint": ["biorxiv_api", "researchgate_web", "scholar_graph"],
}


@dataclass
class EngineResult:
    engine: str
    query: str
    tool: str = ""
    status: str = "pending"
    results: List[Dict] = field(default_factory=list)
    error: str = ""
    retries: int = 0
    elapsed_ms: float = 0.0


@dataclass
class StreamEvent:
    """流式结果 — 引擎完成后立即输出"""
    engine: str
    status: str
    paper_count: int
    elapsed_ms: float
    is_last: bool = False


def search_streaming(
    queries: List[str],
    engines: List[str] = None,
    group: str = "standard",
    limit: int = 10,
    max_retries: int = 3,
    per_engine_timeout_s: float = 30.0,
    on_result: callable = None,  # 回调: (StreamEvent) → None
) -> List[EngineResult]:
    """
    search_streaming(queries, group="standard") → [EngineResult]

    v5.6 双路径架构: 每个引擎 MCP → HTTP 自动降级。
    - MCP 可用 → 优先 MCP 调用 (Tavily/Exa/Scholar/Article/Scholarly/NCBI)
    - MCP 不可用/失败 → 自动 HTTP fallback (Europe PMC/Crossref/OpenAlex/Bing/Chinese native)
    - 中文/预印本原生引擎 → 始终走 HTTP (零 MCP 开销)
    
    流式并行: 先完成的引擎先返回 on_result(event)。
    支持预定义引擎组: quick/standard/full/chinese/preprint
    """
    import concurrent.futures
    import time

    if engines is None:
        engines = ENGINE_GROUPS.get(group, ENGINE_GROUPS["standard"])

    results: List[EngineResult] = []

    # ── Detect MCP availability ──
    _mcp_ok = _mcp_available()
    if not _mcp_ok:
        _mcp_start = time.monotonic()
        while time.monotonic() - _mcp_start < 2.0:
            time.sleep(0.5)
            if _mcp_available():
                _mcp_ok = True
                break

    # ── Lazy-load HTTP fallback registry ──
    try:
        from src.parallel_search import MCP_HTTP_FALLBACK as _hfb
    except ImportError:
        _hfb = {}

    # ── Native HTTP engines (always HTTP, never MCP) ──
    _NATIVE_HTTP_TOOLS = {
        "baidu_scholar", "cnki_web", "wanfang_web", "cas_web",
        "chinese_search", "chinese_sweep",
        "biorxiv_search", "researchgate_web", "europe_pmc_search",
        "web_search",
    }

    def _search_one_dual(engine_id: str, query: str) -> EngineResult:
        """Per-engine dual-path: MCP first → HTTP fallback."""
        t0 = time.perf_counter()
        info = ENGINE_REGISTRY.get(engine_id, {"tool": engine_id, "category": "unknown", "priority": 9})
        tool = info.get("tool", engine_id)
        result = EngineResult(engine=engine_id, query=query, tool=tool)

        # ── Determine path ──
        is_native_http = tool in _NATIVE_HTTP_TOOLS
        http_fn = _hfb.get(tool) if _hfb else None

        # ── Path A: Native HTTP engines → straight to HTTP ──
        if is_native_http:
            if http_fn:
                try:
                    result.results = http_fn(query, limit)
                    result.status = "ok"
                except Exception as e:
                    result.status = "error"
                    result.error = str(e)[:200]
            else:
                result.status = "degraded"
                result.error = f"{tool}: native HTTP provider not found"
            result.elapsed_ms = (time.perf_counter() - t0) * 1000
            return result

        # ── Path B: MCP-capable engines → try MCP first ──
        if _mcp_ok:
            for attempt in range(max_retries):
                try:
                    result.results = _call_mcp_tool(tool, query, limit)
                    result.status = "ok"
                    result.elapsed_ms = (time.perf_counter() - t0) * 1000
                    return result
                except ImportError:
                    # MCP tool not injected → fall through to HTTP
                    break
                except Exception as e:
                    result.retries = attempt + 1
                    if attempt < max_retries - 1:
                        wait = min(1.0 * (2 ** attempt), 8)
                        time.sleep(wait)
                        continue
                    # MCP exhausted → fall through to HTTP
                    break

        # ── Path C: HTTP fallback (MCP not available or exhausted) ──
        if http_fn:
            try:
                result.results = http_fn(query, limit)
                result.status = "ok(fallback)"
                result.tool = f"{tool}→HTTP"
            except Exception as e:
                result.status = "error"
                result.error = str(e)[:200]
        else:
            if not _mcp_ok:
                result.status = "degraded"
                result.error = f"{tool}: MCP unavailable + no HTTP fallback"
            else:
                result.status = "error"
                result.error = f"{tool}: MCP failed + no HTTP fallback"

        result.elapsed_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── Parallel fan-out: all engines × all queries ──
    total = len(engines) * len(queries)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 12)) as ex:
        futures = {}
        for engine_id in engines:
            for query in queries:
                future = ex.submit(_search_one_dual, engine_id, query)
                futures[future] = (engine_id, query)

        for future in concurrent.futures.as_completed(futures):
            engine_id, query = futures[future]
            try:
                result = future.result(timeout=per_engine_timeout_s)
                results.append(result)
                completed += 1
                if on_result:
                    on_result(StreamEvent(
                        engine=result.engine,
                        status=result.status,
                        paper_count=len(result.results),
                        elapsed_ms=result.elapsed_ms,
                        is_last=(completed == total),
                    ))
            except concurrent.futures.TimeoutError:
                results.append(EngineResult(
                    engine=engine_id, query=query,
                    status="error", error=f"timeout ({per_engine_timeout_s}s)"
                ))
                completed += 1

    return results, []  # v5.6: _http_fallback deprecated — each engine handles its own fallback


def _mcp_available() -> bool:
    """Check if MCP tools are injected (Reasonix runtime)."""
    return callable(globals().get("scholar_search_literature_graph"))


def _call_mcp_tool(tool_name: str, query: str, limit: int) -> List[Dict]:
    """
    _call_mcp_tool(tool_name, query, limit) → [papers]

    调用实际的 MCP 搜索工具。在 Reasonix 运行时中可直接调用。

    工具在 Reasonix 中作为 Python callable 注入，不通过标准 import 路径。
    因此使用 globals().get() 或 try/except 尝试调用。

    如果工具不可用 (MCP未运行), 触发 degraded。
    """
    import types

    # 每个工具的函数签名定义
    # 在 Reasonix 中，这些函数直接从全局作用域可用
    _tool_map = {
        "scholar_search_literature_graph": {
            "fn_name": "scholar_search_literature_graph",
            "call": lambda fn: fn(query=query, limit=limit),
        },
        "scholar_search_google_scholar_key_words": {
            "fn_name": "scholar_search_google_scholar_key_words",
            "call": lambda fn: fn(query=query, num_results=min(limit, 20)),
        },
        "ncbi_ncbi_esearch": {
            "fn_name": "ncbi_ncbi_esearch",
            "call": lambda fn: fn(query=query, maxResults=min(limit, 100)),
        },
        "article_search_literature": {
            "fn_name": "article_search_literature",
            "call": lambda fn: fn(keyword=query, max_results=limit),
        },
        "scholarly_research_search": {
            "fn_name": "scholarly_research_search",
            "call": lambda fn: fn(query=query, maxResults=limit),
        },
        "tavily_tavily_search": {
            "fn_name": "tavily_tavily_search",
            "call": lambda fn: fn(query=query, max_results=min(limit, 20)),
        },
        "exa_web_search_exa": {
            "fn_name": "exa_web_search_exa",
            "call": lambda fn: fn(query=query, numResults=min(limit, 20)),
        },
        "web_search": {
            "fn_name": "web_search",
            "call": lambda fn: fn(query=query, topK=min(limit, 10)),
        },
        "article_get_references": {
            "fn_name": "article_get_references",
            "call": lambda fn: fn(identifier=query, id_type="auto", max_results=limit),
        },
        "article_get_literature_relations": {
            "fn_name": "article_get_literature_relations",
            "call": lambda fn: fn(identifiers=[query], relation_types=["similar"], max_results=limit),
        },
    }

    if tool_name not in _tool_map:
        raise ImportError(f"{tool_name}: unknown tool")

    info = _tool_map[tool_name]
    fn_name = info["fn_name"]

    # 尝试从全局作用域获取函数 (Reasonix 注入的 MCP 工具)
    fn = globals().get(fn_name)

    # 如果 globals 中没有, 尝试从 __builtins__ 获取
    if fn is None:
        try:
            fn = __builtins__.get(fn_name) if isinstance(__builtins__, dict) else getattr(__builtins__, fn_name, None)
        except (AttributeError, KeyError):
            fn = None

    # 如果仍然没有, 尝试导入 (某些 MCP 工具可能可 import)
    if fn is None:
        try:
            import importlib
            mod = importlib.import_module(fn_name)
            fn = mod if callable(mod) else None
        except (ImportError, ModuleNotFoundError):
            fn = None

    if fn is None:
        # HTTP fallback: try parallel_search.MCP_HTTP_FALLBACK
        try:
            from src.parallel_search import MCP_HTTP_FALLBACK as _hfb
            if tool_name in _hfb:
                return _hfb[tool_name](query, limit)
        except Exception:
            pass
        raise ImportError(f"{tool_name}({fn_name}): MCP tool not available")

    # 调用工具
    try:
        result = info["call"](fn)
        # 标准化输出
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("results", result.get("papers", [result]))
        else:
            return [result]
    except Exception as e:
        raise ImportError(f"{tool_name}: call failed: {e}")


def aggregate_results(engine_results: List[EngineResult], http_fb: List = None) -> Dict:
    """
    aggregate_results([EngineResult]) → {papers, stats, timeline}

    合并所有引擎的结果, DOI去重, 保留时间线。
    """
    all_papers = []
    timeline = []
    stats = {"total_queries": len(engine_results), "ok": 0, "degraded": 0, "error": 0}

    for r in engine_results:
        stats[r.status] = stats.get(r.status, 0) + 1

        for paper in r.results:
            paper["_source_engine"] = r.engine
            all_papers.append(paper)

        timeline.append({
            "engine": r.engine,
            "query": r.query[:60],
            "status": r.status,
            "papers": len(r.results),
            "ms": r.elapsed_ms,
        })

    # DOI去重
    seen_doi = set()
    merged = []
    for p in all_papers:
        doi = (p.get("doi") or "").lower().strip()
        if doi and doi in seen_doi:
            continue
        if doi:
            seen_doi.add(doi)
        merged.append(p)

    stats["total_raw"] = len(all_papers)
    stats["total_merged"] = len(merged)
    stats["duplicates_removed"] = len(all_papers) - len(merged)

    return {"papers": merged, "stats": stats, "timeline": timeline}


@dataclass
class SearchReport:
    species: str
    conservation: str
    mode: SearchMode
    total: int
    incidental_count: int
    incidental_skipped: int
    categories: Dict[str, List[Dict]]
    variants_used: List[str]


# ═══════════════════════════════════════════════════════
# §6b 引用回溯 — 对高可信度论文展开引用链 (Step 3)
# ═══════════════════════════════════════════════════════

def citation_traversal(
    papers: List[Dict],
    species_name: str,
    max_per_paper: int = 10,
    max_total_calls: int = 20,
    min_credibility: int = 60,
) -> List[Dict]:
    """
    citation_traversal(papers, species_name) → [new_papers]

    对已搜索到的高可信度论文展开引用链，提取目标物种相关论文。

    逻辑:
      1. 过滤: 仅处理 credibility ≥ min_credibility 且有 DOI 的论文
      2. 遍历: 调用 article_get_references 获取每篇论文的参考文献
      3. 筛选: 只保留标题或摘要中包含目标物种名的论文
      4. 去重: 排除已在 papers 中的 DOI

    Args:
        papers: 已完成搜索的论文列表
        species_name: 目标物种学名 (如 "Tribolodon hakonensis")
        max_per_paper: 每篇论文最多获取的参考文献数
        max_total_calls: 最多发起的引用检索调用数
        min_credibility: 触发引用回溯的最小可信度阈值

    Returns:
        新发现的论文列表 (不含已在 papers 中的论文)
    """
    import re
    import time
    from urllib.request import urlopen, Request
    from urllib.parse import quote
    import json

    existing_dois = {
        p.get("doi", "").lower().strip()
        for p in papers if p.get("doi")
    }
    existing_titles = {
        (p.get("title", "") or "").lower().strip()[:80]
        for p in papers
    }

    # 提取物种核心名: Tribolodon hakonensis → 属名+种名
    name_lower = species_name.lower().strip()
    genus = name_lower.split()[0] if " " in name_lower else name_lower

    new_papers: List[Dict] = []
    calls_made = 0

    # 筛选候选论文: 有DOI + 可信度达标
    candidates = [
        p for p in papers
        if p.get("doi") and calls_made < max_total_calls
    ]

    for paper in candidates:
        if calls_made >= max_total_calls:
            break

        doi = paper.get("doi", "").strip()
        if not doi:
            continue

        calls_made += 1

        # 尝试用 MCP article_get_references 获取引用
        refs = _fetch_references_mcp(doi, max_per_paper)

        # MCP 不可用 → HTTP fallback via OpenAlex
        if refs is None:
            refs = _fetch_references_http(doi, max_per_paper)

        if not refs:
            continue

        for ref in refs:
            # 检查是否目标物种论文
            ref_title = (ref.get("title") or "").lower().strip()
            if not ref_title:
                continue

            # 物种名匹配: 属名 或 学名全称 在标题中
            is_about_species = (
                name_lower in ref_title or
                genus in ref_title
            )
            if not is_about_species:
                continue

            # 去重: DOI
            ref_doi = (ref.get("doi") or "").lower().strip()
            if ref_doi and ref_doi in existing_dois:
                continue

            # 去重: 标题
            ref_title_key = ref_title[:80]
            if ref_title_key in existing_titles:
                continue

            # 标记来源
            ref["_source"] = "citation_traversal"
            ref["_source_paper"] = paper.get("title", "")
            ref["_source_doi"] = doi
            ref["_citation_depth"] = 1

            # 添加到新论文
            new_papers.append(ref)
            if ref_doi:
                existing_dois.add(ref_doi)
            existing_titles.add(ref_title_key)

    return new_papers


def _fetch_references_mcp(doi: str, max_results: int) -> Optional[List[Dict]]:
    """通过 MCP article_get_references 获取参考文献。

    Returns:
        List[Dict] 成功时; None 如果 MCP 不可用
    """
    try:
        return _call_mcp_tool(
            "article_get_references",
            doi,
            max_results,
        )
    except (ImportError, Exception):
        return None


def _fetch_references_http(doi: str, max_results: int) -> List[Dict]:
    """HTTP fallback: 通过 OpenAlex API 获取参考文献。"""
    try:
        import json
        from urllib.request import urlopen, Request
        from urllib.parse import quote

        # OpenAlex: 获取论文的 referenced_works
        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        url = f"https://api.openalex.org/works/doi:{quote(doi_clean)}?select=referenced_works"
        req = Request(url, headers={"User-Agent": "Reasonix/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        ref_work_ids = data.get("referenced_works", [])[:max_results]
        if not ref_work_ids:
            return []

        # 批量获取引用论文的元数据
        papers = []
        for wid in ref_work_ids:
            try:
                wurl = f"https://api.openalex.org/works/{wid}"
                with urlopen(Request(wurl, headers={"User-Agent": "Reasonix/1.0"}), timeout=10) as wresp:
                    wdata = json.loads(wresp.read())
                doi_val = (wdata.get("doi") or "").replace("https://doi.org/", "")
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in wdata.get("authorships", [])
                ]
                papers.append({
                    "doi": doi_val,
                    "title": wdata.get("title", ""),
                    "year": wdata.get("publication_year"),
                    "journal": (wdata.get("primary_location") or {})
                               .get("source", {}).get("display_name", ""),
                    "authors": authors,
                    "_source_api": "openalex_references",
                })
            except Exception:
                continue
        return papers
    except Exception:
        return []


# ═══════════════════════════════════════════════════════
# §6c 变体安全网 — OCR 变体搜索补漏 (Step 4)
# ═══════════════════════════════════════════════════════

def variant_safety_net(
    scientific_name: str,
    existing_papers: List[Dict],
    max_variants: int = 5,
    max_per_variant: int = 5,
) -> List[Dict]:
    """
    variant_safety_net(scientific_name, existing_papers) → [new_papers]

    自动生成 OCR 拼写变体并对每个变体执行轻量搜索，填补
    因出版物中物种名拼写错误导致的搜索遗漏。

    逻辑:
      1. 调用 variant_generator.generate_variants() 生成变体
      2. 排除已在检查 taxonomy 时覆盖的变体
      3. 对每个变体执行轻量搜索 (max_results=5)
      4. 与已有论文去重后返回新发现的论文

    Args:
        scientific_name: 规范学名 (如 "Tribolodon hakonensis")
        existing_papers: 已搜索到的论文列表 (用于去重)
        max_variants: 最多尝试的变体数
        max_per_variant: 每个变体最多返回的结果数

    Returns:
        新发现的论文列表
    """
    import time

    # Step 1: 生成 OCR 变体
    parts = scientific_name.strip().split()
    if len(parts) < 2:
        return []

    genus, species = parts[0], parts[1]

    try:
        from src.variant_generator import generate_variants
        variants = generate_variants(genus, species, max_variants=max_variants)
    except ImportError:
        return []

    if not variants:
        return []

    # Step 2: 已有论文 DOI 集合
    existing_dois = {
        p.get("doi", "").lower().strip()
        for p in existing_papers if p.get("doi")
    }
    existing_titles = {
        (p.get("title", "") or "").lower().strip()[:80]
        for p in existing_papers
    }

    new_papers: List[Dict] = []

    # Step 3: 对每个变体执行搜索
    for variant in variants:
        try:
            # 优先使用 scholar_graph MCP
            try:
                results = _call_mcp_tool("scholar_search_literature_graph", variant, max_per_variant)
            except ImportError:
                # MCP 不可用 → HTTP fallback
                from src.parallel_search import MCP_HTTP_FALLBACK
                fn = MCP_HTTP_FALLBACK.get("scholar_search_literature_graph")
                if fn:
                    results = fn(variant, max_per_variant)
                else:
                    results = []

            if not results:
                continue

            for paper in results:
                # 去重
                doi = (paper.get("doi") or "").lower().strip()
                if doi and doi in existing_dois:
                    continue
                title = (paper.get("title") or "").lower().strip()[:80]
                if not title or title in existing_titles:
                    continue

                paper["_source"] = "variant_safety_net"
                paper["_variant"] = variant
                paper["_variant_note"] = f"⚠️ OCR变体: {variant}"

                new_papers.append(paper)
                if doi:
                    existing_dois.add(doi)
                existing_titles.add(title)

        except Exception:
            continue

    return new_papers


# ═══════════════════════════════════════════════════════
# §7 分类学变更检查 (⚠️ 防止属名变更遗漏)
# ═══════════════════════════════════════════════════════

def check_taxonomy(species_name: str) -> List[str]:
    """
    check_taxonomy(name) → [all_valid_names]

    从 species_graph.yaml 加载 variants 字段, 返回所有有效搜索名。

    ⚠️ 铁律: 搜索一个物种前, 必须先调用此函数获取所有曾用名,
             然后对每个名字执行搜索。

    教训: 2026.3 徐子悦 Pseudaspius hakonensis 论文
          因只搜 Tribolodon 而遗漏。
    """
    import yaml
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent / "config" / "species_graph.yaml"
    if not config_path.exists():
        return [species_name]

    with open(config_path, encoding="utf-8") as f:
        graph = yaml.safe_load(f)

    species_list = graph.get("graph", {}).get("species", [])
    name_lower = species_name.lower()

    for s in species_list:
        s_name = s.get("name", "").lower()
        variants = [v.lower() for v in s.get("variants", [])]
        chinese = s.get("chinese", "").lower()
        aliases = [a.lower() for a in s.get("aliases", [])]
        all_names = [s_name] + variants + [chinese] + aliases

        if name_lower in all_names:
            # 返回所有变体 (保持原始大小写)
            result = [s.get("name", species_name)]
            result.extend(s.get("variants", []))
            if s.get("note"):
                result.append(f"⚠️ {s['note']}")
            return result

    # 未在图中找到 → 返回原名
    return [species_name]


def detect_taxonomy_discrepancy(species_name: str) -> Optional[Dict]:
    """
    detect_taxonomy_discrepancy(name) → Optional[Dict]

    检测 c项目(species_graph.yaml) 与 f项目(fish_species_kb.yaml)
    之间的分类学信息不一致。

    返回:
      {
        field: "family",
        c_project_value: "Xenocyprididae",
        f_project_value: "鲤科",
        note: "鳤属…移出，归入鲴科",
        evidence: [{year, author, journal, doi/url}]
      }
      or None if consistent or species not found in both.
    """
    import yaml
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent

    # 加载 c项目 species_graph.yaml
    c_path = root / "config" / "species_graph.yaml"
    if not c_path.exists():
        return None
    with open(c_path, encoding="utf-8") as f:
        c_data = yaml.safe_load(f)

    # 加载 f项目 fish_species_kb.yaml
    f_path = root.parent / "fish-ecology-assistant" / "config" / "fish_species_kb.yaml"
    if not f_path.exists():
        return None
    with open(f_path, encoding="utf-8") as f:
        f_data = yaml.safe_load(f)

    name_lower = species_name.lower().replace(" ", "_")

    # 从 c项目找条目
    c_species = None
    for s in c_data.get("graph", {}).get("species", []):
        sid = s.get("id", "").lower()
        if name_lower in sid or name_lower in s.get("name", "").lower():
            c_species = s
            break
    if not c_species:
        return None

    # 从 f项目找条目 (by id, scientific name, synonyms, or aliases)
    f_species = None
    c_chinese = c_species.get("chinese", "").lower()
    c_aliases = [a.lower() for a in c_species.get("aliases", [])]
    c_all_names = [name_lower, c_chinese] + c_aliases

    for s in f_data.get("species", []):
        sid = s.get("id", "").lower()
        s_sci = s.get("scientific", "").lower().replace(" ", "_")
        s_aliases = [a.lower() for a in s.get("aliases", [])]
        s_synonyms = [syn.lower().replace(" ", "_") for syn in s.get("synonyms", [])]
        s_all = [sid, s_sci] + s_aliases + s_synonyms

        # 任意名称交叉命中
        if any(cn in s_all for cn in c_all_names):
            f_species = s
            break
    if not f_species:
        return None

    # 比较 family
    c_family = c_species.get("family", "")
    f_family = f_species.get("family", "")
    if not c_family or not f_family:
        return None

    # 标准化比较 (中文 vs 拉丁)
    family_consistent = (
        c_family.lower() == f_family.lower() or
        _family_same(c_family, f_family)
    )

    if family_consistent:
        return None

    # 有不一致 → 构建警告
    warning = {
        "field": "family",
        "c_project_value": c_family,
        "f_project_value": f_family,
        "note": f"分类不一致: c项目记录'{c_family}', f项目记录'{f_family}'",
        "evidence": [],
    }

    # 从 c项目 taxonomy 字段提取证据
    c_tax = c_species.get("taxonomy", {})
    if c_tax:
        warning["note"] = c_tax.get("note", warning["note"])
        warning["source"] = c_tax.get("source", "")
        warning["evidence"] = c_tax.get("evidence", [])

    # 从 f项目 taxonomy_log 补充证据
    f_log = f_species.get("taxonomy_log", [])
    if f_log and not warning["evidence"]:
        log_entry = f_log[0]
        warning["evidence"] = log_entry.get("evidence", [])

    # ── P7 通路标记: f项目知识库需要更新 ──
    warning["action_required"] = True
    warning["action"] = "update_fish_kb"
    warning["target"] = {
        "project": "fish-ecology-assistant",
        "file": "config/fish_species_kb.yaml",
        "field": "taxonomy_log",
    }

    return warning


def _family_same(c_family: str, f_family: str) -> bool:
    """检查两个科名是否指向同一分类。"""
    import re
    # 规范名: 无论中文还是拉丁，都映射到统一规范名
    FAMILY_CANONICAL = {
        # 鲤科
        "cyprinidae": "cyprinidae", "鲤科": "cyprinidae",
        # 鲴科
        "xenocyprididae": "xenocyprididae", "鲴科": "xenocyprididae",
        # 鳀科
        "engraulidae": "engraulidae", "鳀科": "engraulidae",
        # 鲿科
        "bagridae": "bagridae", "鲿科": "bagridae",
        # 鳜科
        "sinipercidae": "sinipercidae", "鳜科": "sinipercidae",
        # 鲇科
        "siluridae": "siluridae", "鲇科": "siluridae",
        # 鼠海豚科
        "phocoenidae": "phocoenidae", "鼠海豚科": "phocoenidae",
        # 鲟科
        "acipenseridae": "acipenseridae", "鲟科": "acipenseridae",
    }
    # 去括号注释: "Xenocyprididae (鲴科)" → "xenocyprididae"
    _strip = lambda s: re.sub(r'\s*\(.*?\)\s*', '', s).lower().strip()
    c = _strip(c_family)
    f = _strip(f_family)
    if c == f:
        return True
    ca = FAMILY_CANONICAL.get(c)
    fb = FAMILY_CANONICAL.get(f)
    if ca and fb and ca == fb:
        return True
    return False


# ═══════════════════════════════════════════════════════
# §8 协调搜索 — 单一入口点 (coordinated_search)
# ═══════════════════════════════════════════════════════

# 江汉大学课题组作者列表
_JHU_AUTHORS: set = {
    "fei xiong", "熊飞",
    "hongyan liu", "刘红艳",
    "ying wang", "王莹",
    "fangtao cai", "蔡方陶",
    "dongdong zhai", "翟东东",
    "ziyue xu", "徐子悦",
    "ming xia", "夏明",
    "min zhou", "周敏",
    "wen zheng", "郑雯",
    "yuanyuan chen", "陈媛媛", "chen yuanyuan",
    "xinbin duan", "段辛斌",
    "huiwu tian", "田辉伍",
}


@dataclass
class CoordinatedSearchResult:
    """协调搜索的完整输出。"""
    species_name: str               # 原始输入名
    scientific_name: str            # 规范学名
    chinese_name: str               # 中文名
    conservation: str               # 保护等级
    all_variants: List[str] = field(default_factory=list)
    mode: str = ""                  # exhaustive | classified | review_anchored
    total_papers: int = 0
    papers: List[Dict] = field(default_factory=list)
    categories: Dict[str, List[Dict]] = field(default_factory=dict)
    jhu_papers: List[Dict] = field(default_factory=list)
    incidental_count: int = 0
    engine_stats: Dict = field(default_factory=dict)
    timeline: List[Dict] = field(default_factory=list)
    citation_traversal_papers: int = 0
    citation_traversal_new: List[Dict] = field(default_factory=list)
    variant_net_papers: int = 0
    variant_net_new: List[Dict] = field(default_factory=list)
    elapsed_ms: float = 0.0
    error: str = ""
    taxonomy_warning: Optional[Dict] = None

    def summary(self) -> str:
        lines = [
            f"📊 {self.scientific_name} ({self.chinese_name}) [{self.conservation}]",
            f"模式: {self.mode} | 总计: {self.total_papers}篇",
            f"变体: {', '.join(self.all_variants[:5])}",
        ]
        if self.taxonomy_warning:
            tw = self.taxonomy_warning
            lines.append(f"🔬 分类学警告: {tw['note']}")
            for ev in tw.get('evidence', []):
                lines.append(f"   📄 {ev.get('author','?')} ({ev.get('year','?')}) {ev.get('journal','?')}")
        if self.jhu_papers:
            lines.append(f"🏠 江汉大学: {len(self.jhu_papers)}篇")
        if self.citation_traversal_papers:
            lines.append(f"🔗 引用回溯: +{self.citation_traversal_papers}篇")
        if self.variant_net_papers:
            lines.append(f"⚠️ OCR变体补漏: +{self.variant_net_papers}篇")
        if self.incidental_count:
            lines.append(f"📎 附带: {self.incidental_count}篇")
        if self.engine_stats:
            ok = self.engine_stats.get("ok", 0)
            total = sum(self.engine_stats.values())
            lines.append(f"🔍 引擎: {ok}/{total} OK ({self.elapsed_ms:.0f}ms)")
        lines.append("")
        for cat, papers in self.categories.items():
            if papers:
                latest = max((p.get("year", 0) for p in papers), default=0)
                jhu_in_cat = sum(1 for p in papers if p.get("_is_jhu"))
                tag = f" 🏠x{jhu_in_cat}" if jhu_in_cat else ""
                lines.append(f"  {cat}: {len(papers)}篇 (最新: {latest}){tag}")
        if self.error:
            lines.append(f"\n⚠️ {self.error}")
        return "\n".join(lines)


def _load_species_info(species_name: str) -> dict:
    """从 species_graph.yaml 加载物种元数据。"""
    import yaml
    from pathlib import Path
    config = Path(__file__).resolve().parent.parent / "config" / "species_graph.yaml"
    if not config.exists():
        return {"conservation": "DD", "chinese": "", "genus": "", "family": ""}
    with open(config, encoding="utf-8") as f:
        graph = yaml.safe_load(f)
    name_lower = species_name.lower()
    for s in graph.get("graph", {}).get("species", []):
        s_name = s.get("name", "").lower()
        variants = [v.lower() for v in s.get("variants", [])]
        chinese = s.get("chinese", "").lower()
        aliases = [a.lower() for a in s.get("aliases", [])]
        if name_lower in [s_name] + variants + [chinese] + aliases:
            return {
                "conservation": s.get("conservation", "DD"),
                "chinese": s.get("chinese", ""),
                "genus": s.get("genus", ""),
                "family": s.get("family", ""),
                "note": s.get("note", ""),
            }
    return {"conservation": "DD", "chinese": "", "genus": "", "family": ""}


def _is_jhu_paper(paper: Dict) -> bool:
    """检查论文是否包含江汉大学课题组成员。"""
    authors = paper.get("authors", [])
    for a in authors:
        name = ""
        if isinstance(a, dict):
            name = (a.get("name") or "").strip().lower()
        elif isinstance(a, str):
            name = a.strip().lower()
        if name and name in _JHU_AUTHORS:
            return True
    # 同时检查 title/authors 字符串字段
    text = (
        (paper.get("title") or "") + " " +
        (paper.get("authorString") or paper.get("authors_string") or "")
    ).lower()
    for author in _JHU_AUTHORS:
        if author in text:
            return True
    return False


def coordinated_search(
    species_name: str,
    group: str = "standard",
    limit: int = 10,
    on_result: callable = None,
) -> CoordinatedSearchResult:
    """
    coordinated_search(species_name, group="standard") → CoordinatedSearchResult

    单一入口点 — 整合所有搜索规则，在本会话内直接调用 MCP 工具。

    管线 (7步):
      1. check_taxonomy(name) → 所有有效学名+变体 (含中文名支持)
      2. _load_species_info() → 保护等级/中文名/分类
      3. estimate_mode() → 自适应搜索模式决策
      4. search_streaming() → 多引擎并行搜索 (MCP in-session)
      5. aggregate_results() → DOI去重 + 时间线
         ├─ Step 3: citation_traversal() → 引用回溯 (EXHAUSTIVE/CLASSIFIED)
         └─ Step 4: variant_safety_net() → OCR变体补漏 (EXHAUSTIVE)
      6. classify_paper() + cn_en_label() + _is_jhu_paper()
      7. 江汉大学论文优先排序 → 返回 CoordinatedSearchResult

    用法:
      result = coordinated_search("珠星三块鱼")  # 中文名 → 自动转 Pseudaspius hakonensis
      result = coordinated_search("鳤")           # 中文名 → Ochetobius elongatus
      print(result.summary())
    """
    import time
    t0 = time.perf_counter()

    # ── Step 1: 分类学变更检查 ──
    try:
        variants = check_taxonomy(species_name)
    except Exception as e:
        # 离线兜底: 直接用 YAML 解析
        variants = [species_name]
    if not variants:
        variants = [species_name]

    scientific_name = variants[0]  # 规范学名始终排第一

    # ── Step 2: 物种元数据 ──
    info = _load_species_info(scientific_name)
    conservation = info.get("conservation", "DD")
    chinese_name = info.get("chinese", "")

    # ── Step 2.5: 分类学不一致检测 ──
    # 比较 c项目 species_graph.yaml 与 f项目 fish_species_kb.yaml
    taxonomy_warning = None
    try:
        taxonomy_warning = detect_taxonomy_discrepancy(scientific_name)
    except Exception:
        pass  # 检测失败不中断搜索

    # ── Step 3: 自适应模式决策 ──
    # 粗略估计文献量 (实际会在搜索后校准)
    estimated_volume = 50  # 默认
    decision = estimate_mode(scientific_name, conservation, estimated_volume)

    # ── Step 4: 多引擎并行搜索 (本会话内) ──
    all_queries = list(variants[:3])  # 最多3个学名变体
    if chinese_name:
        all_queries.append(chinese_name)

    engine_results, http_fb = search_streaming(
        queries=all_queries,
        group=group,
        limit=limit,
        on_result=on_result,
    )

    # ── Step 5: 合并 + 去重 ──
    merged = aggregate_results(engine_results, http_fb)
    all_papers = merged.get("papers", [])
    engine_stats = merged.get("stats", {})
    timeline = merged.get("timeline", [])

    # ── Step 3: 引用回溯 (Citation Traversal) ──
    # 对高可信度论文展开引用链, 仅在 EXHAUSTIVE/CLASSIFIED 模式下激活
    citation_new: List[Dict] = []
    enable_citation = decision.mode in (SearchMode.EXHAUSTIVE, SearchMode.CLASSIFIED)
    if enable_citation and all_papers:
        try:
            citation_new = citation_traversal(
                papers=all_papers,
                species_name=scientific_name,
                max_per_paper=10,
                max_total_calls=15,
            )
        except Exception:
            pass
        for p in citation_new:
            p["_search_step"] = "citation_traversal"
            all_papers.append(p)
            timeline.append({
                "engine": "citation_traversal",
                "query": scientific_name[:60],
                "status": "ok",
                "papers": 1,
                "ms": 0,
            })

    # ── Step 4: 变体安全网 (Variant Safety Net) ──
    # 自动生成 OCR 变体并搜索补漏, 仅在 EXHAUSTIVE 模式下激活
    variant_new: List[Dict] = []
    enable_variant = decision.mode == SearchMode.EXHAUSTIVE
    if enable_variant:
        try:
            variant_new = variant_safety_net(
                scientific_name=scientific_name,
                existing_papers=all_papers,
                max_variants=5,
                max_per_variant=5,
            )
        except Exception:
            pass
        for p in variant_new:
            p["_search_step"] = "variant_safety_net"
            all_papers.append(p)
            timeline.append({
                "engine": "variant_safety_net",
                "query": p.get("_variant", scientific_name)[:60],
                "status": "ok",
                "papers": 1,
                "ms": 0,
            })

    # ── Step 5b: 重新去重 (含新论文) ──
    seen_doi = set()
    seen_title = set()
    remerged = []
    for p in all_papers:
        doi = (p.get("doi") or "").lower().strip()
        title = (p.get("title") or "").lower().strip()[:80]
        if doi and doi in seen_doi:
            continue
        if title and title in seen_title:
            continue
        if doi:
            seen_doi.add(doi)
        if title:
            seen_title.add(title)
        remerged.append(p)
    all_papers = remerged

    # ── Step 6: 后处理 (分类 + CN/EN + JHU) ──
    categories: Dict[str, List[Dict]] = {}
    jhu_papers = []
    incidental_count = 0

    for p in all_papers:
        # CN/EN 通道标注
        channel, cred = cn_en_label(p)
        p["_channel"] = channel
        p["_credibility_bonus"] = cred

        # 学科分类
        cat = classify_paper(p).value
        p["_category"] = cat

        # 附带判定
        is_inc, reason = is_incidental(p)
        p["_is_incidental"] = is_inc
        p["_incidental_reason"] = reason
        if is_inc:
            incidental_count += 1

        # 江汉大学标记
        p["_is_jhu"] = _is_jhu_paper(p)
        if p["_is_jhu"]:
            jhu_papers.append(p)

        # 分类索引
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    # ── Step 7: 排序 (JHU优先) ──
    jhu_dois = {p.get("doi", "") for p in jhu_papers}
    jhu_list = [p for p in all_papers if p.get("doi", "") in jhu_dois]
    other_list = [p for p in all_papers if p.get("doi", "") not in jhu_dois]
    sorted_papers = jhu_list + other_list

    elapsed = (time.perf_counter() - t0) * 1000

    return CoordinatedSearchResult(
        species_name=species_name,
        scientific_name=scientific_name,
        chinese_name=chinese_name,
        conservation=conservation,
        all_variants=variants,
        mode=decision.mode.value,
        total_papers=len(sorted_papers),
        papers=sorted_papers,
        categories=categories,
        jhu_papers=jhu_list,
        incidental_count=incidental_count,
        citation_traversal_papers=len(citation_new),
        citation_traversal_new=citation_new,
        variant_net_papers=len(variant_new),
        variant_net_new=variant_new,
        engine_stats=engine_stats,
        timeline=timeline,
        elapsed_ms=elapsed,
        taxonomy_warning=taxonomy_warning,
    )


# ═══════════════════════════════════════════════════════
# §8 KB-First 两阶段搜索 (f项目知识库 → c项目全量搜索)
# ═══════════════════════════════════════════════════════

@dataclass
class KbFirstSearchResult:
    """Result from search_with_kb_first() — wraps both stages.

    Stage 1 (kb_check): KB lookup result from f项目.
    Stage 2 (full_search): Only populated if user chose to continue.
    """
    stage: str                              # "kb_check" | "full_search"
    species_name: str                       # Original query
    kb_found: bool                          # Whether species found in f项目 KB
    kb_summary: str = ""                    # Human-readable KB result summary
    kb_recommendation: str = ""             # "stay_in_kb" | "continue_to_c"
    kb_data: Dict[str, Any] = field(default_factory=dict)  # Raw KB data
    full_search: Optional[CoordinatedSearchResult] = None  # Stage 2 result
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
        import sys
        from pathlib import Path

        # Find fish-ecology-assistant root relative to cognitive-search-engine
        cognitive_root = Path(__file__).resolve().parent.parent
        fish_root = cognitive_root.parent / "fish-ecology-assistant"
        fish_src = fish_root / "src"

        if not fish_src.is_dir():
            return None

        fish_str = str(fish_root)
        if fish_str not in sys.path:
            sys.path.insert(0, fish_str)

        # Import (handle src package namespace collision)
        import importlib
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
    except Exception:
        return None


def search_with_kb_first(
    species_name: str,
    kb_result: Optional[Dict[str, Any]] = None,
    group: str = "standard",
    limit: int = 10,
    on_result: callable = None,
) -> KbFirstSearchResult:
    """KB-First 两阶段搜索 — 先查 f项目知识库，再决定是否启动 c项目。

    This is the RECOMMENDED entry point for species literature search.
    It implements the two-stage workflow:

      Stage 1 (kb_check): Query fish-ecology-assistant knowledge base.
        → Returns KbFirstSearchResult with stage="kb_check".
        → Caller presents ask_user_prompt() to user.

      Stage 2 (full_search): If user says "continue", call
        continue_full_search() → runs coordinated_search().

    Usage:
      # Stage 1: KB check
      result = search_with_kb_first("珠星三块鱼")
      if result.stage == "kb_check":
          print(result.ask_user_prompt())
          # ... wait for user input ...

      # Stage 2: Full search (only if user says continue)
      result = continue_full_search(result, group="full")

    Args:
        species_name: Chinese name or scientific name.
        kb_result: Optional pre-fetched KB result dict (from FishEcologyOrchestrator).
        group: Engine group for full search ("quick"/"standard"/"full").
        limit: Max results per engine.
        on_result: Streaming callback for Stage 2.

    Returns:
        KbFirstSearchResult with stage="kb_check" (first call) or "full_search".
    """
    # If kb_result is already provided (e.g. from a previous cross-project call),
    # use it directly
    if kb_result:
        kb_found = kb_result.get("found", False)
        return KbFirstSearchResult(
            stage="kb_check",
            species_name=species_name,
            kb_found=kb_found,
            kb_summary=kb_result.get("summary_text", ""),
            kb_recommendation=kb_result.get("search_recommendation", "continue_to_c"),
            kb_data=kb_result,
            all_candidates=kb_result.get("all_candidates", []),
            suggested_next="ask_user",
        )

    # Stage 1: Query fish-ecology-assistant KB
    orch = _load_fish_kb()
    if orch is None:
        # f项目不可用 → 直接跳到全量搜索
        full = coordinated_search(species_name, group=group, limit=limit, on_result=on_result)
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
    except Exception:
        # KB lookup failed → fall through to full search
        full = coordinated_search(species_name, group=group, limit=limit, on_result=on_result)
        return KbFirstSearchResult(
            stage="full_search",
            species_name=species_name,
            kb_found=False,
            kb_summary="⚠️ KB查询失败，已直接启动全量搜索。",
            kb_recommendation="continue_to_c",
            full_search=full,
            suggested_next="done",
        )

    kb_data = {
        "found": kb.found,
        "scientific_name": kb.scientific_name,
        "chinese_name": kb.chinese_name,
        "aliases": kb.aliases,
        "synonyms": kb.synonyms,
        "family": kb.family,
        "order": kb.order,
        "conservation": kb.conservation,
        "ecology": kb.ecology,
        "distribution": kb.distribution,
        "category": kb.category,
        "summary_text": kb.summary_text,
        "search_recommendation": kb.search_recommendation,
        "all_candidates": kb.all_candidates,
    }

    return KbFirstSearchResult(
        stage="kb_check",
        species_name=species_name,
        kb_found=kb.found,
        kb_summary=kb.summary_text,
        kb_recommendation=kb.search_recommendation,
        kb_data=kb_data,
        all_candidates=kb.all_candidates,
        suggested_next="ask_user",
    )


def continue_full_search(
    stage1_result: KbFirstSearchResult,
    group: str = "full",
    limit: int = 10,
    on_result: callable = None,
) -> KbFirstSearchResult:
    """Stage 2: Continue to full search with c项目, enriched by KB data.

    Takes the Stage 1 result (kb_check), enriches the search with KB-known
    synonyms/aliases/variants, and runs coordinated_search().

    Args:
        stage1_result: Result from search_with_kb_first() Stage 1.
        group: Engine group ("quick"/"standard"/"full").
        limit: Max results per engine.
        on_result: Streaming callback.

    Returns:
        KbFirstSearchResult with stage="full_search" and populated full_search.
    """
    # Build enriched species name: prefer KB scientific name
    kb = stage1_result.kb_data
    search_name = kb.get("scientific_name", "") or stage1_result.species_name

    # If KB has chinese_name, pass it through for Chinese search
    # (coordinated_search handles Chinese names natively via _load_species_info)

    # Run full coordinated search
    full = coordinated_search(
        species_name=search_name,
        group=group,
        limit=limit,
        on_result=on_result,
    )

    # Attach KB metadata to the full search result
    if kb:
        full._kb_enriched = True
        full._kb_family = kb.get("family", "")
        full._kb_aliases = kb.get("aliases", [])
        full._kb_synonyms = kb.get("synonyms", [])

    stage1_result.stage = "full_search"
    stage1_result.full_search = full
    stage1_result.suggested_next = "done"

    return stage1_result


# ──── Backward-compat: add attrs to CoordinatedSearchResult ────
# These are set dynamically by continue_full_search()
CoordinatedSearchResult._kb_enriched = False
CoordinatedSearchResult._kb_family = ""
CoordinatedSearchResult._kb_aliases = []
CoordinatedSearchResult._kb_synonyms = []
