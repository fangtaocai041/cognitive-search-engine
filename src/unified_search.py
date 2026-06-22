"""
统一物种搜索 — 自适应模式 + 附带过滤 + CN/EN双通道

工程语言化所有搜索规则:
  1. estimate_literature_volume() → 自适应模式决策
  2. is_incidental() → 附带论文判定
  3. classify_paper() → 学科分类
  4. cn_en_label() → CN/EN通道标注

logger = logging.getLogger(__name__)
用法:
  from src.unified_search import estimate_mode, is_incidental, classify_paper
  mode = estimate_mode("Ochetobius elongatus", "CR", 16)
  # → mode="exhaustive", include_incidental=True
"""

from __future__ import annotations

import concurrent.futures
import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

# HTTP fallback engines (from parallel_search)
from .parallel_search import (
    _search_pubmed, _search_europe_pmc, _search_crossref, _search_openalex, _search_arxiv,
    _search_crossref_direct, _search_semantic_scholar,
    _search_biorxiv_medrxiv, _search_researchgate,
    _search_baidu_scholar, _search_cnki_web, _search_wanfang_web,
)


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
    }
    if species_name.lower() in HOT_SPECIES and estimated_volume > 500:
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
# §6 结果分类输出 (懒加载)
# ═══════════════════════════════════════════════════════

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

    def summary(self) -> str:
        lines = [
            f"📊 {self.species} ({self.conservation})",
            f"模式: {self.mode.value} | 总计: {self.total}篇",
        ]
        if self.incidental_count:
            lines.append(f"附带: {self.incidental_count}篇" +
                         (" (已纳入)" if self.mode == SearchMode.EXHAUSTIVE else " (已过滤)"))
        lines.append("")
        for cat, papers in self.categories.items():
            if papers:
                latest = max(p.get("year", 0) for p in papers)
                lines.append(f"  {cat}: {len(papers)}篇 (最新: {latest})")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# §7 分类学服务 (供 search_api.py 和 search_coordinator.py 调用)
# ═══════════════════════════════════════════════════════

# 全局物种图谱缓存
_SPECIES_GRAPH: List[Dict[str, Any]] = []


def _ensure_species_graph_loaded() -> List[Dict[str, Any]]:
    """Lazy-load species graph from config."""
    global _SPECIES_GRAPH
    if _SPECIES_GRAPH:
        return _SPECIES_GRAPH
    try:
        import os
        from pathlib import Path
        import yaml
        base = Path(__file__).resolve().parent.parent  # engine root
        graph_path = base / "config" / "species_graph.yaml"
        if graph_path.exists():
            with open(graph_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            _SPECIES_GRAPH = data.get("graph", {}).get("species", [])
    except Exception as _e:
                logger.warning(f"Suppressed in unified_search.py: {type(_e).__name__}: {_e}")
    return _SPECIES_GRAPH


def check_taxonomy(name: str) -> List[str]:
    """获取搜索所需的所有分类学变体.

    输入学名或中文名，返回所有搜索用名：
      1. 主学名
      2. 同义名/变体
      3. 中文名 (如果有)

    Args:
        name: 物种名 (学名 e.g. "Pseudaspius hakonensis" 或中文 "珠星三块鱼")

    Returns:
        搜索用名列表: ["Pseudaspius hakonensis", "Tribolodon brandti", "珠星三块鱼"]
    """
    species = _ensure_species_graph_loaded()
    name_lower = name.lower().replace(" ", "_")

    # 精确匹配物种 ID
    for s in species:
        sid = s.get("id", "").lower()
        if name_lower == sid or name_lower == s.get("name", "").lower():
            result = [s.get("name", name)]
            result.extend(s.get("variants", []))
            cn = s.get("chinese", "")
            if cn:
                result.append(cn)
            return result

    # 中文名匹配
    for s in species:
        cn = s.get("chinese", "")
        if cn and name == cn:
            result = [s.get("name", name)]
            result.extend(s.get("variants", []))
            result.append(cn)
            return result

    # 别名匹配
    for s in species:
        aliases = s.get("aliases", [])
        if name in aliases:
            result = [s.get("name", name)]
            result.extend(s.get("variants", []))
            cn = s.get("chinese", "")
            if cn:
                result.append(cn)
            return result

    # 未找到 → 返回原始名
    return [name]


def detect_taxonomy_discrepancy(name: str) -> Optional[Dict[str, Any]]:
    """检测 c项目 与 f项目 之间的分类学不一致.

    比较物种图谱中的分类学信息与外部输入。

    Args:
        name: 物种名 (学名或中文名)

    Returns:
        None 或不一致详情 dict
    """
    species = _ensure_species_graph_loaded()
    name_lower = name.lower().replace(" ", "_")

    for s in species:
        sid = s.get("id", "").lower()
        if name_lower == sid or name_lower == s.get("name", "").lower():
            return None  # 完全匹配 → 无不一致

        # 检查是否是变体名
        variants = [v.lower() for v in s.get("variants", [])]
        if name_lower in variants:
            return {
                "field": "taxonomy",
                "c_value": s.get("name", ""),
                "f_value": name,
                "note": f"c项目使用 {s.get('name')} 作为主学名，"
                        f"但f项目请求的是 {name}（变体/旧名）",
                "variants": [s.get("name", "")] + s.get("variants", []),
            }

    # 检查中文名
    for s in species:
        cn = s.get("chinese", "")
        if cn and name == cn:
            return None  # 中文名匹配

    # 未找到 → 返回空
    return None


# ═══════════════════════════════════════════════════════
# §8 全量搜索引擎注册表 + 流式并行搜索
# ═══════════════════════════════════════════════════════

# 可用搜索引擎全量清单 (按优先级)
ENGINE_REGISTRY = {
    # 学术搜索 (Priority 1-3)
    "scholar_graph":    {"tool": "scholar_search_literature_graph", "category": "academic", "priority": 1},
    "scholar_keywords": {"tool": "scholar_search_google_scholar_key_words", "category": "academic", "priority": 1},
    "scholar_advanced": {"tool": "scholar_search_google_scholar_advanced", "category": "academic", "priority": 2},
    "ncbi_esearch":     {"tool": "ncbi_ncbi_esearch", "category": "academic", "priority": 1},
    "crossref_article": {"tool": "article_search_literature", "category": "academic", "priority": 2},
    "crossref_direct":  {"tool": "crossref_direct", "category": "academic", "priority": 2},
    "scholarly_multi":  {"tool": "scholarly_research_search", "category": "academic", "priority": 3},
    "semantic_scholar": {"tool": "semantic_scholar", "category": "academic", "priority": 2},
    # 中文学术搜索 (Priority 2)
    "baidu_scholar":    {"tool": "baidu_scholar", "category": "chinese", "priority": 2},
    "cnki_web":         {"tool": "cnki_web", "category": "chinese", "priority": 2},
    "wanfang_web":      {"tool": "wanfang_web", "category": "chinese", "priority": 3},
    # 预印本 (Priority 3)
    "biorxiv_medrxiv":  {"tool": "biorxiv_medrxiv", "category": "preprint", "priority": 3},
    # 语义/深度搜索 (Priority 4-5)
    "tavily_search":    {"tool": "tavily_tavily_search", "category": "semantic", "priority": 4},
    "tavily_research":  {"tool": "tavily_tavily_research", "category": "semantic", "priority": 5},
    "exa_search":       {"tool": "exa_web_search_exa", "category": "semantic", "priority": 4},
    # 全文/社交搜索 (Priority 5)
    "researchgate":     {"tool": "researchgate", "category": "fulltext", "priority": 5},
    # 内置搜索 (Priority 6)
    "web_search":       {"tool": "web_search", "category": "web", "priority": 6},
    # 引用/关系 (Priority 7)
    "references":       {"tool": "article_get_references", "category": "graph", "priority": 7},
    "relations":        {"tool": "article_get_literature_relations", "category": "graph", "priority": 7},
    # 物种百科 + 全文 (Priority 3 — free, no key)
    "wikipedia":        {"tool": "wikipedia", "category": "species", "priority": 3},
    "duckduckgo":       {"tool": "duckduckgo", "category": "web", "priority": 5},
    "gbif":             {"tool": "gbif", "category": "species", "priority": 3},
    "core":             {"tool": "core", "category": "academic", "priority": 3},
}

# 默认搜索引擎组 (按场景)
ENGINE_GROUPS = {
    "quick":    ["scholar_graph", "ncbi_esearch", "web_search"],
    "standard": ["scholar_graph", "ncbi_esearch", "crossref_article", "scholarly_multi",
                 "tavily_search", "web_search"],
    "full":     ["scholar_graph", "ncbi_esearch", "crossref_article", "crossref_direct",
                 "scholarly_multi", "semantic_scholar", "tavily_search", "tavily_research",
                 "exa_search", "baidu_scholar", "cnki_web", "wanfang_web",
                 "biorxiv_medrxiv", "researchgate", "web_search",
                 "wikipedia", "duckduckgo", "gbif", "core"],
    "species":  ["wikipedia", "gbif", "web_search", "duckduckgo"],
    "chinese":  ["scholar_graph", "ncbi_esearch", "baidu_scholar", "cnki_web", "wanfang_web",
                 "crossref_article", "web_search"],
    "preprint": ["biorxiv_medrxiv", "researchgate", "scholar_graph"],
}


# HTTP fallback dispatch — MCP 不可用时用 HTTP provider 兜底
# 键: 引擎 ID  → 值: (HTTP函数, 是否需要中文名)
HTTP_ENGINES: Dict[str, tuple] = {
    # 国际学术
    "pubmed":         (_search_pubmed, False),
    "europe_pmc":     (_search_europe_pmc, False),
    "crossref":       (_search_crossref, False),
    "crossref_direct": (_search_crossref_direct, False),
    "openalex":       (_search_openalex, False),
    "arxiv":          (_search_arxiv, False),
    "semantic_scholar": (_search_semantic_scholar, False),
    # 中文
    "baidu_scholar":  (_search_baidu_scholar, True),
    "cnki_web":       (_search_cnki_web, True),
    "wanfang_web":    (_search_wanfang_web, True),
    # 预印本
    "biorxiv_medrxiv": (_search_biorxiv_medrxiv, False),
    # 全文
    "researchgate":   (_search_researchgate, False),
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
    max_retries: int = 5,
    per_engine_timeout_s: float = 60.0,
    on_result: Callable = None,
) -> List[EngineResult]:
    """
    流式并行搜索: 先完成的引擎先返回, 后完成的后续合并。

    特性:
      - 异步流式: 每个引擎完成立即回调 on_result(event)
      - 分时执行: 不等最慢的引擎, 先到先得
      - 每组引擎独立30s超时+重试
      - 支持预定义引擎组: quick/standard/full/chinese

    Args:
        queries: 搜索查询列表
        engines: 自定义引擎列表 (覆盖 group)
        group: 预定义引擎组名
        limit: 每引擎最大结果数
        max_retries: 最大重试次数
        per_engine_timeout_s: 单引擎超时
        on_result: 回调 (StreamEvent) -> None

    Returns:
        所有引擎结果列表
    """
    if engines is None:
        engines = ENGINE_GROUPS.get(group, ENGINE_GROUPS["standard"])

    results: List[EngineResult] = []
    total_papers = 0

    # 混合调度: 每引擎先 MCP → 失败后 HTTP 兜底
    for query in queries[:3]:
        for engine_id in engines:
            info = ENGINE_REGISTRY.get(engine_id, {})
            tool_name = info.get("tool", "")
            if not tool_name:
                continue

            t0 = time.perf_counter()
            er = EngineResult(engine=engine_id, query=query, tool=tool_name)

            # === Phase 1: 尝试 MCP (Reasonix 内建工具) ===
            fn = globals().get(tool_name)
            if fn is not None:
                for attempt in range(max_retries):
                    try:
                        response = fn(query=query, limit=limit)
                        if isinstance(response, list):
                            er.results = response
                            er.status = "ok"
                        elif response:
                            er.results = [response]
                            er.status = "ok"
                        else:
                            er.status = "empty"
                        break
                    except Exception as e:
                        er.retries = attempt + 1
                        er.error = str(e)
                        er.status = "mcp_error"
                        if attempt < max_retries - 1:
                            time.sleep(2.0)

            # === Phase 2: MCP 不可用/失败 → HTTP 兜底 ===
            if er.status in ("pending", "mcp_error", "empty") or fn is None:
                http_info = HTTP_ENGINES.get(engine_id)
                if http_info:
                    http_fn, needs_cn = http_info
                    try:
                        if needs_cn:
                            # 中文引擎: 从 queries 找中文名
                            cn_query = next((q for q in queries if re.search(r"[一-鿿]", q)), query)
                            response = http_fn(cn_query, limit)
                        else:
                            response = http_fn(query, limit)
                        if isinstance(response, list):
                            er.results.extend(response)
                        elif response:
                            er.results.append(response)
                        er.status = "http_ok"
                        if er.error:
                            er.error += "; then HTTP fallback succeeded"
                        else:
                            er.error = "MCP unavailable → HTTP fallback"
                    except Exception as e2:
                        er.status = "http_error"
                        er.error = f"{er.error}; HTTP also failed: {e2}"
                elif fn is None:
                    er.status = "unavailable"
                    er.error = "No MCP and no HTTP fallback"

            er.elapsed_ms = (time.perf_counter() - t0) * 1000
            results.append(er)
            total_papers += len(er.results)

            # 流式回调
            if on_result:
                on_result(StreamEvent(
                    engine=engine_id,
                    status=er.status,
                    paper_count=len(er.results),
                    elapsed_ms=er.elapsed_ms,
                ))

    return results


def _mcp_available() -> bool:
    """检查 MCP 工具是否可用."""
    for engine_id, info in ENGINE_REGISTRY.items():
        tool_name = info.get("tool", "")
        if tool_name and globals().get(tool_name) is not None:
            return True
        # 检查 __builtins__
        try:
            fn = getattr(__builtins__, tool_name, None)
            if fn is not None:
                return True
        except Exception as _e:
                logger.warning(f"Suppressed in unified_search.py: {type(_e).__name__}: {_e}")
    return False
