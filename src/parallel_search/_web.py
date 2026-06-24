from __future__ import annotations
from ._shared import _HEADERS, _TIMEOUT_S, logger

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List


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
