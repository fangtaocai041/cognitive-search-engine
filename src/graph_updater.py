"""
graph_updater — 知识图谱更新引擎 (GraphUpdater v1.0)

管理搜索结果的图谱写入：论文节点添加、引用边连接、CN/EN 去重合并。

Usage:
    from src.graph_updater import GraphUpdater

    updater = GraphUpdater()
    updater.add_papers("Coilia_nasus", papers)
    stats = updater.stats("Coilia_nasus")
    updater.persist("Coilia_nasus")
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ── 数据类 ──────────────────────────────────────────


@dataclass
class PaperNode:
    """图谱中的论文节点。"""
    doi: str
    title: str = ""
    title_zh: str = ""         # 中文标题（用于 CN/EN 去重）
    authors: list[str] = field(default_factory=list)
    authors_zh: list[str] = field(default_factory=list)  # 作者中文名
    year: Optional[int] = None
    journal: str = ""
    journal_zh: str = ""       # 中文期刊名
    citations: int = 0
    credibility: float = 0.0   # 0-100 可信度评分
    category: str = "unknown"
    source_engine: str = ""
    added_at: float = 0.0

    def dedup_key(self) -> str:
        """去重键：优先 DOI，其次归一化标题。"""
        if self.doi:
            return f"doi:{self.doi.lower()}"
        norm = self.title.strip().lower().replace(" ", "")
        if self.title_zh:
            norm_zh = self.title_zh.strip().replace(" ", "")
            return f"title:{norm or norm_zh}"
        return f"title:{norm}"


@dataclass
class CitationEdge:
    """论文间的引用边。"""
    source_doi: str
    target_doi: str
    weight: float = 1.0


# ── GraphUpdater ────────────────────────────────────


class GraphUpdater:
    """知识图谱更新引擎。

    维护每个物种的独立子图：节点集 (papers) + 边集 (citations)。
    支持 CN/EN 自动去重、可信度排序、持久化。
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._graphs: dict[str, dict[str, PaperNode]] = {}       # species_id → {dedup_key → PaperNode}
        self._edges: dict[str, list[CitationEdge]] = {}          # species_id → edges
        self._data_dir: Path = (
            Path(data_dir) if data_dir
            else Path(__file__).resolve().parent.parent / "data" / "graphs"
        )
        self._data_dir.mkdir(parents=True, exist_ok=True)

    # ── 节点操作 ────────────────────────────────────

    def add_papers(self, species_id: str, papers: list[dict[str, Any]]) -> dict[str, Any]:
        """批量添加论文到图谱。返回新增/更新/去重统计。"""
        if species_id not in self._graphs:
            self._graphs[species_id] = {}
            self._edges[species_id] = []

        graph = self._graphs[species_id]
        stats: dict[str, Any] = {"added": 0, "updated": 0, "deduped": 0, "total": len(papers)}

        for raw in papers:
            node = self._dict_to_node(raw)
            key = node.dedup_key()

            if key in graph:
                existing = graph[key]
                # 更新：新数据优先级更高
                if raw.get("credibility", 0) > existing.credibility:
                    graph[key] = node
                    stats["updated"] += 1
                else:
                    stats["deduped"] += 1
            else:
                graph[key] = node
                stats["added"] += 1

        return stats

    def _dict_to_node(self, raw: dict[str, Any]) -> PaperNode:
        """将原始论文字典转为 PaperNode。"""
        return PaperNode(
            doi=raw.get("doi", "") or "",
            title=raw.get("title", "") or "",
            title_zh=raw.get("title_zh", "") or raw.get("chinese_title", "") or "",
            authors=raw.get("authors", []) or [],
            authors_zh=raw.get("authors_zh", []) or [],
            year=raw.get("year"),
            journal=raw.get("journal", "") or "",
            journal_zh=raw.get("journal_zh", "") or "",
            citations=int(raw.get("citations", 0) or 0),
            credibility=float(raw.get("credibility", raw.get("trust_score", 0)) or 0),
            category=raw.get("category", "unknown") or "unknown",
            source_engine=raw.get("source_engine", "") or "",
            added_at=time.time(),
        )

    # ── 边操作 ──────────────────────────────────────

    def add_citation(self, species_id: str, source_doi: str, target_doi: str) -> None:
        """添加引用边。"""
        if species_id not in self._edges:
            self._edges[species_id] = []
        self._edges[species_id].append(CitationEdge(source_doi=source_doi, target_doi=target_doi))

    # ── 查询 ────────────────────────────────────────

    def get_papers(self, species_id: str) -> list[PaperNode]:
        """获取物种图谱的所有论文节点。"""
        graph = self._graphs.get(species_id, {})
        return sorted(graph.values(), key=lambda n: n.credibility, reverse=True)

    def get_paper_count(self, species_id: str) -> int:
        """获取物种的论文总数。"""
        return len(self._graphs.get(species_id, {}))

    def stats(self, species_id: str) -> dict[str, Any]:
        """返回物种图谱统计。"""
        graph = self._graphs.get(species_id, {})
        edges = self._edges.get(species_id, [])
        if not graph:
            return {"species_id": species_id, "papers": 0, "edges": 0}
        categories: dict[str, int] = {}
        for node in graph.values():
            categories[node.category] = categories.get(node.category, 0) + 1
        return {
            "species_id": species_id,
            "papers": len(graph),
            "edges": len(edges),
            "categories": categories,
            "avg_credibility": sum(n.credibility for n in graph.values()) / max(len(graph), 1),
        }

    # ── 持久化 ──────────────────────────────────────

    def persist(self, species_id: str) -> None:
        """将物种图谱写入 JSON 文件。"""
        graph = self._graphs.get(species_id, {})
        edges = self._edges.get(species_id, [])
        payload = {
            "species_id": species_id,
            "papers": [{
                "doi": n.doi,
                "title": n.title,
                "title_zh": n.title_zh,
                "authors": n.authors,
                "authors_zh": n.authors_zh,
                "year": n.year,
                "journal": n.journal,
                "journal_zh": n.journal_zh,
                "citations": n.citations,
                "credibility": n.credibility,
                "category": n.category,
                "source_engine": n.source_engine,
            } for n in graph.values()],
            "edges": [{"source_doi": e.source_doi, "target_doi": e.target_doi, "weight": e.weight}
                      for e in edges],
            "updated_at": time.time(),
        }
        path = self._data_dir / f"{species_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, species_id: str) -> bool:
        """从 JSON 文件加载物种图谱。"""
        path = self._data_dir / f"{species_id}.json"
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            graph: dict[str, PaperNode] = {}
            for p in payload.get("papers", []):
                node = PaperNode(**{k: v for k, v in p.items() if k in PaperNode.__dataclass_fields__})
                graph[node.dedup_key()] = node
            self._graphs[species_id] = graph
            self._edges[species_id] = [
                CitationEdge(**e) for e in payload.get("edges", [])
            ]
            return True
        except (json.JSONDecodeError, KeyError, OSError, TypeError):
            return False

    def list_species(self) -> list[str]:
        """列出所有有图谱的物种。"""
        return [p.stem for p in self._data_dir.glob("*.json")]
