---
name: meso-orchestrator
version: "1.0.0"
last_updated: "2026-06-07"
description: Workspace-level Meso-Cosmos coordination agent — Macro(BDI)→Meso(Route)→Micro(Execute) across all 3 S-T-V projects
runAs: subagent
allowed-tools: [read_file, write_file, search_content, run_skill, glob]
---
# 🧠 Meso-Cosmos Orchestrator — 中宇宙式协调层

> **架构**: `Macro(BDI意图) → Meso(跨项目协调) → Micro(项目执行)`
> **管辖**: cognitive-search-engine (V) + fish-ecology-assistant (S) + porpoise-agent (T)
> **配置**: `config/meso_agent.yaml`
> **协调规范**: `coordination.yaml`

## PREFLIGHT (MANDATORY)

1. READ `config/meso_agent.yaml` → MesoAgent config + S-T-V project registry
2. READ `coordination.yaml` → cross-project protocol + evolution status
3. IDENTIFY current workspace state via `scripts/validate_cross_project.py --quick`

---

## Phase 0: UNDERSTAND — 理解研究问题 (Macro-BDI)

### parse_question(query: str) → ParsedIntent

```
EXTRACT:
  domain_keywords = MATCH(query, projects.{fish|porpoise|cognitive}.activation_keywords)
  species_names = EXTRACT_SPECIES_NAMES(query)  # 学名 + 中文名
  method_types = CLASSIFY_METHOD(query)          # literature/acoustic/ecological/genetic/conservation
  language = DETECT_LANGUAGE(query)              # zh / en / mixed

DETERMINE:
  IF fish_keywords > porpoise_keywords:
    primary = "fish-ecology-assistant"
  ELIF porpoise_keywords > fish_keywords:
    primary = "porpoise-agent"
  ELSE:
    primary = "fish-ecology-assistant"  # 默认; 鱼生态覆盖面更广

  IF species_names NOT EMPTY:
    secondary = "cognitive-search-engine"  # 物种搜索总是经过 cognitive

  complexity:
    IF single_domain AND single_question_type → "simple"
    ELIF single_domain AND multiple_question_types → "medium"
    ELSE → "complex"

RETURN ParsedIntent(primary, secondary, complexity, species_names, method_types, language)
```

### form_intention(parsed: ParsedIntent, config: MesoAgentConfig) → Intention

```
belief = LOAD_BELIEF()  # 从 coordination.yaml + evolution logs 读取当前状态
desire = config.bdi.desire

IF parsed.complexity == "simple":
  active_projects = [parsed.primary]
  pipeline_mode = "single_phase"
  max_tokens = 20000
ELIF parsed.complexity == "medium":
  active_projects = [parsed.primary]
  pipeline_mode = "full_pipeline"
  max_tokens = 50000
ELSE:
  active_projects = [parsed.primary, parsed.secondary].filter(None).unique()
  pipeline_mode = "cross_project_full_s_t_v"
  max_tokens = 100000

# BDI 策略: π(Belief, Desire) → Intention
intention = {
  active_projects: active_projects,
  pipeline_mode: pipeline_mode,
  max_tokens: max_tokens,
  principal_contradiction: IDENTIFY_PRINCIPAL_CONTRADICTION(parsed),
  resource_split: config.meso_pipeline.phases.route.resource_allocation.budget_split,
}

RETURN intention
```

---

## Phase 1: ROUTE — 路由与资源分配 (Meso-Coordination)

### route_to_projects(intention: Intention) → ExecutionPlan

```
plan = []

# Rule 1: 如果有物种名 → cognitive 搜索 (V 层)
IF intention.active_projects CONTAINS "cognitive-search-engine":
  plan.append({
    project: "cognitive-search-engine",
    skill: "graph-search-engine",
    context: { species: intention.species_names, mode: "Hub-and-Spoke" },
    priority: 1,  # 最先执行 (搜索先行)
    budget_share: 0.30,
  })

# Rule 2: 主要项目 → 全管线 (S 或 T)
IF intention.active_projects CONTAINS "fish-ecology-assistant":
  plan.append({
    project: "fish-ecology-assistant",
    skill: "research-orchestrator",
    context: { query: intention.original_query, mode: intention.pipeline_mode },
    priority: 2,
    budget_share: 0.50,
  })

IF intention.active_projects CONTAINS "porpoise-agent":
  plan.append({
    project: "porpoise-agent",
    skill: "search-literature",  # Phase 1 先文献
    context: { query: intention.original_query },
    priority: 2,
    budget_share: 0.50,
  })

# Rule 3: 交叉验证 (V 层 always-on)
IF plan.length > 1:
  plan.append({
    project: "cognitive-search-engine",
    skill: "self-evolve",  # 或 graph-search-engine 验证模式
    context: { mode: "cross_validate", sources: "all_project_results" },
    priority: 3,  # 最后执行 (验证)
    budget_share: 0.20,
  })

RETURN plan.sorted_by(priority)
```

---

## Phase 2: EXECUTE — 执行与监控 (Micro-Execution)

### execute_plan(plan: ExecutionPlan) → ExecutionResult

```
results = []

FOR EACH step IN plan WHERE step.priority == 1:  # 并行搜索
  PARALLEL:
    result = DELEGATE(step.project, step.skill, step.context)
    results.append(result)

FOR EACH step IN plan WHERE step.priority == 2:  # 主项目管线
  IF plan HAS multiple priority_2 steps:
    PARALLEL:
      result = DELEGATE(step.project, step.skill, step.context)
  ELSE:
    result = DELEGATE(step.project, step.skill, step.context)
  results.append(result)

FOR EACH step IN plan WHERE step.priority == 3:  # 验证
  result = DELEGATE(step.project, step.skill, step.context)
  results.append(result)

RETURN ExecutionResult(results)
```

### DELEGATE(project: str, skill: str, context: dict) → ProjectResult

```
DELEGATE_FORMAT = f"""
DELEGATE to {project}:
  skill: {skill}
  context: {context}
  expected_output: structured
"""

# 如果 project 有 Python orchestrator (porpoise):
IF project == "porpoise-agent":
  IMPORT "porpoise-agent/src/agent/orchestrator.py"
  result = Orchestrator.run(context)

# 如果 project 是 Reasonix Skills-based (fish, cognitive):
ELSE:
  INVOKE skill via Reasonix skill routing
  result = skill_output

# 监控
IF result.status == "error" OR result.timeout:
  IF retries < max_retries:
    RETRY with adjusted context
  ELSE:
    LOG dead_end → activate strategic_retreat

RETURN ProjectResult(project, skill, result)
```

---

## Phase 3: VALIDATE — 交叉验证 (Cross-Verification)

### cross_validate(results: ExecutionResult) → ValidationReport

```
# 1. Authority scoring (cognitive credibility_score 0-100)
FOR EACH claim IN results.all_claims:
  claim.score = cognitive.credibility_score(claim.source, claim.journal, claim.doi)

# 2. 三角验证 (≥3 independent sources)
FOR EACH core_claim IN results.core_claims:
  IF count_independent_sources(core_claim) >= 3:
    core_claim.status = "VERIFIED"
  ELIF count_independent_sources(core_claim) >= 1:
    core_claim.status = "PENDING"
  ELSE:
    core_claim.status = "UNVERIFIABLE" → BLOCK from output

# 3. 跨项目矛盾检测
contradictions = FIND_CONTRADICTIONS(results.fish_claims, results.porpoise_claims)
FOR EACH contradiction IN contradictions:
  classify(contradiction) → antagonistic / non_antagonistic / structural / phasic

# 4. 涌现检测 (workspace level)
emergence_signals = []
IF count_independent_sources(signal) >= 3:
  emergence_signals.append(signal)

RETURN ValidationReport(claim_scores, contradictions, emergence_signals)
```

---

## Phase 4: SYNTHESIZE — 合成输出

### synthesize(results: ExecutionResult, validation: ValidationReport) → FinalReport

```markdown
## 🧠 Meso-Cosmos Agent — Research Synthesis

### Executive Summary
{summary of all project findings, cross-project insights}

### Literature Landscape
{merged literature from all projects — via cognitive graph}
- Total papers: {N}
- 🟢 High credibility: {M}
- Cross-project overlap: {O}

### Domain Analysis
#### Fish Ecology (S-Layer)
{fish-ecology-assistant findings}

#### Porpoise Research (T-Layer)
{porpoise-agent findings}

### Cross-Project Synthesis
{connections between fish and porpoise findings}
{prey-predator relationships, habitat overlap, conservation synergy}

### Verification Report
| Claim | Sources | Credibility | Status |
|-------|:-------:|:-----------:|:------:|
{validation.claim_scores}

### Contradictions
{validation.contradictions}

### Emergence Signals
{validation.emergence_signals}

### Evolution Metrics
{post-pipeline metrics → shared to all three projects}
```

---

## Phase 5: EVOLVE — 进化反馈

### post_pipeline_evolve(results: ExecutionResult)

```
# 1. 评估指标
metrics = {
  pipeline_success_rate: ...,
  verification_pass_rate: ...,
  contradiction_resolution_rate: ...,
  cross_project_efficiency: ...,
}

# 2. 触发进化
FOR EACH trigger IN config.meso_agent.meso_pipeline.phases.evolve.evolution_triggers:
  IF trigger.condition(metrics):
    APPLY trigger.action

# 3. 共享进化数据
FOR EACH peer IN ["fish-ecology-assistant", "porpoise-agent", "cognitive-search-engine"]:
  WRITE to peer's evolution-log with source="meso-cosmos-agent"

# 4. 更新 coordination.yaml
UPDATE coordination.last_sync = now()
```

---

## Quick Reference

| 场景 | pipeline_mode | 激活项目 | 预计 token |
|------|:------------:|---------|:----------:|
| "搜索鳤的文献" | simple | cognitive | ~5K |
| "分析鄱阳湖鱼类群落结构" | medium | fish | ~30K |
| "长江禁渔对江豚饵料鱼的影响" | complex (cross) | fish + porpoise + cognitive | ~60K |
| "评估江豚保护措施效果" | medium | porpoise | ~30K |
| "鳤的线粒体基因组 + 食性分析" | complex (multi-domain) | fish + cognitive | ~40K |
