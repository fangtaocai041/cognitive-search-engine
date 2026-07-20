"""
AMiner 学术搜索 — MCP 协议接入

AMiner 提供 MCP (Model Context Protocol) 服务，通过 SSE 传输。
可用的搜索工具由 AMiner MCP Server 动态提供。

端点: https://mcp.aminer.cn/sse
认证: Authorization Header Token (通过 AMINER_API_KEY 环境变量注入)
传输: SSE (Server-Sent Events)

使用示例:
    papers = search_aminer_sync("Coilia nasus", limit=10)
"""

from __future__ import annotations
from ._shared import logger

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

_AMINER_MCP_URL = "https://mcp.aminer.cn/sse"
_AMINER_TOKEN = os.environ.get("AMINER_API_KEY", "")


def search_aminer_sync(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """同步版的 AMiner 学术搜索。

    通过 AMiner MCP 的 SSE 端点搜索学术论文。
    MCP 协议原生是异步的，此函数使用 asyncio 事件循环做同步封装。
    """
    if not _AMINER_TOKEN:
        logger.warning("AMiner API key not set (AMINER_API_KEY)")
        return []

    try:
        async def _search():
            try:
                from mcp import ClientSession
                from mcp.client.sse import sse_client

                headers = {"Authorization": f"{_AMINER_TOKEN}"}

                async with sse_client(url=_AMINER_MCP_URL, headers=headers) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()

                        # 获取可用工具列表
                        tools_result = await session.list_tools()
                        tool_names = [t.name for t in tools_result.tools]
                        logger.debug(f"AMiner MCP tools available: {tool_names}")

                        # 查找搜索相关的工具
                        search_tool = None
                        for tool in tools_result.tools:
                            if "search" in tool.name.lower() or "paper" in tool.name.lower():
                                search_tool = tool
                                break

                        if not search_tool:
                            logger.warning("No search tool found in AMiner MCP")
                            return []

                        # 构建搜索参数
                        args = {"query": query}
                        if max_results:
                            args["limit"] = min(max_results, 50)

                        result = await session.call_tool(search_tool.name, args)
                        raw_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        raw = json.loads(raw_text)

                        # AMiner 返回格式: {"code":200, "success":true, "data": [...]}
                        if isinstance(raw, dict) and raw.get("success"):
                            items = raw.get("data", [])
                        elif isinstance(raw, list):
                            items = raw
                        else:
                            items = raw.get("data", raw.get("items", raw.get("results", [])))

                        # 标准化结果
                        papers = []
                        for item in items if isinstance(items, list) else [items]:
                            paper = _normalize_aminer_paper(item)
                            if paper:
                                papers.append(paper)
                        return papers

            except ImportError:
                logger.warning("mcp package not installed. Install with: pip install mcp")
                return []
            except Exception as e:
                logger.debug(f"AMiner MCP search failed: {e}")
                return []

        loop = _get_or_create_event_loop()
        return loop.run_until_complete(_search())

    except Exception as e:
        logger.debug(f"AMiner MCP search error: {e}")
        return []


# 供 _engine.py 使用的别名
_search_aminer = search_aminer_sync


def _get_or_create_event_loop():
    """获取或创建事件循环（兼容不同 Python 版本）"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _normalize_aminer_paper(item: Any) -> Optional[Dict[str, Any]]:
    """标准化 AMiner 论文格式"""
    if isinstance(item, str):
        try:
            item = json.loads(item)
        except json.JSONDecodeError:
            return None
    if not isinstance(item, dict):
        return None
    title = item.get("title") or item.get("Title") or ""
    if not title:
        return None
    authors_raw = item.get("authors") or item.get("Authors") or []
    if isinstance(authors_raw, str):
        authors_raw = [{"name": a.strip()} for a in authors_raw.split(";") if a.strip()]
    doi = item.get("doi") or item.get("DOI") or ""
    year_raw = item.get("year") or item.get("Year") or 0
    year = int(year_raw) if year_raw else 0
    return {
        "title": title,
        "authors": authors_raw,
        "author_str": "; ".join(a.get("name", "") if isinstance(a, dict) else str(a) for a in authors_raw if (a.get("name") if isinstance(a, dict) else str(a))),
        "abstract": item.get("abstract") or item.get("Abstract") or "",
        "year": year,
        "venue": item.get("venue") or item.get("Venue") or item.get("journal") or "",
        "doi": doi,
        "citations": int(item.get("citations") or item.get("citation_count") or 0),
        "keywords": item.get("keywords") or item.get("Keywords") or [],
        "source": "aminer",
        "url": f"https://www.aminer.org/{(doi or item.get('id',''))}",
    }


def _call_aminer_tool(tool_name: str, args: dict) -> list:
    """通用 AMiner MCP 工具调用（同步封装）

    连接 AMiner MCP → 调用指定工具 → 返回标准化结果列表
    """
    if not _AMINER_TOKEN:
        logger.warning("AMiner API key not set (AMINER_API_KEY)")
        return []

    try:
        async def _call():
            try:
                from mcp import ClientSession
                from mcp.client.sse import sse_client

                headers = {"Authorization": f"{_AMINER_TOKEN}"}
                async with sse_client(url=_AMINER_MCP_URL, headers=headers) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, args)
                        raw_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                        raw = json.loads(raw_text)
                        if isinstance(raw, dict) and raw.get("success"):
                            items = raw.get("data", [])
                        elif isinstance(raw, list):
                            items = raw
                        else:
                            items = raw.get("data", raw.get("items", raw.get("results", [])))
                        return items if isinstance(items, list) else [items]
            except ImportError:
                logger.warning("mcp package not installed")
                return []
            except Exception as e:
                logger.debug(f"AMiner tool {tool_name} failed: {e}")
                return []

        loop = _get_or_create_event_loop()
        return loop.run_until_complete(_call())
    except Exception as e:
        logger.debug(f"AMiner tool {tool_name} error: {e}")
        return []


def search_aminer_person(name: str, max_results: int = 10) -> list:
    """搜索学者

    按姓名查找学者，返回学术档案信息。

    Args:
        name: 学者姓名（中英文均可）
        max_results: 最大结果数

    Returns:
        list[dict]: 学者信息列表
    """
    items = _call_aminer_tool("search_person", {"name": name, "offset": 0, "size": min(max_results, 50)})
    results = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        results.append({
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "name_zh": item.get("name_zh", ""),
            "org": item.get("org", ""),
            "org_zh": item.get("org_zh", ""),
            "position": item.get("position", ""),
            "h_index": item.get("h_index", 0),
            "paper_count": item.get("paper_count", 0),
            "citation_count": item.get("citation_count", 0),
            "tags": item.get("tags", []),
            "source": "aminer_person",
            "url": f"https://www.aminer.org/profile/{item.get('id', '')}" if item.get("id") else "",
        })
    return results


def search_aminer_organization(name: str, max_results: int = 10) -> list:
    """搜索机构

    按名称查找学术机构。

    Args:
        name: 机构名称
        max_results: 最大结果数

    Returns:
        list[dict]: 机构信息列表
    """
    items = _call_aminer_tool("search_organization", {"orgs": name})
    results = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        results.append({
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "name_zh": item.get("name_zh", ""),
            "name_en": item.get("name_en", ""),
            "department": item.get("department", ""),
            "country": item.get("country", ""),
            "paper_count": item.get("paper_count", 0),
            "person_count": item.get("person_count", 0),
            "source": "aminer_org",
            "url": f"https://www.aminer.org/organization/{item.get('id', '')}" if item.get("id") else "",
        })
    return results


def search_aminer_patent(query: str, max_results: int = 10) -> list:
    """搜索专利

    按关键词搜索学术专利。

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        list[dict]: 专利信息列表
    """
    items = _call_aminer_tool("search_patent", {"query": query, "page": 1, "size": min(max_results, 50)})
    results = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        results.append({
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "abstract": item.get("abstract", ""),
            "inventors": item.get("inventors", []),
            "applicant": item.get("applicant", ""),
            "patent_number": item.get("patent_number", ""),
            "application_date": item.get("application_date", ""),
            "publication_date": item.get("publication_date", ""),
            "status": item.get("status", ""),
            "source": "aminer_patent",
            "url": f"https://www.aminer.org/patent/{item.get('id', '')}" if item.get("id") else "",
        })
    return results
