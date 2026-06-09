"""
D₃ World Model — BDI (Belief-Desire-Intention) Agent Core.

Implements the classic BDI architecture for cognitive search:

  Belief (信念):   Agent's model of the current search state — known papers,
                   remaining phases, token budget consumed, IG trajectory.
  Desire (愿望):   Target outcome — desired paper count, precision threshold,
                   recall goal, max token budget.
  Intention (意图): Concrete execution plan — which phases to run next, in what
                   order, with what stopping criteria.

BDI → MDP mapping:
  B_t = {papers_found, tokens_used, ig_history, phase_active}
  D   = {min_papers: 8, min_precision: 0.85, max_tokens: 50000}
  I_t = π(B_t, D)  — policy selects next phase(s) from {active phases}

import sys as _sys
from pathlib import Path
_SRC_ROOT = str(Path(__file__).resolve().parent)
if _SRC_ROOT not in _sys.path:
    _sys.path.insert(0, _SRC_ROOT)

  B_{t+1} = update(B_t, I_t, O_t)  — observe new papers, adjust belief

ReAct integration:
  Think   → Evaluate Belief against Desire → select Intention
  Act     → Execute Intention (phase search)
  Observe → Count new papers, compute IG → update Belief
  Reflect → If Belief diverges from Desire, revise Intention or stop

Usage:
  from world_model import WorldModel, Belief, Desire, Intention
  wm = WorldModel()
  pred = wm.predict("Ochetobius_elongatus", graph_known_count=8)
  # → SearchPrediction(estimated_volume=11, depth="exhaustive", ...)
  belief = wm.current_belief()
  desire = wm.desire()
  intention = wm.form_intention(belief, desire)
  # → Intention with active phases, priority order
"""

from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class SearchPrediction:
    """Pre-search outcome simulation (backward-compatible)."""
    estimated_volume: int
    predicted_depth: str          # "exhaustive" | "classified" | "satisficing"
    predicted_tokens: int
    predicted_new_papers: int
    confidence: float = 0.8


@dataclass
class Belief:
    """Agent's internal model of the current search state (B in BDI).

    Updated after every observation.  Drives intention selection.

    In formal terms: B_t = f(B_{t-1}, O_{t-1}) where O is the
    observation (new papers, IG, error signals).
    """
    species_id: str = ""
    known_papers: int = 0           # |P_known| — papers already in graph
    total_papers_found: int = 0     # |P_found| — cumulative after search
    tokens_spent: int = 0           # Σ budget consumed so far
    phases_executed: list[str] = field(default_factory=list)
    ig_history: list[float] = field(default_factory=list)
    current_phase: str = ""
    consecutive_zero: int = 0       # phases with 0 new papers
    discovery_rate: float = 0.3     # avg new papers per known paper
    token_per_paper: float = 250.0  # avg tokens per paper found
    precision: float = 1.0          # ratio of relevant / total papers
    recall_estimate: float = 1.0    # fraction of known corpus found
    stalled: bool = False           # diminishing returns detected

    def summary(self) -> str:
        return (
            f"Belief({self.species_id}): {self.total_papers_found} papers, "
            f"{self.tokens_spent} tokens, "
            f"IG last={self.ig_history[-1] if self.ig_history else 'N/A'}, "
            f"stalled={self.stalled}"
        )


@dataclass
class Desire:
    """Agent's goal specification (D in BDI).

    Encodes what "success" means for this search.  Used by the
    intention-formation policy to decide when to stop or continue.

    v2.1 — 不再单纯以 min_papers 截断。
    seed 阶段收集论文后，enrichment 阶段必须运行以覆盖引用/变体/中文来源。
    停止由 diminishing returns (consecutive_zero ≥ 2) 或 budget 驱动。

    Configurable via config/agent.yaml → search.energy + adaptive_params.
    """
    min_papers: int = 8                 # satisficing threshold (仅用于 stalled 检查)
    max_papers: int = 300               # upper bound (stop expanding, up from 200)
    max_tokens: int = 50000             # hard budget cap
    min_precision: float = 0.85         # minimum acceptable precision
    ig_prune_threshold: float = 0.005   # IG/token below this → prune phase
    trust_threshold: int = 50           # min trust_score to include paper
    depth_mode: str = "adaptive"        # "exhaustive" | "classified" | "satisficing"

    def satisfied(self, belief: Belief) -> bool:
        """Check whether current Belief meets Desire goals.

        v5.6 — consecutive_zero 仅在有足够阶段执行后才触发停止。
        防止前 5 个阶段因图谱饱和产出 0 论文时过早结束，
        导致 variant_search/preprint_search/journal_scan 等
        使用外部引擎的阶段完全被跳过。
        """
        if belief.tokens_spent >= self.max_tokens:
            return True
        # 仅当至少 8 个阶段已执行才允许 consecutive_zero 触发停止
        if belief.consecutive_zero >= 3 and len(belief.phases_executed) >= 8:
            return True
        if belief.total_papers_found >= self.max_papers:
            return True
        if belief.stalled and belief.total_papers_found >= self.max_papers:
            return True
        return False

    def summary(self) -> str:
        return (
            f"Desire: ≥{self.min_papers} papers, "
            f"≤{self.max_tokens} tokens, "
            f"precision≥{self.min_precision}, "
            f"mode={self.depth_mode}"
        )


@dataclass
class Intention:
    """Agent's concrete execution plan (I in BDI).

    Maps to the set of phases that will be activated in the next
    reasoning cycle.  Formed by the policy π(Belief, Desire).

    In formal terms: I_t = π(B_t, D) where π is the phase-selection
    policy (priority ordering + activation conditions + IG pruning).
    """
    active_phases: list[str] = field(default_factory=list)
    stop_reason: str = ""
    should_stop: bool = False
    priority_order: list[str] = field(default_factory=list)
    pruned_phases: list[str] = field(default_factory=list)
    predicted_tokens: int = 0           # estimated cost of this intention
    confidence: float = 0.8

    def summary(self) -> str:
        return (
            f"Intention: {self.active_phases} "
            f"(stop={self.should_stop}, pruned={self.pruned_phases})"
        )


# ═══════════════════════════════════════════════════════════════════════
# World Model (BDI Engine)
# ═══════════════════════════════════════════════════════════════════════

class WorldModel:
    """D₃ Body with full BDI lifecycle management.

    Predicts search outcomes BEFORE execution (D₃ simulation).
    Manages Belief → Desire → Intention → Observe → Reflect loop.
    Learns from prediction-vs-actual gaps via adaptive parameter updates.

    Lifecycle per search:
      1. predict()      → estimate volume, choose depth mode
      2. form_intention() → select phases based on Belief + Desire
      3. observe()      → update Belief with phase results
      4. reflect()      → compare Belief to Desire, adjust strategy
    """

    def __init__(self):
        # Adaptive parameters (learned over time)
        self.discovery_rate: float = 0.3
        self.token_per_paper: float = 250.0
        self._prediction_errors: list[float] = []

        # Current BDI state
        self._belief: Optional[Belief] = None
        self._desire: Optional[Desire] = None
        self._intention_history: list[Intention] = []
        self._observation_history: list[dict] = []

    # ── Prediction (D₃ pre-search simulation) ──

    def predict(self, species_id: str, graph_known_count: int,
                mode: str = "adaptive") -> SearchPrediction:
        """Simulate search outcome BEFORE execution.

        Uses discovery_rate to estimate total literature volume and
        selects search depth mode automatically.
        """
        estimated_volume = max(
            graph_known_count,
            int(graph_known_count / max(1 - self.discovery_rate, 0.01))
        )

        if estimated_volume < 20:
            depth = "exhaustive"
            active_layers = 11
        elif estimated_volume <= 200:
            depth = "classified"
            active_layers = 6
        else:
            depth = "satisficing"
            active_layers = 4

        predicted_tokens = int(graph_known_count * self.token_per_paper * active_layers)
        predicted_new = int(graph_known_count * self.discovery_rate * active_layers)

        return SearchPrediction(
            estimated_volume=estimated_volume,
            predicted_depth=depth,
            predicted_tokens=predicted_tokens,
            predicted_new_papers=predicted_new,
        )

    # ── BDI lifecycle ──

    def init_belief(self, species_id: str, graph_known_count: int,
                    depth_mode: str = "adaptive") -> Belief:
        """Initialize Belief at the start of a new search."""
        self._belief = Belief(
            species_id=species_id,
            known_papers=graph_known_count,
            total_papers_found=0,
            discovery_rate=self.discovery_rate,
            token_per_paper=self.token_per_paper,
        )
        self._desire = Desire(depth_mode=depth_mode)
        self._intention_history = []
        self._observation_history = []
        return self._belief

    def current_belief(self) -> Belief:
        """Return current Belief state or default."""
        if self._belief is None:
            self._belief = Belief()
        return self._belief

    def desire(self) -> Desire:
        """Return current Desire (goal specification)."""
        if self._desire is None:
            self._desire = Desire()
        return self._desire

    def form_intention(self, belief: Belief, desire: Desire,
                       available_phases: list[str],
                       phase_priorities: dict[str, int],
                       phase_activation: dict[str, bool]) -> Intention:
        """Policy π(Belief, Desire) → Intention.

        Selects which phases to execute next based on:
          1. Phase priority (lower = more important)
          2. Activation conditions (is this phase relevant?)
          3. IG pruning (has this phase type stopped yielding results?)
          4. Budget remaining (can we afford this phase?)

        Returns an Intention with active_phases and stop/should_stop flags.
        """
        intention = Intention()

        # Should we stop?
        if desire.satisfied(belief):
            intention.should_stop = True
            intention.stop_reason = (
                f"Desire satisfied: {belief.total_papers_found} ≥ "
                f"{desire.min_papers} papers"
            )
            self._intention_history.append(intention)
            return intention

        # v5.6: 图谱饱和 ≠ 外部引擎无产出。仅当剩余相都已执行过一次以上才停。
        # 防止 variant_search/preprint_search/journal_scan 等因图谱已有数据而被跳过。
        if belief.consecutive_zero >= 2 and len(belief.phases_executed) >= 8:
            intention.should_stop = True
            intention.stop_reason = f"{belief.consecutive_zero} consecutive zero + {len(belief.phases_executed)} phases done"
            self._intention_history.append(intention)
            return intention

        if belief.tokens_spent >= desire.max_tokens:
            intention.should_stop = True
            intention.stop_reason = f"Token budget exhausted ({belief.tokens_spent})"
            self._intention_history.append(intention)
            return intention

        # Select active phases
        remaining_tokens = desire.max_tokens - belief.tokens_spent
        active = []
        pruned = []

        for name in sorted(available_phases, key=lambda n: phase_priorities.get(n, 99)):
            if not phase_activation.get(name, True):
                continue

            # IG pruning: skip if IG below threshold (but NOT after graph_lookup only)
            # graph_lookup always yields IG=0 for unknown species, so we need at least
            # one real search phase before pruning kicks in.
            if belief.ig_history and len(belief.ig_history) >= 2:
                real_phases = sum(1 for ig in belief.ig_history if ig > 0.0)
                if real_phases >= 2:
                    recent_ig = belief.ig_history[-1]
                    if recent_ig < desire.ig_prune_threshold:
                        pruned.append(name)
                        continue

            # Budget check
            phase_cost = phase_priorities.get(name, 500)
            if phase_cost > remaining_tokens:
                pruned.append(name)
                continue

            active.append(name)
            remaining_tokens -= phase_cost

        intention.active_phases = active
        intention.pruned_phases = pruned
        intention.priority_order = sorted(
            active, key=lambda n: phase_priorities.get(n, 99)
        )
        intention.predicted_tokens = sum(
            phase_priorities.get(n, 500) for n in active
        )

        # If all phases were pruned, signal stop
        if not active and pruned:
            intention.should_stop = True
            intention.stop_reason = (
                f"All {len(pruned)} phases pruned (low IG or budget exhausted)"
            )

        self._intention_history.append(intention)
        return intention

    def observe(self, phase_name: str, new_papers: int, tokens_used: int,
                ig: float, error_msg: str = "") -> Belief:
        """Update Belief after executing one intention (phase).

        This is the observation function O_t → B_{t+1}.
        """
        b = self.current_belief()

        b.total_papers_found += new_papers
        b.tokens_spent += tokens_used
        b.phases_executed.append(phase_name)
        b.current_phase = phase_name
        b.ig_history.append(ig)

        if new_papers == 0:
            b.consecutive_zero += 1
        else:
            b.consecutive_zero = 0

        # Adaptive precision tracking
        if new_papers > 0:
            b.precision = (
                0.8 * b.precision + 0.2  # assume new papers are relevant
            ) if b.precision > 0 else 1.0

        # Diminishing returns detection
        # v5.6: 放宽 stall 条件，确保新引擎有充分的执行机会。
        #   - 至少 6 个非图谱阶段已执行（给 chinese/exact/variant/preprint/journal 留足空间）
        #   - AND 连续 0 新论文阶段 >= 3
        #   - AND IG 低于阈值
        # 防止 variant_search、preprint_search、journal_scan 等因图谱已有数据而被跳过。
        non_graph_count = sum(1 for obs in self._observation_history
                              if obs.get("phase") != "graph_lookup")
        if (non_graph_count >= 6
                and b.consecutive_zero >= 3
                and b.ig_history[-1] < 0.005):
            b.stalled = True

        # Error tracking
        obs = {
            "phase": phase_name,
            "new_papers": new_papers,
            "tokens": tokens_used,
            "ig": ig,
            "error": error_msg,
        }
        self._observation_history.append(obs)

        self._belief = b
        return b

    def reflect(self, belief: Belief, desire: Desire) -> dict:
        """Post-phase meta-cognition.

        Compares Belief against Desire.  Returns adjustment suggestions:
          - "continue"   — keep going, current strategy is working
          - "restructure" — revise intention, try different phases
          - "stop_ok"    — desire satisfied, stop with success
          - "stop_stalled" — diminishing returns, stop gracefully

        This is the Reflect step in the ReAct loop.
        """
        if desire.satisfied(belief):
            return {
                "action": "stop_ok",
                "reason": f"Desire satisfied: {belief.total_papers_found} papers",
                "confidence": 0.95,
            }

        # v5.6: stalled 只在至少 8 阶段后才触发，给新引擎充分机会
        if belief.stalled and len(belief.phases_executed) >= 10:
            return {
                "action": "stop_stalled",
                "reason": f"Diminishing returns after {len(belief.phases_executed)} phases",
                "confidence": 0.7,
            }

        # v5.6: 图谱饱和 ≠ 外部引擎无产出。扩大阈值防止早停。
        if belief.consecutive_zero >= 3 and len(belief.phases_executed) >= 8:
            return {
                "action": "stop_stalled",
                "reason": f"{belief.consecutive_zero} consecutive zero + {len(belief.phases_executed)} phases",
                "confidence": 0.8,
            }

        if belief.tokens_spent >= desire.max_tokens:
            return {
                "action": "stop_stalled",
                "reason": "Token budget exhausted",
                "confidence": 0.9,
            }

        # Evaluate strategy: is IG declining?
        if len(belief.ig_history) >= 3:
            recent_3 = belief.ig_history[-3:]
            if recent_3[-1] < recent_3[-2] < recent_3[0]:
                return {
                    "action": "restructure",
                    "reason": "Declining IG — consider pruning or switching phases",
                    "confidence": 0.6,
                }

        return {
            "action": "continue",
            "reason": "Strategy is producing results",
            "confidence": 0.7,
        }

    # ── Learning (post-search adaptation) ──

    def update(self, prediction: SearchPrediction, actual_papers: int,
               actual_tokens: int):
        """Update world model parameters from prediction-vs-actual gap.

        Backward-compatible with original WorldModel.update().
        """
        paper_error = abs(prediction.predicted_new_papers - actual_papers)
        paper_error_rate = paper_error / max(prediction.predicted_new_papers, 1)
        self._prediction_errors.append(paper_error_rate)

        # Adaptive discovery_rate
        if actual_papers > prediction.predicted_new_papers:
            self.discovery_rate *= 1.1
        else:
            self.discovery_rate *= 0.95
        self.discovery_rate = max(0.05, min(0.8, self.discovery_rate))

        # Adaptive token_per_paper
        if actual_papers > 0:
            actual_token_rate = actual_tokens / actual_papers
            self.token_per_paper = 0.7 * self.token_per_paper + 0.3 * actual_token_rate

        # Sync to Belief
        if self._belief:
            self._belief.discovery_rate = self.discovery_rate
            self._belief.token_per_paper = self.token_per_paper

    @property
    def prediction_accuracy(self) -> float:
        """Rolling accuracy of last 10 predictions."""
        if not self._prediction_errors:
            return 1.0
        recent = self._prediction_errors[-10:]
        return 1.0 - sum(recent) / len(recent)

    # ── BDI trace (for display / debugging) ──

    def bdi_trace(self) -> dict:
        """Return a human-readable BDI trace for post-search reporting."""
        return {
            "belief": {
                "papers_found": self._belief.total_papers_found if self._belief else 0,
                "tokens_spent": self._belief.tokens_spent if self._belief else 0,
                "phases": self._belief.phases_executed if self._belief else [],
                "ig_last": (
                    self._belief.ig_history[-1]
                    if self._belief and self._belief.ig_history
                    else None
                ),
            },
            "desire": {
                "min_papers": self._desire.min_papers if self._desire else 8,
                "max_tokens": self._desire.max_tokens if self._desire else 50000,
                "mode": self._desire.depth_mode if self._desire else "adaptive",
            },
            "intentions": len(self._intention_history),
            "observations": len(self._observation_history),
            "prediction_accuracy": round(self.prediction_accuracy, 2),
        }
