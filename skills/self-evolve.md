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

### evaluate_search(result: SearchResult) → Metrics

```
recall = result.papers_found / max(result.estimated_volume, 1)
new_rate = len(result.new_papers) / max(result.total_papers, 1)
efficiency = result.papers_found / max(result.tokens_spent / 1000, 1)
fp_rate = len(filter(result.papers, λp: p.trust == UNVERIFIED)) / max(len(result.review_mined_papers), 1)
baseline = avg(last_10_evolution_logs.metrics)
RETURN Metrics(recall, new_rate, efficiency, fp_rate, baseline)
```

### trigger_evolution(m: Metrics, config: EvolutionConfig) → list[Adaptation]

```
adaptations = []

# Trigger 1: recall_drop
IF m.recall < 0.5 FOR 3 CONSECUTIVE searches:
  config.satisfice_threshold = min(20, config.satisfice_threshold + 2)
  adaptations.append(Adaptation("recall_drop", "satisfice_threshold", +2))

# Trigger 2: efficiency_gain
IF m.efficiency > m.baseline.efficiency × 1.2 FOR 5 CONSECUTIVE searches:
  pruned = prune_lowest_ig_layer()
  adaptations.append(Adaptation("efficiency_gain", "pruned_layer", pruned))

# Trigger 3: false_positive_spike
IF m.fp_rate > 0.15 FOR 2 CONSECUTIVE searches:
  config.trust_score_threshold = min(70, config.trust_score_threshold + 10)
  adaptations.append(Adaptation("fp_spike", "trust_score_threshold", +10))

RETURN adaptations
```

### log_evolution(adaptations: list[Adaptation])

```
FOR EACH a IN adaptations:
  append_jsonl(".evolution/evolution-log.jsonl", {
    timestamp: now_iso(),
    trigger: a.trigger,
    param: a.param_name,
    old_value: a.old_value,
    new_value: a.new_value,
    pre_metric: a.pre_metric,
  })
```

### update_health(adaptations: list[Adaptation])

```
UPDATE component_registry.yaml:
  FOR EACH affected_component IN adaptations.affected_components:
    component.last_verified = now()
    component.effectiveness = recompute_metrics()
  living_system.health_score = recompute_health()
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
