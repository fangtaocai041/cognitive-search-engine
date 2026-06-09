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

# 可用搜索引擎全量清单 (按优先级)
ENGINE_REGISTRY = {
    # 学术搜索 (Priority 1-3)
    "scholar_graph":    {"tool": "scholar_search_literature_graph", "category": "academic", "priority": 1},
    "scholar_keywords": {"tool": "scholar_search_google_scholar_key_words", "category": "academic", "priority": 1},
    "scholar_advanced": {"tool": "scholar_search_google_scholar_advanced", "category": "academic", "priority": 2},
    "ncbi_esearch":     {"tool": "ncbi_ncbi_esearch", "category": "academic", "priority": 1},
    "crossref_article": {"tool": "article_search_literature", "category": "academic", "priority": 2},
    "scholarly_multi":  {"tool": "scholarly_research_search", "category": "academic", "priority": 3},
    # 语义/深度搜索 (Priority 4-5)
    "tavily_search":    {"tool": "tavily_tavily_search", "category": "semantic", "priority": 4},
    "tavily_research":  {"tool": "tavily_tavily_research", "category": "semantic", "priority": 5},
    "exa_search":       {"tool": "exa_web_search_exa", "category": "semantic", "priority": 4},
    # 内置搜索 (Priority 6)
    "web_search":       {"tool": "web_search", "category": "web", "priority": 6},
    # 引用/关系 (Priority 7)
    "references":       {"tool": "article_get_references", "category": "graph", "priority": 7},
    "relations":        {"tool": "article_get_literature_relations", "category": "graph", "priority": 7},
}

# 默认搜索引擎组 (按场景)
ENGINE_GROUPS = {
    "quick":    ["scholar_graph", "ncbi_esearch", "web_search"],                    # 3引擎, ~10s
    "standard": ["scholar_graph", "ncbi_esearch", "crossref_article", "web_search", "tavily_search"],  # 5引擎, ~20s
    "full":     ["scholar_graph", "ncbi_esearch", "crossref_article", "scholarly_multi",
                 "tavily_search", "exa_search", "web_search"],                      # 7引擎, ~30s
    "chinese":  ["scholar_graph", "ncbi_esearch", "web_search"],                   # 含中文源
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

    流式并行搜索: 先完成的引擎先返回, 后完成的后续合并。

    特性:
      - 异步流式: 每个引擎完成立即回调 on_result(event)
      - 分时执行: 不等最慢的引擎, 先到先得
      - 每组引擎独立30s超时+重试
      - 支持预定义引擎组: quick/standard/full/chinese

    用法:
      def on_result(event: StreamEvent):
          print(f"[{event.engine}] {event.status} {event.paper_count}篇 {event.elapsed_ms:.0f}ms")

      results = search_streaming(["Pseudaspius hakonensis"], group="full", on_result=on_result)
    """
    import concurrent.futures
    import time

    if engines is None:
        engines = ENGINE_GROUPS.get(group, ENGINE_GROUPS["standard"])

    results: List[EngineResult] = []
    completed = 0
    total = len(engines) * len(queries)
    _http_fallback: List[Dict] = []  # SearchRuleEngine HTTP results

    def _search_one(engine_id: str, query: str) -> EngineResult:
        t0 = time.perf_counter()
        info = ENGINE_REGISTRY.get(engine_id, {"tool": engine_id, "category": "unknown", "priority": 9})
        result = EngineResult(engine=engine_id, query=query, tool=info["tool"])
        last_error = ""

        for attempt in range(max_retries):
            try:
                # 尝试调用对应的 MCP 工具
                # 当前为框架层 → MCP 服务运行时自动激活
                result.results = _call_mcp_tool(info["tool"], query, limit)
                result.status = "ok"
                break
            except ImportError:
                result.status = "degraded"
                result.error = f"{info['tool']}: MCP not available"
                break
            except Exception as e:
                last_error = str(e)
                result.retries = attempt + 1
                if attempt < max_retries - 1:
                    wait = min(retry_delay_s * (2 ** attempt), 10)  # 指数退避, 上限10s
                    time.sleep(wait)
                continue
        else:
            result.status = "error"
            result.error = last_error[:200]

        result.elapsed_ms = (time.perf_counter() - t0) * 1000
        return result

    # 并行启动所有引擎 — 先完成先返回
    with concurrent.futures.ThreadPoolExecutor(max_workers=total) as ex:
        futures = {}
        for engine_id in engines:
            for query in queries:
                future = ex.submit(_search_one, engine_id, query)
                futures[future] = (engine_id, query)

        for future in concurrent.futures.as_completed(futures):
            engine_id, query = futures[future]
            try:
                result = future.result(timeout=per_engine_timeout_s)
                results.append(result)
                completed += 1

                # 流式回调: 立即通知
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

    # Fallback: SearchRuleEngine HTTP if all MCP engines degraded
    if all(r.status in ("degraded", "error") for r in results):
        try:
            from src.rule_engine import SearchRuleEngine as _SRE
            sr = _SRE(mode="http")
            sp_id = (queries[0] if queries else "").replace(" ", "_")
            res = sr.execute(sp_id)
            for p in res.get("papers", []):
                p.setdefault("source", "http_fallback")
                _http_fallback.append(p)
        except Exception:
            pass
    return results, _http_fallback


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
    elapsed_ms: float = 0.0
    error: str = ""

    def summary(self) -> str:
        lines = [
            f"📊 {self.scientific_name} ({self.chinese_name}) [{self.conservation}]",
            f"模式: {self.mode} | 总计: {self.total_papers}篇",
            f"变体: {', '.join(self.all_variants[:5])}",
        ]
        if self.jhu_papers:
            lines.append(f"🏠 江汉大学: {len(self.jhu_papers)}篇")
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
    with open(config) as f:
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

    管线:
      1. check_taxonomy(name) → 所有有效学名+变体 (含中文名支持)
      2. _load_species_info() → 保护等级/中文名/分类
      3. estimate_mode() → 自适应搜索模式决策
      4. search_streaming() → 多引擎并行搜索 (MCP in-session)
      5. aggregate_results() → DOI去重 + 时间线
      6. classify_paper() + cn_en_label() + _is_jhu_paper()
      7. 江汉大学论文优先排序
      8. 返回 CoordinatedSearchResult

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
        engine_stats=engine_stats,
        timeline=timeline,
        elapsed_ms=elapsed,
    )
