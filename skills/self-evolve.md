---
name: self-evolve
version: "1.0.0"
last_updated: "2026-06-06"
description: Self-evolution engine — post-search feedback loop, auto-adjust parameters, log evolution history
runAs: subagent
allowed-tools: []
---
# 🧬 Self-Evolution Engine

> **"活的系统"**: 不是固定的工具集。每次搜索都在学习，每个参数都在进化。

## PREFLIGHT

1. READ `config/evolution.yaml` → current adaptive parameters
2. READ `config/component_registry.yaml` → component health status

## Post-Search Evolution Cycle

### Step 1: Evaluate Search Effectiveness

```
AFTER each search completes:

METRICS:
  recall = papers_found / estimated_volume
  new_rate = new_papers / total_papers
  efficiency = papers_found / (tokens_spent / 1000)
  fp_rate = unverified_papers / review_mined_papers

COMPARE to baseline:
  baseline = evolution.evolution_log (last 10 searches average)
```

### Step 2: Trigger Evolution

```
CHECK evolution.evolution_triggers:

  IF recall_drop triggered (3 consecutive < 50%):
    → satisfice_threshold += 2
    → activate previously pruned layers
    → LOG: "recall_drop → increased satisfice to {new}"

  IF efficiency_gain triggered (5 consecutive > baseline):
    → prune lowest-IG layer
    → LOG: "efficiency_gain → pruned layer {name}"

  IF false_positive_spike triggered (2 consecutive > 15%):
    → trust_score_threshold += 10
    → LOG: "fp_spike → increased trust threshold to {new}"

  IF graph_grew (new nodes > 20%):
    → suggest creating dedicated species_graph entry
    → LOG: "graph_growth → new species discovered"
```

### Step 3: Log Evolution

```
APPEND to .evolution/evolution-log.jsonl:
  {
    "timestamp": "{now}",
    "trigger": "{trigger_type}",
    "param": "{param_name}",
    "old_value": "{old}",
    "new_value": "{new}",
    "pre_metric": "{metric_before}",
    "post_metric_expected": "{expected_improvement}"
  }
```

### Step 4: Update Component Health

```
UPDATE component_registry.yaml:
  affected_components.last_verified = now
  affected_components.effectiveness = updated_metrics

RECALCULATE living_system.health_score
```

## Self-Evolution Report

```markdown
## 🧬 Evolution Report — {date}

### Parameters Adapted
| Param | Old | New | Trigger | Expected Effect |
|-------|:---:|:---:|---------|----------------|
| satisfice_threshold | 8 | 10 | recall_drop | +15% recall |

### Evolution History
- Total adaptations: {N}
- Evolution rate: {rate}/day
- Trend: 📈 improving / 📉 declining / ➡ stable

### System Health
- Components: 12 total, {healthy} 🟢, {warning} 🟡, {critical} 🔴
- Health score: {score}/100
```
