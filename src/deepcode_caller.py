"""DeepCodeCaller — 论文转代码适配器 (P0 集成).

Wraps deepcode-hku Paper2Code into cognitive-search-engine's pipeline.
Callable from search results to auto-generate reproducible code.

Usage:
    caller = DeepCodeCaller()
    result = caller.paper2code("path/to/paper.pdf")
    # or
    result = caller.paper2code_doi("10.xxxx/xxxxx")
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DeepCodeCaller:
    """Call DeepCode Paper2Code from within cognitive-search-engine.

    Two modes:
      1. paper2code(paper_path)   — local PDF file → code repo
      2. paper2code_doi(doi)       — download via DOI then convert
      3. paper2code_from_search() — called from search pipeline
    """

    def __init__(self, output_base: Optional[str] = None) -> None:
        self._engine: Any = None
        self._available: bool = False
        self._output_base = Path(output_base or self._default_output())
        self._output_base.mkdir(parents=True, exist_ok=True)
        self._lazy_init()

    # ── public API ──

    def paper2code(self, paper_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Convert a research paper PDF to production-ready code.

        Args:
            paper_path: Path to PDF file
            output_dir: Where to write the generated code (default: auto)

        Returns:
            {"status": "ok", "code_dir": "...", "file_count": N, ...}
            or {"status": "unavailable", ...} if DeepCode not installed
        """
        if not self._available:
            return self._unavailable_response("paper2code")

        paper = Path(paper_path)
        if not paper.exists():
            return {"status": "error", "error": f"File not found: {paper_path}"}

        out = Path(output_dir) if output_dir else self._output_base / paper.stem
        out.mkdir(parents=True, exist_ok=True)

        try:
            return self._run_paper2code(str(paper), str(out))
        except Exception as e:
            logger.exception(f"DeepCode paper2code failed: {e}")
            return {"status": "error", "error": str(e), "paper": paper_path}

    def paper2code_doi(self, doi: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Fetch a paper by DOI and convert it."""
        if not self._available:
            return self._unavailable_response("paper2code_doi")

        try:
            # Use paper-search MCP to get the paper, then convert
            from src.mcp_client import get_client

            client = get_client()
            paper_info = client.search_literature(keyword=doi, search_type="precise", max_results=1)

            papers = paper_info if isinstance(paper_info, list) else paper_info.get("papers", [])
            if not papers:
                return {"status": "error", "error": f"No paper found for DOI: {doi}"}

            best = papers[0]
            title = best.get("title", doi.replace("/", "_"))

            out = Path(output_dir) if output_dir else self._output_base / title[:60]
            out.mkdir(parents=True, exist_ok=True)

            # Try to get full text
            pmcid = best.get("pmcid") or best.get("pmc_id", "")
            if pmcid:
                fulltext = client.get_article(pmcid, format="markdown")
                text_path = out / f"{title[:40]}.md"
                if isinstance(fulltext, dict) and "content" in fulltext:
                    text_path.write_text(fulltext["content"], encoding="utf-8")
                    return self._run_paper2code(str(text_path), str(out))
                elif isinstance(fulltext, str):
                    text_path.write_text(fulltext, encoding="utf-8")
                    return self._run_paper2code(str(text_path), str(out))

            return {"status": "error", "error": "No full text available for this DOI",
                    "title": title, "doi": doi}
        except Exception as e:
            logger.exception(f"DeepCode DOI conversion failed: {e}")
            return {"status": "error", "error": str(e), "doi": doi}

    def health(self) -> Dict[str, Any]:
        """Check if DeepCode is available."""
        return {
            "name": "deepcode-caller",
            "available": self._available,
            "engine_loaded": self._engine is not None,
            "output_base": str(self._output_base),
        }

    # ── internals ──

    def _lazy_init(self) -> None:
        """Try importing deepcode — fail gracefully if not installed."""
        try:
            import deepcode  # noqa: F401
            self._available = True
            logger.info("DeepCode available — Paper2Code ready")
        except ImportError:
            self._available = False
            logger.warning("DeepCode not installed ('pip install deepcode-hku') — feature disabled")

    @staticmethod
    def _default_output() -> str:
        return os.environ.get(
            "DEEPCODE_OUTPUT",
            str(Path(__file__).resolve().parent.parent / "data" / "deepcode_output"),
        )

    def _run_paper2code(self, paper_path: str, output_dir: str) -> Dict[str, Any]:
        """Execute DeepCode Paper2Code."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "cli.exec_cli",
             f"Read the paper at {paper_path} and implement its core algorithms as runnable Python code. Generate complete, production-ready code.",
             "-w", output_dir],
            capture_output=True, text=True, timeout=600,
        )

        # Count generated files
        out_path = Path(output_dir)
        generated_files = list(out_path.rglob("*.py")) + list(out_path.rglob("*.R")) \
            + list(out_path.rglob("*.ipynb")) + list(out_path.rglob("*.md"))

        return {
            "status": "ok" if result.returncode == 0 else "partial",
            "paper": paper_path,
            "code_dir": output_dir,
            "file_count": len(generated_files),
            "files": [str(f.relative_to(out_path)) for f in generated_files[:50]],
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }

    def _unavailable_response(self, method: str) -> Dict[str, Any]:
        return {
            "status": "unavailable",
            "method": method,
            "note": "DeepCode not installed. Run: pip install deepcode-hku",
            "enabled": False,
        }


# ── standalone factory ──

def get_deepcode_caller(output_base: Optional[str] = None) -> DeepCodeCaller:
    """Factory: get or create a shared DeepCodeCaller instance."""
    return DeepCodeCaller(output_base=output_base)
