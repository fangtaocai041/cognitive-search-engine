#!/usr/bin/env python3
"""
kb_to_graph_sync.py — 图谱写回 (lit-search §3.1)

将搜索结果写回到 species_graph.yaml, 实现:
  - 新论文条目插入
  - 现有论文的 authors_zh 字段补全 (ZN/EN 双署名)
  - 图谱健康度报告

用法:
  python scripts/kb_to_graph_sync.py --species "鳤" --papers papers.json
  python scripts/kb_to_graph_sync.py --health-check
  python scripts/kb_to_graph_sync.py --backup
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


ENGINE_ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ENGINE_ROOT / "config" / "species_graph.yaml"


def load_graph() -> List[Dict]:
    """加载物种图谱."""
    if not GRAPH_PATH.exists():
        print(f"❌ 图谱文件不存在: {GRAPH_PATH}")
        return []
    try:
        with open(GRAPH_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("graph", {}).get("species", [])
    except Exception as e:
        print(f"❌ 加载图谱失败: {e}")
        return []


def _find_species(species_list: List[Dict], name: str) -> Optional[Dict]:
    """在物种列表中按学名或中文名查找."""
    name_lower = name.lower().replace(" ", "_")
    for s in species_list:
        sid = s.get("id", "").lower()
        if name_lower == sid:
            return s
        if s.get("chinese", "") == name:
            return s
        if s.get("name", "").lower() == name_lower:
            return s
        variants = [v.lower() for v in s.get("variants", [])]
        if name_lower in variants:
            return s
    return None


def sync_papers(species_name: str, papers: List[Dict], dry_run: bool = False) -> int:
    """将论文列表同步至图谱.

    Args:
        species_name: 物种名 (学名或中文名)
        papers: 论文列表
        dry_run: 试运行 (不实际写入)

    Returns:
        新增论文数
    """
    if yaml is None:
        print("❌ 需要 pyyaml: pip install pyyaml")
        return 0

    species_list = load_graph()
    if not species_list:
        return 0

    target = _find_species(species_list, species_name)
    if target is None:
        print(f"❌ 未找到物种: {species_name}")
        return 0

    existing_papers = target.get("papers", [])
    existing_dois = {p.get("doi", "").lower() for p in existing_papers if p.get("doi")}
    new_count = 0

    for paper in papers:
        doi = (paper.get("doi") or "").lower().strip()
        if doi and doi in existing_dois:
            continue  # 已存在

        # 构建新论文条目
        entry: Dict[str, Any] = {
            "title": paper.get("title", ""),
            "year": paper.get("year", 0),
            "journal": paper.get("journal", ""),
            "authors": paper.get("authors", []),
            "source": paper.get("source", "auto_sync"),
        }
        if doi:
            entry["doi"] = doi
            existing_dois.add(doi)
        if paper.get("pmid"):
            entry["pmid"] = paper["pmid"]

        # ZN/EN 双署名 (如果中文作者信息存在)
        authors_zh = paper.get("authors_zh", [])
        if authors_zh:
            entry["authors_zh"] = authors_zh

        # 中文标题
        title_zh = paper.get("title_zh", "")
        if title_zh:
            entry["title_zh"] = title_zh

        existing_papers.append(entry)
        new_count += 1

    target["papers"] = existing_papers

    if dry_run:
        print(f"🔍 试运行: 将新增 {new_count} 篇论文 (未写入)")
        return new_count

    # 写回 YAML
    try:
        with open(GRAPH_PATH, "r", encoding="utf-8") as f:
            full_data = yaml.safe_load(f) or {}
        if "graph" not in full_data:
            full_data["graph"] = {}
        if "species" not in full_data["graph"]:
            full_data["graph"]["species"] = []
        full_data["graph"]["species"] = species_list
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            yaml.dump(full_data, f, allow_unicode=True, default_flow_style=False)
        print(f"✅ 已写入 {new_count} 篇新论文到 {GRAPH_PATH.name}")
    except Exception as e:
        print(f"❌ 写入失败: {e}")
        return 0

    return new_count


def health_check() -> Dict:
    """生成图谱健康度报告."""
    species_list = load_graph()
    total_species = len(species_list)
    total_papers = 0
    species_with_gaps = 0
    gaps = []

    for s in species_list:
        papers = s.get("papers", [])
        total_papers += len(papers)

        # 检查 ZN/EN 双署名缺口
        for p in papers:
            journal = p.get("journal", "")
            authors_zh = p.get("authors_zh", [])
            is_chinese_journal = any(
                cn in journal
                for cn in [
                    "水生生物学报", "中国水产科学", "水产学报",
                    "生物多样性", "湖泊科学", "生态学报", "生态科学",
                    "南方水产科学",
                ]
            )
            if is_chinese_journal and not authors_zh:
                species_with_gaps += 1
                title = p.get("title", "")[:50]
                gaps.append(
                    f"  {s.get('chinese', s.get('name'))}: "
                    f"'{title}' 缺少 authors_zh"
                )
                break  # 每个物种只记一次

    report = {
        "total_species": total_species,
        "total_papers": total_papers,
        "species_with_zn_gap": species_with_gaps,
        "gaps": gaps[:10],  # 最多显示10条
        "timestamp": datetime.now().isoformat(),
    }
    return report


def backup() -> str:
    """创建图谱文件备份."""
    if not GRAPH_PATH.exists():
        return ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = GRAPH_PATH.parent / f"species_graph_{ts}.yaml"
    shutil.copy2(GRAPH_PATH, backup_path)
    return str(backup_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="图谱写回工具")
    parser.add_argument("--species", help="物种名")
    parser.add_argument("--papers", help="论文 JSON 文件")
    parser.add_argument("--dry-run", action="store_true", help="试运行 (不写入)")
    parser.add_argument("--health-check", action="store_true", help="图谱健康检查")
    parser.add_argument("--backup", action="store_true", help="创建图谱备份")
    args = parser.parse_args()

    if args.health_check:
        report = health_check()
        print(f"📊 图谱健康度 ({report['timestamp']})")
        print(f"  物种数: {report['total_species']}")
        print(f"  论文数: {report['total_papers']}")
        print(f"  ZN/EN 双署名缺口: {report['species_with_zn_gap']}")
        for g in report["gaps"]:
            print(f"    {g}")
        return

    if args.backup:
        path = backup()
        if path:
            print(f"✅ 已备份到: {path}")
        else:
            print("❌ 备份失败: 图谱文件不存在")
        return

    if args.species and args.papers:
        with open(args.papers, encoding="utf-8") as f:
            papers = json.load(f)
        papers_list = papers if isinstance(papers, list) else papers.get("papers", [])
        count = sync_papers(args.species, papers_list, args.dry_run)
        print(f"  处理完成: {count} 篇新论文")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
