#!/usr/bin/env python3
"""
search_api.py — cognitive-search-engine CLI API (供 search_species.py 调用)

═══════════════════════════════════════════════════════════
框架角色: c项目搜索引擎 (V/V1 · 搜索验证层)
═══════════════════════════════════════════════════════════

  标准工作流: f项目(search_species.py) → 本脚本 → 结果回写f知识库
  ⚠️ 不要直接调用本脚本！正确入口是 f项目的 search_species.py
     它会先查 f知识库 → 询问用户 → 再调用本脚本 → 自动回写

  协议: subprocess → JSON stdout
  管线: 分类学变体 → 跨项目检测 → 7引擎并行 → DOI去重 → 分类标注

用法:
  python scripts/search_api.py --species "Pseudaspius hakonensis"
  python scripts/search_api.py --species "珠星三块鱼" --format json --max 20
  python scripts/search_api.py --species "Ochetobius elongatus" --group full

返回 JSON schema:
  {
    "status": "ok" | "error",
    "species": { "query", "scientific", "chinese", "family", "variants" },
    "taxonomy_discrepancy": null | { "field", "c_value", "f_value", "note" },
    "papers": [ { "doi", "title", "year", "journal", "authors", "source", ... } ],
    "stats": { "total_raw", "total_merged", "phase_count", "elapsed_s" }
  }

退出码: 0=成功, 1=参数错误, 2=搜索异常
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 确保引擎根目录在 sys.path
ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))


def _load_species_info(name: str) -> Dict[str, Any]:
    """从 species_graph.yaml 加载物种元数据。"""
    try:
        import yaml
        graph_path = ENGINE_ROOT / "config" / "species_graph.yaml"
        if not graph_path.exists():
            return {}
        with open(graph_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        name_lower = name.lower().replace(" ", "_")
        for s in data.get("graph", {}).get("species", []):
            sid = s.get("id", "").lower()
            if name_lower in sid or name_lower in s.get("name", "").lower():
                return s
        # 中文名匹配
        for s in data.get("graph", {}).get("species", []):
            if s.get("chinese", "") == name:
                return s
        return {}
    except Exception:
        return {}


def get_variants(name: str) -> List[str]:
    """获取所有搜索名（学名 + 变体 + 中文名）。"""
    try:
        from src.unified_search import check_taxonomy
        return check_taxonomy(name)
    except ImportError:
        pass
    # 离线兜底: 直接从 YAML 读取
    info = _load_species_info(name)
    if info:
        result = [info.get("name", name)]
        result.extend(info.get("variants", []))
        chinese = info.get("chinese", "")
        if chinese:
            result.append(chinese)
        return result
    return [name]


def detect_taxonomy_gap(name: str) -> Optional[Dict[str, Any]]:
    """检测 c项目 与 f项目 之间的分类学不一致。"""
    try:
        from src.unified_search import detect_taxonomy_discrepancy
        return detect_taxonomy_discrepancy(name)
    except ImportError:
        pass
    return None


def search_http(queries: List[str], max_per_query: int = 20) -> List[Dict]:
    """使用 parallel_search HTTP 并行搜索所有源。

    支持的源: pubmed, europe_pmc, crossref, openalex, arxiv, cnki_web
    """
    try:
        from src.parallel_search import ParallelSearch
        searcher = ParallelSearch(max_workers=4)
        stats = searcher.search_all(queries, max_per_query=max_per_query)
        searcher.close()
        return stats.new_papers
    except Exception as e:
        return [{"error": str(e), "source": "http_fallback"}]


def search_mcp_fallback(queries: List[str], limit: int = 20) -> List[Dict]:
    """尝试 MCP 模式 (Reasonix runtime 中可用)。

    在 Reasonix Desktop 中，scholar_search_literature_graph 工具会被注入。
    CLI 环境中回退到 HTTP 搜索。
    """
    # 检测 MCP 工具是否注入 (Reasonix Desktop runtime)
    try:
        from src.unified_search import coordinated_search
        result = coordinated_search(
            species_name=queries[0] if queries else "",
            scientific_name=queries[0] if queries else "",
            group="standard",
            limit=limit,
        )
        if hasattr(result, "papers") and result.papers:
            return [p.__dict__ if hasattr(p, "__dict__") else p for p in result.papers]
    except (ImportError, AttributeError):
        pass

    # Fallback: check for MCP-injected globals
    mcp_tool = globals().get("scholar_search_literature_graph")
    if callable(mcp_tool):
        papers = []
        for q in queries[:3]:
            try:
                result = mcp_tool(query=q, limit=min(limit, 20))
                if isinstance(result, list):
                    papers.extend(result)
            except Exception:
                pass
        if papers:
            return papers

    # 回退到 HTTP
    return search_http(queries, limit)


def classify_papers(papers: List[Dict]) -> List[Dict]:
    """为论文添加学科分类和 CN/EN 标签。"""
    try:
        from src.unified_search import classify_paper, cn_en_label
        for p in papers:
            try:
                p["category"] = classify_paper(p)
                p["lang"] = cn_en_label(p)
            except Exception:
                p["category"] = "unclassified"
                p["lang"] = "unknown"
    except Exception:
        pass
    return papers


def run_search(species_name: str, max_results: int = 20,
               group: str = "standard") -> Dict[str, Any]:
    """
    执行完整搜索管线并返回结构化结果。

    管线:
      1. 分类学检查 → 获取所有变体
      2. 跨项目不一致检测
      3. 并行 HTTP 搜索 (PubMed + Europe PMC + Crossref + OpenAlex + CN)
      4. DOI 去重 + 分类 + 语言标注
    """
    t0 = time.perf_counter()

    # Step 1: 分类学变体
    variants = get_variants(species_name)
    scientific_name = variants[0] if variants else species_name

    # Step 2: 物种元数据
    info = _load_species_info(scientific_name)
    chinese_name = info.get("chinese", "")
    if not chinese_name and species_name != scientific_name:
        chinese_name = species_name

    # Step 3: 跨项目不一致检测
    taxonomy_gap = detect_taxonomy_gap(scientific_name)

    # Step 4: 搜索
    search_queries = list(variants[:3])  # 最多3个学名变体
    if chinese_name and chinese_name not in search_queries:
        search_queries.append(chinese_name)
    # 追加 ecology 关键词
    if len(search_queries) < 5:
        search_queries.append(f"{scientific_name} ecology")
        search_queries.append(f"{scientific_name} genetics morphology")

    papers = search_http(search_queries, max_per_query=max_results)

    # Step 5: DOI去重
    seen_doi: set = set()
    deduped: List[Dict] = []
    for p in papers:
        doi = (p.get("doi") or "").lower().strip()
        if doi and doi in seen_doi:
            continue
        if doi:
            seen_doi.add(doi)
        deduped.append(p)

    # Step 6: 分类 + 语言标注
    classify_papers(deduped)

    elapsed = time.perf_counter() - t0

    return {
        "status": "ok",
        "species": {
            "query": species_name,
            "scientific": scientific_name,
            "chinese": chinese_name or info.get("chinese", ""),
            "family": info.get("family", ""),
            "conservation": info.get("conservation", ""),
            "variants": variants,
        },
        "taxonomy_discrepancy": taxonomy_gap,
        "papers": deduped[:max_results * 2],  # 上限
        "stats": {
            "total_raw": len(papers),
            "total_merged": len(deduped),
            "max_requested": max_results,
            "elapsed_s": round(elapsed, 2),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="cognitive-search-engine CLI API — 供 f 项目调用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/search_api.py --species "Pseudaspius hakonensis"
  python scripts/search_api.py --species "珠星三块鱼" --max 10
  python scripts/search_api.py --species "Ochetobius elongatus" --group full
        """,
    )
    parser.add_argument("--species", required=True,
                        help="物种名 (学名或中文名)")
    parser.add_argument("--max", type=int, default=20,
                        help="每个查询最大结果数 (默认20)")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json",
                        help="输出格式 (默认json)")
    parser.add_argument("--group", choices=["standard", "full", "minimal"],
                        default="standard",
                        help="搜索深度组 (standard/full/minimal)")
    parser.add_argument("--taxonomy-only", action="store_true",
                        help="仅返回分类学信息，不执行搜索")

    args = parser.parse_args()

    if args.taxonomy_only:
        variants = get_variants(args.species)
        info = _load_species_info(variants[0] if variants else args.species)
        taxonomy_gap = detect_taxonomy_gap(variants[0] if variants else args.species)
        result = {
            "status": "ok",
            "species": {
                "query": args.species,
                "scientific": variants[0] if variants else args.species,
                "chinese": info.get("chinese", ""),
                "family": info.get("family", ""),
                "conservation": info.get("conservation", ""),
                "variants": variants,
            },
            "taxonomy_discrepancy": taxonomy_gap,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    try:
        result = run_search(args.species, max_results=args.max, group=args.group)
    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "species": {"query": args.species},
            "papers": [],
            "stats": {},
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(2)

    if args.format == "jsonl":
        # 先输出 header
        header = {k: v for k, v in result.items() if k != "papers"}
        print(json.dumps(header, ensure_ascii=False))
        # 每行一篇论文
        for p in result.get("papers", []):
            print(json.dumps(p, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
