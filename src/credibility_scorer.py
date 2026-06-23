"""Paper credibility scoring based on SOURCE AUTHORITY, not just journal name.

评分依据信息来源权威性 (0-100):
  95-100: 国际权威机构 (IUCN/FAO/IPBES)
  85-94:  顶级同行评审期刊 (Nature/Science/Scientific Data)
  75-84:  标准SCI期刊 (Animals/Gene/PLOS ONE)
  65-74:  中文核心 (水生生物学报/生物多样性)
  50-64:  一般学术来源
  20-49:  新闻报道
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# 信息来源权威性评级 — 按最长关键词优先匹配
AUTHORITY_TIERS: List[tuple] = [
    ("iucn", 98), ("nature", 94), ("science", 94), ("pnas", 92),
    ("scientific data", 92), ("current biology", 90),
    ("molecular ecology", 88), ("ecology letters", 88),
    ("global change biology", 88),
    ("animals", 82), ("gene", 84), ("bmc biology", 82),
    ("scientific reports", 78), ("plos one", 78),
    ("mitochondrial dna", 80), ("conservation genet resour", 76),
    ("genes", 78), ("aquaculture", 80),
    ("水生生物学报", 72), ("中国水产科学", 72), ("水产学报", 72),
    ("生物多样性", 70), ("湖泊科学", 70), ("生态学报", 70),
    ("南方水产科学", 68), ("acta hydrobiologica sinica", 72),
    ("水生态学杂志", 68), ("淡水渔业", 66),
    ("日报", 30), ("新闻", 25), ("xinhua", 40),
    ("chinadaily", 35), ("科学养鱼", 45), ("水产科技情报", 45),
]
sorted_tiers = sorted(AUTHORITY_TIERS, key=lambda x: -len(x[0]))


def score_paper(paper: Dict[str, Any]) -> int:
    """Score paper credibility (0-100) based on source authority."""
    text = (paper.get("journal", "") + " " + paper.get("source", "")).lower()
    base = 30
    for keyword, score in sorted_tiers:
        if keyword in text:
            base = score
            break
    citations = paper.get("citation_count", 0) if base >= 65 else 0
    if citations > 100: base += 5
    elif citations > 50: base += 3
    elif citations > 20: base += 2
    elif citations > 5: base += 1
    return min(base, 100)


def score_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for p in papers:
        p["credibility_score"] = score_paper(p)
    return sorted(papers, key=lambda x: x.get("credibility_score", 0), reverse=True)


def credibility_symbol(score: int) -> str:
    if score >= 95: return "[顶]"
    elif score >= 85: return "[优]"
    elif score >= 75: return "[良]"
    elif score >= 65: return "[核]"
    elif score >= 50: return "[标]"
    elif score >= 20: return "[闻]"
    return "[--]"


def source_authority_label(score: int) -> str:
    if score >= 95: return "国际权威"
    elif score >= 85: return "顶级期刊"
    elif score >= 75: return "SCI期刊"
    elif score >= 65: return "中文核心"
    elif score >= 50: return "一般学术"
    elif score >= 20: return "新闻报道"
    return "未验证"


def detect_journal_tier(journal: str) -> str:
    text = journal.lower()
    for keyword, score in sorted_tiers:
        if keyword in text:
            if score >= 95: return "top"
            elif score >= 85: return "excellent"
            elif score >= 75: return "standard_sci"
            elif score >= 65: return "core_cn"
            elif score >= 50: return "academic"
            elif score >= 20: return "news"
            return "unknown"
    return "unknown"


def format_credibility(score: int) -> str:
    symbol = credibility_symbol(score)
    label = source_authority_label(score)
    return f"{symbol} {score}分 {label}"


def is_predatory(journal: str) -> bool:
    predatory = ["waset", "world academy of science", "omcs", "predatory"]
    return any(ind in journal.lower() for ind in predatory)
