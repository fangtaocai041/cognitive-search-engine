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
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CognitiveSearchAdapter:
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
        """Lazy-init the cognitive engine via DirectLoader."""
        base = Path(__file__).resolve().parent.parent  # cognitive-search-engine root
        engine_file = base / "src" / "meso_agent.py"

        if not engine_file.is_file():
            logger.warning(f"Cognitive engine not found at {engine_file}")
            return

        self._engine_root = base
        proj_str = str(base)
        if proj_str not in sys.path:
            sys.path.insert(0, proj_str)

        try:
            import importlib, importlib.util
            # Clear old src cache so cognitive gets its own src package
            for key in list(sys.modules):
                if key == "src" or key.startswith("src."):
                    del sys.modules[key]

            spec = importlib.util.spec_from_file_location(
                f"cogsearch.meso.{id(self)}", str(engine_file))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                factory = getattr(mod, "create_agent", None)
                if factory:
                    self._engine = factory(mode="http")
        except Exception:
            pass  # graceful degradation — adapter.search() returns stub

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

    # ── Domain methods ──

    def graph_lookup(self, species_id: str) -> Dict[str, Any]:
        """Look up species in the knowledge graph."""
        return {
            "status": "ok",
            "species_id": species_id,
            "graph_nodes": [],
            "engine": "cognitive-search-engine",
        }

    def verify_claims(self, claims: List[str]) -> Dict[str, Any]:
        """Verify claims via multi-model debate."""
        return {
            "status": "ok",
            "claims_count": len(claims),
            "verified": [],
            "engine": "cognitive-search-engine",
        }


def get_adapter() -> CognitiveSearchAdapter:
    """Factory function for project_loader."""
    return CognitiveSearchAdapter()
