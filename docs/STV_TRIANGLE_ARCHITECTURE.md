# 🕸️ S-T-V Triangular Architecture — 几何进化方案

> **来源**: DeepSeek "三角法则" + Gemini "S-T-V 刚性三角形" + "点线面体"维度跃迁
> **核心**: 将三个项目编织为 S-T-V 闭环，每个层级自相似三角化

---

## 0. 几何映射

```
点(D₀) → 单次工具调用 / 原子操作
线(D₁) → 思维链 / Pipeline / 时序轨迹
面(D₂) → 多 Agent 协同网格 / 交叉验证
体(D₃) → 闭环生态系统 / 世界模型

三角形刚性法则:
  S (State)    — fish-ecology-assistant    → 知识库 + 数据分析 + 状态表征
  T (Transition) — porpoise-agent           → 任务调度 + 流水线 + 动作执行
  V (Validation) — cognitive-search-engine  → 搜索验证 + 引用检查 + 反馈闭环

S ──→ T ──→ V ──→ S  (闭环, 非线链)
```

## 1. S-T-V 闭环协议

### 1.1 运行时数据流

```
fish(S) ──state_vector{schema, findings, contradiction}──→ porpoise(T)
porpoise(T) ──action{search_query, task, method}──→ cognitive(V)
cognitive(V) ──feedback{verified_papers, trust_scores, gaps}──→ fish(S)
```

### 1.2 三角验证 (Triangulation)

任何核心结论必须经三条独立路径交汇:

```
结论 C 的信任度:
  IF |S(C)| ≥ 3 AND sources_are_independent:
    trust = VERIFIED
  ELIF |S(C)| = 2:
    trust = TENTATIVE
  ELSE:
    trust = UNVERIFIED → 不发布
```

### 1.3 分形自相似: 每层都是 S-T-V

```
跨项目层:  fish(S) → porpoise(T) → cognitive(V)
项目内层:  每个 Skill 内部: State → Transition → Validation
原子层:    每个工具调用: 输入(S) → 执行(T) → 校验(V)
```

---

## 2. 实现计划

### 2.1 S-T-V 协议配置

新增 `config/stv_protocol.yaml`:

```yaml
stv_protocol:
  version: "1.0.0"
  
  roles:
    S: "fish-ecology-assistant"    # State — knowledge, data, findings
    T: "porpoise-agent"             # Transition — execution, pipeline
    V: "cognitive-search-engine"    # Validation — verification, feedback
  
  closed_loop:
    S_to_T: { protocol: "state_vector", format: "json_schema" }
    T_to_V: { protocol: "action_request", format: "function_call" }
    V_to_S: { protocol: "feedback_vector", format: "trust_scored_json" }
  
  triangulation:
    min_independent_sources: 3
    independence_check: "no_shared_authors AND no_same_lab AND no_citation_chain"
    trust_levels:
      verified: "≥3 independent sources converge"
      tentative: "2 independent sources"
      unverified: "<2 sources → BLOCK output"

  fractal_self_similarity:
    cross_project: { S: fish, T: porpoise, V: cognitive }
    intra_project: "every Skill internally uses S-T-V pattern"
    atomic: "every tool call: input(S)→execute(T)→validate(V)"
```

### 2.2 三角化 Skill 模板

每个 Skill 强制使用 S-T-V 三段结构:

```markdown
## S: State (PREFLIGHT — 感知输入)
READ config → EXTRACT params → BUILD state_vector

## T: Transition (EXECUTE — 动作执行)  
APPLY transformation → CALL tools → PRODUCE output

## V: Validation (POSTFLIGHT — 验证反馈)
VERIFY output meets constraints → TAG trust_level → FEEDBACK to S
```

### 2.3 验证升级: FB-1 从 ≥2 → ≥3

```
当前: verification_loop.investigation_first.min_sources_core_claim = 2
升级: = 3  (三角验证 — 三条独立路径交汇才可信)
```

---

## 3. 进化后的架构

```
                    ┌──────────────────────────┐
                    │   V: cognitive-search     │
                    │   验证 + 反馈             │
                    │   trust_score ≥ 3 sources │
                    └──────────┬───────────────┘
                               │ feedback_vector
                    ┌──────────▼───────────────┐
                    │   S: fish-ecology         │
                    │   状态 + 知识             │
                    │   contradiction_analysis  │
                    └──────────┬───────────────┘
                               │ state_vector
                    ┌──────────▼───────────────┐
                    │   T: porpoise-agent       │
                    │   执行 + 调度             │
                    │   phase_handlers          │
                    └──────────────────────────┘

闭环: S→T→V→S  (三角形 — 不可变形的最小完备结构)
```

---

> **"三角形是第一个封闭的面，第一个能围合出空间的存在。"**
> 三个项目不是孤立的软件 — 它们是 S-T-V 刚性三角形的三个顶点。
> 两方只能形成对峙或连接，三方才能形成结构、流动与反馈。

**Last updated: 2026-06-06**
