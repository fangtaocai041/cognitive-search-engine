#!/usr/bin/env python3
"""
credibility_scorer.py — 论文可信度评分 (三角验证评分 §2.1)

实现 lit-search §2.1 三角验证评分规则:
  评分 = 50(基础) + 30(SCI期刊) + 25(CSCD核心) + 10(有DOI) + 10(有PMID)
         - 30(预印本) - 100(掠夺性期刊)

标签: 🟢高(≥75) / 🟡中(45-74) / 🟠低(20-44) / 🔴不可用(<20)

用法:
  python scripts/credibility_scorer.py --paper '{"journal":"Nature","doi":"10.xxx","pmid":"123"}'
  python scripts/credibility_scorer.py --input papers.json --output scored.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List


# ── 期刊权威白名单 ──
SCI_T1 = {  # Q1 / 顶级
    "nature", "science", "pnas", "current biology",
    "molecular ecology", "ecology letters", "global change biology",
}
SCI_T2 = {  # Q2 / 优秀
    "bmc biology", "scientific data", "scientific reports",
    "plos one", "genes", "gene", "animals",
    "mitochondrial dna", "conservation genetics resources",
}
CSCD_CORE = {  # 中文核心 (CSCD)
    "水生生物学报", "中国水产科学", "水产学报",
    "生物多样性", "湖泊科学", "生态学报", "生态科学",
    "南方水产科学",
}
PREDATORY_INDICATORS = [
    "waset", "world academy of science",
    "journal of applied sciences",
]


def score_paper(paper: Dict[str, Any], species_name: str = "") -> Dict[str, Any]:
    """为单篇论文计算可信度评分.

    Args:
        paper: 论文 dict (含 journal, doi, pmid, title, year 等字段)
        species_name: 物种名 (用于兼容性标记)

    Returns:
        添加了 _credibility_score, _label, _flag, _detail 的 paper
    """
    score = 50  # 基础分
    detail_parts = ["基础 50"]

    journal = (paper.get("journal") or paper.get("venue") or "").strip()
    doi = paper.get("doi", "")
    pmid = paper.get("pmid", "")
    title = (paper.get("title") or "").lower()

    # SCI 加分
    if journal in SCI_T1:
        score += 30
        detail_parts.append("SCI_T1 +30")
    elif journal in SCI_T2:
        score += 20
        detail_parts.append("SCI_T2 +20")

    # CSCD 核心加分 (中文期刊)
    if journal in CSCD_CORE:
        score += 25
        detail_parts.append("CSCD +25")

    # DOI / PMID 加分
    if doi:
        score += 10
        detail_parts.append("DOI +10")
    if pmid:
        score += 10
        detail_parts.append("PMID +10")

    # 预印本扣分
    if any(x in title for x in ["preprint", "ssrn", "research square", "biorxiv"]):
        score -= 30
        detail_parts.append("预印本 -30")

    # 掠夺性期刊扣分
    if any(ind in journal.lower() for ind in PREDATORY_INDICATORS):
        score -= 100
        detail_parts.append("掠夺性 -100")

    # 阈值限定
    score = max(0, min(100, score))

    # 标签
    if score >= 75:
        label = "高"
        flag = "🟢"
    elif score >= 45:
        label = "中"
        flag = "🟡"
    elif score >= 20:
        label = "低"
        flag = "🟠"
    else:
        label = "不可用"
        flag = "🔴"

    paper["_credibility_score"] = score
    paper["_credibility_label"] = label
    paper["_credibility_flag"] = flag
    paper["_credibility_detail"] = ", ".join(detail_parts)

    return paper


def score_papers(papers: List[Dict], species_name: str = "") -> List[Dict]:
    """批量评分."""
    return [score_paper(p, species_name) for p in papers]


def format_credibility(score: int, flag: str = "") -> str:
    """将得分格式化为可视化标识.

    Args:
        score: 0-100 的得分
        flag: 可选，已有标记

    Returns:
        如 "🟢 高 85" 或 "🔴 不可用 15"
    """
    if not flag:
        if score >= 75:
            flag = "🟢"
            label = "高"
        elif score >= 45:
            flag = "🟡"
            label = "中"
        elif score >= 20:
            flag = "🟠"
            label = "低"
        else:
            flag = "🔴"
            label = "不可用"
    else:
        if score >= 75:
            label = "高"
        elif score >= 45:
            label = "中"
        elif score >= 20:
            label = "低"
        else:
            label = "不可用"
    return f"{flag} {label} {score}"


def main() -> None:
    parser = argparse.ArgumentParser(description="论文可信度评分")
    parser.add_argument("--paper", help="单篇论文 JSON 字符串")
    parser.add_argument("--input", help="JSON 输入文件 (论文列表)")
    parser.add_argument("--output", default="", help="JSON 输出文件")
    parser.add_argument("--species", default="", help="物种名")
    args = parser.parse_args()

    if args.paper:
        paper = json.loads(args.paper)
        result = score_paper(paper, args.species)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        papers = data if isinstance(data, list) else data.get("papers", [])
        scored = score_papers(papers, args.species)
        if args.output:
            if isinstance(data, dict):
                data["papers"] = scored
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(scored, f, ensure_ascii=False, indent=2)
            print(f"已写入 {args.output}")
        else:
            print(json.dumps(scored, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
