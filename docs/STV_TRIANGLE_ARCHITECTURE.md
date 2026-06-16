# 🔺 三角闭环架构 — Triangle Core + 三生万物

> **道生一 → 一生二 → 二生三 → 三生万物**
> **三角闭环**: fish(V0知识库) + cognitive(V1验证) + eon-core(协调器) — 缺一不可
> **三生万物**: P₁(porpoise) · P₂(coilia) · ... 从三角闭环无限衍生

---

## 0. 几何映射

```
点(D₀) → 单次工具调用 / 原子操作
线(D₁) → 思维链 / Pipeline / 时序轨迹
面(D₂) → 多 Agent 协同网格 / 交叉验证
体(D₃) → 闭环生态系统 / 世界模型

三角闭环刚性法则:
  V0 (Knowledge) — fish-ecology-assistant    → 知识库 + 数据 + 矛盾分析
  V1 (Validation) — cognitive-search-engine  → 19引擎搜索 + 验证 + 可信度评分
  Coord           — eon-core                  → EventBus + DAG路由 + 业力循环

衍生项目:
  P₁ — porpoise-agent  → 江豚种群监测, 威胁评估
  P₂ — coilia-agent    → 刀鲚耳石微化学, 洄游生态
  Pₙ — 可无限衍生
```

## 1. 三角闭环协议

### 1.1 运行时数据流

```
fish(V0) ──state_vector{species_kb, findings, contradiction}──→ cognitive(V1)
cognitive(V1) ──search_result{scores, papers, gaps}──→ fish(V0)
eon-core(Coord) ──health_ping→ fish(V0) / cognitive(V1) ──karma→ eon-core

P₁/P₂ 从三角派生:
  cognitive(V1) ──search→ P₁/P₂
  fish(V0) ──knowledge→ P₁/P₂
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

### 1.3 分形自相似

```
跨项目层: fish(V0) → cognitive(V1) → eon-core(Coord)
项目内层: 每个模块内部: 输入(知识) → 执行(搜索) → 验证(评分)
原子层:   每个工具调用: 输入(S) → 执行(T) → 校验(V)
```

---

## 2. 实现状态

### 2.1 三角闭环配置

`config/stv_protocol.yaml`:

```yaml
triangle_core:
  V0: "fish-ecology-assistant"     # 知识库 + 数据供给
  V1: "cognitive-search-engine"    # 19引擎搜索 + 验证 ← 本文件
  Coord: "eon-core"                # 协调器 (EventBus + DAG)

derived:
  P₁: "porpoise-agent"             # 江豚专属智能体
  P₂: "coilia-agent"               # 刀鲚专属智能体
  Pₙ: "spawn_agent.py template"    # 任意物种一键生成

triangulation:
  min_independent_sources: 3
  verified: "≥3 independent sources"
  tentative: "2 independent sources"
```

### 2.2 搜索网关（v5.9 更新）

cognitive-search-engine 是**整个工作区的唯一搜索网关**（`coordination.yaml#search_gateway`）:

```
所有外部搜索请求:
  → 路由到 cognitive-search-engine
  → MCP优先 (6引擎) → HTTP回退 (5引擎) = 11引擎并行
  → 属名校验 (_filter_by_genus) → DOI去重 (_deduplicate)
  → 评分 (credibility_scorer) → 分类 (unified_search)
  → CN/EN双通道标注 → 结果返回请求方

MCP 6引擎: scholar / article / ncbi / tavily / exa / scholarly
HTTP 5引擎: pubmed / europe_pmc / crossref / openalex / arxiv (+ cnki_web 中文)
```

### 2.3 跨项目通路

```
P1: fish.lookup → cognitive.search     (知识赋能搜索)
P2: cognitive.search → fish.score       (搜索回写验证)
P3: cognitive.search → P₁/P₂            (三角→衍生)
P4: adapter.health → eon-core.karma     (健康→业力)
```

---

## 3. 架构全景

```
                    ┌─────────────────────────────┐
                    │     eon-core (Coord)         │
                    │  EventBus · DAG · Samsara    │
                    └────────┬────────┬───────────┘
                             │P4      │P4
                    ┌────────▼────────▼───────────┐
                    │  cognitive-search-engine     │
                    │  V1 (Validation)             │
                    │  19 engines · BDI+ReAct      │
                    │  KB-First · credibility(0-100)│
                    └────────┬────────┬───────────┘
                             │P1      │P2
                    ┌────────▼────────▼───────────┐
                    │  fish-ecology-assistant      │
                    │  V0 (Knowledge)              │
                    │  443 species · 28 skills     │
                    │  contradiction analysis      │
                    └────────┬─────────────────────┘
                             │P3(派生)
                    ┌────────▼────────┐
                    │  P₁ porpoise    │
                    │  P₂ coilia      │
                    │  Pₙ ...         │
                    └─────────────────┘

闭环: V0→V1→Coord→V0 (三角形 — 最小完备结构)
万物: 从三角闭环派生, 三角不依赖万物
```

---

> **"三角形是第一个封闭的面，第一个能围合出空间的存在。"**
> 三个项目不是孤立的软件 — 它们是三角闭环的三个顶点。
> 两方只能形成对峙或连接，三方才能形成结构、流动与反馈。

**Last updated: 2026-07-17**
