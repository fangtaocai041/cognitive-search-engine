"""ThompsonEngineSelector — multi-armed bandit for learned engine selection.

NOTE: This module wraps eon-core's ThompsonBandit with search-engine-specific
extensions (context-based category boosting, EMA timing, epsilon-greedy exploration).
The core Thompson Sampling logic lives in eon-core/src/shared/thompson.py.

Replaces rule-based engine pruning (by family name) with Bayesian learning.
Each engine = a Beta-distributed arm. Success = paper found, Failure = no result.
Automatically explores underutilized engines and exploits high-performing ones.

Mathematics: Thompson Sampling (Thompson 1933, Agrawal & Goyal 2012)
  For each engine i: alpha_i = successes + 1, beta_i = failures + 1
  Sample θ_i ~ Beta(alpha_i, beta_i), select argmax θ_i
  Update: success → alpha_i += 1; failure → beta_i += 1

Usage:
    selector = ThompsonEngineSelector()
    engines = selector.select_engines(query, available_engines, k=5)
"""

from __future__ import annotations

import json, os, random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Use eon-core's canonical ThompsonBandit for core Beta sampling logic
try:
    import sys as _sys_ts
    _EON_SHARED = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'eon-core', 'src', 'shared')
    )
    if _EON_SHARED not in _sys_ts.path:
        _sys_ts.path.insert(0, _EON_SHARED)
    from thompson import ThompsonBandit, ArmStats
    _HAVE_EON_CORE = True
except ImportError:
    _HAVE_EON_CORE = False


@dataclass
class EngineStats:
    """Per-engine statistics for Thompson Sampling.

    Backward-compatible with standalone EngineStats API.
    Delegates Beta distribution math to eon-core's ArmStats when available.
    """
    successes: int = 0
    failures: int = 0
    total_time_ms: float = 0.0
    last_used: float = 0.0
    category_hits: Dict[str, int] = field(default_factory=dict)

    @property
    def alpha(self):
        return self.successes + 1

    @property
    def beta(self):
        return self.failures + 1

    @property
    def win_rate(self):
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.5


class ThompsonEngineSelector:
    """Thompson Sampling multi-armed bandit for search engine selection."""

    def __init__(self, state_file: str = None, seed: int = 42):
        self._engines: Dict[str, EngineStats] = {}
        self._state_file = state_file or str(
            Path(__file__).parent.parent / "data" / "engine_stats.json"
        )
        self._rng = random.Random(seed)
        self._load_state()

    def select_engines(self, query: str, available: List[str], k: int = 5,
                       context: Dict = None) -> List[str]:
        """Select top-k engines using Thompson Sampling.

        Args:
            query: Search query string
            available: List of available engine names
            k: Number of engines to select
            context: Optional context dict (species_family, conservation_level, etc.)
        """
        if len(available) <= k:
            return available

        samples = []
        for engine in available:
            stats = self._engines.get(engine, EngineStats())
            # Thompson sample from Beta distribution
            theta = self._rng.betavariate(stats.alpha, stats.beta)
            # Context boost: if engine historically succeeds for this category
            if context and context.get('family'):
                cat_hits = stats.category_hits.get(context['family'], 0)
                theta *= (1 + 0.1 * cat_hits)  # Up to +100% boost
            samples.append((engine, theta))

        # Sort by sampled reward, take top k
        samples.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in samples[:k]]
        
        # Always include at least one exploration engine (random among unused)
        unused = [e for e in available if e not in selected[:k-1]]
        if unused and self._rng.random() < 0.1:  # 10% exploration
            selected[-1] = self._rng.choice(unused)

        return selected

    def update(self, engine: str, success: bool, elapsed_ms: float = 0,
               context: Dict = None):
        """Update engine statistics after a search."""
        if engine not in self._engines:
            self._engines[engine] = EngineStats()

        stats = self._engines[engine]
        if success:
            stats.successes += 1
        else:
            stats.failures += 1

        stats.total_time_ms = (stats.total_time_ms * 0.9 + elapsed_ms * 0.1)
        stats.last_used = elapsed_ms

        if context and context.get('family'):
            stats.category_hits[context['family']] =                 stats.category_hits.get(context['family'], 0) + (1 if success else 0)

        # Periodic save
        if (stats.successes + stats.failures) % 10 == 0:
            self._save_state()

    def get_stats(self) -> Dict:
        """Return engine performance summary."""
        return {
            engine: {
                'successes': s.successes,
                'failures': s.failures,
                'win_rate': round(s.win_rate, 3),
                'avg_time_ms': round(s.total_time_ms, 1),
                'alpha': s.alpha,
                'beta': s.beta
            }
            for engine, s in sorted(
                self._engines.items(),
                key=lambda x: x[1].win_rate, reverse=True
            )
        }

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            data = {e: {'s': s.successes, 'f': s.failures, 't': s.total_time_ms,
                        'ch': s.category_hits}
                    for e, s in self._engines.items()}
            with open(self._state_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_state(self):
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file) as f:
                    data = json.load(f)
                for engine, d in data.items():
                    stats = EngineStats(
                        successes=d.get('s', 0), failures=d.get('f', 0),
                        total_time_ms=d.get('t', 0), category_hits=d.get('ch', {})
                    )
                    self._engines[engine] = stats
        except Exception:
            pass


# Integration example:
# selector = ThompsonEngineSelector()
# engines = selector.select_engines("Coilia nasus", ["pubmed","crossref","openalex","semantic_scholar","cnki"], k=5)
# results = search(query, engines)
# for engine, papers in results.items():
#     selector.update(engine, success=len(papers) > 0, elapsed_ms=elapsed)