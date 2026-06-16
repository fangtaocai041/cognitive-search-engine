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

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# 导入 unified_search 的规则引擎
# ═══════════════════════════════════════════════════════

try:
    from src.unified_search import (
        check_taxonomy, estimate_mode, is_incidental, classify_paper,
        cn_en_label, search_streaming, aggregate_results, ENGINE_REGISTRY,
        ENGINE_GROUPS, EngineResult, StreamEvent, SearchMode,
    )
    _HAVE_RULES = True
except ImportError:
    _HAVE_RULES = False


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

def search(species: str, group: str = "full", limit: int = 10) -> SearchResult:
    """
    search("鳤") → SearchResult

    统一入口: 分类学检查 → 模式决策 → 多引擎并行 → 规则分类 → 课题组优先
    """
    t0 = time.perf_counter()

    # 1. 分类学变更检查 (unified_search §7)
    try:
        variants = check_taxonomy(species)
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

    # 3. 多引擎并行搜索 — 直接调用 MCP 工具 (本会话可用)
    engine_results = _run_real_search(variants, group, limit)

    # 4. 合并 + 去重
    merged = aggregate_results(engine_results) if callable(aggregate_results) else {}
    all_papers = merged.get("papers", [])
    engine_stats = merged.get("stats", {})
    if not engine_stats:
        engine_stats = {"ok": 0, "degraded": 0, "error": 0}
        for r in engine_results:
            engine_stats[r.status] = engine_stats.get(r.status, 0) + 1

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
    )


# ═══════════════════════════════════════════════════════
# 内部辅助函数
# ═══════════════════════════════════════════════════════

def _run_real_search(variants: List[str], group: str, limit: int) -> List[EngineResult]:
    """实际调用 MCP 工具执行搜索。

    在 Reasonix 会话中, 所有 MCP 函数可直接调用 (globals()).
    在离线环境, 返回 degraded 状态。
    """
    engines = ENGINE_GROUPS.get(group, ENGINE_GROUPS["full"])
    results = []

    # 对每个变体×每个引擎依次调用
    for variant in variants[:3]:  # 最多3个变体
        for engine_id in engines:
            info = ENGINE_REGISTRY.get(engine_id, {})
            tool_name = info.get("tool", "")
            if not tool_name:
                continue

            t0 = time.perf_counter()
            er = EngineResult(engine=engine_id, query=variant, tool=tool_name)

            # 尝试从 globals() 获取MCP函数并调用
            fn = globals().get(tool_name)
            if fn is None:
                # 尝试 __builtins__
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
    except Exception:
        pass
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
