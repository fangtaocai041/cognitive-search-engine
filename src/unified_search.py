"""
统一物种搜索 — 自适应模式 + 附带过滤 + CN/EN双通道

工程语言化所有搜索规则:
  1. estimate_literature_volume() → 自适应模式决策
  2. is_incidental() → 附带论文判定
  3. classify_paper() → 学科分类
  4. cn_en_label() → CN/EN通道标注

用法:
  from src.unified_search import estimate_mode, is_incidental, classify_paper
  mode = estimate_mode("Ochetobius elongatus", "CR", 16)
  # → mode="exhaustive", include_incidental=True
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
