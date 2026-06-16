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

            # 将 abstract_inverted_index 还原为可读文本
            inverted = result.get("abstract_inverted_index")
            abstract_text = ""
            if isinstance(inverted, dict) and inverted:
                # 按位置重建单词顺序
                word_positions = []
                for word, positions in inverted.items():
                    if isinstance(positions, list):
                        for pos in positions:
                            word_positions.append((int(pos), word))
                word_positions.sort(key=lambda x: x[0])
                abstract_text = " ".join(w for _, w in word_positions)
            elif isinstance(inverted, str):
                abstract_text = inverted

            paper = {
                "doi": doi,
                "title": result.get("title", ""),
                "authors": authors,
                "year": str(result.get("publication_year", "")),
                "journal": (result.get("primary_location") or {}).get("source", {}).get("display_name", ""),
                "abstract": abstract_text,
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
        # 用精确搜索 + site 限定提升相关性
        safe_query = urllib.parse.quote(f"{chinese_name} 研究 论文 期刊 水产 生物")
        bing_url = (
            "https://www.bing.com/search?"
            + urllib.parse.urlencode({
                "q": f"{chinese_name} 研究 论文 期刊 水产 生物",
                "count": max_results * 2,  # 多取一些再过滤
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
        for sn in snippets[:max_results * 2]:
            title_m = re.search(r'<h2>.*?<a[^>]*>(.*?)</a>', sn, re.DOTALL)
            url_m = re.search(r'href="(https?://[^"]+)"', sn)
            desc_m = re.search(r'<p[^>]*>(.*?)</p>', sn, re.DOTALL)
            title = re.sub(r'<.*?>', '', title_m.group(1)).strip() if title_m else ""
            url = url_m.group(1) if url_m else ""
            abstract = re.sub(r'<.*?>', '', desc_m.group(1)).strip() if desc_m else ""

            # 过滤垃圾结果：无标题 或 含中文字符不够（游戏广告页）
            if not title:
                continue
            cn_chars = len(re.findall(r'[\u4e00-\u9fff]', title + abstract))
            if cn_chars < 2:
                continue  # 没有足够中文字符 → 无关页面

            paper = {
                "doi": "",
                "title": title,
                "authors": [],
                "year": "",
                "journal": "",
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
def _search_baidu_scholar(chinese_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search Baidu Scholar for Chinese academic papers.

    Uses xueshu.baidu.com search with site scraping.
    """
    papers: List[Dict[str, Any]] = []
    if not chinese_name:
        return papers
    try:
        safe_q = urllib.parse.quote(chinese_name)
        url = f"https://xueshu.baidu.com/s?wd={safe_q}&rsv_bp=0&tn=SE_baiduxueshu_c1g0"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract paper entries
        entries = re.findall(
            r'<div class="result[^"]*"(.*?)</div>\s*</div>\s*</div>\s*<div class="pager"',
            html, re.DOTALL
        ) or re.findall(r'<div class="sc_content"[^>]*>(.*?)</div>\s*<!--/sc_content-->', html, re.DOTALL)
        
        if not entries:
            entries = re.findall(r'<h3[^>]*class="t"[^>]*>(.*?)</h3>', html, re.DOTALL)[:max_results]

        for i, entry in enumerate(entries[:max_results]):
            title_m = re.search(r'<a[^>]*>(.*?)</a>', entry, re.DOTALL)
            title = re.sub(r'<.*?>', '', title_m.group(1)).strip() if title_m else ""
            if not title:
                title_m2 = re.search(r'class="t"[^>]*>(.*?)</a>', entry, re.DOTALL)
                title = re.sub(r'<.*?>', '', title_m2.group(1)).strip() if title_m2 else ""

            paper = {
                "doi": "",
                "title": title,
                "authors": [],
                "year": "",
                "journal": "",
                "abstract": "",
                "source": "baidu_scholar",
                "pmid": "", "pmcid": "",
                "url": "",
                "credibility_score": 35,
                "_channel": "CN",
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"Baidu Scholar search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: Wanfang Data (中文)
# ═══════════════════════════════════════════════════════════════

def _search_wanfang_web(chinese_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search Wanfang Data via web interface for Chinese papers."""
    papers: List[Dict[str, Any]] = []
    if not chinese_name:
        return papers
    try:
        safe_q = urllib.parse.quote(chinese_name)
        url = f"https://s.wanfangdata.com.cn/paper?q={safe_q}&p=1&ps={max_results}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            text = resp.read().decode("utf-8", errors="replace")

        # Extract paper titles and metadata
        titles = re.findall(r'<a[^>]*class="title"[^>]*>(.*?)</a>', text, re.DOTALL)[:max_results]
        for title_html in titles:
            title = re.sub(r'<.*?>', '', title_html).strip()
            if not title:
                continue
            paper = {
                "doi": "",
                "title": title,
                "authors": [],
                "year": "",
                "journal": "",
                "abstract": "",
                "source": "wanfang_web",
                "pmid": "", "pmcid": "",
                "url": "",
                "credibility_score": 35,
                "_channel": "CN",
            }
            papers.append(paper)
    except Exception as e:
        logger.debug(f"Wanfang web search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: CrossRef Direct API
# ═══════════════════════════════════════════════════════════════

def _search_crossref_direct(query: str, max_results: int = 15) -> List[Dict[str, Any]]:
    """Search CrossRef REST API directly (free, no key needed).

    More flexible than the MCP article-mcp, with email-based polite pool.
    """
    papers: List[Dict[str, Any]] = []
    try:
        params = urllib.parse.urlencode({
            "query": query,
            "rows": min(max_results, 30),
            "sort": "relevance",
            "order": "desc",
            "mailto": "fangtaocai041@gmail.com",  # polite pool
        })
        url = f"https://api.crossref.org/works?{params}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.8 (fangtaocai041@gmail.com)",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("message", {}).get("items", [])
        for item in items[:max_results]:
            title = (item.get("title") or [""])[0]
            if not title:
                continue
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                authors.append(f"{given} {family}".strip())
            doi = item.get("DOI", "")
            year = ""
            if item.get("published-print"):
                year = str(item["published-print"].get("date-parts", [[None]])[0][0] or "")
            elif item.get("published-online"):
                year = str(item["published-online"].get("date-parts", [[None]])[0][0] or "")
            journal = (item.get("container-title") or [""])[0]

            papers.append({
                "doi": doi,
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "abstract": "",
                "source": "crossref_direct",
                "pmid": "", "pmcid": "",
                "url": f"https://doi.org/{doi}" if doi else "",
                "credibility_score": 60,
            })
    except Exception as e:
        logger.debug(f"CrossRef direct search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: Semantic Scholar API
# ═══════════════════════════════════════════════════════════════

def _search_semantic_scholar(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search Semantic Scholar API (free, no key for basic)."""
    papers: List[Dict[str, Any]] = []
    try:
        params = urllib.parse.urlencode({
            "query": query,
            "limit": min(max_results, 50),
            "fields": "title,authors,year,journal,externalIds,abstract,url",
        })
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.8 (fangtaocai041@gmail.com)",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for p in data.get("data", [])[:max_results]:
            title = p.get("title", "")
            if not title:
                continue
            authors = [a.get("name", "") for a in p.get("authors", []) if a.get("name")]
            year = str(p.get("year", ""))
            journal = (p.get("journal", {}) or {}).get("name", "")
            ext_ids = p.get("externalIds", {}) or {}
            doi = ext_ids.get("DOI", "")
            pmid = ext_ids.get("PubMed", "")

            papers.append({
                "doi": doi,
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "abstract": p.get("abstract", ""),
                "source": "semantic_scholar",
                "pmid": pmid,
                "pmcid": "",
                "url": p.get("url", f"https://doi.org/{doi}" if doi else ""),
                "credibility_score": 65,
            })
    except Exception as e:
        logger.debug(f"Semantic Scholar search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: bioRxiv / medRxiv (预印本)
# ═══════════════════════════════════════════════════════════════

def _search_biorxiv_medrxiv(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search bioRxiv/medRxiv API for preprints."""
    papers: List[Dict[str, Any]] = []
    try:
        for server in ["biorxiv", "medrxiv"]:
            params = urllib.parse.urlencode({"q": query})
            url = f"https://api.biorxiv.org/details/{server}/2020-01-01/2030-12-31/0/{max_results}?{params}"
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "ReasonixCognitiveSearch/5.8",
                })
                with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("collection", [])[:max_results]:
                    title = item.get("title", "")
                    if not title or query.lower() not in title.lower():
                        continue
                    papers.append({
                        "doi": item.get("doi", ""),
                        "title": title,
                        "authors": [item.get("author", "")],
                        "year": str(item.get("date", "")[:4]),
                        "journal": f"{server} preprint",
                        "abstract": item.get("abstract", ""),
                        "source": server,
                        "pmid": "", "pmcid": "",
                        "url": f"https://doi.org/{item.get('doi', '')}" if item.get('doi') else "",
                        "credibility_score": 40,
                    })
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"bioRxiv/medRxiv search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: ResearchGate (web scrape)
# ═══════════════════════════════════════════════════════════════

def _search_researchgate(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search ResearchGate via public web search.

    ResearchGate has no public API, so uses Bing site: search as fallback.
    """
    papers: List[Dict[str, Any]] = []
    try:
        safe_q = urllib.parse.quote(f"{query} site:researchgate.net/publication")
        bing_url = (
            "https://www.bing.com/search?"
            + urllib.parse.urlencode({"q": f"{query} researchgate publication", "count": max_results})
        )
        req = urllib.request.Request(bing_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        snippets = re.findall(r'<li class="b_algo"(.*?)</li>', html, re.DOTALL)
        for sn in snippets[:max_results]:
            title_m = re.search(r'<h2>.*?<a[^>]*>(.*?)</a>', sn, re.DOTALL)
            title = re.sub(r'<.*?>', '', title_m.group(1)).strip() if title_m else ""
            if not title:
                continue
            papers.append({
                "doi": "",
                "title": title,
                "authors": [],
                "year": "",
                "journal": "",
                "abstract": "",
                "source": "researchgate",
                "pmid": "", "pmcid": "",
                "url": "",
                "credibility_score": 30,
            })
    except Exception as e:
        logger.debug(f"ResearchGate search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: Wikipedia API (free, no key)
# ═══════════════════════════════════════════════════════════════

def _search_wikipedia(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search Wikipedia for species pages, taxonomy, common names.

    Uses Wikipedia's REST API — free, no key required.
    Returns species overview with common names and scientific classification.
    """
    papers: List[Dict[str, Any]] = []
    try:
        # Wikipedia search for the query
        safe_q = urllib.parse.quote(query)
        search_url = (
            "https://en.wikipedia.org/w/api.php?"
            + "action=query&list=search&srsearch=" + safe_q
            + "&format=json&srlimit=" + str(max_results)
        )
        req = urllib.request.Request(search_url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.9 (fangtaocai041@gmail.com)",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            search_data = json.loads(resp.read().decode("utf-8"))

        for result in search_data.get("query", {}).get("search", [])[:max_results]:
            title = result.get("title", "")
            snippet = re.sub(r'<.*?>', '', result.get("snippet", ""))
            papers.append({
                "doi": "",
                "title": f"[Wikipedia] {title}",
                "authors": ["Wikipedia"],
                "year": "",
                "journal": "Wikipedia (百科全书)",
                "abstract": snippet[:500],
                "source": "wikipedia",
                "pmid": "", "pmcid": "",
                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                "credibility_score": 25,
            })
    except Exception as e:
        logger.debug(f"Wikipedia search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: DuckDuckGo Instant Answer API (free, no key)
# ═══════════════════════════════════════════════════════════════

def _search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search DuckDuckGo Instant Answer API.

    Free, no API key. Returns abstracts and topic summaries.
    """
    papers: List[Dict[str, Any]] = []
    try:
        safe_q = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={safe_q}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.9",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Extract abstract text
        abstract = data.get("AbstractText", "")
        if abstract:
            papers.append({
                "doi": "",
                "title": f"[DuckDuckGo] {data.get('Heading', query)}",
                "authors": ["DuckDuckGo"],
                "year": "",
                "journal": "DuckDuckGo (网络百科)",
                "abstract": abstract[:800],
                "source": "duckduckgo",
                "source_url": data.get("AbstractURL", ""),
                "pmid": "", "pmcid": "",
                "credibility_score": 20,
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results-1]:
            if isinstance(topic, dict) and "Text" in topic:
                text = topic.get("Text", "")
                if text:
                    papers.append({
                        "doi": "",
                        "title": f"[DuckDuckGo] {text[:100]}",
                        "authors": ["DuckDuckGo"],
                        "year": "",
                        "journal": "",
                        "abstract": "",
                        "source": "duckduckgo",
                        "pmid": "", "pmcid": "",
                        "credibility_score": 15,
                    })
    except Exception as e:
        logger.debug(f"DuckDuckGo API failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: GBIF API (free, no key)
# ═══════════════════════════════════════════════════════════════

def _search_gbif(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search GBIF (Global Biodiversity Information Facility) API.

    Free, no key. Returns species occurrences, distribution data,
    and taxonomic information.
    """
    papers: List[Dict[str, Any]] = []
    try:
        safe_q = urllib.parse.quote(query)
        url = f"https://api.gbif.org/v1/species/suggest?q={safe_q}&limit={max_results}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.9 (fangtaocai041@gmail.com)",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for item in data[:max_results]:
            kingdom = item.get("kingdom", "")
            phylum = item.get("phylum", "")
            cl = item.get("class", "")
            order = item.get("order", "")
            family = item.get("family", "")
            taxonomy = f"界:{kingdom} 门:{phylum} 纲:{cl} 目:{order} 科:{family}".replace("None", "-")

            papers.append({
                "doi": "",
                "title": f"[GBIF] {item.get('scientificName', query)} — {item.get('canonicalName', '')}",
                "authors": ["GBIF"],
                "year": "",
                "journal": "GBIF (全球生物多样性信息网络)",
                "abstract": f"Taxonomy: {taxonomy}. Rank: {item.get('rank', '?')}. Key: {item.get('nubKey', '')}.",
                "source": "gbif",
                "pmid": "", "pmcid": "",
                "url": f"https://www.gbif.org/species/{item.get('nubKey', '')}" if item.get("nubKey") else "",
                "credibility_score": 30,
            })
    except Exception as e:
        logger.debug(f"GBIF search failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════
# Provider: CORE API (free, no key — open access papers)
# ═══════════════════════════════════════════════════════════════

def _search_core(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search CORE (COnnecting REpositories) API.

    Free, no key. 250M+ open access full-text papers.
    """
    papers: List[Dict[str, Any]] = []
    try:
        safe_q = urllib.parse.quote(query)
        url = f"https://api.core.ac.uk/v3/search/works?q={safe_q}&limit={max_results}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "ReasonixCognitiveSearch/5.9",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for item in data.get("results", [])[:max_results]:
            papers.append({
                "doi": item.get("doi", ""),
                "title": item.get("title", ""),
                "authors": [a.get("name", "") for a in item.get("authors", [])],
                "year": str(item.get("yearPublished", "")),
                "journal": item.get("publisher", item.get("journal", {}).get("title", "")),
                "abstract": item.get("abstract", "")[:500],
                "source": "core",
                "pmid": "", "pmcid": "",
                "url": item.get("downloadUrl", item.get("sourceFulltextUrls", [""])[0] if item.get("sourceFulltextUrls") else ""),
                "credibility_score": 35,
            })
    except Exception as e:
        logger.debug(f"CORE API failed: {e}")
    return papers


# ═══════════════════════════════════════════════════════════════

_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "pubmed": (_search_pubmed, 10),
    "europe_pmc": (_search_europe_pmc, 20),
    "crossref": (_search_crossref, 20),
    "openalex": (_search_openalex, 20),
    "arxiv": (_search_arxiv, 10),
    "crossref_direct": (_search_crossref_direct, 15),
    "semantic_scholar": (_search_semantic_scholar, 10),
    "biorxiv_medrxiv": (_search_biorxiv_medrxiv, 10),
    "researchgate": (_search_researchgate, 10),
    "wikipedia": (_search_wikipedia, 5),
    "duckduckgo": (_search_duckduckgo, 8),
    "gbif": (_search_gbif, 5),
    "core": (_search_core, 10),
}

# Chinese providers run separately with chinese_name
_CN_PROVIDERS: Dict[str, Tuple[Callable, int]] = {
    "cnki_web": (_search_cnki_web, 10),
    "baidu_scholar": (_search_baidu_scholar, 10),
    "wanfang_web": (_search_wanfang_web, 10),
}


# ═══════════════════════════════════════════════════════════════
# Genus filter — 噪音论文过滤
# ═══════════════════════════════════════════════════════════════

def _extract_genus(query: str) -> Optional[str]:
    """从搜索查询中提取属名（首个拉丁单词，首字母大写）。"""
    query = query.strip()
    # 匹配合法学名：首字母大写的拉丁词
    m = re.match(r'([A-Z][a-z]+)', query)
    if m:
        return m.group(1).lower()
    return None


def _filter_by_genus(query: str, papers: List[Dict[str, Any]],
                     strict_sources: Optional[set] = None) -> List[Dict[str, Any]]:
    """按属名/物种名过滤论文，移除标题中不含目标属名的噪音条目。

    Args:
        query: 搜索查询（从中提取属名）
        papers: 论文列表
        strict_sources: 启用严格模式的源名集合
                        (arXiv/Crossref 噪音大，默认启用)

    Returns:
        过滤后的论文列表
    """
    if strict_sources is None:
        strict_sources = {"arxiv", "crossref"}

    genus = _extract_genus(query)
    if not genus:
        return papers  # 无法提取属名时不过滤

    filtered: List[Dict[str, Any]] = []
    for p in papers:
        source = p.get("source", "")
        title = (p.get("title") or "").lower()
        abstract = (p.get("abstract") or "")
        if isinstance(abstract, dict):
            abstract = str(abstract)
        abstract = abstract.lower()

        # 标题中包含属名 → 保留
        if genus in title:
            filtered.append(p)
            continue

        # arXiv: 严格模式 — 标题必须含属名
        if source in strict_sources:
            continue  # 跳过

        # 其他源: 标题或摘要含属名均可
        if genus in abstract:
            # 摘要匹配比标题匹配可信度低
            p["credibility_score"] = min(p.get("credibility_score", 50), 45)
            filtered.append(p)
            continue

        # 完全不相关
        logger.debug(f"Filtered out '{p.get('title', '')[:60]}' (genus={genus}, source={source})")

    return filtered


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

        # 属名校验 — 过滤标题不含目标属名的噪音论文
        filtered = _filter_by_genus(query, deduped)

        return SearchStats(
            total_raw=len(all_papers),
            total_merged=len(filtered),
            new_papers=filtered,
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

# ═══════════════════════════════════════════════════════════════
# Provider: Baidu Scholar (中文)
# ═══════════════════════════════════════════════════════════════

