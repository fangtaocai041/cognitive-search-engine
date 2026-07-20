"""
paper_qa — 论文问答（借鉴 SciSpace AI）

对一篇论文提问，自动获取论文全文并用 LLM 回答。

支持的论文标识:
  - PMCID: "PMC1234567"
  - PMID:  "12345678"
  - DOI:   "10.1000/xyz123"
  - arXiv: "2106.12345"

工作流:
  1. 根据标识类型获取论文全文/摘要
  2. 将文本分段后传给 LLM
  3. LLM 基于论文内容回答问题

使用示例:
    from src.paper_qa import ask_paper

    answer = ask_paper("PMC1234567", "这篇论文用了什么方法?")
    # → "本文使用了随机对照试验方法..."
"""

from __future__ import annotations
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# LLM 配置
_LLM_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
_LLM_BASE_URL = "https://api.deepseek.com/v1"
_LLM_MODEL = "deepseek-chat"


# ═══════════════════════════════════════════════════════════════
# 论文内容获取
# ═══════════════════════════════════════════════════════════════

def fetch_paper_content(identifier: str) -> Dict[str, Any]:
    """获取论文全文/摘要

    自动检测标识类型，使用最合适的工具获取内容。

    Args:
        identifier: DOI / PMID / PMCID / arXiv ID

    Returns:
        {"title": str, "content": str, "source": str, "error": str}
    """
    ident_upper = identifier.upper().strip()

    # 1. PMCID → Europe PMC 全文
    if ident_upper.startswith("PMC"):
        return _fetch_from_pmc(ident_upper)

    # 2. PMID → NCBI 摘要
    if ident_upper.isdigit():
        return _fetch_from_pubmed(ident_upper)

    # 3. arXiv ID
    if "/" in identifier or any(c.isdigit() for c in identifier[:5]):
        # 尝试从 arXiv 获取
        return _fetch_from_arxiv(identifier)

    # 4. DOI → Crossref 元数据 + 尝试全文
    if "/" in identifier and ("." in identifier):
        return _fetch_from_doi(identifier)

    return {"title": "", "content": "", "source": "unknown",
            "error": f"无法识别的标识格式: {identifier}"}


def _fetch_from_pmc(pmcid: str) -> Dict[str, Any]:
    """从 Europe PMC / PMC 获取全文"""
    result = {"title": "", "content": "", "source": "pmc", "error": ""}
    try:
        # 尝试通过 article 工具获取
        article_fn = globals().get("get_article_details")
        if article_fn:
            data = article_fn(pmcid=[pmcid], format="text")
            articles = data.get("articles", [])
            if articles and articles[0].get("fulltext"):
                result["title"] = articles[0].get("title", "")
                result["content"] = articles[0]["fulltext"][:30000]
                return result
        # 没有 MCP 工具时返回空
        result["error"] = "PMC article tool not available in this session"
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


def _fetch_from_pubmed(pmid: str) -> Dict[str, Any]:
    """从 PubMed 获取摘要"""
    result = {"title": "", "content": "", "source": "pubmed", "error": ""}
    try:
        ncbi_fn = globals().get("ncbi_efetch")
        if ncbi_fn:
            data = ncbi_fn(pmid=pmid)
            if data:
                result["title"] = data.get("title", "")
                abstract = data.get("abstract", "")
                result["content"] = abstract[:20000]
                return result
        result["error"] = "NCBI tool not available in this session"
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


def _fetch_from_arxiv(arxiv_id: str) -> Dict[str, Any]:
    """从 arXiv 获取论文"""
    result = {"title": "", "content": "", "source": "arxiv", "error": ""}
    try:
        arxiv_fn = globals().get("read_arxiv_paper")
        if arxiv_fn:
            text = arxiv_fn(paper_id=arxiv_id)
            if text and len(text) > 100:
                lines = text.split("\n")
                result["title"] = lines[0][:200] if lines else ""
                result["content"] = text[:30000]
                return result
        result["error"] = "arXiv tool not available"
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


def _fetch_from_doi(doi: str) -> Dict[str, Any]:
    """通过 DOI 获取论文信息"""
    result = {"title": "", "content": "", "source": "doi", "error": ""}
    try:
        crossref_fn = globals().get("get_crossref_paper_by_doi")
        if crossref_fn:
            data = crossref_fn(doi=doi)
            if data:
                result["title"] = data.get("title", "")
                abstract = data.get("abstract", "")
                result["content"] = (abstract or "")[:20000]
                return result
        result["error"] = "CrossRef tool not available"
    except Exception as e:
        result["error"] = str(e)[:200]
    return result


# ═══════════════════════════════════════════════════════════════
# LLM 问答
# ═══════════════════════════════════════════════════════════════

def ask_llm(paper_content: str, question: str, api_key: str = "") -> str:
    """用 LLM 基于论文内容回答问题

    Args:
        paper_content: 论文全文/摘要文本
        question: 用户问题
        api_key: DeepSeek API key (默认从 DEEPSEEK_API_KEY 环境变量读取)

    Returns:
        LLM 的回答文本
    """
    key = api_key or _LLM_API_KEY
    if not key:
        return "需要设置 DEEPSEEK_API_KEY 环境变量或传入 api_key 参数"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=_LLM_BASE_URL)

        # 截断论文内容到合理长度
        max_chars = 25000
        truncated = paper_content[:max_chars]
        if len(paper_content) > max_chars:
            truncated += "\n\n[...论文较长，已截断...]"

        response = client.chat.completions.create(
            model=_LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个学术论文助手。基于以下论文内容回答问题。"
                 "如果论文内容不足以回答问题，请如实说明。引用论文中的具体内容来支持你的回答。"},
                {"role": "user", "content": f"论文内容：\n{truncated}\n\n问题：{question}"},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        return f"LLM 调用失败: {e}"


# ═══════════════════════════════════════════════════════════════
# 主接口
# ═══════════════════════════════════════════════════════════════

def ask_paper(
    identifier: str,
    question: str,
    api_key: str = "",
    verbose: bool = False,
) -> Dict[str, Any]:
    """对一篇论文提问

    Args:
        identifier: 论文标识 (DOI / PMID / PMCID / arXiv ID)
        question: 你的问题
        api_key: DeepSeek API key (可选，默认读环境变量)
        verbose: 是否返回论文内容等详细信息

    Returns:
        {"answer": str, "title": str, "source": str, "error": str}
    """
    # 1. 获取论文内容
    paper = fetch_paper_content(identifier)

    if paper["error"]:
        return {
            "answer": f"无法获取论文: {paper['error']}",
            "title": paper.get("title", ""),
            "source": paper.get("source", ""),
            "error": paper["error"],
        }

    if not paper["content"]:
        return {
            "answer": "获取到论文但内容为空，可能是付费论文或格式不支持。",
            "title": paper.get("title", ""),
            "source": paper.get("source", ""),
            "error": "empty content",
        }

    # 2. 用 LLM 回答
    answer = ask_llm(paper["content"], question, api_key)

    result = {
        "answer": answer,
        "title": paper["title"],
        "source": paper["source"],
        "error": "",
    }

    if verbose:
        result["content_preview"] = paper["content"][:500]

    return result
