"""PIDRateLimiter — PID-controlled adaptive API rate limiting.

Replaces fixed delays with feedback control:
  - Kp: Proportional — responds to current error rate
  - Ki: Integral — corrects accumulated backlog
  - Kd: Derivative — anticipates trend changes

Target: keep error rate < 5% while maximizing throughput.
Auto-tunes delay between API requests based on success/failure feedback.

Mathematics: PID Controller
  e(t) = target_error_rate - current_error_rate
  u(t) = Kp*e(t) + Ki*∫e(t)dt + Kd*de(t)/dt
  delay = clamp(base_delay + u(t), min_delay, max_delay)

Usage:
    limiter = PIDRateLimiter()
    delay = limiter.wait("pubmed", success=True)
    time.sleep(delay)
"""

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class ProviderState:
    successes: int = 0
    failures: int = 0
    total_requests: int = 0
    integral_error: float = 0.0
    last_error: float = 0.0
    current_delay: float = 1.0


class PIDRateLimiter:
    """PID controller for adaptive API rate limiting."""

    def __init__(self, target_error_rate: float = 0.05,
                 kp: float = 0.5, ki: float = 0.1, kd: float = 0.2,
                 min_delay: float = 0.1, max_delay: float = 10.0,
                 base_delay: float = 1.0):
        self._target = target_error_rate
        self._kp, self._ki, self._kd = kp, ki, kd
        self._min, self._max = min_delay, max_delay
        self._base = base_delay
        self._providers: Dict[str, ProviderState] = {}

    def wait(self, provider: str, success: bool) -> float:
        """Update state and return recommended delay in seconds.

        Call this AFTER each API request. Returns delay to use BEFORE next request.
        """
        if provider not in self._providers:
            self._providers[provider] = ProviderState()

        state = self._providers[provider]
        state.total_requests += 1
        if success:
            state.successes += 1
        else:
            state.failures += 1

        # Compute error
        error_rate = state.failures / max(state.total_requests, 1)
        error = self._target - error_rate

        # PID terms
        p_term = self._kp * error
        state.integral_error = max(-5, min(5, state.integral_error + error))
        i_term = self._ki * state.integral_error
        d_term = self._kd * (error - state.last_error)
        state.last_error = error

        # Compute delay
        adjustment = p_term + i_term + d_term
        state.current_delay = max(self._min, min(self._max,
                                                  self._base + adjustment))

        # Adaptive: reduce delay if error rate is low
        if error_rate < self._target and state.total_requests > 20:
            state.current_delay = max(self._min, state.current_delay * 0.95)

        # Anti-thrashing: increase delay sharply after burst of failures
        recent_failures = sum(1 for _ in range(min(10, state.total_requests))
                              if not success)
        if recent_failures >= 3:
            state.current_delay = min(self._max, state.current_delay * 1.5)

        return state.current_delay

    def get_stats(self) -> Dict:
        return {
            p: {
                'delay': round(s.current_delay, 2),
                'error_rate': round(
                    s.failures / max(s.total_requests, 1), 3
                ),
                'requests': s.total_requests
            }
            for p, s in self._providers.items()
        }


# Integration:
# limiter = PIDRateLimiter()
# for engine in engines:
#     delay = limiter.wait(engine, success=True)  # read delay
#     time.sleep(delay)
#     result = search_engine(engine, query)
#     delay = limiter.wait(engine, success=bool(result))  # update state