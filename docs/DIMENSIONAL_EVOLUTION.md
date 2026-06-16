# 🌐 三角闭环维度进化 — 点线面体全场景矩阵

> **三角闭环**: fish(V0) + cognitive(V1) + eon-core(Coord)
> **三生万物**: P₁(porpoise) · P₂(coilia) · ... 从三角衍生
> **维度**: 三个项目分别占据 D₁→D₂→D₃，编织为三角闭环体

---

## 0. 三维度映射

```
D₀ (点): 原子操作 — 单次 SQL/API/工具调用
D₁ (线): 因果轨迹 — Pipeline/Workflow/CoT
D₂ (面): 拓扑网格 — 多 Agent 协同/交叉验证/图谱遍历
D₃ (体): 闭环实体 — 自愈生态/世界模型/数字孪生

项目维度分配:
  fish-ecology-assistant:    D₁(线) → D₂(面) — 多 Agent 网状交叉验证
  porpoise-agent:            D₁(线) → D₂(面) → D₃(体) — 自愈式动态生态
  cognitive-search-engine:   D₂(面) → D₃(体) — 世界模型 + 预测仿真
```

## 1. 全场景矩阵 (项目化映射)

| 维度 | 数据分析 (fish) | 自动化工作流 (porpoise) | 具身交互 (cognitive) |
|------|---------------|----------------------|---------------------|
| **D₀ 点** | `stats-assistant` 单次 R 代码执行 | `_invoke_skill()` 单次工具调用 | `search_exact()` 单次搜索 |
| **D₁ 线** | Pipeline: plan→search→analyze→write→review | Orchestrator: 5-phase FSM | 11-layer search protocol |
| **D₂ 面** | 🆕 多 Agent 辩论网格 (统计学家+数学家+审计) | 🆕 网状拓扑 + 动态路由 | Graph traversal + review mining |
| **D₃ 体** | 🆕 自主知识图谱 + 闭环实验 | 🆕 自愈监控体 + 熵值熔断 | 🆕 世界模型 + Pre-search 仿真 |

## 2. D₂ 面: 多 Agent 网状交叉验证 (fish-ecology)

```
当前 (D₁ 线):
  planner → executor → analyst → writer → reviewer (线性)

进化 (D₂ 面):
                    ┌─────────────┐
                    │  analyst    │ ← 主分析师
                    └──────┬──────┘
                           │ findings
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ statistician│  │ mathematician│ │ code_auditor│
   │ 统计学检验  │  │ 数学严谨性  │  │ 代码审计   │
   └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                    ┌──────▼──────┐
                    │   debate    │ ← 辩论合成
                    │ ≥2/3 agree  │
                    └─────────────┘
```

### 实现: 新增 `debate-validator` Skill

```yaml
debate_validator:
  agents: [statistician, mathematician, code_auditor]
  quorum: 2  # ≥2/3 agree → pass
  checks:
    statistician: "p-value < 0.05, effect size > 0.2, no p-hacking"
    mathematician: "assumptions verified, no division by zero, convergence checked"
    code_auditor: "no unsafe eval, reproducible seed, version pinned"
```

## 3. D₃ 体: 自愈监控体 (porpoise-agent)

```
当前 (D₁ 线 → D₂ 面):
  _should_continue() → phase handlers → _detect_dead_end()

进化 (D₃ 体):
  ┌──────────────────────────────────────┐
  │  Global Entropy Monitor (自愈监控体)  │
  │  - token_consumption_rate            │
  │  - phase_stagnation_timer            │
  │  - memory_pressure                   │
  │  - error_rate                        │
  │                                      │
  │  IF entropy > threshold:             │
  │    → inject_reset_operator()         │
  │    → restructure_task_topology()     │
  │    → log self_healing_event          │
  └──────────────────────────────────────┘
```

### 实现: 新增 `self_healing_monitor` 到 orchestrator

```python
class SelfHealingMonitor:
    def check(self, state: OrchestratorState) -> HealingAction:
        entropy = (
            0.3 * state.token_rate / MAX_TOKEN_RATE +
            0.3 * state.stagnation_time / MAX_STAGNATION +
            0.2 * state.memory_mb / MAX_MEMORY +
            0.2 * state.error_count / MAX_ERRORS
        )
        if entropy > 0.7:
            return HealingAction.RESTRUCTURE
        elif entropy > 0.5:
            return HealingAction.INJECT_RESET
        return HealingAction.NONE
```

## 4. D₃ 体: 世界模型 (cognitive-search-engine)

```
当前 (D₂ 面):
  search → mine → verify → merge

进化 (D₃ 体):
  ┌──────────────────────────────────────┐
  │  Pre-Search World Model (搜索前仿真)  │
  │                                      │
  │  BEFORE executing search:            │
  │    1. estimate_volume(species_id)    │
  │    2. predict_search_depth(mode)     │
  │    3. simulate_token_cost(depth)     │
  │    4. IF cost > benefit → warn       │
  │    5. ELSE → execute                 │
  │                                      │
  │  AFTER search:                       │
  │    6. compare predicted vs actual    │
  │    7. update world_model parameters  │
  └──────────────────────────────────────┘
```

### 实现: `WorldModel` 类

```python
class WorldModel:
    def predict(self, species_id: str, mode: SearchMode) -> SearchPrediction:
        return SearchPrediction(
            estimated_volume=estimate_volume(species_id),
            predicted_depth=select_mode(estimated_volume),
            predicted_tokens=mode.budget * len(mode.active_layers),
            predicted_new_papers=graph_known_count(species_id) * mode.discovery_rate,
        )
    
    def update(self, prediction: SearchPrediction, result: SearchResult):
        error = abs(prediction.papers - result.papers) / max(prediction.papers, 1)
        self.discovery_rate *= (1 + 0.1 * (1 - error))  # adaptive learning
```

---

> **"点动成线，线动成面，面动成体。"**
> D₁(fish 线) → D₂(fish 面+porpoise 面) → D₃(porpoise 体+cognitive 体)
> 三个项目沿三角闭环轨迹运动，从线性流水线进化为三维闭环生态系统。

**Last updated: 2026-06-06**
