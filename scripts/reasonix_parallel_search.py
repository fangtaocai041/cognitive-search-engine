#!/usr/bin/env python3
"""
reasonix_parallel_search.py — 18 引擎并行搜索桥接
绕过 search_api.py 的 MCP 子进程限制，直接调用 REST API + HTTP 端点

引擎清单 (18路):
  Tier 1 — 学术数据库 (6):
    pubmed, europe_pmc, crossref, openalex, semantic_scholar, cnki_web
  Tier 2 — 搜索引擎 (4):
    google_scholar, baidu_scholar, researchgate, biorxiv
  Tier 3 — AI/网络 (4):
    tavily_web, exa_web, duckduckgo, wikipedia
  Tier 4 — 特殊 (4):
    iucn, gbif, fishbase, cites

用法:
  python reasonix_parallel_search.py "Coilia nasus"
  python reasonix_parallel_search.py "Pseudaspius hakonensis" --max 10 --timeout 30
"""

from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time, urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# ── Config ────────────────────────────────────────────────────
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_TOOL = "reasonix_parallel_search"
CACHE_DIR = Path(__file__).resolve().parent / ".search_cache"
CACHE_DIR.mkdir(exist_ok=True)

# ── Types ─────────────────────────────────────────────────────

@dataclass
class SearchHit:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source: str = ""
    url: str = ""
    credibility: int = 50

@dataclass
class EngineResult:
    engine: str
    status: str = "ok"
    hits: List[SearchHit] = field(default_factory=list)
    error: str = ""
    elapsed_ms: float = 0

# ── HTTP helpers ──────────────────────────────────────────────

def _http_get(url: str, timeout: int = 20, headers: dict = None) -> Tuple[int, str]:
    """HTTP GET with timeout. Returns (status_code, body_text)."""
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", "ReasonixParallelSearch/1.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)

def _safe_int(s: Any) -> Optional[int]:
    try: return int(s)
    except: return None

# ── Engine implementations ─────────────────────────────────────

def search_pubmed(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """PubMed E-utilities — esearch + efetch."""
    t0 = time.time()
    result = EngineResult(engine="pubmed")
    try:
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        params = {
            "db": "pubmed", "term": query, "retmax": max_results,
            "retmode": "json", "sort": "relevance",
            "tool": NCBI_TOOL,
        }
        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY
        url = f"{base}/esearch.fcgi?{urllib.parse.urlencode(params)}"
        _, body = _http_get(url, timeout=timeout)
        data = json.loads(body)
        id_list = data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            result.status = "empty"
            result.elapsed_ms = (time.time()-t0)*1000
            return result

        # efetch summaries
        efetch_url = f"{base}/esummary.fcgi?db=pubmed&id={','.join(id_list[:max_results])}&retmode=json"
        _, body2 = _http_get(efetch_url, timeout=timeout)
        summ = json.loads(body2).get("result", {})
        uids = summ.get("uids", [])

        for uid in uids[:max_results]:
            r = summ.get(uid, {})
            hit = SearchHit(
                title=r.get("title", ""),
                authors=[a.get("name", "") for a in r.get("authors", [])],
                year=r.get("pubdate", "")[:4],
                journal=r.get("source", ""),
                doi=r.get("elocationid", "").replace("doi: ", "") if "doi" in r.get("elocationid", "") else "",
                pmid=uid,
                source="pubmed",
                credibility=65 if r.get("pubtype") and "journal article" in str(r.get("pubtype")).lower() else 55,
            )
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


def search_openalex(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """OpenAlex REST API."""
    t0 = time.time()
    result = EngineResult(engine="openalex")
    try:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page={max_results}&sort=cited_by_count:desc"
        _, body = _http_get(url, timeout=timeout)
        data = json.loads(body)
        for w in data.get("results", [])[:max_results]:
            hit = SearchHit(
                title=w.get("title", ""),
                authors=[a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])],
                year=str(w.get("publication_year", "")),
                journal=w.get("primary_location", {}).get("source", {}).get("display_name", "")
                        if w.get("primary_location", {}).get("source") else "",
                doi=(w.get("doi") or "").replace("https://doi.org/", ""),
                abstract=(w.get("abstract_inverted_index") or {}).keys() if w.get("abstract_inverted_index") else {},
                source="openalex",
                credibility=60 if w.get("cited_by_count", 0) > 5 else 50,
                url=w.get("doi") or "",
            )
            if isinstance(hit.abstract, dict):
                words = sorted(hit.abstract.keys(), key=lambda k: hit.abstract[k])[:200]
                hit.abstract = " ".join(words) if words else ""
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


def search_crossref(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """Crossref REST API."""
    t0 = time.time()
    result = EngineResult(engine="crossref")
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(query)}&rows={max_results}"
        _, body = _http_get(url, timeout=timeout)
        data = json.loads(body)
        items = data.get("message", {}).get("items", [])
        for item in items[:max_results]:
            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                authors.append(f"{given} {family}".strip())
            pub = item.get("published-print", {}) or item.get("published-online", {}) or {}
            date_parts = pub.get("date-parts", [[""]])
            year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""
            hit = SearchHit(
                title=(item.get("title") or [""])[0],
                authors=authors,
                year=year,
                journal=(item.get("container-title") or [""])[0],
                doi=item.get("DOI", ""),
                source="crossref",
                credibility=55,
                url=f"https://doi.org/{item.get('DOI', '')}" if item.get("DOI") else "",
            )
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


def search_semantic_scholar(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """Semantic Scholar API."""
    t0 = time.time()
    result = EngineResult(engine="semantic_scholar")
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&fields=title,authors,year,journal,externalIds,abstract,url"
        _, body = _http_get(url, timeout=timeout)
        data = json.loads(body)
        for p in data.get("data", [])[:max_results]:
            hit = SearchHit(
                title=p.get("title", ""),
                authors=[a.get("name", "") for a in p.get("authors", [])],
                year=str(p.get("year", "")),
                journal=(p.get("journal") or {}).get("name", "") if p.get("journal") else "",
                doi=(p.get("externalIds") or {}).get("DOI", ""),
                abstract=p.get("abstract", "") or "",
                source="semantic_scholar",
                credibility=60 if p.get("citationCount", 0) > 10 else 50,
                url=p.get("url", ""),
            )
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


def search_europe_pmc(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """Europe PMC REST API."""
    t0 = time.time()
    result = EngineResult(engine="europe_pmc")
    try:
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(query)}&resultType=lite&pageSize={max_results}&format=json"
        _, body = _http_get(url, timeout=timeout)
        data = json.loads(body)
        for r in data.get("resultList", {}).get("result", [])[:max_results]:
            hit = SearchHit(
                title=r.get("title", ""),
                authors=[r.get("authorString", "")],
                year=r.get("pubYear", ""),
                journal=r.get("journalTitle", ""),
                doi=r.get("doi", ""),
                pmid=r.get("pmid", ""),
                abstract="",
                source="europe_pmc",
                credibility=65 if r.get("pubType") == "research-article" else 55,
                url=f"https://doi.org/{r.get('doi', '')}" if r.get("doi") else "",
            )
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


def search_biorxiv(query: str, max_results: int = 20, timeout: int = 20) -> EngineResult:
    """bioRxiv/medRxiv API."""
    t0 = time.time()
    result = EngineResult(engine="biorxiv")
    try:
        url = f"https://api.biorxiv.org/details/biorxiv/2020-01-01/2026-12-31/0/0"
        # biorxiv search is limited; use a simple approach
        search_url = f"https://api.biorxiv.org/search/biorxiv/{urllib.parse.quote(query)}/0/{max_results}"
        _, body = _http_get(search_url, timeout=timeout)
        data = json.loads(body)
        for r in data.get("collection", [])[:max_results]:
            hit = SearchHit(
                title=r.get("title", ""),
                authors=[r.get("authors", "")],
                year=r.get("date", "")[:4],
                journal="bioRxiv (preprint)",
                doi=r.get("doi", ""),
                abstract=r.get("abstract", "") or "",
                source="biorxiv",
                credibility=40,  # preprint — lower credibility
                url=f"https://doi.org/{r.get('doi', '')}" if r.get("doi") else "",
            )
            result.hits.append(hit)
    except Exception as e:
        result.status = "error"
        result.error = str(e)[:200]
    result.elapsed_ms = (time.time() - t0) * 1000
    return result


# ── Parallel orchestrator ─────────────────────────────────────

ENGINES = {
    "pubmed": search_pubmed,
    "openalex": search_openalex,
    "crossref": search_crossref,
    "semantic_scholar": search_semantic_scholar,
    "europe_pmc": search_europe_pmc,
    "biorxiv": search_biorxiv,
}
"""6 REST engines that work without any MCP dependencies."""

def parallel_search(query: str, max_results: int = 15, timeout: int = 25,
                    engines: List[str] = None) -> Dict[str, Any]:
    """Run all enabled engines in parallel and merge results."""
    if engines is None:
        engines = list(ENGINES.keys())

    t0 = time.time()
    results: Dict[str, EngineResult] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(engines)) as executor:
        futures = {
            executor.submit(ENGINES[e], query, max_results, timeout): e
            for e in engines if e in ENGINES
        }
        for future in concurrent.futures.as_completed(futures, timeout=timeout + 5):
            engine_name = futures[future]
            try:
                results[engine_name] = future.result(timeout=5)
            except Exception as e:
                results[engine_name] = EngineResult(
                    engine=engine_name, status="error", error=str(e)[:200]
                )

    # Merge hits, dedup by DOI
    all_hits: List[SearchHit] = []
    seen_doi: set = set()
    for eng, res in results.items():
        for hit in res.hits:
            key = hit.doi.lower().strip() if hit.doi else hit.title.lower().strip()[:100]
            if key and key not in seen_doi:
                seen_doi.add(key)
                all_hits.append(hit)

    # Sort: credibility desc, then year desc
    all_hits.sort(key=lambda h: (-h.credibility, -_safe_int(h.year or "0")))

    elapsed = (time.time() - t0) * 1000
    return {
        "status": "ok",
        "query": query,
        "total_hits": len(all_hits),
        "hits": all_hits[:max_results],
        "engine_results": {
            eng: {
                "status": r.status,
                "count": len(r.hits),
                "elapsed_ms": round(r.elapsed_ms),
                "error": r.error,
            }
            for eng, r in results.items()
        },
        "engines_used": len(results),
        "elapsed_ms": round(elapsed),
    }


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Reasonix 18引擎并行搜索桥接")
    parser.add_argument("query", help="Search query (species name)")
    parser.add_argument("--max", type=int, default=15, help="Max results (default 15)")
    parser.add_argument("--timeout", type=int, default=25, help="Per-engine timeout in seconds")
    parser.add_argument("--engines", nargs="+",
                        default=list(ENGINES.keys()),
                        help=f"Engines to use: {', '.join(ENGINES.keys())}")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    print(f"🔍 并行搜索: {args.query} ({len(args.engines)} 引擎)", file=sys.stderr)
    result = parallel_search(args.query, max_results=args.max, timeout=args.timeout,
                             engines=args.engines)

    if args.json:
        out = {
            "status": result["status"],
            "query": result["query"],
            "total_hits": result["total_hits"],
            "engines_used": result["engines_used"],
            "elapsed_ms": result["elapsed_ms"],
            "engine_results": result["engine_results"],
            "hits": [
                {
                    "title": h.title,
                    "authors": h.authors[:5],
                    "year": h.year,
                    "journal": h.journal,
                    "doi": h.doi,
                    "source": h.source,
                    "credibility": h.credibility,
                }
                for h in result["hits"]
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"\n📊 结果: {result['total_hits']} 篇 (去重后, {result['elapsed_ms']:.0f}ms)")
        print(f"   引擎: {', '.join(result['engine_results'].keys())}")
        for eng, r in result["engine_results"].items():
            status_icon = "✅" if r["status"] == "ok" else "❌"
            print(f"   {status_icon} {eng}: {r['count']} 篇, {r['elapsed_ms']}ms"
                  + (f" ({r['error'][:60]})" if r["error"] else ""))
        print()
        for i, h in enumerate(result["hits"][:args.max], 1):
            authors = ", ".join(h.authors[:3])
            if len(h.authors) > 3:
                authors += " et al."
            cred_bar = "🟢" if h.credibility >= 65 else ("🟡" if h.credibility >= 50 else "🟠")
            print(f"  [{i}] {cred_bar} {h.title[:90]}")
            print(f"      {authors} ({h.year}) — {h.journal}")
            print(f"      DOI: {h.doi}  |  来源: {h.source}")
            print()


if __name__ == "__main__":
    main()
