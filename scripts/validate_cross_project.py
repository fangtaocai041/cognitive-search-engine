#!/usr/bin/env python3
"""
Cross-Project Validation Script — 三项目一致性检查
==================================================
Validates coordination.yaml consistency across all three projects:
  - cognitive-search-engine (V)
  - fish-ecology-assistant (S)
  - porpoise-agent (T)

Usage:
  python scripts/validate_cross_project.py           # full check
  python scripts/validate_cross_project.py --quick   # badge counts only
  python scripts/validate_cross_project.py --ci      # CI mode (exit code)

CI Integration:
  Add to .github/workflows/validate.yml in any of the three repos:
    - name: Cross-Project Validation
      run: python D:/Reasonix/scripts/validate_cross_project.py --ci
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/Reasonix")

PROJECTS = {
    "cognitive-search-engine": {
        "role": "V",
        "agent_yaml": "config/agent.yaml",
        "readme_en": "README.md",
        "readme_zh": "README.zh.md",
        "skills_dir": "skills",
        "mcp_yaml": "config/mcp_servers.yaml",
        "evolution_yaml": "config/evolution.yaml",
        "component_registry": "config/component_registry.yaml",
    },
    "fish-ecology-assistant": {
        "role": "S",
        "agent_yaml": "config/agent.yaml",
        "readme_en": "README.md",
        "readme_zh": "README.zh.md",
        "skills_dir": ".reasonix/skills",
        "mcp_yaml": "config/mcp_servers.yaml",
        "evolution_yaml": "config/evolution.yaml",
        "component_registry": "config/component_registry.yaml",
    },
    "porpoise-agent": {
        "role": "T",
        "agent_yaml": "config/agent.yaml",
        "readme_en": "README.md",
        "readme_zh": "README.zh.md",
        "skills_dir": "src/skills",
        "mcp_yaml": "config/mcp_servers.yaml",
        "evolution_yaml": "config/evolution.yaml",
        "component_registry": "config/component_registry.yaml",
    },
}

COORDINATION_PATH = ROOT / "coordination.yaml"

# ── helpers ──────────────────────────────────────────────

def ok(msg):
    return f"  ✅ {msg}"

def warn(msg):
    return f"  ⚠️ {msg}"

def fail(msg):
    return f"  ❌ {msg}"

def count_files_in_dir(path: Path, pattern="*"):
    if not path.is_dir():
        return 0
    return len(list(path.glob(pattern)))

def extract_badge_count(line: str, badge_name: str) -> int | None:
    """Extract number from a README badge line like '[skills-25]' or '[MCP-22]'."""
    import re
    # Match patterns like "skills-25", "MCP-22", "Skills:25"
    m = re.search(rf'{badge_name}[:\- ]*(\d+)', line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def read_skill_count_from_agent_yaml(path: Path) -> int | None:
    """Count skills listed in agent.yaml."""
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    # Count lines with '- ' under skills sections
    import re
    in_skills = False
    count = 0
    for line in content.splitlines():
        if 'skills:' in line and not line.strip().startswith('#'):
            in_skills = True
            continue
        if in_skills and line.strip().startswith('- ') and not line.strip().startswith('#') and 'skill_' not in line:
            # Only count actual skill names (not config keys)
            skill_name = line.strip()[2:].strip()
            if skill_name and not skill_name.startswith(('auto_', 'default_', 'skill_', 'external_')):
                count += 1
        elif in_skills and not line.strip().startswith('- ') and not line.strip().startswith('#'):
            if line.strip() and not line.startswith(' '):
                in_skills = False
    return count if count > 0 else None

def count_mcp_servers(path: Path) -> int | None:
    """Count MCP servers defined in mcp_servers.yaml."""
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    # Count server blocks (top-level keys under 'servers:')
    import re
    in_servers = False
    count = 0
    for line in content.splitlines():
        if line.strip() == 'servers:':
            in_servers = True
            continue
        if in_servers and line and not line.startswith(' ') and not line.startswith('#'):
            if ':' in line and not line.startswith('  '):
                in_servers = False
                continue
        if in_servers and line.startswith('  ') and not line.startswith('    ') and not line.startswith('  #'):
            if ':' in line and not line.strip().startswith('#'):
                count += 1
    return count if count > 0 else None


# ── checks ───────────────────────────────────────────────

def check_file_exists(path: Path, label: str) -> tuple[bool, str]:
    if path.exists():
        return True, ok(f"{label} exists: {path.relative_to(ROOT)}")
    return False, fail(f"{label} MISSING: {path.relative_to(ROOT)}")

def check_coordination_yaml():
    """Validate coordination.yaml integrity."""
    results = []
    if not COORDINATION_PATH.exists():
        results.append(fail("coordination.yaml MISSING at workspace root!"))
        return results
    
    results.append(ok("coordination.yaml found"))
    content = COORDINATION_PATH.read_text(encoding="utf-8")
    
    # Check version
    import re
    m = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', content)
    if m:
        results.append(ok(f"coordination version: {m.group(1)}"))
    
    # Check all three projects referenced
    for name in PROJECTS:
        if name in content:
            results.append(ok(f"Project referenced: {name}"))
        else:
            results.append(fail(f"Project NOT referenced: {name}"))
    
    # Check S-T-V triangle complete
    for role in ['S', 'T', 'V']:
        if f'"{role}"' in content or f"'{role}'" in content or f'role: "{role}"' in content:
            pass  # role found
        else:
            results.append(warn(f"S-T-V role '{role}' may not be explicitly referenced"))
    
    return results

def check_project(name: str, cfg: dict):
    """Validate a single project."""
    results = []
    proj_root = ROOT / name
    
    if not proj_root.is_dir():
        results.append(fail(f"Project directory MISSING: {name}"))
        return results
    
    results.append(ok(f"\n── {name} ({cfg['role']}) ──"))
    
    # Agent yaml
    agent_path = proj_root / cfg["agent_yaml"]
    exists, msg = check_file_exists(agent_path, "agent.yaml")
    results.append(msg)
    
    if exists:
        content = agent_path.read_text(encoding="utf-8")
        # Check shared section
        if "shared:" in content:
            results.append(ok("agent.yaml has 'shared' section"))
        else:
            results.append(warn("agent.yaml missing 'shared' section"))
    
    # Evolution yaml
    evo_path = proj_root / cfg.get("evolution_yaml", "")
    exists, msg = check_file_exists(evo_path, "evolution.yaml")
    results.append(msg)
    
    # Component registry
    reg_path = proj_root / cfg.get("component_registry", "")
    exists, msg = check_file_exists(reg_path, "component_registry.yaml")
    results.append(msg)
    
    # README EN
    readme_en = proj_root / cfg["readme_en"]
    exists, msg = check_file_exists(readme_en, "README.md (EN)")
    results.append(msg)
    
    # README ZH
    readme_zh = proj_root / cfg["readme_zh"]
    exists, msg = check_file_exists(readme_zh, "README.zh.md (ZH)")
    results.append(msg)
    
    # Skill count
    skills_dir = proj_root / cfg["skills_dir"]
    if skills_dir.is_dir():
        if name == "porpoise-agent":
            # Count subdirectories with SKILL.md
            skill_count = count_files_in_dir(skills_dir, "*/SKILL.md")
        else:
            skill_count = count_files_in_dir(skills_dir, "*.md")
        results.append(ok(f"Skills directory: {skills_dir.relative_to(ROOT)} → {skill_count} files"))
        
        # Check against README badge
        if readme_en.exists():
            readme_content = readme_en.read_text(encoding="utf-8")
            badge_count = extract_badge_count(readme_content, "skills")
            if badge_count:
                if badge_count == skill_count:
                    results.append(ok(f"README skills badge ({badge_count}) matches actual ({skill_count})"))
                else:
                    results.append(fail(f"README skills badge ({badge_count}) ≠ actual ({skill_count})"))
    else:
        results.append(fail(f"Skills directory MISSING: {skills_dir.relative_to(ROOT)}"))
    
    # MCP count
    mcp_path = proj_root / cfg["mcp_yaml"]
    if mcp_path.exists():
        mcp_count = count_mcp_servers(mcp_path)
        if mcp_count:
            results.append(ok(f"MCP servers defined: {mcp_count}"))
            
            if readme_en.exists():
                readme_content = readme_en.read_text(encoding="utf-8")
                badge_count = extract_badge_count(readme_content, "MCP")
                if badge_count:
                    if badge_count == mcp_count or abs(badge_count - mcp_count) <= 1:
                        results.append(ok(f"README MCP badge ({badge_count}) ≈ actual ({mcp_count})"))
                    else:
                        results.append(fail(f"README MCP badge ({badge_count}) ≠ actual ({mcp_count})"))
    
    # CI/CD
    ci_path = proj_root / ".github/workflows/validate.yml"
    exists, msg = check_file_exists(ci_path, "CI/CD validate.yml")
    results.append(msg)
    
    return results

def check_cross_consistency():
    """Check cross-project consistency."""
    results = []
    results.append(ok("\n── Cross-Project Consistency ──"))
    
    # Check all three have evolution.yaml
    all_have_evolution = True
    for name, cfg in PROJECTS.items():
        evo_path = ROOT / name / cfg["evolution_yaml"]
        if not evo_path.exists():
            results.append(warn(f"{name} missing evolution.yaml"))
            all_have_evolution = False
    if all_have_evolution:
        results.append(ok("All three projects have evolution.yaml"))
    
    # Check all three have component_registry
    all_have_registry = True
    for name, cfg in PROJECTS.items():
        reg_path = ROOT / name / cfg["component_registry"]
        if not reg_path.exists():
            results.append(warn(f"{name} missing component_registry.yaml"))
            all_have_registry = False
    if all_have_registry:
        results.append(ok("All three projects have component_registry.yaml"))
    
    # Check READMEs have S-T-V triangle references
    for name, cfg in PROJECTS.items():
        readme_en = ROOT / name / cfg["readme_en"]
        if readme_en.exists():
            content = readme_en.read_text(encoding="utf-8")
            if "S-T-V" in content or "S-T-V Triangle" in content or "STV" in content:
                pass  # found
            else:
                results.append(warn(f"{name} README missing S-T-V triangle reference"))
    
    # Check all README.zh exist and have similar structure to EN
    for name, cfg in PROJECTS.items():
        readme_en = ROOT / name / cfg["readme_en"]
        readme_zh = ROOT / name / cfg["readme_zh"]
        if readme_en.exists() and readme_zh.exists():
            en_len = len(readme_en.read_text(encoding="utf-8"))
            zh_len = len(readme_zh.read_text(encoding="utf-8"))
            ratio = zh_len / max(en_len, 1)
            if 0.5 < ratio < 2.0:
                results.append(ok(f"{name} README EN↔ZH length ratio: {ratio:.2f} (reasonable)"))
            else:
                results.append(warn(f"{name} README EN↔ZH length ratio: {ratio:.2f} (may need sync)"))
    
    return results


# ── main ─────────────────────────────────────────────────

def main():
    quick = "--quick" in sys.argv
    ci_mode = "--ci" in sys.argv
    
    print(f"🔗 Cross-Project Validation — {datetime.now().isoformat()[:19]}")
    print(f"   Workspace: {ROOT}")
    print()
    
    all_results = []
    failures = 0
    
    # 1. Coordination check
    all_results.extend(check_coordination_yaml())
    
    if not quick:
        # 2. Per-project checks
        for name, cfg in PROJECTS.items():
            all_results.extend(check_project(name, cfg))
        
        # 3. Cross-consistency
        all_results.extend(check_cross_consistency())
    
    # Print results
    for r in all_results:
        print(r)
        if r.startswith("  ❌"):
            failures += 1
    
    print()
    print(f"── Summary ──")
    print(f"  Total checks: {len(all_results)}")
    print(f"  Failures: {failures}")
    
    if failures == 0:
        print("  ✅ All checks passed!")
    else:
        print(f"  ❌ {failures} check(s) failed — review above")
    
    if ci_mode:
        sys.exit(0 if failures == 0 else 1)

if __name__ == "__main__":
    main()
