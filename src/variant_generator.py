"""Re-export from eon-core — canonical source of truth.

This file is kept for backward compatibility. All implementations
now live in eon-core/src/shared/variant_generator.py.

Usage remains the same:
    from src.variant_generator import generate_variants, generate_full_species_variants
"""

from __future__ import annotations
import sys as _sys
import os as _os

# Add eon-core shared to path and re-export
_EON_SHARED = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), '..', '..', 'eon-core', 'src', 'shared')
)
if _EON_SHARED not in _sys.path:
    _sys.path.insert(0, _EON_SHARED)

from variant_generator import (  # type: ignore[import-untyped]
    generate_variants,
    generate_full_species_variants,
)

__all__ = ["generate_variants", "generate_full_species_variants"]
