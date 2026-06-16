"""
ParallelSearch — 多源 HTTP 并行搜索模块

替代 MCP 无法使用时的 HTTP 直连搜索。
支持 PubMed E-utilities、Europe PMC、Crossref、OpenAlex、CNKI/Bing。
在 Reasonix 外部 CLI 环境中也可独立运行。

用法:
    from src.parallel_search import ParallelSearch

    searcher = ParallelSearch(max_workers=4)
    papers = searcher.search("Ochetobius elongatus")
    searcher.close()

返回统一的论文 dict 格式:
    { "doi", "title", "authors": [], "year", "journal", "abstract",
      "source", "pmid", "pmcid", "url", "credibility_score" }
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── User-Agent ──────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": "ReasonixCognitiveSearch/5.8 (fangtaocai041@gmail.com)",
    "Accept": "application/json",
}

_TIMEOUT_S = 15  # per-provider timeout


# ═══════════════════════════════════════════════════════════════
# Provider: PubMed (E-utilities)
# ═══════════════════════════════════════════════════════════════

def _search_pubmed(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Search PubMed via NCBI E-utilities (esearch + esummary).

    Free API, no key required. Rate limit ~3/s.
    """
    papers: List[Dict[str, Any]] = []
    try:
        # Step 1: esearch — get PMIDs
        esearch_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
            + urllib.parse.urlencode({
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            })
        )
        req = urllib.request.Request(esearch_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            esearch_data = json.loads(resp.read())

        id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return papers

        # Step 2: esummary — get metadata
        esummary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            + urllib.parse.urlencode({
                "db": "pubmed",
                "id": ",".join(id_list[:max_results]),
                "retmode": "json",
            })
        )
        req = urllib.request.Request(esummary_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            esummary_data = json.loads(resp.read())

        for pmid in id_list:
            record = esummary_data.get("result", {}).get(pmid, {})
            if not record:
                continue
            authors = []
            for a in record.get("authors", []):
                if isinstance(a, dict):
                    name = a.get("name", "")
                    if name:
                        authors.append(name)
                elif isinstance(a, str):
                    authors.append(a)

            doi = ""
            for aid in record.get("articleids", record.get("elocationid", "")):
                if isinstance(aid, dict) and aid.get("idtype", "").lower() == "doi":
                    doi = aid.get("value", "")
                elif isinstance(aid, str) and aid.startswith("doi:"):
                    doi = aid[4:]
                elif isinstance(aid, str):
                    pass

            paper = {
                "doi": doi,
                "title": record.get("title", ""),
                "authors": authors,
                "year": record.get("pubdate", "")[:4],
                "journal": record.get("source", ""),
                "abstract": record.get("abstract", ""),
                "source": "pubmed",
                "pmid": pmid,
                "pmcid": "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "credibility_score": 60,
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"PubMed search failed for '{query}': {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: Europe PMC
# ═══════════════════════════════════════════════════════════════

def _search_europe_pmc(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Search Europe PMC REST API.

    Free API, no key required. Returns rich metadata.
    """
    papers: List[Dict[str, Any]] = []
    try:
        url = (
            "https://www.ebi.ac.uk/europepmc/api/search?"
            + urllib.parse.urlencode({
                "query": query,
                "pageSize": max_results,
                "format": "json",
                "resultType": "core",
            })
        )
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read())

        for result in data.get("resultList", {}).get("result", []):
            doi = result.get("doi", "") or ""
            paper = {
                "doi": doi,
                "title": result.get("title", ""),
                "authors": [a.get("fullName", "") for a in result.get("authorList", {}).get("author", []) if a.get("fullName")],
                "year": str(result.get("firstPublicationDate", ""))[:4],
                "journal": result.get("journalTitle", result.get("bookOrReportDetails", {}).get("publisher", "")),
                "abstract": result.get("abstractText", ""),
                "source": "europe_pmc",
                "pmid": str(result.get("pmid", "")),
                "pmcid": result.get("pmcid", ""),
                "url": f"https://europepmc.org/article/med/{result.get('pmid', '')}",
                "credibility_score": 55,
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"Europe PMC search failed for '{query}': {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: Crossref
# ═══════════════════════════════════════════════════════════════

def _search_crossref(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Search Crossref REST API.

    Polite pool: free. Include mailto for better priority.
    """
    papers: List[Dict[str, Any]] = []
    try:
        params = {"query": query, "rows": max_results}
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            **_HEADERS,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read())

        for item in data.get("message", {}).get("items", []):
            doi = item.get("DOI", "")
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                if family:
                    authors.append(f"{given} {family}" if given else family)
            paper = {
                "doi": doi if doi else "",
                "title": (item.get("title") or [""])[0],
                "authors": authors,
                "year": str(item.get("published-print", {}).get("date-parts", [[0]])[0][0]
                           or item.get("created", {}).get("date-parts", [[0]])[0][0]),
                "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "abstract": item.get("abstract", ""),
                "source": "crossref",
                "pmid": "",
                "pmcid": "",
                "url": f"https://doi.org/{doi}" if doi else "",
                "credibility_score": 50,
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"Crossref search failed for '{query}': {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: OpenAlex
# ═══════════════════════════════════════════════════════════════

def _search_openalex(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Search OpenAlex API.

    Free tier (no key required). Rich metadata including cited_by_count.
    """
    papers: List[Dict[str, Any]] = []
    try:
        url = (
            "https://api.openalex.org/works?"
            + urllib.parse.urlencode({
                "search": query,
                "per_page": max_results,
                "sort": "relevance_score:desc",
            })
        )
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read())

        for result in data.get("results", []):
            doi = (result.get("doi") or "").replace("https://doi.org/", "")
            authors = []
            for a in result.get("authorships", []):
                name = (a.get("author") or {}).get("display_name", "")
                if name:
                    authors.append(name)
            paper = {
                "doi": doi,
                "title": result.get("title", ""),
                "authors": authors,
                "year": str(result.get("publication_year", "")),
                "journal": (result.get("primary_location") or {}).get("source", {}).get("display_name", ""),
                "abstract": result.get("abstract_inverted_index", ""),
                "source": "openalex",
                "pmid": "",
                "pmcid": "",
                "url": f"https://doi.org/{doi}" if doi else "",
                "credibility_score": min(55 + (result.get("cited_by_count", 0) or 0) // 5, 90),
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"OpenAlex search failed for '{query}': {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: arXiv
# ═══════════════════════════════════════════════════════════════

def _search_arxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search arXiv API.

    Free, no key. Returns preprints.
    """
    papers: List[Dict[str, Any]] = []
    try:
        url = (
            "http://export.arxiv.org/api/query?"
            + urllib.parse.urlencode({
                "search_query": f"all:{query}",
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            })
        )
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            xml_data = resp.read().decode("utf-8", errors="replace")

        # Simple XML parsing (no lxml dependency needed)
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", "", ns)).strip()
            title = re.sub(r"\s+", " ", title)
            paper_id = entry.findtext("atom:id", "", ns).strip()
            doi = paper_id.replace("http://arxiv.org/abs/", "arXiv.")
            authors = [a.findtext("atom:name", "", ns).strip()
                       for a in entry.findall("atom:author", ns)]
            published = entry.findtext("atom:published", "", ns)[:4]
            summary = entry.findtext("atom:summary", "", ns).strip()[:500]
            paper = {
                "doi": doi,
                "title": title,
                "authors": authors,
                "year": published,
                "journal": "arXiv preprint",
                "abstract": summary,
                "source": "arxiv",
                "pmid": "",
                "pmcid": "",
                "url": paper_id,
                "credibility_score": 40,
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"arXiv search failed for '{query}': {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: CNKI (via Bing web search)
# ═══════════════════════════════════════════════════════════════

def _search_cnki_web(chinese_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search Chinese literature via Bing web search.

    Fallback when cnki_xue_search.py isn't available.
    Extracts paper metadata from Bing result snippets.
    """
    papers: List[Dict[str, Any]] = []
    if not chinese_name:
        return papers
    try:
        bing_url = (
            "https://www.bing.com/search?"
            + urllib.parse.urlencode({
                "q": f"{chinese_name} 研究 论文 期刊 水产 生物",
                "count": max_results,
                "setlang": "zh-cn",
            })
        )
        req = urllib.request.Request(bing_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract result snippets
        snippets = re.findall(r'<li class="b_algo"(.*?)</li>', html, re.DOTALL)
        for sn in snippets[:max_results]:
            title_m = re.search(r'<h2>.*?<a[^>]*>(.*?)</a>', sn, re.DOTALL)
            url_m = re.search(r'href="(https?://[^"]+)"', sn)
            desc_m = re.search(r'<p[^>]*>(.*?)</p>', sn, re.DOTALL)
            title = re.sub(r'<.*?>', '', title_m.group(1)).strip() if title_m else ""
            url = url_m.group(1) if url_m else ""
            abstract = re.sub(r'<.*?>', '', desc_m.group(1)).strip() if desc_m else ""
            paper = {
                "doi": "",
                "title": title,
                "authors": [],
                "year": "",
                "journal": "中文文献",
                "abstract": abstract,
                "source": "cnki_web",
                "pmid": "",
                "pmcid": "",
                "url": url,
                "credibility_score": 30,
                "_channel": "CN",
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"CNKI web search failed: {e}")

    return papers


# ═══════════════════════════════════════════════════════════════
# Provider registry
# ═══════════════════════════════════════════════════════════════

_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "pubmed": (_search_pubmed, 10),
    "europe_pmc": (_search_europe_pmc, 20),
    "crossref": (_search_crossref, 20),
    "openalex": (_search_openalex, 20),
    "arxiv": (_search_arxiv, 10),
}

# Chinese providers run separately with chinese_name
_CN_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "cnki_web": (_search_cnki_web, 10),
}


# ═══════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════

def _deduplicate(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by DOI (primary) then title (secondary)."""
    seen_dois: set = set()
    seen_titles: set = set()
    result: List[Dict[str, Any]] = []

    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title = (p.get("title") or "").strip().lower()[:100]

        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)
        result.append(p)

    return result


# ═══════════════════════════════════════════════════════════════
# ParallelSearch
# ═══════════════════════════════════════════════════════════════

@dataclass
class SearchStats:
    total_raw: int = 0
    total_merged: int = 0
    new_papers: List[Dict[str, Any]] = field(default_factory=list)
    providers_succeeded: List[str] = field(default_factory=list)
    providers_failed: List[str] = field(default_factory=list)
    elapsed_s: float = 0.0


class ParallelSearch:
    """多源 HTTP 并行搜索。

    使用 ThreadPoolExecutor 同时查询多个学术搜索引擎。
    结果自动去重（DOI + 标题）。
    """

    def __init__(self, max_workers: int = 4,
                 providers: Optional[List[str]] = None):
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._providers = providers or list(_PROVIDERS.keys())

    def search(self, query: str, chinese_name: str = "",
               max_per_provider: int = 20) -> SearchStats:
        """并行搜索所有已配置的源.

        Args:
            query: 搜索关键词（通常是学名）
            chinese_name: 中文名，用于中文源
            max_per_provider: 每源最大结果数

        Returns:
            SearchStats with merged papers
        """
        t0 = time.perf_counter()
        all_papers: List[Dict[str, Any]] = []
        succeeded: List[str] = []
        failed: List[str] = []
        futures = []

        # 提交国际源
        for name in self._providers:
            fn, default_max = _PROVIDERS.get(name, (None, 0))
            if fn is None:
                continue
            limit = min(max_per_provider, default_max)
            futures.append((name, self._pool.submit(fn, query, limit)))

        # 提交中文源
        if chinese_name:
            for name, (fn_cn, default_max_cn) in _CN_PROVIDERS.items():
                limit = min(max_per_provider, default_max_cn)
                futures.append((name, self._pool.submit(fn_cn, chinese_name, limit)))

        # 收集结果
        for name, future in futures:
            try:
                result = future.result(timeout=_TIMEOUT_S + 5)
                if result:
                    all_papers.extend(result)
                    succeeded.append(name)
                else:
                    failed.append(name)
            except Exception as e:
                logger.debug(f"Provider '{name}' failed: {e}")
                failed.append(name)

        # 去重
        deduped = _deduplicate(all_papers)

        return SearchStats(
            total_raw=len(all_papers),
            total_merged=len(deduped),
            new_papers=deduped,
            providers_succeeded=succeeded,
            providers_failed=failed,
            elapsed_s=time.perf_counter() - t0,
        )

    def search_all(self, queries: List[str],
                   max_per_query: int = 20) -> SearchStats:
        """对多个查询执行搜索，结果合并去重.

        Args:
            queries: 多个搜索词（学名变体 + 中文名）
            max_per_query: 每查询每源最大结果数

        Returns:
            SearchStats with merged papers from all queries
        """
        all_papers: List[Dict[str, Any]] = []
        all_succeeded: set = set()
        all_failed: set = set()

        for q in queries:
            # Detect if Chinese
            chinese_name = q if re.search(r'[\u4e00-\u9fff]', q) else ""
            search_query = q if not chinese_name else q
            stats = self.search(search_query, chinese_name=chinese_name,
                                max_per_provider=max_per_query)
            all_papers.extend(stats.new_papers)
            all_succeeded.update(stats.providers_succeeded)
            all_failed.update(stats.providers_failed)

        deduped = _deduplicate(all_papers)
        return SearchStats(
            total_raw=len(all_papers),
            total_merged=len(deduped),
            new_papers=deduped,
            providers_succeeded=list(all_succeeded),
            providers_failed=list(all_failed),
        )

    def close(self) -> None:
        """关闭线程池."""
        self._pool.shutdown(wait=False)

    def __enter__(self) -> "ParallelSearch":
        return self

    def __exit__(self, *args) -> None:
        self.close()
