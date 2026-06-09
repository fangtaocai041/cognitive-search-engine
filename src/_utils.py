"""Internal utilities shared across cognitive-search-engine modules.

Extracted from agent_core.py + rule_engine.py (v5.7 de-duplication).
"""

from __future__ import annotations


class DotDict(dict):
    """Nested dict with attribute-style access for eval() expressions.

    >>> d = DotDict({"a": {"b": {"c": 8}}})
    >>> d.a.b.c
    8
    """
    __slots__ = ()

    def __getattr__(self, key):
        try:
            val = self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")
        if isinstance(val, dict) and not isinstance(val, DotDict):
            val = DotDict(val)
            self[key] = val
        return val

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")
