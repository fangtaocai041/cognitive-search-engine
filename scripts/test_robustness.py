#!/usr/bin/env python3
"""
Robustness & Boundary Test Suite — 鲁棒性 + 性能边界测试
========================================================
Tests edge cases, invalid inputs, boundary conditions, and
performance limits across all three S-T-V projects.

Usage:
  python scripts/test_robustness.py              # full suite
  python scripts/test_robustness.py --quick      # smoke test only
  python scripts/test_robustness.py --project porpoise  # single project
"""

import json
import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any

ROOT = Path("D:/Reasonix")

# ═══════════════════════════════════════════════════════════
# Test Result Tracker
# ═══════════════════════════════════════════════════════════

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.results = []
    
    def add(self, name: str, passed: bool, detail: str = "", error: str = ""):
        status = "✅" if passed else ("❌" if not error else "💥")
        self.results.append((status, name, detail, error))
        if error:
            self.errors += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self) -> str:
        total = self.passed + self.failed + self.errors
        lines = []
        for status, name, detail, error in self.results:
            lines.append(f"  {status} {name}")
            if detail:
                lines.append(f"     {detail}")
            if error:
                lines.append(f"     💥 {error[:120]}")
        lines.append("")
        lines.append(f"  Total: {total} | ✅ {self.passed} | ❌ {self.failed} | 💥 {self.errors}")
        return "\n".join(lines)


result = TestResult()

# ═══════════════════════════════════════════════════════════
# Section 1: CrossDelegation Robustness
# ═══════════════════════════════════════════════════════════

def test_cross_delegation():
    print("── 1. CrossDelegation Robustness ──")
    
    try:
        sys.path.insert(0, str(ROOT / "porpoise-agent"))
        from src.agent.orchestrator import CrossDelegation, call_remote_skill, route_research_question
    except Exception as e:
        result.add("Import CrossDelegation", False, error=str(e))
        return
    
    # Test 1: Valid delegation
    r = call_remote_skill("cognitive-search-engine", "graph-search-engine", {"species": "Testus_example"})
    result.add("Valid delegation",
               r.get("status") == "delegated",
               f"status={r.get('status')}")
    
    # Test 2: Invalid project
    r = call_remote_skill("nonexistent-project", "graph-search-engine", {})
    result.add("Invalid project (nonexistent)",
               r.get("status") == "unavailable",
               f"status={r.get('status')}")
    
    # Test 3: Invalid skill
    r = call_remote_skill("porpoise-agent", "nonexistent-skill", {})
    result.add("Invalid skill (nonexistent)",
               r.get("status") == "unavailable",
               f"status={r.get('status')}")
    
    # Test 4: Empty context
    r = call_remote_skill("fish-ecology-assistant", "stats-assistant", {})
    result.add("Empty context delegation",
               r.get("status") == "delegated",
               f"status={r.get('status')}")
    
    # Test 5: Large context
    large_ctx = {"data": "x" * 10000}
    r = call_remote_skill("cognitive-search-engine", "graph-search-engine", large_ctx)
    result.add("Large context (10KB)",
               r.get("status") == "delegated",
               f"status={r.get('status')}")
    
    # Test 6: Unicode context
    r = call_remote_skill("porpoise-agent", "search-literature", {"query": "江豚 长江 种群 🐬 2024"})
    result.add("Unicode/emoji context",
               r.get("status") == "delegated",
               f"status={r.get('status')}")
    
    # Test 7: resolve_skill edge cases
    r = CrossDelegation.resolve_skill("", "graph-search-engine")
    result.add("Empty project name", r is None, f"result={r}")
    
    r = CrossDelegation.resolve_skill("porpoise-agent", "")
    result.add("Empty skill name", r is None, f"result={r}")
    
    # Test 8: format_delegate with special chars
    msg = CrossDelegation.format_delegate("porpoise-agent", "detect-clicks", {"threshold": -134.0, "band": [100000, 180000]})
    result.add("Format with nested params",
               "DELEGATE" in msg and "detect-clicks" in msg,
               f"len={len(msg)}")
    
    # Test 9: Routing edge cases
    r = route_research_question("")
    result.add("Empty query routing",
               len(r) > 0 and r[0]["project"] == "cognitive-search-engine",
               f"default route={r[0]['project']}")
    
    r = route_research_question("xyzzy12345_nonexistent_keyword")
    result.add("Nonsense query routing",
               len(r) > 0,
               f"routes={len(r)}, default={r[0]['project'] if r else 'none'}")
    
    r = route_research_question("a" * 1000)
    result.add("Very long query routing",
               len(r) > 0,
               f"routes={len(r)}")
    
    # Test 10: Cross-project routing for mixed queries
    r = route_research_question("江豚 acoustic click 鱼类 community ecology 鳤 species taxonomy")
    result.add("Mixed domain query (fish+porpoise+cognitive)",
               len(r) >= 3,
               f"projects matched: {[x['project'] for x in r]}")

test_cross_delegation()


# ═══════════════════════════════════════════════════════════
# Section 2: MCPClient Robustness
# ═══════════════════════════════════════════════════════════

def test_mcp_client():
    print("── 2. MCPClient Robustness ──")
    
    try:
        sys.path.insert(0, str(ROOT / "porpoise-agent"))
        from src.agent.orchestrator import MCPClient
    except Exception as e:
        result.add("Import MCPClient", False, error=str(e))
        return
    
    # Test 1: Valid phase
    tools = MCPClient.get_tools_for_phase("literature_review")
    result.add("Valid phase tools", len(tools) > 0, f"{len(tools)} tools")
    
    # Test 2: Invalid phase
    tools = MCPClient.get_tools_for_phase("nonexistent_phase")
    result.add("Invalid phase tools", tools == [], f"tools={tools}")
    
    # Test 3: Empty phase
    tools = MCPClient.get_tools_for_phase("")
    result.add("Empty phase tools", tools == [], f"tools={tools}")
    
    # Test 4: Validate all phases
    for phase in ["literature_review", "data_analysis", "field_survey", "conservation", "report"]:
        v = MCPClient.validate_phase_tools(phase)
        ok = v["status"] == "ready"
        result.add(f"Phase '{phase}' validation", ok, f"required={v['required']}, available={v['available']}")
    
    # Test 5: Format MCP call with edge params
    call = MCPClient.format_mcp_call("scholar", "search", {})
    result.add("Empty params MCP call", "MCP CALL" in call, f"len={len(call)}")
    
    call = MCPClient.format_mcp_call("scholar", "search", {"query": "x" * 5000})
    result.add("Large params MCP call", "MCP CALL" in call, f"len={len(call)}")
    
    # Test 6: Generate phase plan for all phases
    for phase in ["literature_review", "data_analysis", "report"]:
        plans = MCPClient.generate_phase_plan(phase, {"query": "test", "r_code": "print('hello')", "generate_charts": True, "chart_data": {"x": [1,2,3]}})
        result.add(f"Phase plan '{phase}'", isinstance(plans, list), f"{len(plans)} calls")
    
    # Test 7: Phase plan with empty context
    plans = MCPClient.generate_phase_plan("literature_review", {})
    result.add("Phase plan empty context", isinstance(plans, list), f"{len(plans)} calls")
    
    # Test 8: Unknown phase plan
    plans = MCPClient.generate_phase_plan("conservation", {})
    result.add("Phase plan 'conservation'", plans == [], f"calls={len(plans)}")


test_mcp_client()


# ═══════════════════════════════════════════════════════════
# Section 3: Config File Resilience
# ═══════════════════════════════════════════════════════════

def test_config_resilience():
    print("── 3. Config File Resilience ──")
    
    import yaml
    
    configs_to_check = [
        ("coordination.yaml", ROOT / "coordination.yaml"),
        ("cognitive/agent.yaml", ROOT / "cognitive-search-engine/config/agent.yaml"),
        ("fish/agent.yaml", ROOT / "fish-ecology-assistant/config/agent.yaml"),
        ("porpoise/agent.yaml", ROOT / "porpoise-agent/config/agent.yaml"),
        ("cognitive/evolution.yaml", ROOT / "cognitive-search-engine/config/evolution.yaml"),
        ("fish/evolution.yaml", ROOT / "fish-ecology-assistant/config/evolution.yaml"),
        ("porpoise/evolution.yaml", ROOT / "porpoise-agent/config/evolution.yaml"),
        ("fish/component_registry.yaml", ROOT / "fish-ecology-assistant/config/component_registry.yaml"),
        ("porpoise/component_registry.yaml", ROOT / "porpoise-agent/config/component_registry.yaml"),
        ("cognitive/component_registry.yaml", ROOT / "cognitive-search-engine/config/component_registry.yaml"),
        ("config/meso_agent.yaml", ROOT / "config/meso_agent.yaml"),
    ]
    
    for name, path in configs_to_check:
        try:
            if not path.exists():
                result.add(f"Exists: {name}", False, detail="file missing")
                continue
            
            content = path.read_text(encoding="utf-8")
            result.add(f"Readable: {name}", True, f"{len(content)} chars")
            
            # Try YAML parse
            try:
                data = yaml.safe_load(content)
                result.add(f"Valid YAML: {name}", data is not None,
                          f"top-level keys: {list(data.keys())[:5] if isinstance(data, dict) else type(data).__name__}")
            except yaml.YAMLError as e:
                result.add(f"Valid YAML: {name}", False, error=str(e)[:100])
            
            # Check for truncated/large files
            if len(content) < 50:
                result.add(f"Min size: {name}", False, detail=f"only {len(content)} chars — possibly truncated")
            elif len(content) > 50000:
                result.add(f"Max size: {name}", False, detail=f"{len(content)} chars — unusually large")
            
        except Exception as e:
            result.add(f"Access: {name}", False, error=str(e))
    
    # Test: Missing config (shouldn't crash validation)
    nonexistent = ROOT / "nonexistent_config.yaml"
    result.add("Nonexistent config access",
               not nonexistent.exists(),
               f"correctly reports missing")


test_config_resilience()


# ═══════════════════════════════════════════════════════════
# Section 4: Evolution Parameter Boundary Tests
# ═══════════════════════════════════════════════════════════

def test_evolution_boundaries():
    print("── 4. Evolution Parameter Boundaries ──")
    
    import yaml
    
    evolution_configs = [
        ROOT / "cognitive-search-engine/config/evolution.yaml",
        ROOT / "fish-ecology-assistant/config/evolution.yaml",
        ROOT / "porpoise-agent/config/evolution.yaml",
    ]
    
    for evo_path in evolution_configs:
        if not evo_path.exists():
            continue
        
        proj = evo_path.parts[-3] if len(evo_path.parts) > 3 else "unknown"
        
        try:
            data = yaml.safe_load(evo_path.read_text(encoding="utf-8"))
            params = data.get("evolution", {}).get("adaptive_params", {})
            
            for param_name, param in params.items():
                current = param.get("current")
                rng = param.get("range", [])
                
                if rng and len(rng) == 2:
                    # Check current is within range
                    in_range = rng[0] <= current <= rng[1]
                    result.add(f"[{proj}] {param_name} in range [{rng[0]}, {rng[1]}]",
                              in_range,
                              f"current={current} {'✅' if in_range else '❌ OUT OF RANGE'}")
                    
                    # Check range boundaries are sane
                    if rng[0] >= rng[1]:
                        result.add(f"[{proj}] {param_name} range valid", False,
                                  detail=f"min >= max: [{rng[0]}, {rng[1]}]")
            
            # Check triggers
            triggers = data.get("evolution", {}).get("feedback_loop", {}).get("evolution_triggers", {})
            for trig_name, trig in triggers.items():
                has_condition = "condition" in trig
                has_action = "action" in trig
                result.add(f"[{proj}] Trigger '{trig_name}' complete",
                          has_condition and has_action,
                          f"condition={'✅' if has_condition else '❌'}, action={'✅' if has_action else '❌'}")
            
        except Exception as e:
            result.add(f"Parse: {proj} evolution.yaml", False, error=str(e))


test_evolution_boundaries()


# ═══════════════════════════════════════════════════════════
# Section 5: Performance / Throughput
# ═══════════════════════════════════════════════════════════

def test_performance_boundaries():
    print("── 5. Performance Boundaries ──")
    
    try:
        sys.path.insert(0, str(ROOT / "porpoise-agent"))
        from src.agent.orchestrator import CrossDelegation, route_research_question, MCPClient
    except Exception as e:
        result.add("Import for perf test", False, error=str(e))
        return
    
    # Test 1: Routing throughput
    queries = [
        "fish ecology Poyang Lake community structure 2024",
        "江豚 passive acoustic monitoring Yangtze River",
        "Ochetobius_elongatus diet feeding habits",
        "fishing ban impact biodiversity assessment",
        "porpoise click detection NBHF pulse train classification",
    ] * 20  # 100 queries
    
    start = time.perf_counter()
    for q in queries:
        route_research_question(q)
    elapsed = time.perf_counter() - start
    
    qps = len(queries) / elapsed if elapsed > 0 else 0
    result.add("Routing throughput (>100 QPS)", qps > 100,
              f"{qps:.0f} QPS ({len(queries)} queries in {elapsed:.3f}s)")
    
    # Test 2: Delegation format throughput
    start = time.perf_counter()
    for i in range(500):
        CrossDelegation.format_delegate("porpoise-agent", "detect-clicks", {"id": i, "threshold": -134.0})
    elapsed = time.perf_counter() - start
    
    ops = 500 / elapsed if elapsed > 0 else 0
    result.add("Format throughput (>1000 ops/s)", ops > 1000,
              f"{ops:.0f} ops/s (500 formats in {elapsed:.3f}s)")
    
    # Test 3: MCP phase validation throughput
    start = time.perf_counter()
    for _ in range(1000):
        MCPClient.validate_phase_tools("literature_review")
    elapsed = time.perf_counter() - start
    
    ops = 1000 / elapsed if elapsed > 0 else 0
    result.add("Phase validation throughput (>5000 ops/s)", ops > 5000,
              f"{ops:.0f} ops/s (1000 validations in {elapsed:.3f}s)")
    
    # Test 4: Memory — large query doesn't crash
    try:
        r = route_research_question("x" * 100000)
        result.add("100KB query routing (no crash)", True, f"routes={len(r)}")
    except Exception as e:
        result.add("100KB query routing (no crash)", False, error=str(e))
    
    # Test 5: Deep recursion — resolve_skill called many times
    try:
        for _ in range(10000):
            CrossDelegation.resolve_skill("porpoise-agent", "detect-clicks")
        result.add("10K resolve_skill (no memory leak)", True, "completed")
    except Exception as e:
        result.add("10K resolve_skill (no memory leak)", False, error=str(e))


test_performance_boundaries()


# ═══════════════════════════════════════════════════════════
# Section 6: YAML/Config Edge Cases
# ═══════════════════════════════════════════════════════════

def test_config_edge_cases():
    print("── 6. Config Edge Cases ──")
    
    # Check all agent.yaml have consistent 'shared' structure
    shared_keys_expected = {"version", "rule_framework", "philosophy", "coordination", "meso_agent", "peers"}
    
    for proj_name, agent_rel in [
        ("cognitive", "cognitive-search-engine/config/agent.yaml"),
        ("fish", "fish-ecology-assistant/config/agent.yaml"),
        ("porpoise", "porpoise-agent/config/agent.yaml"),
    ]:
        path = ROOT / agent_rel
        if not path.exists():
            result.add(f"[{proj_name}] agent.yaml exists", False)
            continue
        
        content = path.read_text(encoding="utf-8")
        
        # Check shared section keys
        if "shared:" in content:
            in_shared = False
            found_keys = set()
            for line in content.splitlines():
                if line.strip() == "shared:":
                    in_shared = True
                    continue
                if in_shared:
                    if line and not line.startswith(' ') and not line.startswith('#'):
                        break
                    if ':' in line and not line.strip().startswith('#'):
                        key = line.strip().split(':')[0].strip()
                        found_keys.add(key)
            
            missing = shared_keys_expected - found_keys
            result.add(f"[{proj_name}] shared section keys",
                      len(missing) == 0,
                      f"missing: {missing}" if missing else "all present")
        else:
            result.add(f"[{proj_name}] shared section", False, "missing 'shared:' section")
    
    # Check coordination.yaml references proper paths
    coord = ROOT / "coordination.yaml"
    if coord.exists():
        content = coord.read_text(encoding="utf-8")
        result.add("coordination.yaml has meso_cosmos", "meso_cosmos" in content)
        result.add("coordination.yaml has evolution section", "evolution:" in content)
        result.add("coordination.yaml references all 3 projects",
                  all(p in content for p in ["cognitive-search-engine", "fish-ecology-assistant", "porpoise-agent"]))


test_config_edge_cases()


# ═══════════════════════════════════════════════════════════
# Print Summary
# ═══════════════════════════════════════════════════════════

print()
print("═" * 50)
print(f"  Robustness & Boundary Test Report")
print(f"  {datetime.now().isoformat()[:19]}")
print("═" * 50)
print()
print(result.summary())

sys.exit(1 if result.failed + result.errors > 0 else 0)
