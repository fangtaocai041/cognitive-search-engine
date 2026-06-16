# 🧬 三角闭环进化全量图谱

> **道→一→二→三→万物**: 五项目活系统协同进化
> **三角闭环**: fish(V0知识库) + cognitive(V1验证) + eon-core(协调器) — 缺一不可
> **三生万物**: P₁(porpoise) + P₂(coilia) + ...Pₙ — 从三角闭环无限衍生
> **通路**: P1(fish↔cognitive) P2(cognitive→fish) P3(cognitive→P₁/P₂) P4(health→eon-core)

---

## 0. 五项目进化架构 (v7.4)

```
                          ┌─────────────────────────────┐
                          │        eon-core (Coord)      │
                          │    ☯️ OriginKernel · Samsara  │
                          │    道: 10层内核 · 业力轮回    │
                          └────────┬──────┬──────┬───────┘
                                   │P4    │P4    │P4
              ┌────────────────────┼──────┼──────┼──────────────┐
              │                    │      │      │              │
     ┌────────▼────────┐  ┌───────▼──────▼──────▼──────┐       │
     │ fish-ecology    │  │  cognitive-search-engine   │       │
     │ S/V0 (知识供给)  │◄─┤  V/V1 (验证引擎)           │       │
     │ lookup_species  │P1│  search_species            │       │
     │ 28 skills       │──► 15 modules · 5 skills      │       │
     │ 21 MCP          │P2│  7 MCP · BDI+ReAct         │       │
     └────────┬────────┘  └──────────┬─────────────────┘       │
              │                      │P3(派生)                 │
              │         ┌────────────┼────────────┐            │
              │         │            │            │            │
     ┌────────▼─────────▼──┐ ┌──────▼────────────▼──┐        │
     │  porpoise-agent     │ │  coilia-agent         │        │
     │  P₁/V2 (江豚专研)    │ │  P₂/V3 (刀鲚专研)      │        │
     │  矛盾驱动路由        │ │  耳石微化学·洄游生态   │        │
     │  18 skills · 17 MCP │ │  3 skills · 知识库     │        │
     └─────────────────────┘ └───────────────────────┘        │
                                                              │
     ┌────────────────────────────────────────────────────────┘
     │  万物: spawn_agent.py → P₃(中华鲟) P₄ ... Pₙ
     └── 三角派生无限领域专精模板
```

## 1. 各自进化能力

| 能力 | fish (S/V0) | cognitive (V/V1) | porpoise (P₁) | coilia (P₂) | eon-core |
|------|:---:|:---:|:---:|:---:|:---:|
| 组件注册表 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 健康检查 | ✅ | ✅ | ✅ | ✅ | ✅ OriginKernel |
| 自适应参数 | — | ✅ 4参数 | ✅ 5阈值 | — | ✅ CognitiveBudget |
| 自动修复 | ✅ auto-fix | — | ✅ SelfHealing | — | ✅ Samsara重生 |
| 进化日志 | — | ✅ | ✅ audit | — | ✅ karma_records |
| 搜索反馈 | ✅ | ✅ post-search | — | — | — |
| 矛盾检测 | ✅ | ✅ _analyze_ | ✅ primary | — | ✅ Court |
| 通路执行 | P1 P2 | P1 P2 P3 | P3 | P3 | P4 |
| 模板派生 | — | — | ✅(模板源) | ✅(模板源) | — |

## 2. 协同进化路径

### 2.1 三角形内 (P1/P2/P4)

```
P1: fish.lookup → cognitive.search     (知识赋能搜索)
P2: cognitive.search → fish.score       (搜索结果评分反馈)
P4: adapter.health → eon-core.karma     (健康状态→业力评估)

闭环: 搜索越多 → 评分越准 → 业力越高 → token越多 → 搜索越深
```

### 2.2 三角→派生 (P3)

```
cognitive.search → P₁(contradiction_analysis)  (江豚矛盾驱动)
cognitive.search → P₂(species_assessment)      (刀鲚领域评估)
cognitive.search → Pₙ(任意物种)                (模板复制)

派生: 三角形稳定 → 任意物种一键生成 Pₙ Agent
```

### 2.3 交叉进化

```
fish 发现新物种 → 写入 species_graph.yaml → cognitive 可搜索
cognitive 搜索到新论文 → 图谱回写 → 所有项目可见
P₁/P₂ 领域分析 → 反馈矛盾信号 → eon-core karma 调整
eon-core Samsara 评估 → DEVA/NARAKA → token 分配策略调整
```

## 3. 进化指标

| 指标 | 三角形 | P₁/P₂ | 目标 |
|------|:-----:|:-----:|:----:|
| 搜索 recall | 95% | — | ≥98% |
| 通路可执行率 | 4/4 ✅ | 1/1 ✅ | 保持 |
| 独立验证通过率 | 3/3 ✅ | 2/2 ✅ | 保持 |
| 规则覆盖率 | 18/18 ✅ | — | 保持 |
| 业力 DEVA 率 | — | — | ≥70% |
| Pₙ 派生能力 | — | 1命令13文件 | 保持 |
| 图谱物种数 | 7 | — | 持续增长 |
| Token 效率 | ~2000/search | — | ≤1500 |

## 4. 演化周期

```
持续: eon-core Samsara 每60s评估业力 → DEVA/NARAKA 升降
每日: verify_standalone + verify_pathways --live → 通路完整性
每周: verify_philosophy_rules → 18规则覆盖检查
每月: demo_evolution → 道→一→二→三→万物 全链路
随需: spawn_agent.py → 新物种 Pₙ Agent 一键派生
```

---

> **道生一·一生二·二生三·三生万物**
> 三角形是稳定的内核。万物是无限的派生。
> 每个组件可独立验证。每条通路可端到端执行。
> 五项目通过 eon-core 的 Samsara 业力循环自我调节。

**Last updated: 2026-06-09**
**Verification: verify_standalone.py 5/5 · verify_pathways.py 16/16 · verify_philosophy_rules.py 18/18**
