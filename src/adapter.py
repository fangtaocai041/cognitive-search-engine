"""CognitiveSearchAdapter — cognitive-search-engine (V1 / V-Verify).

Wraps the existing MesoAgent + SearchRuleEngine into a standard
IProjectAdapter interface for project_loader.

Capabilities:
  - search(query, mode="adaptive") → species literature search
  - graph_lookup(species_id) → knowledge graph traversal
  - verify_claims(claims) → multi-source verification
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import shared adapter protocol (workspace root on sys.path)
try:
    from scripts.adapter_protocol import IProjectAdapter
except ImportError:
    IProjectAdapter = object  # fallback for standalone usage


class CognitiveSearchAdapter(IProjectAdapter):
    """Adapter for cognitive-search-engine (V1 — 验证引擎).

    Wraps MesoAgent.search() for cross-project consumption.
    Maintains importlib cache internally.
    """

    project_name = "cognitive-search-engine"

    def __init__(self) -> None:
        self._engine: Any = None
        self._engine_root: Optional[Path] = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Lazy-init the cognitive engine via direct import."""
        try:
            from src.meso_agent import create_agent
            self._engine = create_agent(mode="http")
            self._engine_root = Path(__file__).resolve().parent.parent
        except Exception as exc:
            logger.warning(f"Cognitive engine init failed: {exc}")

    # ── IProjectAdapter interface ──

    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute a cognitive search.

        IF engine available THEN call MesoAgent.search().
        ELSE return stub.

        Args:
          query: species name or search query
          mode: "adaptive" (BDI+ReAct), "linear" (phases), "graph" (traversal only)
        """
        mode = kwargs.get("mode", "adaptive")

        if self._engine:
            try:
                species_id = query.replace(" ", "_")
                result = self._engine.search(species_id)
                if hasattr(result, "to_dict"):
                    return result.to_dict()
                return {"status": "ok", "result": str(result)}
            except Exception as exc:
                return {"status": "error", "error": str(exc)}

        return {
            "status": "unavailable",
            "query": query,
            "mode": mode,
            "note": "Cognitive engine not loaded — install or check path",
        }

    def health(self) -> Dict[str, Any]:
        """Health check."""
        return {
            "project": self.project_name,
            "status": "HEALTHY" if self._engine else "DEGRADED",
            "engine_loaded": self._engine is not None,
            "engine_root": str(self._engine_root) if self._engine_root else None,
        }

    def info(self) -> Dict[str, Any]:
        """Version + capabilities."""
        return {
            "project": self.project_name,
            "role": "V1_VerifyVertex",
            "symbol": "🌙 太阴·老阴",
            "wuxing": "木 (WOOD)",
            "capabilities": [
                "species_search",
                "graph_traversal",
                "multi_model_debate",
                "variant_generation",
                "credibility_scoring",
                "BDI_cognitive_architecture",
            ],
        }

    # ── KB-First: 搜索前检查 f 项目知识库 ──

    def check_fish_knowledge_base(self, species_id: str) -> Dict[str, Any]:
        """搜索前检查 fish-ecology-assistant 知识库已有内容.

        三角闭环: V0(fish) → V1(cognitive) 状态同步.
        避免重复搜索已知文献.

        Returns:
            {"found": bool, "papers_count": int, "kb_path": str}
        """
        import os
        from pathlib import Path

        base = Path(__file__).resolve().parent.parent.parent
        kb_dir = base / "fish-ecology-assistant" / "data" / "knowledge_base"

        if not kb_dir.exists():
            return {"found": False, "papers_count": 0, "kb_path": str(kb_dir), "note": "f项目知识库不存在"}

        # 搜索匹配的知识库文件
        species_key = species_id.replace("_", " ").lower()
        matched_files = list(kb_dir.glob(f"*{species_key.replace(' ', '_')}*"))
        matched_files += list(kb_dir.glob(f"*{species_key.split(' ')[0]}*"))

        total_papers = 0
        for mf in matched_files:
            try:
                text = mf.read_text(encoding="utf-8", errors="replace")
                # 粗略统计论文条目
                import re
                papers = re.findall(r'(?:^|\n)#+\s+|^-\s+\[|^\[\d+\]|DOI[:：]', text, re.MULTILINE)
                total_papers += len(papers)
            except Exception:
                pass

        return {
            "found": len(matched_files) > 0,
            "papers_count": total_papers,
            "files_found": [str(mf.relative_to(kb_dir)) for mf in matched_files],
            "kb_path": str(kb_dir),
            "note": None if total_papers > 0 else "知识库文件存在但未解析出论文条目",
        }

    # ── 三角闭环状态同步 ──

    def sync_stv_state(self, species_id: str,
                       state_vector: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """三角闭环状态同步.

        从 V0(fish) 接收 state_vector, 返回 V1(cognitive) 的验证状态.

        Args:
            species_id: 物种 ID
            state_vector: S 项目传来的状态向量 (schema, findings, contradiction)
        """
        # 查询图谱
        graph_info = self.graph_lookup(species_id)

        # 验证状态
        verification = {
            "species_id": species_id,
            "verified_papers": graph_info.get("papers_count", 0) if isinstance(graph_info, dict) else 0,
            "engine": "cognitive-search-engine",
            "role": "V_Validation",
            "feedback": "可用",
        }

        if state_vector:
            # 处理 S 项目传来的矛盾信号
            contradiction = state_vector.get("contradiction")
            if contradiction:
                verification["contradiction_detected"] = True
                verification["action"] = "需要重新搜索验证"
        else:
            verification["contradiction_detected"] = False

        return verification

    # ── Domain methods ──

    def graph_lookup(self, species_id: str) -> Dict[str, Any]:
        """Look up species in the knowledge graph (species_graph.yaml).

        Delegates to graph_updater.load_species_graph() if available.
        """
        try:
            from src.graph_updater import load_species_graph
            papers = load_species_graph(species_id)
            return {
                "status": "ok",
                "species_id": species_id,
                "graph_nodes": papers,
                "node_count": len(papers),
                "engine": "cognitive-search-engine",
            }
        except ImportError:
            return {"status": "degraded", "species_id": species_id,
                    "graph_nodes": [], "note": "graph_updater not available"}

    def verify_claims(self, claims: List[str]) -> Dict[str, Any]:
        """Verify claims via cross-project validator.

        Delegates to validator.validate_papers() if available.
        """
        try:
            from src.validator import validate_papers
            # Convert claims to minimal paper dicts for validation
            papers = [{"title": c, "source": "claim"} for c in claims]
            result = validate_papers(papers, min_sources=2, min_projects=1)
            stats = getattr(result, "stats", {}) or {}
            return {
                "status": "ok",
                "claims_count": len(claims),
                "verified": stats.get("verified_count", 0) if isinstance(stats, dict) else 0,
                "independence_passed": stats.get("independence_passed", False) if isinstance(stats, dict) else False,
                "engine": "cognitive-search-engine",
            }
        except ImportError:
            return {"status": "degraded", "claims_count": len(claims),
                    "verified": 0, "note": "validator not available"}

    def verify(self, query: str, **kwargs) -> Dict[str, Any]:
        """Standard pipeline verification stage.

        Called by cross_project pipeline as cognitive.verify.
        Accepts prior_outputs from fish.search stage and validates
        the search results via multi-source cross-checking.

        Args:
            query: species name or search query
            prior_outputs: dict of prior stage outputs (from fish.search)
            species: species name override
        """
        prior = kwargs.get("prior_outputs", {})
        species = kwargs.get("species", query)

        # Extract claims from prior fish.search output
        claims = []
        fish_output = prior.get("fish", {})
        if isinstance(fish_output, dict):
            # Extract species data as claims
            species_data = fish_output.get("species_data", {})
            if species_data:
                for key in ("scientific_name", "chinese_name", "family",
                            "conservation", "ecology"):
                    val = species_data.get(key, "")
                    if val:
                        claims.append(f"{key}: {val}")
            # Extract knowledge items
            for item in fish_output.get("knowledge_items", []):
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    item_data = item.get("data", {})
                    if item_data:
                        claims.append(f"{item_type}: {str(item_data)[:200]}")

        if not claims:
            # Fallback: verify the query itself as a claim
            claims = [f"species: {query}"]

        # Run verification
        verify_result = self.verify_claims(claims)

        # Also do a KB check
        kb_check = self.check_fish_knowledge_base(species.replace(" ", "_"))

        return {
            "status": "ok",
            "query": query,
            "species": species,
            "claims_verified": len(claims),
            "verification": verify_result,
            "kb_check": kb_check,
            "engine": "cognitive-search-engine",
            "role": "V1_VerifyVertex",
            "method": "verify",
        }


    # ── AMiner 实体搜索（学者/机构/专利） ──

    def aminer_search_person(self, name: str, max_results: int = 10) -> dict:
        """AMiner 学者搜索 — 按姓名查找学术档案"""
        try:
            from .entity import search_person
            results = search_person(name, max_results)
            return {"status": "ok", "source": "aminer_person", "count": len(results), "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def aminer_search_org(self, name: str, max_results: int = 10) -> dict:
        """AMiner 机构搜索 — 按名称查找学术机构"""
        try:
            from .entity import search_org
            results = search_org(name, max_results)
            return {"status": "ok", "source": "aminer_org", "count": len(results), "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def aminer_search_patent(self, query: str, max_results: int = 10) -> dict:
        """AMiner 专利搜索 — 按关键词搜索专利"""
        try:
            from .entity import search_patent
            results = search_patent(query, max_results)
            return {"status": "ok", "source": "aminer_patent", "count": len(results), "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_llm_tools(self) -> list:
        """获取 LLM function calling 工具定义"""
        try:
            from .tool_schema import ALL_TOOLS
            return ALL_TOOLS
        except Exception:
            return []

    # ── 论文问答（借鉴 SciSpace） ──

    def ask_paper(self, identifier: str, question: str, api_key: str = "") -> dict:
        """对一篇论文提问

        参数:
            identifier: 论文标识 (DOI/PMID/PMCID/arXiv)
            question: 你的问题

        返回:
            {"answer": str, "title": str, "source": str}
        """
        try:
            from .paper_qa import ask_paper as _ask
            return _ask(identifier, question, api_key)
        except Exception as e:
            return {"answer": "", "title": "", "error": str(e)}


def get_adapter() -> CognitiveSearchAdapter:
    """Factory function for project_loader."""
    return CognitiveSearchAdapter()
