"""
Report Formatter — Hub-and-Spoke classification output with credibility visualization.

Implements the fuzzy-species-search-rule v5.0 output template:
  - Classification table per category (综述 / 遗传与分子 / 形态与表型 / ...)
  - Credibility score visualization (🟢🟡🟠🔴)
  - On-demand detail loading protocol
  - OCR variant flagging
  - Chinese journal authority whitelist integration

Usage:
  from src.report_formatter import format_report, classify_papers

  classified = classify_papers(papers, species_id)
  report = format_report(classified)
  print(report)  # Markdown classification table
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════
# Classification categories (from fuzzy-species-search-rule v5.0)
# ═══════════════════════════════════════════════════════════════════════

CATEGORY_DEFS = {
    "reviews": {
        "label": "综述",
        "emoji": "📖",
        "keywords": [
            "review", "综述", "survey", "研究进展", "进展", "概述",
            "meta-analysis", "bibliometric", "retrospective", "展望",
        ],
        "desc": "综述 (Reviews)",
    },
    "genetics": {
        "label": "遗传与分子",
        "emoji": "🧬",
        "keywords": [
            "genetic", "diversity", "population", "mitochondrial", "microsatellite",
            "snp", "ssr", "haplotype", "phyloge", "遗传", "群体", "多态",
            "线粒体", "分子标记", "系统发育", "phylogen", "进化",
        ],
        "desc": "遗传与分子生物学",
        "subcats": ["线粒体基因组", "群体遗传学", "分子标记", "系统发育"],
    },
    "morphology": {
        "label": "形态与表型",
        "emoji": "📐",
        "keywords": [
            "morpholog", "phenotype", "shape", "geometric", "形态",
            "表型", "测量", "meristic", "可塑性", "plasticity",
        ],
        "desc": "形态与表型",
        "subcats": ["几何形态测量", "传统形态测量", "表型可塑性"],
    },
    "genomics": {
        "label": "基因组学",
        "emoji": "🧪",
        "keywords": [
            "genome", "chromosome", "assembly", "sequencing", "基因组",
            "染色体", "组装", "测序", "全基因组", "comparative",
        ],
        "desc": "基因组学",
        "subcats": ["全基因组组装", "比较基因组学"],
    },
    "diet_physiology": {
        "label": "食性与生理",
        "emoji": "🍽️",
        "keywords": [
            "diet", "feeding", "digestive", "stomach", "intestine",
            "食性", "消化道", "胃", "肠道", "gut", "microbiome",
            "微生物", "生理", "physiology",
        ],
        "desc": "食性与生理",
        "subcats": ["消化道形态组织学", "食性分析", "肠道微生物"],
    },
    "ecology": {
        "label": "生态与资源",
        "emoji": "🌊",
        "keywords": [
            "survey", "diversity", "community", "resource", "habitat",
            "migration", "spawning", "growth", "reproduction",
            "调查", "多样性", "渔获", "资源", "栖息", "洄游",
            "群落", "种群", "生态", "ecology",
        ],
        "desc": "生态与资源",
        "subcats": ["鱼类多样性调查", "渔业资源评估", "栖息地/洄游"],
    },
    "toxicology": {
        "label": "毒理与环境",
        "emoji": "☣️",
        "keywords": [
            "toxic", "pollut", "contamin", "pfas", "metal",
            "毒理", "污染", "重金属", "环境", "environmental",
        ],
        "desc": "毒理与环境",
    },
    "conservation": {
        "label": "保护政策",
        "emoji": "📢",
        "keywords": [
            "conservation", "endangered", "protected", "recovery",
            "保护", "濒危", "禁渔", "policy", "management",
            "红皮书", "esu", "mu",
        ],
        "desc": "保护政策",
    },
    "low_credibility": {
        "label": "低可信度 / OCR 变体",
        "emoji": "⚠️",
        "desc": "低可信度 / OCR 变体",
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ClassifiedPaper:
    """A paper with classification metadata."""
    title: str
    year: Optional[int] = None
    journal: str = ""
    authors: list[str] = field(default_factory=list)
    doi: str = ""
    credibility_score: int = 50
    credibility_label: str = "🟡"
    category: str = ""
    is_ocr_variant: bool = False
    is_new: bool = False
    source: str = ""
    note: str = ""

    def credibility_emoji(self) -> str:
        score = self.credibility_score
        if score >= 80:
            return "🟢"
        elif score >= 60:
            return "🟡"
        elif score >= 40:
            return "🟠"
        else:
            return "🔴"

    @property
    def latest_year(self) -> str:
        return str(self.year) if self.year else "—"


@dataclass
class ClassificationReport:
    """Complete classification report for a species."""
    species_name: str = ""
    chinese_name: str = ""
    total_papers: int = 0
    high_cred: int = 0       # 🟢 ≥80
    medium_cred: int = 0     # 🟡 60-79
    low_cred: int = 0        # 🟠 40-59
    rejected: int = 0        # 🔴 <40
    categories: dict[str, list[ClassifiedPaper]] = field(default_factory=dict)
    # Per-category latest paper for summary table
    category_latest: dict[str, str] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════
# Classification Engine
# ═══════════════════════════════════════════════════════════════════════

def classify_papers(papers: list[dict], species_name: str = "",
                    chinese_name: str = "",
                    genus: str = "",
                    species_ep: str = "") -> ClassificationReport:
    """Classify papers into Hub-and-Spoke categories.

    Args:
        papers: List of paper dicts from search results
        species_name: e.g. "Ochetobius elongatus"
        chinese_name: e.g. "鳤"
        genus: e.g. "Ochetobius"
        species_ep: e.g. "elongatus"

    Returns:
        ClassificationReport with papers sorted into categories.
    """
    report = ClassificationReport(
        species_name=species_name,
        chinese_name=chinese_name,
        total_papers=len(papers),
    )

    # Build classified papers
    for p in papers:
        title = p.get("title", "") or ""
        title_lower = title.lower()
        journal = p.get("journal", "") or ""
        doi = p.get("doi", "") or ""
        year = p.get("year")
        authors = p.get("authors", []) or []
        source = p.get("source", p.get("source_project", "")) or ""
        trust = p.get("trust", "")

        # Credibility score — use the richer credibility_score if available
        cs = p.get("credibility_score", p.get("trust_score", 50)) or 50

        # Detect OCR variant
        abstract = p.get("abstract", "") or ""
        is_ocr = _is_ocr_variant(doi, source, title, genus, species_ep, abstract)

        # Detect new (unindexed) paper
        is_new = _is_new_paper(p, source)

        cp = ClassifiedPaper(
            title=title,
            year=year,
            journal=journal,
            authors=authors,
            doi=doi,
            credibility_score=cs,
            is_ocr_variant=is_ocr,
            is_new=is_new,
            source=source,
            note=p.get("note", ""),
        )

        # ── Score buckets ──
        if cs >= 80:
            report.high_cred += 1
        elif cs >= 60:
            report.medium_cred += 1
        elif cs >= 40:
            report.low_cred += 1
        else:
            report.rejected += 1

        # ── Classify into category ──
        category = _classify_single(title, title_lower, journal, trust)
        cp.category = category
        report.categories.setdefault(category, []).append(cp)

    # ── Compute per-category latest ──
    for cat, items in report.categories.items():
        years = [p.year for p in items if p.year]
        if years:
            latest_p = max(items, key=lambda p: p.year or 0)
            report.category_latest[cat] = (
                f"{latest_p.authors[0] if latest_p.authors else '?'} {latest_p.year}"
            )
        else:
            report.category_latest[cat] = "—"

    return report


def _is_ocr_variant(doi: str, source: str, title: str,
                     genus: str, species_ep: str,
                     abstract: str = "") -> bool:
    """Detect if paper was found via OCR variant search."""
    if "variant" in source.lower():
        return True
    # OCR 变体只在标题含拼写错误时标记
    # 标题不含属名但摘要含属名的是附带论文，不是 OCR 变体
    if genus and species_ep:
        expected = f"{genus.lower()} {species_ep.lower()}"
        title_lower = title.lower()
        if expected not in title_lower:
            # 检查标题是否有拼写变异（如 Ochetobibus → Ochetobius）
            # 实际 OCR 变体：标题包含近似的属名拼写
            from difflib import SequenceMatcher
            words = title_lower.split()
            for w in words:
                if SequenceMatcher(None, w, genus.lower()).ratio() > 0.8 and w != genus.lower():
                    return True  # 拼写相近但不同 → OCR 变体
        return False  # 不含属名是附带论文，不是 OCR 变体
    # 无 species_ep 时的兜底
    if genus and genus.lower() not in title.lower():
        # 摘要含属名 → 附带论文，非 OCR 变体
        if abstract and genus.lower() in abstract.lower():
            return False
        return True
    return False


def _is_new_paper(paper: dict, source: str) -> bool:
    """Detect new (unindexed) papers — year ≥ current-1 and no PMID."""
    import datetime
    raw_year = paper.get("year")
    pmid = paper.get("pmid")
    current = datetime.datetime.now().year
    try:
        year = int(raw_year) if raw_year else 0
    except (ValueError, TypeError):
        year = 0
    return bool(year and year >= current - 1 and not pmid)


def _classify_single(title: str, title_lower: str, journal: str,
                      trust: str) -> str:
    """Route a single paper to the best-matching category."""
    # Reviews first
    for kw in CATEGORY_DEFS["reviews"]["keywords"]:
        if kw in title_lower:
            return "reviews"

    best_cat = "other"
    best_score = 0

    category_order = [
        "genetics", "morphology", "genomics",
        "diet_physiology", "ecology", "toxicology", "conservation",
    ]
    for cat_key in category_order:
        cat_def = CATEGORY_DEFS.get(cat_key, {})
        score = sum(1 for kw in cat_def.get("keywords", [])
                    if kw in title_lower)
        if score > best_score:
            best_score = score
            best_cat = cat_key

    # If no keywords matched, check for low credibility
    if best_score == 0:
        if trust in ("unverified", "tentative"):
            return "low_credibility"
        return "other"

    return best_cat


# ═══════════════════════════════════════════════════════════════════════
# Output Template (fuzzy-species-search-rule v5.0)
# ═══════════════════════════════════════════════════════════════════════

def format_report(report: ClassificationReport,
                  detail_level: str = "summary") -> str:
    """Generate the markdown classification report.

    Args:
        report: ClassificationReport from classify_papers()
        detail_level:
          - "summary" → one-line category counts (default)
          - "expanded" → paper titles + year + journal
          - "full" → titles + authors + abstracts (for user-requested detail)

    Returns:
        Markdown-formatted report string.
    """
    name = report.chinese_name or report.species_name or "Unknown"
    lines = []
    ocr_count = sum(
        1 for cats in report.categories.values()
        for p in cats if p.is_ocr_variant
    )

    # ── Header ──
    lines.append(f"## {report.species_name or name} 文献图谱")
    lines.append("")
    ocr_seg = f" | ⚠️ OCR变体 {ocr_count} 篇" if ocr_count else ""
    lines.append(
        f"📊 总计: {report.total_papers} 篇"
        f" | 🟢高可信 {report.high_cred} 篇"
        f" | 🟡中 {report.medium_cred} 篇"
        + ocr_seg
    )
    lines.append("")

    # ── Classification Summary Table ──
    lines.append("| 分类 | 论文数 | 最新 |")
    lines.append("|------|:------:|------|")

    shown_cats = ["reviews", "genetics", "morphology", "genomics",
                   "diet_physiology", "ecology", "toxicology",
                   "conservation", "low_credibility"]
    for cat_key in shown_cats:
        cat_def = CATEGORY_DEFS.get(cat_key, {})
        emoji = cat_def.get("emoji", "")
        label = cat_def.get("label", cat_key)
        papers_in_cat = report.categories.get(cat_key, [])
        count = len(papers_in_cat)
        latest = report.category_latest.get(cat_key, "—")
        lines.append(f"| {emoji} {label} | {count} | {latest} |")

    # Add "other" category if it has papers
    other = report.categories.get("other", [])
    if other:
        latest_other = report.category_latest.get("other", "—")
        lines.append(f"| 📄 其他 | {len(other)} | {latest_other} |")

    lines.append("")
    lines.append("输入分类名展开详情")

    # ── Expanded detail: per-category paper lists ──
    if detail_level in ("expanded", "full"):
        for cat_key in shown_cats:
            cat_def = CATEGORY_DEFS.get(cat_key, {})
            emoji = cat_def.get("emoji", "")
            desc = cat_def.get("desc", cat_key)
            papers_in_cat = report.categories.get(cat_key, [])
            if not papers_in_cat:
                continue

            lines.append("")
            lines.append(f"### {emoji} {desc}")
            lines.append("")

            for p in sorted(papers_in_cat, key=lambda x: x.year or 0, reverse=True):
                cred = p.credibility_emoji()
                flags = ""
                if p.is_ocr_variant:
                    flags += " ⚠️OCR变体"
                if p.is_new:
                    flags += " 🆕未索引"
                author = p.authors[0] if p.authors else "?"
                journal_short = p.journal[:40] if p.journal else "?"
                lines.append(
                    f"- {cred} {p.title} — "
                    f"{author} {p.latest_year} "
                    f"*{journal_short}*"
                    + flags
                )

                if detail_level == "full":
                    if len(p.authors) > 1:
                        lines.append(f"  - 作者: {'; '.join(p.authors)}")
                    if p.doi:
                        lines.append(f"  - DOI: [{p.doi}](https://doi.org/{p.doi})")
                    if p.source:
                        lines.append(f"  - 来源: `{p.source}`")
                    if p.note:
                        lines.append(f"  - 备注: {p.note}")
    else:
        # Summary: just mention which categories have content
        lines.append("")
        lines.append("---")
        lines.append("💡 输入分类名（如 `遗传与分子`）展开详情")
        lines.append("💡 输入 `全部展开` 显示所有论文标题")

    return "\n".join(lines)


def format_category_detail(report: ClassificationReport,
                           category_key: str) -> str:
    """Format a single category with full detail.

    Args:
        report: ClassificationReport
        category_key: e.g. "genetics", "diet_physiology"

    Returns:
        Markdown for the requested category.
    """
    cat_def = CATEGORY_DEFS.get(category_key, {})
    emoji = cat_def.get("emoji", "📄")
    desc = cat_def.get("desc", category_key)
    papers = report.categories.get(category_key, [])

    if not papers:
        return f"{emoji} **{desc}**: 暂无论文"

    lines = [f"### {emoji} {desc} ({len(papers)} 篇)", ""]

    # Subcategories if defined
    subcats = cat_def.get("subcats", [])
    if subcats:
        lines.append(f"> 子方向: {' · '.join(subcats)}")
        lines.append("")

    for p in sorted(papers, key=lambda x: x.year or 0, reverse=True):
        cred = p.credibility_emoji()
        flags = ""
        if p.is_ocr_variant:
            flags += " ⚠️OCR变体"
        if p.is_new:
            flags += " 🆕未索引"

        authors_str = "; ".join(p.authors[:5])
        if len(p.authors) > 5:
            authors_str += f" et al."
        if not authors_str:
            authors_str = "?"

        lines.append(f"**{p.title}**{flags}")
        lines.append(f"- 作者: {authors_str}")
        lines.append(f"- 年份: {p.latest_year} | 期刊: *{p.journal or '?'}*")
        if p.doi:
            lines.append(f"- DOI: `{p.doi}` | 可信度: {cred} ({p.credibility_score})")
        else:
            lines.append(f"- 可信度: {cred} ({p.credibility_score})")
        if p.source:
            lines.append(f"- 来源: `{p.source}`")
        if p.note:
            lines.append(f"- 备注: {p.note}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════════════════

def generate_quick_report(papers: list[dict],
                          species_name: str = "",
                          chinese_name: str = "",
                          genus: str = "",
                          species_ep: str = "",
                          detail: str = "summary") -> str:
    """One-liner: classify and format a report from search results.

    Args:
        papers: Search result paper dicts
        species_name: e.g. "Ochetobius elongatus"
        chinese_name: e.g. "鳤"
        genus: e.g. "Ochetobius"
        species_ep: e.g. "elongatus"
        detail: "summary" | "expanded" | "full"

    Returns:
        Markdown report string.
    """
    report = classify_papers(
        papers,
        species_name=species_name,
        chinese_name=chinese_name,
        genus=genus,
        species_ep=species_ep,
    )
    return format_report(report, detail_level=detail)
