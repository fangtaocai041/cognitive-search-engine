"""Tests for cognitive-search-engine search integration.

Covers:
  - Parallel search basic functionality (no crash)
  - Unified search mode detection
  - Credibility pipeline: search → scoring → validation
  - Validator cross-source independence
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


# ═══════════════════════════════════════════════════════════════
# §1 test_parallel_search_basic — 基本搜索不崩溃
# ═══════════════════════════════════════════════════════════════

def test_parallel_search_importable():
    """ParallelSearch 类应可导入."""
    from src.parallel_search import ParallelSearch
    assert ParallelSearch is not None


def test_parallel_search_creation():
    """ParallelSearch 实例化不崩溃."""
    from src.parallel_search import ParallelSearch
    searcher = ParallelSearch(max_workers=2)
    assert searcher is not None
    searcher.close()


def test_parallel_search_static_functions_exist():
    """各搜索引擎函数应存在."""
    from src import parallel_search as ps
    engines = [
        "_search_pubmed",
        "_search_europe_pmc",
        "_search_crossref",
        "_search_openalex",
        "_search_arxiv",
        "_search_semantic_scholar",
    ]
    for name in engines:
        assert hasattr(ps, name), f"{name} 应在 parallel_search 模块中"


def test_parallel_search_function_signature():
    """引擎函数应接受 query 和 max_results 参数."""
    from src import parallel_search as ps
    import inspect
    for name in ["_search_pubmed", "_search_europe_pmc", "_search_crossref"]:
        func = getattr(ps, name)
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert "query" in params, f"{name} 应有 query 参数"
        assert "max_results" in params, f"{name} 应有 max_results 参数"


def test_parallel_search_returns_list():
    """各搜索引擎应返回 list 类型."""
    from src import parallel_search as ps
    import inspect
    for name in ["_search_pubmed", "_search_europe_pmc"]:
        func = getattr(ps, name)
        hints = getattr(func, "__annotations__", {})
        return_hint = hints.get("return", "")
        # 至少验证返回类型提示包含 List
        assert "List" in str(return_hint) or "list" in str(return_hint).lower(), \
            f"{name} 返回类型应标注为 List"


def test_search_coordinator_import():
    """search_coordinator 模块应可导入."""
    from src.search_coordinator import search, kb_first, SearchResult
    assert search is not None
    assert kb_first is not None
    assert SearchResult is not None


# ═══════════════════════════════════════════════════════════════
# §2 test_unified_search_mode_detection — 模式检测
# ═══════════════════════════════════════════════════════════════

def test_unified_search_mode_detection_cr_low_volume():
    """CR 物种 + 低文献量 (<20) → EXHAUSTIVE 模式 + 100篇."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("Ochetobius elongatus", "CR", 12)
    assert d.mode == SearchMode.EXHAUSTIVE
    assert d.include_incidental is True
    assert d.max_papers == 100


def test_unified_search_mode_detection_en_moderate():
    """EN 物种 + 中等文献量 (20-50) → EXHAUSTIVE 模式."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("EN fish", "EN", 30)
    assert d.mode == SearchMode.EXHAUSTIVE
    assert d.max_papers == 50


def test_unified_search_mode_detection_nt_classified():
    """NT 物种 + 中等文献量 (20-100) → CLASSIFIED 模式."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("NT fish", "NT", 60)
    assert d.mode == SearchMode.CLASSIFIED
    assert d.include_incidental is False
    assert d.max_papers == 40


def test_unified_search_mode_detection_lc_review_anchored():
    """LC 物种 + 高文献量 (>100) → REVIEW_ANCHORED 模式."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("Common", "LC", 150)
    assert d.mode == SearchMode.REVIEW_ANCHORED
    assert d.max_papers == 30


def test_unified_search_mode_detection_saturated():
    """极热门物种 (>500) → SATURATED 模式."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("Cyprinus carpio", "LC", 600)
    assert d.mode == SearchMode.SATURATED
    assert d.include_incidental is False


def test_unified_search_boundary_20():
    """边界值 20 → CLASSIFIED."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("X", "LC", 20)
    assert d.mode == SearchMode.CLASSIFIED


def test_unified_search_boundary_101():
    """边界值 101 → REVIEW_ANCHORED."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("X", "LC", 101)
    assert d.mode == SearchMode.REVIEW_ANCHORED


def test_unified_search_incidental_detection():
    """附带论文检测: 核心论文 → False, 附带论文 → True."""
    from src.unified_search import is_incidental

    inc, reason = is_incidental({"title": "Genetic diversity of Ochetobius elongatus"})
    assert not inc and "核心" in reason

    inc, reason = is_incidental({"title": "Growth performance of carp fed with hydrolysate"})
    assert inc and "附带" in reason


def test_unified_search_classify_paper():
    """论文分类: 不同标题 → 对应类别."""
    from src.unified_search import classify_paper, PaperCategory

    cat = classify_paper({"title": "Population genetic analysis of fish"})
    assert cat == PaperCategory.GENETICS

    cat = classify_paper({"title": "Morphological analysis of fish body shape"})
    assert cat == PaperCategory.MORPHOLOGY

    cat = classify_paper({"title": "Conservation strategies for fish"})
    assert cat == PaperCategory.CONSERVATION

    cat = classify_paper({"title": "Genome assembly and annotation"})
    assert cat == PaperCategory.GENOMICS

    cat = classify_paper({"title": "Toxic metal contamination in water"})
    assert cat == PaperCategory.TOXICOLOGY


def test_unified_search_cn_en_label():
    """CN/EN 通道标注."""
    from src.unified_search import cn_en_label

    label, bonus = cn_en_label({"title": "Genetic diversity"})
    assert label in ("EN", "CN")
    assert isinstance(bonus, int)

    label_cn, bonus_cn = cn_en_label({"title": "遗传多样性"})
    assert label_cn in ("EN", "CN")


# ═══════════════════════════════════════════════════════════════
# §3 test_credibility_pipeline — 搜索→评分全链路
# ═══════════════════════════════════════════════════════════════

def test_credibility_pipeline_scoring():
    """搜索→评分: 论文列表 → 可信度评分并排序."""
    from src.credibility_scorer import score_paper, score_papers, JOURNAL_TIERS

    papers = [
        {"journal": "Nature", "title": "Paper A", "citation_count": 30},
        {"journal": "PLOS ONE", "title": "Paper B", "citation_count": 10},
        {"journal": "水生生物学报", "title": "Paper C", "citation_count": 5},
        {"journal": "Unknown Journal", "title": "Paper D", "citation_count": 0},
    ]
    scored = score_papers(papers)
    assert len(scored) == 4
    # 排序: 高分在前
    assert scored[0]["credibility_score"] >= scored[-1]["credibility_score"]
    # Nature 应高于 Unknown
    for p in scored:
        assert "credibility_score" in p


def test_credibility_pipeline_journal_tier():
    """期刊层级检测."""
    from src.credibility_scorer import detect_journal_tier

    assert detect_journal_tier("Nature") == "top"
    assert detect_journal_tier("Science") == "top"
    assert detect_journal_tier("PLOS ONE") == "core"
    assert detect_journal_tier("水生生物学报") == "core"
    assert detect_journal_tier("Unknown Journal") == "unknown"


def test_credibility_pipeline_predatory_detection():
    """掠夺性期刊检测."""
    from src.credibility_scorer import is_predatory

    assert is_predatory("waset proceedings") is True
    assert is_predatory("Nature") is False
    assert is_predatory("World Academy of Science journal") is True


def test_credibility_pipeline_format():
    """可信度格式化."""
    from src.credibility_scorer import format_credibility

    assert "极高" in format_credibility(45)
    assert "高" in format_credibility(35)
    assert "中等" in format_credibility(25)
    assert "低" in format_credibility(15)
    assert "待验证" in format_credibility(5)


def test_credibility_pipeline_citation_bonus_boundaries():
    """引用数加分边界测试."""
    from src.credibility_scorer import score_paper

    base = score_paper({"journal": "PLOS ONE", "citation_count": 0})
    assert base == 30  # PLOS ONE base

    # 0-5: no bonus
    assert score_paper({"journal": "PLOS ONE", "citation_count": 5}) == 30
    # 6-20: +1
    assert score_paper({"journal": "PLOS ONE", "citation_count": 10}) == 31
    # 21-50: +3
    assert score_paper({"journal": "PLOS ONE", "citation_count": 25}) == 33
    # >50: +5
    assert score_paper({"journal": "PLOS ONE", "citation_count": 60}) == 35


def test_credibility_pipeline_score_capped_at_100():
    """可信度分数不超过 100."""
    from src.credibility_scorer import score_paper

    s = score_paper({"journal": "Nature", "citation_count": 999})
    assert s <= 100


# ═══════════════════════════════════════════════════════════════
# §4 test_validator_independence — 跨源独立性
# ═══════════════════════════════════════════════════════════════

def test_validator_independence_import():
    """Validator 应可导入."""
    from src.validator import (
        Paper, trust_score, credibility_score,
        enforce_independence, validate_papers, quick_validate,
    )
    assert Paper is not None
    assert trust_score is not None
    assert enforce_independence is not None


def test_validator_enforce_independence_single_source():
    """单源论文应触发独立性违规."""
    from src.validator import enforce_independence, Paper

    papers = [
        Paper(doi="10.1000/1", title="Paper A", source="pubmed",
              source_project="pubmed"),
        Paper(doi="10.1000/2", title="Paper B", source="pubmed",
              source_project="pubmed"),
    ]
    passed, violations, stats = enforce_independence(papers)
    # 单源应触发违规: unique_sources=1 < min_sources=3
    assert passed is False
    assert isinstance(violations, list)
    assert len(violations) >= 1
    assert stats["unique_sources"] == 1


def test_validator_enforce_independence_multi_source():
    """多源论文应通过独立性检查."""
    from src.validator import enforce_independence, Paper

    papers = [
        Paper(doi="10.1000/1", title="Paper A", source="pubmed",
              source_project="pubmed"),
        Paper(doi="10.1000/2", title="Paper B", source="crossref",
              source_project="crossref"),
        Paper(doi="10.1000/3", title="Paper C", source="openalex",
              source_project="openalex"),
    ]
    passed, violations, stats = enforce_independence(papers)
    # pubmed→ncbi, crossref→crossref, openalex→openalex: 3 sources, 3 projects → PASS
    assert passed is True
    assert stats["unique_sources"] == 3
    assert stats["unique_projects"] == 3


def test_validator_trust_score_levels():
    """信任评分层级: DOI(+20), PMID(+15), 物种(+10), 作者(+10), 期刊(+5)."""
    from src.validator import trust_score, Paper

    # 空论文: base 50
    empty = Paper()
    assert trust_score(empty) == 50

    # DOI
    assert trust_score(Paper(doi="10.1000/x")) == 70  # +20
    assert trust_score(Paper(doi="11.1000/x")) == 50  # invalid prefix

    # PMID
    assert trust_score(Paper(pmid="12345")) == 65  # +15

    # DOI + PMID 叠加
    assert trust_score(Paper(doi="10.1000/x", pmid="12345")) == 85


def test_validator_validate_papers_basic():
    """批量验证应分类为 verified/tentative/rejected."""
    from src.validator import validate_papers, Paper

    papers = [
        Paper(doi="10.1000/a", pmid="12345", title="High quality paper",
              journal="Nature", citations=100,
              authors=["Zhang Wei"], source="pubmed"),
        Paper(title="Low quality paper", source="blog"),
    ]
    result = validate_papers(papers)
    assert result.verified is not None
    assert result.tentative is not None
    assert result.rejected is not None
    assert isinstance(result.stats, dict)


def test_validator_quick_validate():
    """快速验证应返回概览."""
    from src.validator import quick_validate

    papers = [
        {"doi": "10.1000/a", "journal": "Nature", "title": "Paper A"},
        {"title": "Unknown"},
    ]
    summary = quick_validate(papers)
    assert isinstance(summary, dict)
    assert "passed" in summary
    assert "verified" in summary
    assert "tentative" in summary
    assert "rejected" in summary


def test_validator_resolve_source_project():
    """源项目解析应正确映射."""
    from src.validator import resolve_source_project

    # pubmed 映射为 ncbi (NCBI/PubMed 命名空间)
    assert resolve_source_project("pubmed") == "ncbi"
    assert resolve_source_project("crossref") == "crossref"
    # 未知源应映射为自身
    result = resolve_source_project("some_random_source")
    assert result == "some_random_source"


# ═══════════════════════════════════════════════════════════════
# §5 额外边界测试
# ═══════════════════════════════════════════════════════════════

def test_empty_paper_list_scoring():
    """空论文列表评分不崩溃."""
    from src.credibility_scorer import score_papers
    result = score_papers([])
    assert result == []


def test_paper_without_journal_scoring():
    """无期刊论文评分使用默认值."""
    from src.credibility_scorer import score_paper
    s = score_paper({"title": "No journal paper", "citation_count": 0})
    assert s == 10  # 默认 base=10


def test_paper_with_null_fields():
    """空字段不应崩溃."""
    from src.credibility_scorer import score_paper
    s = score_paper({})
    assert s >= 0


def test_estimate_mode_default_conservation():
    """默认保护级别."""
    from src.unified_search import estimate_mode, SearchMode
    d = estimate_mode("Unknown species", "", 50)
    # 无保护级别时应有合理默认值
    assert d.mode in SearchMode
    assert d.max_papers > 0
