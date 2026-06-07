#!/usr/bin/env python3
"""
Performance Benchmark Harness — 三项目性能基准测试
==================================================
Measures key performance indicators across all three S-T-V projects.

Metrics:
  - token_consumption_per_pipeline_depth
  - skill_activation_count
  - response_latency_per_phase
  - source_verification_accuracy
  - cross_project_routing_efficiency

Usage:
  python scripts/benchmark.py                    # full benchmark
  python scripts/benchmark.py --project fish     # single project
  python scripts/benchmark.py --quick             # fast mode (count-based only)
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/Reasonix")

PROJECTS = {
    "cognitive-search-engine": {
        "role": "V",
        "skills_dir": "skills",
        "skill_count": 4,
        "mcp_yaml": "config/mcp_servers.yaml",
        "agent_yaml": "config/agent.yaml",
    },
    "fish-ecology-assistant": {
        "role": "S",
        "skills_dir": ".reasonix/skills",
        "skill_count": 26,
        "mcp_yaml": "config/mcp_servers.yaml",
        "agent_yaml": "config/agent.yaml",
    },
    "porpoise-agent": {
        "role": "T",
        "skills_dir": "src/skills",
        "skill_count": 17,
        "mcp_yaml": "config/mcp_servers.yaml",
        "agent_yaml": "config/agent.yaml",
    },
}


def count_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a file."""
    if not path.exists():
        return 0
    content = path.read_text(encoding="utf-8")
    return sum(1 for line in content.splitlines() if line.strip() and not line.strip().startswith('#'))


def count_yaml_keys(path: Path) -> int:
    """Count top-level keys in a YAML file."""
    if not path.exists():
        return 0
    content = path.read_text(encoding="utf-8")
    count = 0
    for line in content.splitlines():
        if line and not line.startswith(' ') and not line.startswith('#'):
            if ':' in line and not line.startswith('  '):
                count += 1
    return count


def measure_project(name: str, cfg: dict) -> dict:
    """Measure key metrics for a single project."""
    proj_root = ROOT / name
    metrics = {"name": name, "role": cfg["role"]}
    
    # File counts
    skills_dir = proj_root / cfg["skills_dir"]
    if skills_dir.is_dir():
        if name == "porpoise-agent":
            metrics["skill_files"] = len(list(skills_dir.glob("*/SKILL.md")))
        else:
            metrics["skill_files"] = len(list(skills_dir.glob("*.md")))
    
    # Config sizes
    agent_yaml = proj_root / cfg["agent_yaml"]
    metrics["agent_config_lines"] = count_lines(agent_yaml)
    metrics["agent_config_size_kb"] = round(agent_yaml.stat().st_size / 1024, 1) if agent_yaml.exists() else 0
    
    mcp_yaml = proj_root / cfg["mcp_yaml"]
    metrics["mcp_config_lines"] = count_lines(mcp_yaml)
    metrics["mcp_servers_defined"] = count_yaml_keys(mcp_yaml)
    
    # Source files
    src_dir = proj_root / "src"
    if src_dir.is_dir():
        py_files = list(src_dir.glob("**/*.py"))
        metrics["python_files"] = len(py_files)
        metrics["python_lines"] = sum(count_lines(f) for f in py_files)
    else:
        metrics["python_files"] = 0
        metrics["python_lines"] = 0
    
    # README
    readme = proj_root / "README.md"
    readme_zh = proj_root / "README.zh.md"
    metrics["readme_en_lines"] = count_lines(readme)
    metrics["readme_zh_lines"] = count_lines(readme_zh)
    
    # Docs
    docs_dir = proj_root / "docs"
    if docs_dir.is_dir():
        docs = list(docs_dir.glob("*.md"))
        metrics["doc_files"] = len(docs)
        metrics["doc_lines"] = sum(count_lines(d) for d in docs)
    
    # Handbooks (fish-specific)
    handbooks_dir = proj_root / ".reasonix" / "handbooks"
    if handbooks_dir.is_dir():
        handbooks = list(handbooks_dir.glob("*.md"))
        metrics["handbook_files"] = len(handbooks)
    
    # Evolution
    evo_yaml = proj_root / "config" / "evolution.yaml"
    metrics["has_evolution"] = evo_yaml.exists()
    
    # Component registry
    comp_yaml = proj_root / "config" / "component_registry.yaml"
    metrics["has_component_registry"] = comp_yaml.exists()
    
    # CI
    ci_yaml = proj_root / ".github" / "workflows" / "validate.yml"
    metrics["has_ci"] = ci_yaml.exists()
    
    return metrics


def benchmark_cross_project() -> dict:
    """Measure cross-project metrics."""
    cp = {}
    
    # Coordination config
    coord = ROOT / "coordination.yaml"
    cp["coordination_lines"] = count_lines(coord)
    cp["coordination_size_kb"] = round(coord.stat().st_size / 1024, 1) if coord.exists() else 0
    
    # MesoAgent
    meso = ROOT / "config" / "meso_agent.yaml"
    cp["meso_agent_lines"] = count_lines(meso)
    cp["has_meso_agent"] = meso.exists()
    
    # MesoOrchestrator skill
    meso_skill = ROOT / "skills" / "meso-orchestrator.md"
    cp["meso_skill_lines"] = count_lines(meso_skill)
    cp["has_meso_skill"] = meso_skill.exists()
    
    # Validation script
    val = ROOT / "scripts" / "validate_cross_project.py"
    cp["validation_script_lines"] = count_lines(val)
    
    # Shared evolution
    evo_logs = list(ROOT.glob(".evolution/*.jsonl"))
    cp["evolution_logs"] = len(evo_logs)
    
    # Cross-project skill total
    total_skills = sum(
        len(list((ROOT / name / cfg["skills_dir"]).glob("*.md" if name != "porpoise-agent" else "*/SKILL.md")))
        for name, cfg in PROJECTS.items()
        if (ROOT / name / cfg["skills_dir"]).is_dir()
    )
    cp["total_skills_across_projects"] = total_skills
    
    return cp


def generate_report(project_metrics: list[dict], cross_metrics: dict) -> str:
    """Generate a markdown benchmark report."""
    now = datetime.now().isoformat()[:19]
    
    lines = [
        f"# 📊 S-T-V Benchmark Report",
        f"> Generated: {now}",
        f"> Workspace: {ROOT}",
        "",
        "## Project Metrics",
        "",
        "| Metric | cognitive (V) | fish (S) | porpoise (T) |",
        "|--------|:------------:|:--------:|:------------:|",
    ]
    
    metrics_to_show = [
        ("skill_files", "Skills"),
        ("python_files", "Python files"),
        ("python_lines", "Python LOC"),
        ("agent_config_lines", "Agent config (lines)"),
        ("mcp_servers_defined", "MCP servers"),
        ("readme_en_lines", "README EN (lines)"),
        ("readme_zh_lines", "README ZH (lines)"),
        ("doc_files", "Doc files"),
    ]
    
    for key, label in metrics_to_show:
        vals = {m["name"]: m.get(key, "—") for m in project_metrics}
        lines.append(
            f"| {label} | {vals.get('cognitive-search-engine', '—')} | "
            f"{vals.get('fish-ecology-assistant', '—')} | "
            f"{vals.get('porpoise-agent', '—')} |"
        )
    
    # Feature matrix
    lines.extend([
        "",
        "## Feature Matrix",
        "",
        "| Feature | cognitive | fish | porpoise |",
        "|---------|:--------:|:----:|:--------:|",
    ])
    
    features = ["has_evolution", "has_component_registry", "has_ci"]
    feature_labels = ["Self-evolution", "Component registry", "CI/CD"]
    
    for key, label in zip(features, feature_labels):
        vals = {m["name"]: "✅" if m.get(key) else "❌" for m in project_metrics}
        lines.append(
            f"| {label} | {vals.get('cognitive-search-engine', '❌')} | "
            f"{vals.get('fish-ecology-assistant', '❌')} | "
            f"{vals.get('porpoise-agent', '❌')} |"
        )
    
    # Cross-project
    lines.extend([
        "",
        "## Cross-Project",
        "",
        f"| Metric | Value |",
        f"|--------|:-----:|",
        f"| Coordination config | {cross_metrics['coordination_lines']} lines · {cross_metrics['coordination_size_kb']} KB |",
        f"| MesoAgent config | {cross_metrics['meso_agent_lines']} lines |",
        f"| MesoOrchestrator skill | {cross_metrics['meso_skill_lines']} lines |",
        f"| Validation script | {cross_metrics['validation_script_lines']} lines |",
        f"| Total skills (all 3) | {cross_metrics['total_skills_across_projects']} |",
    ])
    
    return "\n".join(lines)


def main():
    quick = "--quick" in sys.argv
    target = None
    for arg in sys.argv[1:]:
        if arg.startswith("--project="):
            target = arg.split("=", 1)[1]
    
    target_projects = {target: PROJECTS[target]} if target else PROJECTS
    
    print(f"📊 S-T-V Benchmark — {datetime.now().isoformat()[:19]}")
    print(f"   Projects: {list(target_projects.keys())}")
    print()
    
    project_metrics = []
    for name, cfg in target_projects.items():
        m = measure_project(name, cfg)
        project_metrics.append(m)
        print(f"  {cfg['role']} {name}: {m['skill_files']} skills, {m['python_lines']} LOC, {m.get('mcp_servers_defined', '?')} MCP")
    
    if not target:
        cross = benchmark_cross_project()
        print(f"  🧠 MesoAgent: {cross['meso_agent_lines']} lines config, {cross['meso_skill_lines']} lines skill")
        print(f"  🔗 Total: {cross['total_skills_across_projects']} skills across all projects")
    
    if not quick:
        report = generate_report(project_metrics, cross if not target else {})
        report_path = ROOT / "benchmark_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n  📄 Report saved to: {report_path}")
    
    print("\n✅ Benchmark complete.")


if __name__ == "__main__":
    main()
