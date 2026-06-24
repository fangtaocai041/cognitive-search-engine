"""
rcca_core.py - RCCA Core (Recursive Convergence Cognitive Architecture)

!! SHIM !! Canonical source: eon-core/src/shared/rcca_core.py
All imports transparently forwarded to canonical source.
This ensures all 7 projects always use the same version.

Includes:
  - SelfModelEngine (DSM damped self-model)
  - EmotionEngine (resource allocation strategy)
  - TranspositionLayer (jumping-gene transposition layer)
  - ReflectionLoop (reflection loop)
  - RecursiveThinker (recursive thinker)
"""

import sys
from pathlib import Path

# Ensure eon-core/src/shared is on sys.path
_SHARED = Path(__file__).resolve().parent.parent.parent / "eon-core" / "src" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

# Transparently re-export all symbols from canonical source
from rcca_core import *  # noqa: F401, F403, E402
