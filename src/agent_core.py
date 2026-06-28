"""agent_core — ⚠ DEPRECATED since v5.7.

Original BDI + ReAct CognitiveAgent logic has moved to:
    src/meso_agent/_agent.py → MesoAgent

This file is kept as a backward-compat shim for test imports.
New code should import from src.meso_agent directly.
"""

from __future__ import annotations

from src._utils import DotDict  # noqa: F401 — re-export for backward compat

__all__ = ["DotDict"]
