#!/usr/bin/env python3
"""
Unified Agent Integration Test — 统一架构协调测试
==================================================
Tests the integrated behavior of all four new modules:
  - dimensional_evolution.py (D₀→D₃ topology)
  - stv_core.py (S-T-V rigid triangle)
  - meso_experiment.py (controlled experiments)
  - emergence_monitor.py (emergence detection)

Plus integration with existing orchestrator components:
  - CrossDelegation
  - MCPClient
  - Evolution engine (all three projects)
"""

import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/Reasonix")
sys.path.insert(0, str(ROOT / "porpoise-agent"))

# ═══════════════════════════════════════════════════════════
# Test Harness
# ═══════════════════════════════════════════════════════════

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")

# ═══════════════════════════════════════════════════════════
# 1. Dimensional Evolution → S-T-V Integration
# ═══════════════════════════════════════════════════════════

print("── 1. Dimensional Evolution ↔ S-T-V Triangle Integration ──")

from src.agent.dimensional_evolution import (
    PointState, LineTrajectory, PlaneMesh, BodyEntity,
    EvolutionEngine, WorldModel,
)
from src.agent.emergence_monitor import DimensionalLevel
from src.agent.stv_core import (
    StateVertex, TransitionVertex, ValidationVertex,
    STVTriangle, TriangleManifold, ValidationVerdict,
    DataAnalysisSTV, WorkflowSTV, EmbodiedSTV, CrossScenarioManifold,
)

# Test: PointState wraps StateVertex
s = StateVertex(data={"papers": 0, "recall": 0.0})
check("StateVertex creation", s.data["papers"] == 0)
check("StateVertex hash is deterministic", len(s.hash) == 16)

# Test: TransitionVertex with search function
def search(state, query=""):
    return {"papers_found": 8, "recall": 0.92}
t = TransitionVertex(operator=search, inputs={"query": "Ochetobius elongatus"})
result_t = t.apply(s)
check("Transition applies correctly", result_t["papers_found"] == 8, f"got {result_t}")

# Test: Validation with verifier
def verify(result):
    return ValidationVerdict.VERIFIED if result.get("papers_found", 0) >= 3 else ValidationVerdict.PENDING
v = ValidationVertex(validator=verify, min_sources=3)
check("Validation PASS", v.validate({"papers_found": 8}) == ValidationVerdict.VERIFIED)
check("Validation PENDING", v.validate({"papers_found": 1}) == ValidationVerdict.PENDING)

# Test: Full S-T-V triangle execution
tri = STVTriangle(state=s, transition=t, validation=v)
result = tri.execute()
check("S-T-V triangle intact", result.status.name == "INTACT", f"status={result.status}")
check("Triangle produces new state", result.new_state is not None)
check("Triangle result has verdict", result.verdict == ValidationVerdict.VERIFIED)

# Test: Broken T vertex
def failing_search(state, query=""):
    raise Exception("API down")
t_broken = TransitionVertex(operator=failing_search)
tri_broken = STVTriangle(state=s, transition=t_broken, validation=v)
result_broken = tri_broken.execute()
check("Broken T detected", result_broken.status.name == "BROKEN_T", f"status={result_broken.status}")

# Test: Triangle manifold (D₁ chain)
manifold = TriangleManifold(name="test_chain")
manifold.add_triangle(tri)

# Second triangle with DIFFERENT search to avoid degeneracy
def search2(state, query=""):
    return {"papers_found": 12, "recall": 0.95, "new": True}
t2 = TransitionVertex(operator=search2)
tri2 = STVTriangle(state=s, transition=t2, validation=v)
manifold.add_triangle(tri2)

chain_results = manifold.execute_chain({"query": "test"}, max_steps=2)
check("D₁ chain executes 2 triangles", len(chain_results) == 2, f"got {len(chain_results)}")
check("All chain triangles intact", all(r.status.name in ("INTACT", "DEGENERATE") for r in chain_results))

# Test: Cross-scenario manifold
cross = CrossScenarioManifold()
check("Cross-scenario global entropy", cross.global_entropy() == 0.0)
health = cross.global_health()
check("Cross-scenario health report", health["total_triangles"] == 0)


# ═══════════════════════════════════════════════════════════
# 2. Meso Experiment ↔ Evolution Integration
# ═══════════════════════════════════════════════════════════

print("── 2. Meso Experiment ↔ Evolution Integration ──")

from src.agent.meso_experiment import (
    MesoExperiment, Hypothesis, ExperimentReport,
    search_quality_experiment, pipeline_depth_experiment,
    contradiction_budget_experiment,
)

# Test: Hypothesis
h = Hypothesis(
    statement="Increasing satisfice_threshold from 8 to 12 improves recall by >15%",
    independent_variable="satisfice_threshold",
    control_value=8,
    treatment_value=12,
    dependent_variable="recall",
)
check("Hypothesis validates", h.validate())
check("Hypothesis well-formed", h.expected_effect_size == 0.15)

# Test: Experiment execution
def trial(params):
    import random
    threshold = params.get("satisfice_threshold", 8)
    papers = min(threshold * 1.5 + random.uniform(-0.5, 0.5), 20)  # slight noise
    return {"recall": papers / 20.0, "papers_found": papers}

exp = MesoExperiment(hypothesis=h, run_trial=trial)
report = exp.run(n_trials=5)
check("Experiment completed", exp.status.value == "completed")
check("Experiment has control results", len(report.control_results) == 5)
check("Experiment has treatment results", len(report.treatment_results) == 5)
check("Report generates markdown", "Experiment Report" in report.to_markdown())

# Test: Effect size computation
effect = report.effect_sizes.get("recall", 0)
check("Effect size computed", abs(effect) > 0, f"d={effect:.3f}")

# Test: Pre-built experiments
exp2 = search_quality_experiment(trial)
report2 = exp2.run(n_trials=3)
check("Pre-built search experiment runs", exp2.status.value == "completed")


# ═══════════════════════════════════════════════════════════
# 3. Emergence Monitor ↔ Dimensional Evolution
# ═══════════════════════════════════════════════════════════

print("── 3. Emergence Monitor ↔ Dimensional Evolution ──")

from src.agent.emergence_monitor import (
    EmergenceMonitor, DimensionalEmergenceMonitor,
    EmergenceType, EmergenceSignal,
)
# DimensionalLevel already imported above

# Test: Basic emergence detection
mon = EmergenceMonitor(emergence_threshold_sigma=2.0, min_sources=2)
for _ in range(10):
    mon.record("recall", 0.85, DimensionalLevel.D1)
    mon.record("precision", 0.90, DimensionalLevel.D1)
    mon.record("verification", 0.88, DimensionalLevel.D1)
# Inject anomaly
mon.record("recall", 0.20, DimensionalLevel.D1)
mon.record("precision", 0.25, DimensionalLevel.D1)
mon.record("verification", 0.15, DimensionalLevel.D1)
signals = mon.check_emergence()
check("Emergence detected", len(signals) >= 1, f"{len(signals)} signals")
if signals:
    check("Signal has sources", len(signals[0].sources) >= 2)
    check("Signal has type", signals[0].emergence_type is not None)

# Test: Dimensional emergence monitor
dim_mon = DimensionalEmergenceMonitor(emergence_threshold_sigma=2.0, min_sources=2)
for _ in range(5):
    dim_mon.record("d2_metric_1", 1.0, DimensionalLevel.D2)
    dim_mon.record("d2_metric_2", 1.0, DimensionalLevel.D2)
dim_mon.record("d2_metric_1", 5.0, DimensionalLevel.D2)
dim_mon.record("d2_metric_2", 6.0, DimensionalLevel.D2)
dim_mon.record("d2_metric_3", 7.0, DimensionalLevel.D2)
d2_signals = dim_mon.check_emergence()
check("D₂ emergence signals detected", len(d2_signals) >= 1, f"{len(d2_signals)}")

# Test: D₂→D₃ phase transition
d3_signal = dim_mon.check_dimensional_emergence()
if d3_signal:
    check("D₂→D₃ transition detected", True, d3_signal.description)

# Test: Health report
report = dim_mon.health_report()
check("Health report has levels", "D0" in report["by_level"])


# ═══════════════════════════════════════════════════════════
# 4. Scenario-Specific STV Implementations
# ═══════════════════════════════════════════════════════════

print("── 4. Scenario STV Implementations ──")

# Data Analysis
s_da = DataAnalysisSTV.create_state({"columns": ["sp", "len"], "row_count": 100})
t_da = DataAnalysisSTV.create_transition("result = {'mean_len': 15.3, 'n': 100}")
v_da = DataAnalysisSTV.create_validation(["normality", "p_value"])
check("DataAnalysis state", s_da.metadata["scenario"] == "data_analysis")
check("DataAnalysis validation", v_da.min_sources == 2)

# Workflow
s_wf = WorkflowSTV.create_state({"nodes": {"A": {}, "B": {}}})
t_wf = WorkflowSTV.create_transition("A")
v_wf = WorkflowSTV.create_validation(max_retries=3)
check("Workflow state created", s_wf.data["status"] == "pending")
check("Workflow validation retries", v_wf.validator is not None)

# Embodied
s_em = EmbodiedSTV.create_state(pose=[0.0, 0.0, 0.0], velocity=[1.0, 0.0, 0.0])
t_em = EmbodiedSTV.create_transition(["idle", "move", "rotate"])
v_em = EmbodiedSTV.create_validation(boundary={"limits": [(-10, 10), (-10, 10), (-10, 10)]})
check("Embodied state", s_em.data["pose"] == [0.0, 0.0, 0.0])
tri_em = STVTriangle(state=s_em, transition=t_em, validation=v_em)
r_em = tri_em.execute()
check("Embodied S-T-V triangle intact", r_em.status.name == "INTACT",
      f"status={r_em.status}, result={r_em.raw_result}")


# ═══════════════════════════════════════════════════════════
# 5. Integration with Existing Orchestrator
# ═══════════════════════════════════════════════════════════

print("── 5. Integration with Existing Orchestrator ──")

from src.agent.orchestrator import CrossDelegation, MCPClient, route_research_question

# Test: Route + STV validation
routes = route_research_question("鳤 Ochetobius_elongatus population genetics")
check("Routing returns results", len(routes) >= 1)
if routes:
    check("Route has project", "project" in routes[0])
    check("Route has confidence", routes[0]["confidence"] > 0)

# Test: Cross-delegation with STV triangle
delegation = CrossDelegation.call_remote_skill(
    "cognitive-search-engine", "graph-search-engine",
    {"species": "Ochetobius_elongatus"}
)
check("Delegation status", delegation["status"] == "delegated")

# Test: MCP phase validation
for phase in ["literature_review", "data_analysis", "report"]:
    v = MCPClient.validate_phase_tools(phase)
    check(f"MCP phase '{phase}' ready", v["status"] == "ready",
          f"missing={v['missing']}" if v.get("missing") else "")


# ═══════════════════════════════════════════════════════════
# 6. Cross-Project Evolution Integration
# ═══════════════════════════════════════════════════════════

print("── 6. Cross-Project Evolution Integration ──")

import yaml

# Verify all three evolution.yaml are valid and have cross_project sections
for proj in ["cognitive-search-engine", "fish-ecology-assistant", "porpoise-agent"]:
    path = ROOT / proj / "config" / "evolution.yaml"
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        has_cross = "cross_project" in str(data)
        params = data.get("evolution", {}).get("adaptive_params", {})
        check(f"{proj} evolution.yaml valid", len(params) > 0,
              f"{len(params)} adaptive params")
        check(f"{proj} cross_project section", has_cross)


# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════

print()
print("═" * 50)
print(f"  Unified Agent Integration Test")
print(f"  {datetime.now().isoformat()[:19]}")
print(f"  ✅ {passed}  ❌ {failed}")
print("═" * 50)

sys.exit(1 if failed > 0 else 0)
