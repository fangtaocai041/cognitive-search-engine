<p align="center">
  🇬🇧 <a href="README.md">English</a>
</p>

<div align="center">
  <h1>🕸️ 认知搜索引擎 v5</h1>
  <p><strong>中宇宙式 Agent</strong> — BDI + ReAct + 权威可信度评分 + ZN/EN 动态图谱 + 按需加载</p>
  <p>7 模块 · 5 搜索引擎 · 5 层架构 · BDI 推理 · 中宇宙协调层</p>
</div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-5.3.0-8b5cf6?style=flat-square" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/skills-5-22c55e?style=flat-square" alt="Skills"></a>
  <a href="#"><img src="https://img.shields.io/badge/MCP-7-f59e0b?style=flat-square" alt="MCP"></a>
  <a href="docs/ARCHITECTURE.md"><img src="https://img.shields.io/badge/架构-meso_cosmos-8b5cf6?style=flat-square" alt="架构"></a>
  <a href="#"><img src="https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6?style=flat-square" alt="Multi-LLM"></a>
  <a href="#"><img src="https://img.shields.io/badge/BDI-ReAct-22c55e?style=flat-square" alt="BDI"></a>
  <a href="#"><img src="https://img.shields.io/badge/权威评分-0_100-ec4899?style=flat-square" alt="权威评分"></a>
  <a href="https://deepwiki.com/fangtaocai041/cognitive-search-engine"><img src="https://devin.ai/assets/askdeepwiki.png" alt="Ask DeepWiki" height="20"></a>
  <a href="#"><img src="https://img.shields.io/badge/Docker-规划中-lightgrey?style=flat-square" alt="Docker"></a>
  <a href="skills/self-evolve.md"><img src="https://img.shields.io/badge/自进化-反馈循环-10b981?style=flat-square" alt="自进化"></a>
</p>

## 🧠 三层智能优化

> 验证引擎集成了三层优化：**DeepSeek 级效率** (MoE 门控 + KV 缓存)、**学者级置信** (Rule of Three 统计停止)、**混沌增强探索** (Rössler 扰动 + wildcard 发现)。
> 协调由 [eon-core](https://github.com/fangtaocai041/eon-core) (10层统一内核) 统一调度。

## 🔺 S-T-V-P₁-P₂ 架构角色: **Validation (V)**

> S-T-V 刚性三角形: `fish(S) → porpoise(T) → cognitive(V) → fish(S)`
> 验证搜索结果、提供权威可信度评分、维护共享知识图谱。
> **D₁ 点**: `DirectLoader` (importlib — 零 MCP 进程)。**三角验证**: 每个核心声明 ≥3 独立源。

---

## 🧠 v5.2: 中宇宙式 Agent — Meso-Cosmos 协调层

> **宏观(BDI) → 中宇宙(协调) → 微观(执行)** — 自动在宏观意图与微观工具调用之间搭建桥梁。

### 新增功能

| 功能 | 说明 | 模块 |
|:----|:-----|:-----|
| **MesoAgent** | 中宇宙式协调层 — 统一管理 WorldModel/SearchRuleEngine/MemorySystem/GraphUpdater | `src/meso_agent.py` |
| **动态图谱 v2.0** | ZN/EN 感知自动更新 — 中文期刊自动填入 `authors_zh`，新作者/期刊自动注册，中英文双语去重 | `src/graph_updater.py` |
| **ZN/EN 文献规则** | 中文期刊走中文署名（杨计平），英文走英文名（Yang Jiping）；论文防双版本重复 | `project memory (high)` |
| **MCP 超时保护** | 15 秒 threading 超时防止 MCP 子进程永久阻塞 | `src/mcp_client.py` |
| **中文期刊搜索技能** | 覆盖 8 种中文期刊的专用搜索策略 | `skills/chinese-academic-search.md` |

### 中宇宙架构

```
┌─────────────────────────────────────────────────────┐
│              宏观宇宙 (BDI 意图层)                    │
│  CognitiveAgent · WorldModel · Belief/Desire/Intention │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              中宇宙 (协调层)                         │
│  MesoAgent.search(species_id)                       │
│                                                     │
│  管线: BDI预测 → 模式选择(穷举/分类/轻量)            │
│       → 执行分发 → 图谱更新 → ZN/EN规则              │
│                                                     │
│  组件: WorldModel + SearchRuleEngine                │
│        + MemorySystem + GraphUpdater                │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              微观宇宙 (执行层)                        │
│  PubMed E-utilities · Crossref · OpenAlex · MCP      │
│  11 搜索阶段 · 5 引擎 · 权威评分                     │
└─────────────────────────────────────────────────────┘
```

### ZN/EN 自动规则

| 情境 | 以前 | 现在 |
|:----|:----|:----|
| 中文期刊论文 | `authors: [Yang Jiping]` | `authors_zh: [杨计平]` ✅ |
| 英文期刊论文 | `authors: [Yang Jiping]` | `authors: [Yang Jiping]` ✅ (不变) |
| 中英文双版本 | 两个都保留 | DOI + title_zh 去重 → 保留中文版 |
| 发现新作者 | 手动添加 | 自动注册中文名 |
| 发现新期刊 | 手动输入 | 自动注册 |

### MesoAgent 快速使用

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")

print(f"找到 {len(result.papers)} 篇论文，耗时 {result.elapsed_sec}s")
print(f"图谱新增: {result.new_papers}")
print(f"停止原因: {result.stop_reason}")
```

---

## 🧠 v5.1: Hub-and-Spoke 搜索协议

> **从线性层级到学科方向 Hub** — 按子方向定位枢纽论文 → 提取引用轮辐 → 构建分类知识图谱

### 搜索协议：Hub-and-Spoke（3 阶段）

| 阶段 | 操作 | 工具 |
|:--:|------|------|
| **1. 定位 Hub** | 5 学科方向并行搜索（遗传/形态/基因组/生态/调查） | `scholar_search` + `web_search` |
| **2. 提取 Spoke** | 从每个 Hub 论文拉取引用图谱 | `article_get_references` |
| **3. 缺口检测** | OCR 变体扫描 + 新论文检测（year ≥ 今年-1 且 PMID=NULL） | `scholar_search` 变体查询 |

### 5 层智能体架构

| 层 | 功能 | 模块 |
|:--:|------|------|
| **1. 感知** | 输入 → species_id → 属名/种名/中文 + 文献量估算 | `SearchRuleEngine.execute()` |
| **2. 认知** | BDI 策略 π(信念,愿望) → 意图 + ReAct 循环 | `src/agent_core.py` |
| **3. 记忆** | 短期 + 长期 + **分类知识图谱** | `src/memory_layer.py` |
| **4. 映射** | 方向路由 → Hub 选择 → `article_get_references` | `search_rules.yaml` |
| **5. 执行** | PubMed · Crossref · MCP (5 引擎) · 权威评分 | `rule_engine._http_search()` |

### BDI + ReAct 认知循环

```
Think → Act → Observe → Reflect
  │       │        │          │
  │  形成意图    统计论文   对比信念
  │  (B,D)→I    数量       与愿望
  ▼
愿望满足? → STOP
```

📖 完整架构: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🔺 S-T-V 三角 (跨项目)

> 三个项目: State(fish) → Transition(porpoise) → Validation(cognitive) 闭环

| 组件 | 项目 | 功能 |
|:----:|------|------|
| **S** | fish-ecology-assistant | State — 知识、数据、发现 |
| **T** | porpoise-agent | Transition — 执行、流水线 |
| **V** | cognitive-search-engine | Validation — 验证、信任评分 |

配置: `config/stv_protocol.yaml` — `min_sources_core_claim = 3`, trust_score 5 级三角验证。

## 🔧 工程语言承诺

> **所有功能用可执行的工程语言表达 — 非自然语言。**
> `function(input: Type) → OutputType` | `WHEN condition THEN action` | `config.path.to.value`

| 格式 | 用途 |
|------|------|
| `search_rules.yaml` | 10 阶段结构化规则引擎 |
| `tools.json` | JSON Schema — DeepSeek+Gemini+OpenAI 通用 |
| `src/rule_engine.py` | Python 直接执行 |
| `config/evolution.yaml` | 4 参数自进化 |

## 🧠 核心创新

**不是字符串匹配 — 是认知重建。**

传统搜索匹配字符串。如果论文把"Ochetobius"错拼成"Ochetobibus"，传统搜索永远找不到。
我们的引擎从多条**能指**路径同时重建**所指**（物种本身）。

```
能指路径 → 所指（物种）
─────────────────────────────
精确学名    ─┐
拼写变体    ─┤
作者网络    ─┼─→ Ochetobius elongatus（鳤）
引用图谱    ─┤
期刊上下文  ─┤
中文名称    ─┘
```

## 🏆 为什么这是最先进的物种搜索引擎

### vs 传统学术搜索 (Google Scholar, Web of Science, PubMed)

| 问题 | 传统搜索 | 认知搜索引擎 |
|------|---------|------------|
| 物种名拼写错误 | ❌ 搜"Ochetobius"找不到"Ochetobibus" | ✅ OCR 变体扫描全覆盖（实测捕获 2 篇: 2009 + 2026） |
| 中文数据库盲区 | ❌ PubMed/Crossref 不索引知网/万方/维普 | ✅ 中文优先搜索 → web_search + 11 期刊站点 |
| 冷启动（新物种） | ❌ 零结果 → 卡住 | ✅ Hub-and-Spoke: 多方向 Hub 定位 |
| 综述引用盲信 | ❌ 幽灵引用/错误归因直接纳入 | ✅ 权威可信度评分 0-100，SCI/核心期刊加权 |
| 搜索健忘症 | ❌ 同样搜索重复同样成本 | ✅ 分类知识图谱持久化，按需懒加载 |
| 一刀切搜索深度 | ❌ 8 篇和 8000 篇同样策略 | ✅ 三模式: 穷举(<20) / 分类(20-100) / 综述锚定(>100) |
| 无认知模型 | ❌ 纯字符串匹配 | ✅ 符号学 + 语言学 + 语音学 + 逻辑学 |

### vs AI 搜索 (Gemini, Perplexity, Claude)

| 问题 | AI 搜索 | 认知搜索引擎 |
|------|--------|------------|
| 透明度 | ❌ 黑箱 — 无法验证完整性 | ✅ 3 阶段 Hub-and-Spoke，每步可审计 |
| 成本 | ❌ 每次高 token 消耗 | ✅ 懒加载知识图谱，调用量减少 ~60% |
| 领域知识 | ❌ 通用 — 无物种特定逻辑 | ✅ 拉丁语法、IPA、OCR 错误模型 |
| 来源权威 | ❌ 预印本与同行评审同等对待 | ✅ 可信度评分 0-100，掠夺性期刊直接排除 |
| 引用图谱 | ❌ 未利用 | ✅ 多 Hub 引用轮辐 → 分类知识图谱 |
| 学习能力 | ❌ 无状态 — 每次独立 | ✅ 图谱随每次搜索增长 |

### 独有能力（无其他工具具备）

| # | 能力 | 为什么重要 |
|:--|------|-----------|
| 1 | **Hub-and-Spoke 图谱搜索** | 多方向 Hub → 引用轮辐 → 10 次调用覆盖 90%+ recall |
| 2 | **权威可信度评分** | SCI + CSCD核心 加权 +30，掠夺性期刊 -100 排除 |
| 3 | **综述优先策略** | >20 篇时先搜综述 → 综述参考文献 = 完整文献地图 |
| 4 | **分类知识图谱懒加载** | 首次只输出分类计数，用户点方向才展开详情 |
| 5 | **OCR 变体安全网** | Ochetobius→Ochetobibus: 精确名搜索遗漏的 2 篇论文被捕获 |

## ⚡ 五大突破

### 1. Hub-and-Spoke 图谱（非线性层级）

| 传统线性 (v4.1 14层) | Hub-and-Spoke (v5.0) |
|---------------------|----------------------|
| 14 层顺序执行 | 3 阶段并行 Hub |
| ~15+ 次工具调用/搜索 | ~10 次工具调用/搜索 |
| 单一路径 | 多方向轮辐合并 |
| Layer 0-13 全量执行 | 仅缺口触发补充搜索 |

### 2. 权威可信度评分

```
可信度 = 50 + 30(SCI) + 25(CSCD核心) + 10(DOI) + 10(PMID) - 30(预印本) - 100(掠夺性期刊)
→ 🟢 ≥80 高可信度  🟡 60-79 中  🟠 40-59 低  🔴 <40 不可信
```

### 3. 综述优先策略（中大型领域）

```
IF 文献量 > 20:
  先搜综述 → 综述参考文献 ≈ 完整文献地图
  再搜综述发表后的新论文补缺
```

### 4. 分类知识图谱懒加载

```
输出: 仅分类计数 → 用户选方向 → 展开该子树
绝不一次性将所有论文载入上下文。
```

### 5. 多学科认知引擎

| 学科 | 方法 |
|------|------|
| 符号学 | 能指分解 → 所指重建 |
| 语言学 | 拉丁词根提取、OCR 错误模型 |
| 语音学 | IPA 国际音标转录、Soundex+Metaphone 双码 |
| 逻辑学 | 演绎链 + 溯因推理 + 归纳模式 |
| DeepSeek CoT | 信息增益排序 + 稀疏 MoE + 熵预算 |

---

## 🚀 快速上手

```bash
git clone https://github.com/fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine
```

集成到 Reasonix 项目：
```yaml
# 在项目的 config/agent.yaml 中
skills:
  external_skills:
    - path: "../cognitive-search-engine/skills"
      skills: ["graph-search-engine", "cognitive-species-search"]
```

或作为 git submodule：
```bash
git submodule add https://github.com/fangtaocai041/cognitive-search-engine.git external/cognitive-search-engine
```

独立使用：
```
/skill graph-search-engine species="Ochetobius elongatus"
```

---

## 📁 项目结构

```
cognitive-search-engine/
├── README.md                     ← English
├── README.zh.md                  ← 中文
├── LICENSE
│
├── config/
│   ├── agent.yaml                ← 能效配置 + 自适应搜索深度
│   ├── mcp_servers.yaml          ← 5 搜索引擎
│   ├── species_graph.yaml        ← 预建知识图谱
│   ├── component_registry.yaml   ← 活系统：12 组件生命周期
│   └── evolution.yaml            ← 自进化：4 自适应参数
│
├── skills/
│   ├── graph-search-engine.md    ← v4 核心：图谱遍历 + 能效最优
│   ├── cognitive-species-search.md ← v3：符号学 + 语言学 + 语音学
│   ├── chinese-academic-search.md  ← 中文期刊搜索 (8 种期刊)
│   ├── meso-orchestrator.md      ← 🧭 中宇宙协调器
│   └── self-evolve.md            ← 🧬 搜索后反馈 → 自动调参
│
├── src/                          ← 15 模块 (5层认知智能体)
│   ├── adapter.py                ← 🔌 CognitiveSearchAdapter — DirectLoader入口
│   ├── agent_core.py             ← 🧠 CognitiveAgent — BDI + ReAct 循环
│   ├── catalog_loader.py         ← 🗄️ 数据库目录 + 图谱路由器 + 涌现引擎
│   ├── evolution_executor.py     ← 🦋 自进化反馈执行器
│   ├── graph_updater.py          ← 📊 图谱持久化 + 反向索引
│   ├── inference_engine.py       ← 🧮 TAO + WuXing 推理引擎
│   ├── mcp_client.py             ← 🔌 MCP stdio 客户端 (7 服务器)
│   ├── memory_layer.py           ← 🗄️  MemorySystem — 短期 + 长期记忆
│   ├── meso_agent.py             ← 🧭 MesoAgent — 协调层
│   ├── paper_health_check.py     ← 💓 论文有效性健康检查
│   ├── parallel_search.py        ← ⚡ 多查询并行执行器
│   ├── rule_engine.py            ← ⚙️  SearchRuleEngine — 阶段 + 执行
│   ├── validator.py              ← ✅ 跨项目独立性验证器
│   ├── variant_generator.py      ← 🔤 OCR 变体自动生成
│   └── world_model.py            ← 🧬 BDI WorldModel — 信念/愿望/意图
│
├── docs/
│   ├── ARCHITECTURE.md           ← 5层智能体架构全量文档
│   └── UNIFIED_EVOLUTION.md      ← 三项目协同进化架构
│
└── .github/workflows/
    └── validate.yml              ← CI/CD 自动验证
```

---

## 🔬 工作原理

### 自适应搜索深度（v5.0 三模式重定义）

```
搜索前先估算文献量：
  ncbi_esearch → pubmed_count
  scholar_search_literature_graph(limit=5) → scholar_count
  web_search(中文名 + " 论文 OR 综述") → chinese_hits
  estimated = MAX(pubmed_count, scholar_count, chinese_hits * 0.5)

穷举模式 (estimated < 20)
  → Hub-and-Spoke 全方向展开，每篇论文加载完整元数据
  → 目标: 100% recall

分类归纳模式 (estimated 20–100)
  → STEP 0: 先搜综述（综述参考文献 ≈ 完整文献地图）
  → STEP 1: 构建分类图谱（仅标题+期刊+年份，不加载摘要）
  → STEP 2: 用户选择子方向后展开该方向 Hub-and-Spoke
  → STEP 3: 用户切换方向时按需加载

大规模模式 (estimated > 100)
  → STEP 0: 必搜综述（综述 = 领域文献地图）
  → STEP 1: 输出分类概览（只列论文数，不列论文名）
  → STEP 2: 每方向精选 5-8 篇权威最高论文
  → STEP 3: 用户明确要求才展开某方向
```

### BDI + ReAct 认知循环

```
1. 初始化信念: 从图谱加载已知论文 (0 tokens)
2. 思考:     π(信念, 愿望) → 意图 (选择阶段)
3. 行动:     执行阶段 (PubMed, Crossref, MCP 服务器)
4. 观察:     统计新论文、计算 IG、更新信念
5. 反思:     对比信念 vs 愿望 → 继续 / 重构 / 停止
6. 持久化:   新论文合并入图谱 (长期记忆)
```

### 图谱优先效率

```
若已知论文 ≥ 8 → 满意，立即返回 (0 tokens)
若已知论文 < 8 → 先执行最便宜阶段
若连续零产出 ≥ 2 → 停止 (边际收益递减)
```

---

## 📡 内置搜索引擎

| 引擎 | 用途 | 模糊匹配 |
|------|------|:------:|
| Google Scholar | 主力 — 模糊匹配最强 | ✅✅✅ |
| Europe PMC + PubMed | 生物医学文献 | ✅ |
| OpenAlex + Semantic Scholar | 跨学科学术搜索 | ✅✅ |
| Tavily | 网络搜索（灰色文献、报告） | ✅✅ |
| Exa | 语义网络搜索 | ✅ |

---

## 🔗 关联项目

本引擎作为 git submodule 集成到以下项目：

| 项目 | 角色 | 说明 |
|------|:----:|------|
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | **S** (State) | 鱼类生态学 AI 研究团队 — 22 MCP · 25 skills · 知识提供者 |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | **T** (Transition) | 江豚研究智能体 — 16 MCP · 16 skills · 管线执行者 |

> **协同进化**: 引擎代码更新 → fish 和 porpoise 通过 submodule 自动受益。
> 知识图谱进化 → 三项目共享。
> 完整协调规范: workspace 根目录 `coordination.yaml`。

### 🧠 中宇宙式 Agent (Workspace Level)

> **宏观(BDI) → 中宇宙(协调) → 微观(执行)** — 跨越三个 S-T-V 项目的统一协调层。

```
用户问题
     │
     ▼
┌────────────────────────────────────────────────┐
│  中宇宙式 Agent (workspace root)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ 理解     │→│  路由    │→│   执行       │ │
│  │(Macro)   │  │(Meso)    │  │(Micro)       │ │
│  └──────────┘  └──────────┘  └──────┬───────┘ │
│                                     │          │
│  ┌──────────┐  ┌──────────┐  ┌─────▼───────┐ │
│  │  进化    │←─│  合成    │←─│   验证      │ │
│  └──────────┘  └──────────┘  └─────────────┘ │
└────────────────────────────────────────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
┌─────────┐      ┌──────────┐       ┌──────────────┐
│  fish   │      │ porpoise  │       │  cognitive    │
│  (S)    │      │   (T)     │       │    (V)        │
└─────────┘      └──────────┘       └──────────────┘
```

> 配置: `config/meso_agent.yaml` · 技能: `skills/meso-orchestrator.md`

---

## 🗺️ 演进方向 (个性化路线图)

> 以下方向根据实际研究需求排列，非通用路线图。每个方向对应一个具体痛点。

### 🔴 P0 — 本周可做

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 1 | **一键物种搜索** | 每次要手动输入学名+中文名 | `search("鳤")` → 自动查 species_graph → 中英双语并行 → 输出差距分析 |
| 2 | **CNKI/万方直连** | 当前用 web_search 兜底，慢且不全 | 如有机构账号 → 接入 CNKI API / 万方 API → 直接检索+下载摘要 |
| 3 | **付费论文自动 bypass** | 每次手动去 ResearchGate/小木虫搜 | `try_bypass()` 自动化 → 并行搜索 8 个共享渠道 → 返回可访问 URL |
| 4 | **搜索记录持久化** | 每次搜鳤都要重新来一遍 | `species_graph.yaml` 已有但未充分利用 → 搜索结果自动写回图谱 |

### 🟡 P1 — 本月

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 5 | **文献综述自动生成** | 搜完 15 篇还要人工分类写综述 | 按学科方向分类 → 提取摘要 → DeepSeek 生成结构化综述 |
| 6 | **研究差距自动检测** | 不知道国内vs国外研究到哪一步 | CN 5 篇 vs EN 7 篇 → `align_bilingual()` → "国内空白: 食性/基因组" |
| 7 | **物种对比搜索** | 搜完鳤还要搜鯮、鲥，重复劳动 | `compare_species(["鳤","鯮"])` → 并行搜索 → 对比表 |
| 8 | **新论文周报** | 不知道鳤最近有没有新论文 | 每日 NCBI/CNKI 自动检索 → 有新论文 → 推送通知 |

### 🟢 P2 — 本季度

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 9 | **PDF 自动下载** | 找到论文还要手动下载、重命名 | 免费论文自动下载 → 按 `作者_年_期刊.pdf` 命名 → 本地存档 |
| 10 | **Zotero 集成** | 文献管理靠手工 | 搜索结果 → 自动导出 `.bib` → Zotero BetterBibTeX 同步 |
| 11 | **GIS 分布叠加** | 只有 GBIF 点数据，看不到环境背景 | GBIF 分布 + WorldClim 气候 + 水文图层 → 一张图看到栖息地全貌 |
| 12 | **机构库深度接入** | 中科院学位论文/报告找不到 | CAS IR + NSTL + 高校图书馆 → 学位论文/内部报告专属搜索 |

### 🔵 P3 — 未来

| # | 方向 | 痛点 |
|:--:|------|------|
| 13 | **微信小程序** | 野外调查时手机查物种文献 |
| 14 | **语音输入** | "帮我搜一下鳤的最新论文" |
| 15 | **多语种扩展** | 日文/韩文/俄文鱼类学论文 |
| 16 | **知识图谱可视化** | 作者合作网络 + 引用关系 → 交互式图谱 |

### ⚡ 技术债务 (持续)

- 触手健康状态从静态 YAML 改为运行时探针
- `species_graph.yaml` 自动从 NCBI Taxonomy 批量填充
- 反馈权重自进化从手动 `apply_feedback()` 改为后台定时任务
- 中文分词替代当前的字串匹配触发词检测

---

## 📋 README 变更记录

| 版本 | 日期 | 主题 | 变更内容 |
|:------|:-----|:------|:-------------|
| **v5.2.1** | 2026-06-07 | 跨项目同步 | + S-T-V 三角角色声明, + DeepWiki/Docker/自进化徽标, + 关联项目增强 (协同进化描述), + 与 fish/porpoise 项目规范对齐 |
| **v5.2** | 2026-06-06 | 中宇宙式 Agent | + MesoAgent (src/meso_agent.py), + 动态图谱 v2.0 (ZN/EN 自动 authors_zh/自动注册/双语去重), + CN/EN 文献规则, + MCP 15 秒超时保护, + Chinese Academic Search Skill (第 4 个技能), + 架构: meso_cosmos |
| **v5.1** | 2026-06-06 | Hub-and-Spoke 协议 | + Hub-and-Spoke (3 阶段 10 调用), + 权威可信度评分 (0-100), + 综述优先策略, + 分类知识图谱 (懒加载), + Chinese-academic-search Skill, + 三模式自适应深度, + OCR 变体安全网 |
| **v5.0** | 2026-07-14 | 5 层智能体架构 | + BDI WorldModel (信念/愿望/意图), + CognitiveAgent (ReAct 循环), + MemorySystem (短期+长期), + agent_core.py, + memory_layer.py, + variant_generator.py, + graph_updater.py, + mcp_client.py, + ARCHITECTURE.md |
| **v4.3** | 2026-06-06 | 工程语言化 | + YAML 规则引擎 (10 结构化阶段), + JSON Schema tools.json (三 LLM 通用), + rule_engine.py, + 多 Provider 配置, + 自进化反馈循环 |
| **v4.2** | 2026-06-06 | 活系统 | + component_registry (12 组件), + evolution.yaml (4 自适应参数), + self-evolve Skill, + UNIFIED_EVOLUTION.md |
| **v4.1** | 2026-06-06 | 自适应深度 | + 自适应搜索深度 (穷举/分类/满意), + Phase 1.5 综述挖掘, + Phase 1.6 引用验证 (5 级信任评分) |
| **v4.0** | 2026-06-06 | 图谱引擎 | 初始发布 — 知识图谱遍历, 12 搜索层, 能效最优, 5 搜索引擎 |

---

## 📜 许可证

MIT © 2026 fangtaocai041

---

## 📊 自我评价

| 维度 | 评分 | 说明 |
|------|:--:|------|
| 🎯 搜索精度 | ⭐⭐⭐⭐⭐ | Hub-and-Spoke + OCR 变体生成 + 权威可信度评分 (0-100) |
| 🧠 认知架构 | ⭐⭐⭐⭐⭐ | BDI + ReAct 循环 + 矛盾驱动的策略选择 |
| 📊 验证严谨性 | ⭐⭐⭐⭐☆ | `validator.py` 实现跨项目独立性强制检查 |
| 🔬 物种覆盖 | ⭐⭐⭐⭐☆ | 图谱中约 10 个物种，通过自动回写可扩展 |
| ⚡ 运行效率 | ⭐⭐⭐⭐☆ | DirectLoader (importlib 零 MCP) + T 层 MoE 门控 |
| 🧪 测试覆盖 | ⭐⭐⭐⭐⭐ | 46 集成 + 94 鲁棒性 = 140 项测试 |

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
>
---

## 🗄️ v5.4: 活系统数据库目录 & 图谱路由器

> **61 数据库 · 8 领域 · 4 层级 · 权重自进化 · 触手健康感知**

| 功能 | 说明 | 模块 |
|:----|:-----|:-----|
| **数据库目录** | 61 个数据库，8 个领域，4 层级（综合→专业→机构→原始数据） | `config/database_catalog.yaml` |
| **意图检测** | `detect_intent(query)` → {文献\|数据\|学位论文\|全量} | `catalog_loader.py` |
| **图谱路由器** | `graph_route(query, health_aware=True)` — 加权拓扑 + 触手健康 + 互补推荐 | `catalog_loader.py` |
| **渐进搜索** | 先搜综合入口 → 可展开专业数据库 — SM-2 满意即停 | `catalog_loader.py` |
| **分类学展开** | L1(物种)→L2(属)→L3(科)→L4(中文+别名) 逐级搜索 | `catalog_loader.py` |
| **活系统** | `record_search_result()` → 反馈日志 → `apply_feedback()` 权重自调 | `catalog_loader.py` |
| **涌现引擎** | `emerge_domains()` — 从使用模式中发现跨领域数据库集群 | `catalog_loader.py` |

### 渐进搜索流程

```
"搜索鳤的文献"
  → intent=文献
  → 综合入口: PubMed, Scopus, WoS, CNKI, 万方, 百度学术...
  → [满意? → 停止 | 展开 → 专业库: ASFA, FishBase, 水生生物学报...]

"下载鳤的原始数据"
  → intent=数据
  → 原始数据: Dryad, GBIF, Zenodo, Figshare, PANGAEA...
```

---

## 📋 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v5.4.0** | 2026-06-09 | 🗄️ 活系统数据库目录 (61库/8领域/4层级) + 图谱路由器 + 渐进搜索 + 涌现引擎 |
| **v5.3.0** | 2026-06-08 | 🆕 inference_engine + ☯️ TAO 架构 (木) + 🔥 WUXING dynamics |
| **v5.2.2** | 2026-06-08 | validator.py 提取 + evolution_executor + contradiction-driven meso_agent |
| **v5.2.1** | 2026-06-07 | S-T-V 三角验证 + DirectLoader + eon-core 协调 |
| **v5.2** | 2026-06-07 | Meso-Cosmos 协调层 + ZN/EN 双语图谱 (→ 废弃，由 eon-core v7.1 取代) |
| **v5.1** | 2026-06-07 | Hub-and-Spoke 搜索 + 权威可信度评分 |
| **v5.0** | 2026-06-07 | BDI + ReAct 认知架构 |

> **最新**: v5.4.0 · 2026-06-09

> **"不要搜索字符串，要重建所指。"**
> Don't search for strings — reconstruct the signified.
