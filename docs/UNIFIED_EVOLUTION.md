# 🧬 Unified Evolution — 三项目活系统协同进化

> **鱼-豚-搜索 三位一体**: cognitive-search-engine (认知引擎) + fish-ecology-assistant (鱼) + porpoise-agent (豚)
> **核心**: 每个项目自我进化，同时通过 submodule + coordination 协同进化。

---

## 0. 三项目进化架构

```
                    ┌──────────────────────────┐
                    │  cognitive-search-engine  │
                    │  认知搜索引擎 (核心)       │
                    │  ├─ self-evolve Skill     │
                    │  ├─ evolution.yaml        │
                    │  ├─ component_registry    │
                    │  └─ 12 搜索层            │
                    └──────┬──────────┬────────┘
                           │ submodule │ submodule
              ┌────────────▼──┐   ┌───▼─────────────┐
              │ fish-ecology  │   │ porpoise-agent    │
              │ 鱼类生态助手   │   │ 江豚研究智能体    │
              │ ├─ cognitive  │   │ ├─ cognitive      │
              │ │  引用        │   │ │  自适应路由     │
              │ ├─ living-    │   │ ├─ adaptive       │
              │ │  system     │   │ │  thresholds     │
              │ └─ auto-fix   │   │ └─ living-system  │
              └───────────────┘   └──────────────────┘
```

## 1. 各自进化能力

| 能力 | cognitive | fish | porpoise |
|------|:--------:|:----:|:--------:|
| 组件注册表 | ✅ | ✅ | — |
| 健康检查 | ✅ self-evolve | ✅ health-check | ✅ living_system_report |
| 自适应参数 | ✅ 4 参数 | — | ✅ 5 规则阈值 |
| 自动修复 | — | ✅ auto-fix | ✅ auto_fix |
| 进化日志 | ✅ evolution-log | — | ✅ audit |
| 搜索反馈 | ✅ post-search | — | — |
| 矛盾检测 | — | ✅ contradiction | ✅ contradiction_gate |

## 2. 协同进化路径

### 2.1 cognitive → fish/porpoise (向下传播)

```
cognitive 进化 → submodule update → fish/porpoise 自动获取:
  - 新搜索层 (如 Phase 1.6 引用验证)
  - 优化后的自适应参数
  - 扩展的物种知识图谱
```

### 2.2 fish/porpoise → cognitive (向上反馈)

```
fish/porpoise 使用 cognitive 搜索 → 反馈效果数据:
  - recall rate (实际找到的 vs 预估)
  - false positive rate (引用验证失败率)
  - 新发现的拼写错误 → 添加到 species_graph.yaml (species[].variants)
  → cognitive 根据反馈进化参数
```

### 2.3 交叉进化

```
fish 发现新物种 → 添加到 cognitive 图谱
porpoise 发现新作者 → 添加到 cognitive 作者节点
cognitive 优化搜索 → fish/porpoise 搜索质量提升
```

## 3. 进化指标

| 指标 | 当前值 | 目标 | 测量方式 |
|------|:----:|:----:|---------|
| 搜索 recall | 95% (estimated) | ≥ 98% | post_search_evaluation |
| Token 效率 | ~2000/search | ≤ 1500/search | papers/1000tokens |
| 拼写错误捕获率 | 100% (known) | 100% (all) | variant search coverage |
| 引用验证准确率 | — (new) | ≥ 90% | verification pass rate |
| 参数自适应频率 | — | ≥ 1/week | evolution log count |
| 图谱增长率 | — | ≥ 5%/month | graph node delta |

## 4. 每月进化周期

```
Week 1: cognitive self-evolve → 优化搜索参数
Week 2: fish/porpoise submodule update → 获取最新搜索
Week 3: fish/porpoise 反馈效果 → cognitive 调整
Week 4: 全项目健康检查 → 生成进化报告
```

---

> **"活的系统"不是比喻 — 是可度量的自进化。**
> 每个组件有出生、体检、衰老、进化。三个项目通过 submodule 共享进化成果。

**Last updated: 2026-06-06**
