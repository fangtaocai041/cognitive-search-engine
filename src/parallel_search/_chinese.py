from __future__ import annotations
from ._shared import _HEADERS, _TIMEOUT_S, logger

import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List


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
