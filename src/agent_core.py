"""
Agent Core — Cognitive layer implementing the ReAct reasoning loop.

The CognitiveAgent orchestrates the full 5-layer architecture:

  Layer 1 (Perception)  → species_id input, query formation
  Layer 2 (Cognitive)   → Think (phase selection via BDI policy)
  Layer 3 (Memory)      → Recall (graph lookup) + Record (phase traces)
  Layer 4 (Mapping)     → Route intention to search tools
  Layer 5 (Execution)   → Act (HTTP/MCP tool calls) + Observe (results)

ReAct Cycle per phase:
  1. Think    → Evaluate Belief vs Desire → form Intention
  2. Act      → Execute one phase (search)
  3. Observe  → Count new papers, compute IG
  4. Reflect  → Compare outcome to Desire, adjust or stop

This loop continues until:
  - Desire is satisfied (≥ min_papers with acceptable precision)
  - Token budget is exhausted
  - Diminishing returns detected (consecutive zeros or declining IG)

Integration point:
  - SearchRuleEngine.execute() delegates to CognitiveAgent.run()
  - CognitiveAgent.run() calls SearchRuleEngine._execute_phase() for each phase
  - WorldModel provides BDI lifecycle
  - MemorySystem provides context tracking + graph access

Usage:
  from agent_core import CognitiveAgent
  agent = CognitiveAgent(mode="http")
  result = agent.search("Ochetobius_elongatus")
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import yaml
except ImportError:
    yaml = None

from src.world_model import WorldModel, Belief, Desire, Intention
from src.memory_layer import MemorySystem, PhaseTrace


class DotDict(dict):
    """Nested dict with attribute-style access for eval() expressions."""
    def __getattr__(self, key):
        try:
            val = self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")
        if isinstance(val, dict) and not isinstance(val, DotDict):
            val = DotDict(val)
            self[key] = val
        return val


# ═══════════════════════════════════════════════════════════════════════
# Phase definition (from search_rules.yaml)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class PhaseSpec:
    """Specification of a search phase from search_rules.yaml."""
    name: str
    function: str                # handler name in rule_engine
    priority: int = 99
    budget: int = 500
    tools: list[str] = field(default_factory=list)
    activation_condition: Optional[str] = None  # Python expression or None
    stop_condition: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════
# Cognitive Agent
# ═══════════════════════════════════════════════════════════════════════

class CognitiveAgent:
    """Cognitive layer implementing the ReAct reasoning loop.

    Connects:
      - WorldModel (BDI)   → decision-making
      - MemorySystem       → short-term + long-term memory
      - RuleEngine         → phase execution (delegated)
      - search_rules.yaml  → phase configuration
    """

    def __init__(self, mode: str = "http",
                 rules_path: str = "config/search_rules.yaml"):
        self.mode = mode
        self.world = WorldModel()
        self.memory = MemorySystem()

        # Load phase specs
        self._phase_specs: dict[str, PhaseSpec] = {}
        self._load_phases(rules_path)

        # Phase executor (set by RuleEngine after init)
        self._phase_executor: Optional[Callable] = None

        # Trace
        self._trace: list[dict] = []

    def _load_phases(self, rules_path: str) -> None:
        """Parse phase configurations from search_rules.yaml."""
        if yaml is None:
            return
        try:
            path = Path(rules_path)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    rules = yaml.safe_load(f)
                for name, cfg in (rules.get("phases", {}) or {}).items():
                    self._phase_specs[name] = PhaseSpec(
                        name=name,
                        function=cfg.get("function", name),
                        priority=cfg.get("priority", 99),
                        budget=cfg.get("budget", 500),
                        tools=cfg.get("tools", []),
                        activation_condition=cfg.get("activation"),
                        stop_condition=cfg.get("stop_condition"),
                    )
        except Exception:
            pass

    @property
    def phase_specs(self) -> dict[str, PhaseSpec]:
        return self._phase_specs

    def set_executor(self, executor: Callable) -> None:
        """Wire the phase executor (rule_engine._execute_phase)."""
        self._phase_executor = executor

    # ── Public API ──

    def search(self, species_id: str, genus: str = "",
               species: str = "", chinese_name: str = "",
               graph_papers: list[dict] = None) -> dict[str, Any]:
        """Run the full ReAct search loop for a species.

        This is the main entry point.  It replaces the flat sequential
        phase execution in the old RuleEngine with a proper BDI-based
        Think → Act → Observe → Reflect loop.

        Returns a result dict compatible with the old RuleEngine API.
        """
        graph_papers = graph_papers or []
        graph_known_count = len(graph_papers)

        # ── Init BDI ──
        self.world.init_belief(species_id, graph_known_count)
        prediction = self.world.predict(species_id, graph_known_count)

        # ── Init Memory ──
        self.memory.start_search(species_id, load_graph=True)

        # ── Phase 0: Graph lookup (free, always first) ──
        self.memory.track_phase(
            "graph_lookup",
            papers_found=graph_known_count,
            tokens_used=0,
            source="graph",
        )
        self.world.observe("graph_lookup", graph_known_count, 0,
                          graph_known_count / 1.0 if graph_known_count > 0 else 0)

        # Prepare context
        ctx = {
            "species_id": species_id,
            "genus": genus,
            "species": species,
            "chinese_name": chinese_name,
            "all_papers": graph_papers,
            "graph_papers": graph_papers,
            "total_tokens": 0,
        }

        all_papers: list[dict] = list(graph_papers)
        all_dois: set[str] = set()
        for p in graph_papers:
            doi = (p.get("doi", "") if isinstance(p, dict) else getattr(p, "doi", ""))
            if doi:
                all_dois.add(doi.lower().strip())

        new_papers_by_phase: dict[str, list[dict]] = {}
        phases_executed: list[str] = []
        self._trace = []

        # ── ReAct Loop ──
        round_num = 0
        max_rounds = 20

        should_stop_outer = False

        while round_num < max_rounds and not should_stop_outer:
            round_num += 1
            belief = self.world.current_belief()
            desire = self.world.desire()

            # ── Think: form intention ──
            intention = self._think(ctx, belief, desire)
            self._trace.append({
                "round": round_num,
                "step": "think",
                "intention": intention.summary(),
            })

            if intention.should_stop:
                self._trace.append({
                    "round": round_num,
                    "step": "stop",
                    "reason": intention.stop_reason,
                })
                break

            # No active phases → nothing to do, exit
            if not intention.active_phases:
                self._trace.append({
                    "round": round_num,
                    "step": "stop",
                    "reason": "No active phases (all pruned or budget exhausted)",
                })
                break

            # ── Act: execute one phase at a time ──
            phase_made_progress = False
            for phase_name in intention.active_phases:
                spec = self._phase_specs.get(phase_name)
                if spec is None:
                    continue

                # Check activation condition
                if not self._check_activation(spec, ctx, belief):
                    self._trace.append({
                        "round": round_num,
                        "step": "skip",
                        "phase": phase_name,
                        "reason": "activation condition false",
                    })
                    continue

                # Execute phase
                phase_result = self._act(phase_name, spec, ctx)
                phases_executed.append(phase_name)

                new_papers = phase_result.get("new_papers", [])
                tokens_used = phase_result.get("tokens_used", spec.budget)
                error = phase_result.get("error", "")

                # Deduplicate
                unique_new = []
                for p in new_papers:
                    p_doi = (p.get("doi", "") if isinstance(p, dict)
                             else getattr(p, "doi", "")).lower().strip()
                    if p_doi and p_doi not in all_dois:
                        unique_new.append(p)
                        all_dois.add(p_doi)
                    elif not p_doi:
                        unique_new.append(p)

                n_new = len(unique_new)

                # ── Observe: update world + memory ──
                ig = n_new / max(tokens_used / 1000, 1)
                self.world.observe(phase_name, n_new, tokens_used, ig, error)
                trace = self.memory.track_phase(
                    phase_name, n_new, tokens_used,
                    query=phase_result.get("query", ""),
                    error=error,
                    source=phase_result.get("source", ""),
                    new_papers=unique_new,
                )

                ctx["total_tokens"] = (ctx.get("total_tokens", 0) or 0) + tokens_used

                if unique_new:
                    all_papers.extend(unique_new)
                    new_papers_by_phase[phase_name] = unique_new
                    phase_made_progress = True

                self._trace.append({
                    "round": round_num,
                    "step": "act+observe",
                    "phase": phase_name,
                    "new_papers": n_new,
                    "tokens": tokens_used,
                    "ig": round(ig, 4),
                })

                # ── Reflect: should we continue? ──
                reflection = self._reflect(belief, desire)
                self._trace.append({
                    "round": round_num,
                    "step": "reflect",
                    "action": reflection["action"],
                    "reason": reflection["reason"],
                })

                if reflection["action"] in ("stop_ok", "stop_stalled"):
                    should_stop_outer = True
                    break

            if not phase_made_progress and belief.consecutive_zero < 2:
                # All phases in this round produced nothing → likely done
                pass

        # ── Finish ──
        self.memory.commit_to_long_term()
        self.memory.finish_search()

        # Build result
        result = {
            "papers": all_papers,
            "paper_count": len(all_papers),
            "tokens_spent": ctx.get("total_tokens", 0),
            "phases_executed": phases_executed,
            "new_papers_by_phase": new_papers_by_phase,
            "efficiency": (
                len(all_papers) / max(ctx.get("total_tokens", 0) / 1000, 1)
            ),
            "stop_reason": self._stop_reason(belief, desire),
            "bdi_trace": self.world.bdi_trace(),
            "memory_state": self.memory.memory_state,
        }

        # D₃ post-search update
        if prediction:
            self.world.update(prediction, len(all_papers),
                             ctx.get("total_tokens", 0))
            result["world_model"] = {
                "predicted_volume": prediction.estimated_volume,
                "predicted_tokens": prediction.predicted_tokens,
                "actual_papers": len(all_papers),
                "actual_tokens": ctx.get("total_tokens", 0),
                "prediction_accuracy": round(self.world.prediction_accuracy, 2),
            }

        return result

    # ── ReAct steps ──

    def _think(self, ctx: dict, belief: Belief,
               desire: Desire) -> Intention:
        """Think step: select which phases to execute next.

        Uses the BDI policy π(Belief, Desire) → Intention.
        """
        available = list(self._phase_specs.keys())
        priorities = {n: s.priority for n, s in self._phase_specs.items()}
        activation = {
            n: self._check_activation(self._phase_specs[n], ctx, belief)
            for n in available
            if n in self._phase_specs
        }

        return self.world.form_intention(
            belief, desire, available, priorities, activation
        )

    def _act(self, phase_name: str, spec: PhaseSpec,
             ctx: dict) -> dict:
        """Act step: execute one phase.

        Delegates to the phase executor (rule_engine._execute_phase)
        if wired; otherwise falls back to a direct search call.
        """
        if self._phase_executor:
            try:
                return self._phase_executor(phase_name, {
                    "function": spec.function,
                    "tools": spec.tools,
                    "budget": spec.budget,
                }, ctx)
            except Exception as e:
                return {
                    "new_papers": [],
                    "tokens_used": 0,
                    "error": str(e),
                }

        # Fallback: direct HTTP search (if no executor wired)
        return self._fallback_act(spec, ctx)

    def _reflect(self, belief: Belief, desire: Desire) -> dict:
        """Reflect step: compare Belief to Desire, decide next action."""
        return self.world.reflect(belief, desire)

    # ── Activation check ──

    def _check_activation(self, spec: PhaseSpec, ctx: dict,
                          belief: Belief) -> bool:
        """Evaluate a phase's activation condition against current context."""
        condition = spec.activation_condition
        if condition is None:
            return True

        try:
            return eval(condition, {"__builtins__": {}}, {
                "len": len,
                "any": any,
                "max": max,
                "min": min,
                "all_papers": ctx.get("all_papers", []),
                "graph_papers": ctx.get("graph_papers", []),
                "total_tokens": ctx.get("total_tokens", 0),
                "config": DotDict({
                    "search": {
                        "energy": {
                            "min_papers_satisfice": 8,
                            "max_total_tokens": 50000,
                        }
                    }
                }),
            })
        except Exception:
            return True  # on eval error, activate (fail open)

    # ── Fallback execution (when RuleEngine not wired) ──

    def _fallback_act(self, spec: PhaseSpec, ctx: dict) -> dict:
        """Fallback: execute a phase via direct HTTP search."""
        genus = ctx.get("genus", "")
        sp = ctx.get("species", "")
        chinese = ctx.get("chinese_name", "")

        if spec.function == "search_scholar_article":
            query = f"{genus} {sp}"
        elif spec.function == "search_variants":
            query = f"{genus} {sp}"  # variants handled by rule_engine
        else:
            query = f"{genus} {sp}"

        try:
            import urllib.request
            import urllib.parse
            import json

            # PubMed ESearch
            eurl = (
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                f"db=pubmed&term={urllib.parse.quote_plus(query)}&retmax=10&retmode=json"
            )
            with urllib.request.urlopen(eurl, timeout=10) as resp:
                data = json.loads(resp.read())
            id_list = data.get("esearchresult", {}).get("idlist", [])

            papers = []
            for pmid in id_list[:5]:
                papers.append({
                    "doi": f"pmid:{pmid}",
                    "title": f"PubMed result {pmid} for {query}",
                    "pmid": pmid,
                    "authors": [],
                    "year": None,
                    "source": "pubmed",
                })
            return {
                "new_papers": papers,
                "tokens_used": spec.budget,
                "query": query,
                "source": "pubmed",
            }
        except Exception as e:
            return {
                "new_papers": [],
                "tokens_used": 0,
                "error": str(e),
            }

    # ── Helpers ──

    def _stop_reason(self, belief: Belief, desire: Desire) -> str:
        if desire.satisfied(belief):
            return f"Desire satisfied: {belief.total_papers_found} ≥ {desire.min_papers} papers"
        if belief.stalled:
            return "Diminishing returns detected"
        if belief.consecutive_zero >= 2:
            return "2 consecutive zero-yield phases"
        if belief.tokens_spent >= desire.max_tokens:
            return "Token budget exhausted"
        return "All phases completed"

    @property
    def trace(self) -> list[dict]:
        """Return the ReAct execution trace."""
        return self._trace
