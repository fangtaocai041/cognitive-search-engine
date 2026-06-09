"""
Parallel Search Executor — Multi-query concurrent species search.

Core of the 12-layer protocol's multi-query parallelism:
  - All queries (exact name + variants + Chinese + ecology keywords) fire simultaneously
  - Results merge with DOI-deduplication
  - Supports asyncio (true I/O parallelism) and threading (fallback)

Usage:
    from src.parallel_search import ParallelSearch

    searcher = ParallelSearch(mode="http")
    results = await searcher.search_all([
        "Ochetobius elongatus",
        "Ochetobibus elongatus",
        "鳤",
        "Ochetobius elongatus ecology",
    ])
"""

import asyncio
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class SearchResult:
    query: str
    papers: list[dict] = field(default_factory=list)
    source: str = ""
    error: Optional[str] = None
    elapsed_ms: float = 0.0
    paper_count: int = 0


@dataclass
class MergeStats:
    total_raw: int = 0
    unique: int = 0
    deduped: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    new_papers: list[dict] = field(default_factory=list)


# ──── Search Provider Registry ────

SearchFn = Callable[[str, int], list[dict]]

SEARCH_PROVIDERS: dict[str, SearchFn] = {}


def register_provider(name: str):
    """Decorator: register a search provider (e.g. pubmed, crossref)."""
    def decorator(fn: SearchFn):
        SEARCH_PROVIDERS[name] = fn
        return fn
    return decorator


# ──── Parallel Search Engine ────

class ParallelSearch:
    """Execute multiple search queries concurrently and merge results."""

    def __init__(self, mode: str = "http",
                 max_workers: int = 4,
                 providers: Optional[list[str]] = None):
        """
        Args:
            mode: "http" (REST APIs), "mock" (test data), "mcp" (MCP servers)
            max_workers: Max concurrent search threads/connections
            providers: Which providers to use (default: all registered)
        """
        self.mode = mode
        self.max_workers = max_workers
        self.providers = providers or list(SEARCH_PROVIDERS.keys())
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def search_all(self, queries: list[str],
                   max_per_query: int = 20,
                   dedup: bool = True) -> MergeStats:
        """
        Execute all queries concurrently, merge results.

        Args:
            queries: List of search query strings
            max_per_query: Max results per query
            dedup: Deduplicate merged results by DOI

        Returns:
            MergeStats with unique papers and per-source breakdown
        """
        futures = {}
        for q in queries:
            future = self._pool.submit(self._search_single, q, max_per_query)
            futures[future] = q

        all_results: list[SearchResult] = []
        for future in as_completed(futures):
            q = futures[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                all_results.append(SearchResult(query=q, error=str(e)))

        return self._merge(all_results, dedup)

    async def search_all_async(self, queries: list[str],
                                max_per_query: int = 20,
                                dedup: bool = True) -> MergeStats:
        """Async version — uses asyncio for true I/O concurrency."""
        tasks = [self._search_single_async(q, max_per_query) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[SearchResult] = []
        for q, r in zip(queries, results):
            if isinstance(r, Exception):
                all_results.append(SearchResult(query=q, error=str(r)))
            else:
                all_results.append(r)

        return self._merge(all_results, dedup)

    def _search_single(self, query: str, n: int) -> SearchResult:
        """Execute a single query across all registered providers."""
        start = time.time()
        all_papers: list[dict] = []
        errors: list[str] = []

        for provider_name in self.providers:
            fn = SEARCH_PROVIDERS.get(provider_name)
            if not fn:
                continue
            try:
                papers = fn(query, n)
                for p in papers:
                    p["_source"] = provider_name
                all_papers.extend(papers)
            except Exception as e:
                errors.append(f"{provider_name}: {e}")

        elapsed = (time.time() - start) * 1000
        return SearchResult(
            query=query,
            papers=all_papers,
            elapsed_ms=elapsed,
            paper_count=len(all_papers),
            error="; ".join(errors) if errors else None,
        )

    async def _search_single_async(self, query: str, n: int) -> SearchResult:
        """Async single query via run_in_executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._pool, self._search_single, query, n
        )

    def _merge(self, results: list[SearchResult],
               dedup: bool) -> MergeStats:
        """Merge results, deduplicate, return stats."""
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[dict] = []
        by_source: dict[str, int] = {}
        total_raw = 0

        for r in results:
            for p in r.papers:
                total_raw += 1
                source = p.get("_source", "unknown")
                by_source[source] = by_source.get(source, 0) + 1

                if not dedup:
                    unique.append(p)
                    continue

                doi = (p.get("doi", "") or "").lower().strip()
                title = (p.get("title", "") or "").lower().strip()[:80]

                key = doi if doi else title
                if key and key not in seen_dois:
                    seen_dois.add(key)
                    seen_titles.add(title)
                    unique.append(p)

        return MergeStats(
            total_raw=total_raw,
            unique=len(unique),
            deduped=total_raw - len(unique),
            by_source=by_source,
            new_papers=unique,
        )

    def close(self):
        self._pool.shutdown(wait=False)


# ──── HTTP Search Providers ────

@register_provider("pubmed")
def search_pubmed(query: str, n: int = 20) -> list[dict]:
    """Search PubMed via NCBI E-utilities."""
    try:
        esearch_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            f"db=pubmed&term={urllib.parse.quote(query)}&retmax={n}&retmode=json"
        )
        with urllib.request.urlopen(esearch_url, timeout=15) as resp:
            esearch_data = json.loads(resp.read())

        id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        ids = ",".join(id_list[:n])
        esummary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"db=pubmed&id={ids}&retmode=json"
        )
        with urllib.request.urlopen(esummary_url, timeout=15) as resp:
            summary_data = json.loads(resp.read())

        papers = []
        result = summary_data.get("result", {})
        for uid in id_list:
            item = result.get(uid, {})
            if not item:
                continue
            authors = [
                a.get("name", "") for a in item.get("authors", [])
                if "name" in a
            ]
            papers.append({
                "doi": (item.get("elocationid") or "").replace("doi: ", ""),
                "title": item.get("title", ""),
                "year": item.get("pubdate", "")[:4],
                "journal": item.get("source", ""),
                "authors": authors,
                "pmid": uid,
                "abstract": item.get("abstract", ""),
            })
        return papers
    except Exception:
        return []


@register_provider("crossref")
def search_crossref(query: str, n: int = 20) -> list[dict]:
    """Search Crossref REST API."""
    try:
        url = (
            "https://api.crossref.org/works?"
            f"query={urllib.parse.quote(query)}&rows={n}"
        )
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())

        papers = []
        for item in data.get("message", {}).get("items", []):
            doi = item.get("DOI", "")
            title_list = item.get("title", [])
            author_list = item.get("author", [])
            papers.append({
                "doi": f"10.{doi}" if doi and not doi.startswith("10.") else doi,
                "title": title_list[0] if title_list else "",
                "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0]
                        or item.get("created", {}).get("date-parts", [[None]])[0][0],
                "journal": (item.get("container-title") or [""])[0],
                "authors": [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in author_list
                ],
                "publisher": item.get("publisher", ""),
                "type": item.get("type", ""),
                "citations": item.get("is-referenced-by-count", 0),
            })
        return papers
    except Exception:
        return []


@register_provider("openalex")
def search_openalex(query: str, n: int = 20) -> list[dict]:
    """Search OpenAlex API."""
    try:
        url = (
            "https://api.openalex.org/works?"
            f"search={urllib.parse.quote(query)}&per_page={n}"
        )
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())

        papers = []
        for item in data.get("results", []):
            doi = item.get("doi", "").replace("https://doi.org/", "")
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in item.get("authorships", [])
            ]
            papers.append({
                "doi": doi,
                "title": item.get("title", ""),
                "year": item.get("publication_year"),
                "journal": (item.get("primary_location") or {})
                           .get("source", {}).get("display_name", ""),
                "authors": authors,
                "citations": item.get("cited_by_count", 0),
                "open_access": item.get("open_access", {}).get("is_oa", False),
            })
        return papers
    except Exception:
        return []


@register_provider("openalex_references")
def search_openalex_references(doi: str, n: int = 20) -> list[dict]:
    """通过 OpenAlex API 获取一篇论文的参考文献。

    输入: DOI or identifier (如 "10.3390/ani16091369")
    输出: 引用该论文的其他论文列表 (引用回溯)
    """
    try:
        import json as _json
        from urllib.request import urlopen, Request
        from urllib.parse import quote

        doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        url = f"https://api.openalex.org/works/doi:{quote(doi_clean)}?select=referenced_works"
        req = Request(url, headers={"User-Agent": "Reasonix/1.0"})
        with urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())

        ref_ids = data.get("referenced_works", [])[:n]
        if not ref_ids:
            return []

        papers = []
        for wid in ref_ids:
            try:
                wurl = f"https://api.openalex.org/works/{wid}"
                with urlopen(Request(wurl, headers={"User-Agent": "Reasonix/1.0"}), timeout=10) as wresp:
                    wdata = _json.loads(wresp.read())
                doi_val = (wdata.get("doi") or "").replace("https://doi.org/", "")
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in wdata.get("authorships", [])
                ]
                papers.append({
                    "doi": doi_val,
                    "title": wdata.get("title", ""),
                    "year": wdata.get("publication_year"),
                    "journal": (wdata.get("primary_location") or {})
                               .get("source", {}).get("display_name", ""),
                    "authors": authors,
                    "_source_api": "openalex_references",
                })
            except Exception:
                continue
        return papers
    except Exception:
        return []


# ═══════════════════════════════════════════════════════
# 中文搜索提供者 (v2.0 - 填补 PubMed/Crossref 盲区)
# ═══════════════════════════════════════════════════════

@register_provider("baidu_scholar")
def search_baidu_scholar(query: str, n: int = 20) -> list[dict]:
    """搜索百度学术 (Baidu Scholar) — 中文论文检索。

    ⚠️ 百度有反爬 CAPTCHA，此函数可能返回空列表。
    改用 search_bing_web() + search_crossref() 代替。

    HTTP GET → Baidu Scholar → 正则解析 HTML
    """
    try:
        url = (
            "https://xueshu.baidu.com/s?"
            f"wd={urllib.parse.quote(query)}&pn=0&tn=SE_baiduxueshu_c1g0"
            f"&ie=utf-8&sc_hit=1"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        if "安全验证" in html or "captcha" in html.lower():
            return []  # CAPTCHA blocked

        papers = []
        blocks = re.findall(
            r'<div\s+class="result"[^>]*>(.*?)</div>\s*</div>',
            html, re.DOTALL
        )
        for block in blocks[:n]:
            try:
                title_match = re.search(
                    r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    block, re.DOTALL
                )
                if not title_match:
                    continue
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                info_text = re.sub(r'<[^>]+>', ' ', block)
                info_text = re.sub(r'\s+', ' ', info_text)
                year_match = re.search(r'(19\d{2}|20\d{2})', info_text)
                year = int(year_match.group(1)) if year_match else None
                papers.append({
                    "doi": "",
                    "title": title,
                    "year": year,
                    "journal": "",
                    "authors": [],
                    "_source": "baidu_scholar",
                })
            except Exception:
                continue
        return papers
    except Exception:
        return []


@register_provider("bing_web")
def search_bing_web(query: str, n: int = 10) -> list[dict]:
    """搜索 Bing Web — 通用网页搜索 (中文优先)。"""
    try:
        url = (
            "https://www.bing.com/search?"
            f"q={urllib.parse.quote(query)}&count={n}"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        papers = []
        blocks = re.findall(
            r'<li\s+class="b_algo"[^>]*>(.*?)</li>',
            html, re.DOTALL
        )
        for block in blocks[:n]:
            try:
                title_match = re.search(
                    r'<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    block, re.DOTALL
                )
                if not title_match:
                    continue
                link = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                snippet_match = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
                snippet = re.sub(r'<[^>]+>|\s+', ' ', snippet_match.group(1)).strip() if snippet_match else ""
                papers.append({
                    "doi": "",
                    "title": title,
                    "year": None,
                    "journal": "Bing Web",
                    "authors": [],
                    "source_url": link,
                    "abstract": snippet[:300],
                    "_source": "bing_web",
                })
            except Exception:
                continue
        return papers
    except Exception:
        return []


# ──── MCP → HTTP Fallback Registry ────

MCP_HTTP_FALLBACK = {
    "scholar_search_literature_graph": search_openalex,
    "scholar_search_google_scholar_key_words": search_openalex,
    "ncbi_ncbi_esearch": search_pubmed,
    "ncbi_ncbi_esummary": lambda q, n: search_pubmed(q, n),
    "article_search_literature": lambda q, n: search_pubmed(q, n) + search_crossref(q, n),
    "article_get_article_details": lambda q, n: search_pubmed(q, n),
    "article_get_references": lambda q, n: search_openalex_references(q, n),
    "article_get_literature_relations": lambda q, n: search_openalex(q, n),
    "scholarly_research_search": search_openalex,
    "tavily_tavily_search": search_bing_web,
    "exa_web_search_exa": search_bing_web,
    "web_search": search_bing_web,
    "chinese_search": lambda q, n: search_bing_web(q + " 论文", n) + search_crossref(q, n),
}


# ──── Utility ────

def build_search_queries(genus: str, species: str,
                          chinese_name: str = "",
                          variants: Optional[list[str]] = None,
                          keywords: Optional[list[str]] = None) -> list[str]:
    """Build the full set of search queries for a species.

    This is the Layer 0 → Layer 1 → Layer 2 → Layer 4 query builder
    from the 12-layer protocol. Returns all queries to run in parallel.

    Args:
        genus: Genus name (e.g. "Ochetobius")
        species: Species epithet (e.g. "elongatus")
        chinese_name: Chinese common name (e.g. "鳤")
        variants: Known spelling variants
        keywords: Ecology keywords (e.g. ["diet", "habitat"])

    Returns:
        List of query strings ready for parallel execution
    """
    queries = []

    # Layer 1: Exact scientific name
    full_name = f"{genus} {species}"
    queries.append(full_name)

    # Layer 1+: Scientific name + ecology keywords
    for kw in (keywords or []):
        queries.append(f"{full_name} {kw}")

    # Layer 2: Known variants
    for v in (variants or []):
        queries.append(f'"{v}"')

    # Layer 4: Chinese name
    if chinese_name:
        queries.append(chinese_name)

    # Layer 4+: Chinese name + scientific name
    if chinese_name:
        queries.append(f"{chinese_name} {full_name}")

    return queries


# ──── CLI / Quick Test ────

if __name__ == "__main__":
    import sys
    queries = sys.argv[1:] if len(sys.argv) > 1 else [
        "Ochetobius elongatus",
        "Ochetobibus elongatus",
        "鳤",
    ]
    searcher = ParallelSearch(mode="http")
    stats = searcher.search_all(queries, max_per_query=10)
    print(f"Queries: {len(queries)}")
    print(f"Total raw: {stats.total_raw}")
    print(f"Unique: {stats.unique}")
    print(f"By source: {stats.by_source}")
    for p in stats.new_papers[:5]:
        print(f"  • {p.get('title', '?')[:80]} ({p.get('doi', 'no DOI')})")
    searcher.close()
