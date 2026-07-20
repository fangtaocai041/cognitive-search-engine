"""
paper_analyzer — 论文结构化分析（借鉴 SciSpace）

对一篇论文提取结构化信息：方法、发现、局限性、结论。
工作流: DOI → CrossRef 获取元数据 → 获取全文 → LLM 分析 → 结构化输出

使用 DeepSeek API（兼容 OpenAI 格式），需设置 DEEPSEEK_API_KEY 环境变量。

用法:
    from src.paper_analyzer import analyze_paper
    result = analyze_paper("10.1007/s10641-020-00986-1")
    print(result["methods"][:200])
    print(result["findings"][:200])
"""

from __future__ import annotations
from ._shared import _HEADERS, _TIMEOUT_S, logger

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional

_DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 如果环境变量没有，尝试从 Reasonix 全局 .env 读取
if not _DEEPSEEK_API_KEY:
    _reasonix_env = os.path.expanduser("~/AppData/Roaming/reasonix/.env")
    try:
        with open(_reasonix_env) as f:
            for line in f:
                if line.startswith("DEEPSEEK_API_KEY="):
                    _DEEPSEEK_API_KEY = line.strip().split("=", 1)[1]
                    break
    except Exception:
        pass
_DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
_DEEPSEEK_MODEL = "deepseek-chat"

# ── 1. 通过 CrossRef 获取论文元数据 ──


def _fetch_metadata(doi: str) -> Dict[str, Any]:
    """通过 CrossRef API 获取论文元数据"""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        req = urllib.request.Request(url, headers={**_HEADERS, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            data = json.loads(resp.read())
            msg = data.get("message", {})
            return {
                "title": msg.get("title", [""])[0] if msg.get("title") else "",
                "authors": [a.get("given", "") + " " + a.get("family", "") for a in msg.get("author", [])],
                "year": msg.get("published-print", {}).get("date-parts", [[0]])[0][0] or 0,
                "journal": msg.get("container-title", [""])[0] if msg.get("container-title") else "",
                "abstract": msg.get("abstract", ""),
                "doi": doi,
            }
    except Exception as e:
        logger.debug(f"CrossRef metadata failed for {doi}: {e}")
        return {"title": "", "abstract": "", "doi": doi}


# ── 2. 通过 DeepSeek 分析论文 ──

_ANALYSIS_PROMPT = """你是一位鱼类生态学领域的论文分析助手。请分析以下论文，提取关键信息并以 JSON 格式返回。

论文信息：
标题: {title}
作者: {authors}
年份: {year}
期刊: {journal}
摘要: {abstract}

请严格按以下 JSON 格式返回（不要加 markdown 标记，只返回纯 JSON）：
{{
    "methods": "该论文使用的研究方法（2-3句话）",
    "findings": "主要研究发现（3-4句话）",
    "limitations": "论文提到的局限性（1-2句话，如未提及则写\"未明确提及\"）",
    "conclusion": "研究结论（2-3句话）",
    "species": "研究对象物种名（如无则写\"无\"）",
    "keywords_extracted": ["关键词1", "关键词2"]
}}

如果没有摘要，请基于标题和期刊信息给出合理推测，并在每个字段前加"[推测]"前缀。"""


def _analyze_with_llm(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """调用 DeepSeek API 分析论文"""
    if not _DEEPSEEK_API_KEY:
        return {
            "methods": "需设置 DEEPSEEK_API_KEY 环境变量",
            "findings": "需设置 DEEPSEEK_API_KEY 环境变量",
            "limitations": "需设置 DEEPSEEK_API_KEY 环境变量",
            "conclusion": metadata.get("abstract", "")[:300] if metadata.get("abstract") else "需设置 API key",
            "species": "",
            "keywords_extracted": [],
        }

    title = metadata.get("title", "")
    authors = "; ".join(metadata.get("authors", [])[:5])
    year = metadata.get("year", 0)
    journal = metadata.get("journal", "")
    abstract = metadata.get("abstract", "")[:2000]

    prompt = _ANALYSIS_PROMPT.format(title=title, authors=authors, year=year, journal=journal, abstract=abstract)

    try:
        body = json.dumps({
            "model": _DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1500,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_DEEPSEEK_API_KEY}",
        }
        req = urllib.request.Request(_DEEPSEEK_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]

            # 尝试解析 JSON 响应
            import re as _re
            json_match = _re.search(r"\{.*\}", content, _re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"methods": content[:500], "findings": "", "limitations": "",
                    "conclusion": "", "species": "", "keywords_extracted": []}
    except Exception as e:
        logger.debug(f"LLM analysis failed: {e}")
        return {
            "methods": f"分析失败: {e}",
            "findings": "",
            "limitations": "",
            "conclusion": abstract[:500] if abstract else "",
            "species": "",
            "keywords_extracted": [],
        }


# ── 3. 对外接口 ──


def analyze_paper(doi: str) -> Dict[str, Any]:
    """分析一篇论文的结构化信息

    参数:
        doi: DOI 标识符

    返回:
        {
            "title": str,           # 论文标题
            "authors": list,        # 作者列表
            "year": int,            # 发表年份
            "journal": str,         # 期刊
            "methods": str,         # 研究方法
            "findings": str,        # 主要发现
            "limitations": str,     # 局限性
            "conclusion": str,      # 结论
            "species": str,         # 研究物种
            "keywords_extracted": list,  # 提取的关键词
        }
    """
    metadata = _fetch_metadata(doi)
    analysis = _analyze_with_llm(metadata)

    return {
        "title": metadata.get("title", ""),
        "authors": metadata.get("authors", []),
        "year": metadata.get("year", 0),
        "journal": metadata.get("journal", ""),
        "doi": doi,
        "methods": analysis.get("methods", ""),
        "findings": analysis.get("findings", ""),
        "limitations": analysis.get("limitations", ""),
        "conclusion": analysis.get("conclusion", ""),
        "species": analysis.get("species", ""),
        "keywords_extracted": analysis.get("keywords_extracted", []),
    }
