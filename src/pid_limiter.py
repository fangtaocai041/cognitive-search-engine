"""Re-export from eon-core — canonical source of truth.

This file is kept for backward compatibility. All implementations
now live in eon-core/src/shared/pid_limiter.py.

Usage remains the same:
    from src.pid_limiter import PIDRateLimiter
"""

from __future__ import annotations
import sys as _sys
import os as _os

_EON_SHARED = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), '..', '..', 'eon-core', 'src', 'shared')
)
if _EON_SHARED not in _sys.path:
    _sys.path.insert(0, _EON_SHARED)

from pid_limiter import PIDRateLimiter  # type: ignore[import-untyped]

__all__ = ["PIDRateLimiter"]