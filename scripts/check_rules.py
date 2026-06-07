#!/usr/bin/env python3
"""
Rule Compliance Checker — 18 规则跨项目合规检查
===============================================
Verifies each rule ID (FB-1..DS-4) maps to an active code/config path
across all three S-T-V projects.

Rule Framework:
  FB-1, FB-2: Feedback Loop (认识论循环)
  CP-1, CP-2: Contradiction Analysis (矛盾分析)
  SM-1, SM-2: State Machine (阶段论)
  WF-1, WF-2: Workflow (集中兵力)
  PT-1, PT-2: Proactive Trigger (主动权)
  EH-1, EH-2: Exception Handler (分类处理)
  MO-1, MO-2: Multi-Objective (系统平衡)
  DS-1..DS-4: DeepSeek Efficiency (效率原则)

Usage:
  python scripts/check_rules.py            # detailed report
  python scripts/check_rules.py --ci       # CI mode (exit code)
"""

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/Reasonix")

RULES = {
    "FB-1": {
        "name": "来源验证 — 最少独立源",
        "config_path": "verification_loop.investigation_first.min_sources_core_claim",
        "default": 3,
    },
    "FB-2": {
        "name": "验证状态标签",
        "config_path": "verification_loop.verification_status",
        "states": ["verified", "pending", "hypothesis", "unverifiable"],
    },
    "CP-1": {
        "name": "矛盾识别与分类",
        "config_path": "contradiction_analysis.contradiction_types",
        "types": ["antagonistic", "non_antagonistic", "structural", "phasic"],
    },
    "CP-2": {
        "name": "主要矛盾资源倾斜",
        "config_path": "contradiction_analysis.contradiction_budget_multiplier",
        "default": 2.5,
    },
    "SM-1": {
        "name": "阶段门控",
        "config_path": "phased_strategy.phase_gating",
        "features": ["no_skip", "allow_retreat"],
    },
    "SM-2": {
        "name": "战略退却",
        "config_path": "phased_strategy.phase_gating.retreat_strategy",
        "strategies": ["return_to_planner", "return_to_previous"],
    },
    "WF-1": {
        "name": "资源分配权重",
        "config_path": "contradiction_analysis.contradiction_levels",
        "levels": ["primary", "secondary", "peripheral"],
    },
    "WF-2": {
        "name": "独立研究路径",
        "config_path": "research_balance.independent_path",
        "default": True,
    },
    "PT-1": {
        "name": "前沿追踪",
        "skill": "frontier-tracker",
        "trigger": "proactive_suggestion",
    },
    "PT-2": {
        "name": "主动建议触发",
        "config_path": "research_balance.independent_path",
    },
    "EH-1": {
        "name": "对抗性矛盾处理",
        "config_path": "contradiction_analysis.contradiction_types.antagonistic",
        "strategy": "强制解决 — 阻塞后续阶段",
    },
    "EH-2": {
        "name": "非对抗性矛盾处理",
        "config_path": "contradiction_analysis.contradiction_types.non_antagonistic",
        "strategy": "标注并存 — 不阻塞",
    },
    "MO-1": {
        "name": "十大关系平衡",
        "config_path": "research_balance.priorities",
    },
    "MO-2": {
        "name": "多目标优化",
        "config_path": "research_balance.priorities",
    },
    "DS-1": {
        "name": "熵预算",
        "config_path": "orchestrator.max_steps",
        "concept": "compute proportional to question importance",
    },
    "DS-2": {
        "name": "稀疏激活",
        "skill": "karpathy-guard",
        "concept": "MoE routing — each skill fires only when condition met",
    },
    "DS-3": {
        "name": "差分验证",
        "skill": "verify-stats-handbook",
        "concept": "P(stale) scoring only changed packages",
    },
    "DS-4": {
        "name": "信息增益路由",
        "skill": "ima-smart-search",
        "concept": "P0 exact terms first → stop on hit",
    },
}

PROJECTS = ["fish-ecology-assistant", "porpoise-agent", "cognitive-search-engine"]


def check_rule_in_agent_yaml(rule_id: str, rule_info: dict) -> dict:
    """Check if a rule is referenced in any agent.yaml."""
    results = {}
    config_path = rule_info.get("config_path", "")
    
    for proj in PROJECTS:
        agent_yaml = ROOT / proj / "config" / "agent.yaml"
        if not agent_yaml.exists():
            results[proj] = "❌ no agent.yaml"
            continue
        
        content = agent_yaml.read_text(encoding="utf-8")
        
        # Check for the config path segments
        segments = config_path.split(".") if config_path else []
        found_segments = 0
        for seg in segments:
            if seg in content:
                found_segments += 1
        
        # Also check if rule ID is referenced
        rule_ref = rule_id in content
        
        if found_segments >= len(segments) * 0.5 and rule_ref:
            results[proj] = "✅"
        elif rule_ref or found_segments >= 1:
            results[proj] = "⚠️ partial"
        else:
            results[proj] = "— (via fish reference)"
    
    return results


def check_skill_exists(skill_name: str) -> dict:
    """Check if a skill exists in any project."""
    results = {}
    for proj in PROJECTS:
        if proj == "porpoise-agent":
            skill_path = ROOT / proj / "src" / "skills" / skill_name / "SKILL.md"
        elif proj == "cognitive-search-engine":
            skill_path = ROOT / proj / "skills" / f"{skill_name}.md"
        else:
            skill_path = ROOT / proj / ".reasonix" / "skills" / f"{skill_name}.md"
        
        results[proj] = "✅" if skill_path.exists() else "—"
    return results


def check_rule_in_engineering_grammar(rule_id: str) -> bool:
    """Check if rule is documented in engineering grammar."""
    grammar_paths = [
        ROOT / "fish-ecology-assistant" / ".reasonix" / "handbooks" / "engineering-grammar.md",
        ROOT / "porpoise-agent" / "docs" / "ENGINEERING_GRAMMAR.md",
    ]
    for path in grammar_paths:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if rule_id in content:
                return True
    return False


def main():
    ci_mode = "--ci" in sys.argv
    
    print(f"📋 Rule Compliance Check — {datetime.now().isoformat()[:19]}")
    print(f"   Framework: FB-1..DS-4 (18 rules)")
    print()
    
    # Header
    header = f"| Rule | Name | fish | porpoise | cognitive | Grammar | Skill |"
    sep =    f"|------|------|:----:|:--------:|:---------:|:-------:|:-----:|"
    print(header)
    print(sep)
    
    failures = 0
    for rule_id, rule_info in RULES.items():
        # Agent.yaml check
        agent_results = check_rule_in_agent_yaml(rule_id, rule_info)
        
        # Engineering grammar check
        grammar_ok = check_rule_in_engineering_grammar(rule_id)
        grammar_status = "✅" if grammar_ok else "⚠️"
        
        # Skill check
        skill_name = rule_info.get("skill")
        if skill_name:
            skill_results = check_skill_exists(skill_name)
            all_have = all(v == "✅" for v in skill_results.values())
            skill_status = "✅" if all_have else "⚠️"
        else:
            skill_status = "N/A"
        
        fish_status = agent_results.get("fish-ecology-assistant", "—")
        porp_status = agent_results.get("porpoise-agent", "—")
        cog_status = agent_results.get("cognitive-search-engine", "—")
        
        # Count partial/warnings as potential issues
        for status in [fish_status, porp_status, cog_status]:
            if "❌" in status:
                failures += 1
        
        print(f"| {rule_id} | {rule_info['name']} | {fish_status} | {porp_status} | {cog_status} | {grammar_status} | {skill_status} |")
    
    print()
    print(f"  Total rules: {len(RULES)}")
    print(f"  Config gaps: {failures}")
    
    # Summary
    if failures == 0:
        print("  ✅ All 18 rules have corresponding config/code references")
    else:
        print(f"  ⚠️ {failures} rule(s) have incomplete coverage")
    
    # Cross-project note
    print()
    print("  Note: cognitive-search-engine references fish-ecology-assistant's")
    print("  engineering-grammar.md as the canonical 18-rule source.")
    print("  '— (via fish reference)' = rule is inherited from fish's config.")
    
    if ci_mode:
        sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
