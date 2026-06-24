from __future__ import annotations
from ._shared import _HEADERS, _TIMEOUT_S, logger

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List


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
