"""
shared_types.py — SHIM: canonical source at eon-core/scripts/shared_types.py

All imports transparently forwarded via importlib (avoids sys.path conflicts).
"""

import sys
import importlib.util
from pathlib import Path

# Locate and load canonical shared_types.py
_EON = Path(__file__).resolve().parent.parent.parent / "eon-core" / "scripts" / "shared_types.py"
_spec = importlib.util.spec_from_file_location("shared_types", str(_EON))
_mod = importlib.util.module_from_spec(_spec)
sys.modules["shared_types"] = _mod
_spec.loader.exec_module(_mod)

# Copy all public names into this shim's namespace
for _name in dir(_mod):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_mod, _name)
