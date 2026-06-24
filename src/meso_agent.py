# ⚠ REFACTORED: This module has been split into the `meso_agent` package.
# Importing from here still works for backward compatibility, but new code
# should import directly from `src.meso_agent`.
#
# Usage (new):
#     from src.meso_agent import MesoAgent, create_agent, MesoConfig
#
# This file is kept as a thin re-export shim.

from __future__ import annotations

from src.meso_agent import (
    MesoAgent,
    MesoConfig,
    MesoSearchResult,
    create_agent,
    _extract_papers,
    _normalize_paper,
    _dedup_papers,
)
