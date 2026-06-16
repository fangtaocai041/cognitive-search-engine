"""Cognitive Search Engine — 全量文献搜索引擎 (V/V0).

多源并行搜索（Google Scholar + 中文期刊 + PubMed）+ 可信度评分 + 全文获取。
是 Triangle Core 的 V/V0 搜索验证层。

Usage:
    from src import get_search_engine
    engine = get_search_engine()
    results = engine.search("Ochetobius elongatus")
    print(results[0].title, results[0].credibility_score)
"""

__version__ = "3.2.0"
