#!/usr/bin/env python3
"""知网研学(CNKI研学)搜索 — 优先中文文献获取。

通过知网研学账号（温州大学团队会员）直连 CNKI 数据库，
搜索中文物种文献，获取完整元数据（标题/作者/期刊/摘要/关键词）。
比 web_search + site: 方式更快、更全、更准确。

用法:
    python scripts/cnki_xue_search.py "鳤"
    python scripts/cnki_xue_search.py "珠星三块鱼" --max-results 20

依赖:
    pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

logger = logging.getLogger("cnki_xue")

# ─── 配置 ───────────────────────────────────────────────
# 知网研学搜索 API 端点
CNKI_SEARCH_URL = "https://kns.cnki.net/kns8/defaultresult/index"
CNKI_DETAIL_URL = "https://kns.cnki.net/kcms2/article/abstract"

# Cookie 文件路径 (由 playwright 登录后保存)
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "cnki_cookies.json")


@dataclass
class Paper:
    """一篇 CNKI 论文元数据"""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    keywords: List[str] = field(default_factory=list)
    abstract: str = ""
    cnki_link: str = ""
    source: str = "cnki"
    dbcode: str = "CJFQ"  # CJFQ=期刊, CDMD=博硕, CIPD=会议


def load_cookies() -> Dict[str, str]:
    """从本地加载知网研学 Cookie。"""
    if os.path.isfile(COOKIE_FILE):
        with open(COOKIE_FILE) as f:
            data = json.load(f)
            cookies = data.get("cookies", "")
            if isinstance(cookies, str):
                return dict(item.split("=", 1) for item in cookies.split("; ") if "=" in item)
            return cookies
    # Fallback: 从环境变量读取
    cookie_str = os.environ.get("CNKI_COOKIES", "")
    if cookie_str:
        return dict(item.split("=", 1) for item in cookie_str.split("; ") if "=" in item)
    return {}


def save_cookies(cookie_str: str):
    """保存 Cookie 到本地文件。"""
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    with open(COOKIE_FILE, "w") as f:
        json.dump({"cookies": cookie_str}, f, ensure_ascii=False)
    logger.info(f"Cookies saved to {COOKIE_FILE}")


def search_cnki(
    keyword: str,
    max_results: int = 10,
    cookies: Optional[Dict[str, str]] = None,
    dbcode: str = "CJFQ",
) -> List[Paper]:
    """搜索知网研学，返回论文列表。

    Args:
        keyword: 搜索关键词 (物种中文名/学名)
        max_results: 最大返回数
        cookies: 知网研学 Cookie
        dbcode: 数据库代码 (CJFQ=期刊, CDMD=博硕)

    Returns:
        List[Paper]: 论文元数据列表
    """
    if cookies is None:
        cookies = load_cookies()

    if not cookies:
        logger.warning("No CNKI cookies found. Run playwright login first.")
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://kns.cnki.net/kns8/defaultresult/index",
        "X-Requested-With": "XMLHttpRequest",
    }

    # 构建搜索参数
    params = {
        "dbcode": dbcode,
        "dbvalue": f"首字母={keyword[0] if keyword else ''}",
        "kw": keyword,
        "korder": "KY",  # 关键词排序
        "pageSize": min(max_results, 50),
        "pageNum": 1,
    }

    try:
        import requests as req
    except ImportError:
        logger.error("requests 未安装: pip install requests")
        return []

    try:
        resp = req.get(
            CNKI_SEARCH_URL,
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            logger.warning(f"CNKI search failed: HTTP {resp.status_code}")
            return []

        papers = _parse_search_results(resp.text, keyword)
        logger.info(f"CNKI: {len(papers)} papers for '{keyword}'")
        return papers[:max_results]

    except Exception as e:
        logger.warning(f"CNKI search error: {e}")
        return []


def _parse_search_results(html: str, keyword: str) -> List[Paper]:
    """从 CNKI 搜索结果 HTML 中解析论文列表。"""
    papers = []
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 未安装: pip install beautifulsoup4 lxml")
        return papers

    soup = BeautifulSoup(html, "lxml")

    # CNKI 搜索结果列表
    for item in soup.select("table.result-table tr, .result-list > div, .list-item"):
        try:
            paper = Paper(source="cnki")

            # 标题 + 链接
            title_el = item.select_one("a[href*='kns.cnki.net']")
            if not title_el:
                continue
            paper.title = title_el.get_text(strip=True)
            paper.cnki_link = title_el.get("href", "")

            # 作者
            author_el = item.select_one(".author, .authors")
            if author_el:
                paper.authors = [
                    a.strip()
                    for a in author_el.get_text(strip=True).replace(";", ",").split(",")
                    if a.strip()
                ]

            # 期刊/来源
            journal_el = item.select_one(".source, .journal")
            if journal_el:
                paper.journal = journal_el.get_text(strip=True)

            # 年份
            year_el = item.select_one(".year, .date")
            if year_el:
                paper.year = year_el.get_text(strip=True)

            # DOI
            doi_el = item.select_one(".doi")
            if doi_el:
                paper.doi = doi_el.get_text(strip=True)

            papers.append(paper)
        except Exception:
            continue

    # 如果 HTML 解析失败，尝试 JSON 格式
    if not papers:
        try:
            data = json.loads(html)
            for item in data.get("data", []):
                paper = Paper(
                    title=item.get("title", ""),
                    authors=item.get("authors", []),
                    journal=item.get("source", ""),
                    year=str(item.get("year", "")),
                    doi=item.get("doi", ""),
                    cnki_link=item.get("url", ""),
                    keywords=item.get("keywords", []),
                    abstract=item.get("abstract", ""),
                    source="cnki",
                )
                if paper.title:
                    papers.append(paper)
        except (json.JSONDecodeError, TypeError):
            pass

    return papers


def search_cnki_web(
    keyword: str,
    max_results: int = 10,
    cookies: Optional[Dict[str, str]] = None,
) -> List[Paper]:
    """知网研学 Web 搜索 (通过 Playwright 浏览器)。

    当 API 方式不可用时，回退到浏览器自动化搜索。
    """
    # 由 playwright 直接操作浏览器实现
    # 当前返回空——由外部 Playwright 会话驱动
    return []


# ─── 测试入口 ───────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="知网研学文献搜索")
    parser.add_argument("keyword", help="搜索关键词 (物种中文名/学名)")
    parser.add_argument("--max-results", type=int, default=10, help="最大返回数")
    parser.add_argument("--dbcode", default="CJFQ", help="数据库代码")
    args = parser.parse_args()

    papers = search_cnki(args.keyword, max_results=args.max_results, dbcode=args.dbcode)
    print(json.dumps([asdict(p) for p in papers], ensure_ascii=False, indent=2))
    print(f"\n总计: {len(papers)} 篇")
