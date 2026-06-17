<p align="center">
  🇬🇧 <a href="README.md">English</a>
</p>

<div align="center">
  <h1>🕸️ 认知搜索引擎 v5</h1>
  <p><strong>中宇宙式 Agent</strong> — BDI + ReAct + 权威可信度评分 + 中英动态图谱 + 按需加载</p>
  <p>15 模块 · 7 搜索引擎 · 5 层架构 · BDI 推理 · 中宇宙协调层 · Thompson 采样 · PID 控制</p>
</div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-5.4.0-8b5cf6?style=flat-square" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/skills-5-22c55e?style=flat-square" alt="Skills"></a>
  <a href="#"><img src="https://img.shields.io/badge/MCP-7-f59e0b?style=flat-square" alt="MCP"></a>
  <a href="docs/ARCHITECTURE.md"><img src="https://img.shields.io/badge/架构-meso_cosmos-8b5cf6?style=flat-square" alt="架构"></a>
  <a href="#"><img src="https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6?style=flat-square" alt="Multi-LLM"></a>
  <a href="#"><img src="https://img.shields.io/badge/BDI-ReAct-22c55e?style=flat-square" alt="BDI"></a>
  <a href="#"><img src="https://img.shields.io/badge/权威评分-0_100-ec4899?style=flat-square" alt="权威评分"></a>
  <a href="https://deepwiki.com/fangtaocai041/cognitive-search-engine"><img src="https://devin.ai/assets/askdeepwiki.png" alt="Ask DeepWiki" height="20"></a>
  <a href="#"><img src="https://img.shields.io/badge/Docker-规划中-lightgrey?style=flat-square" alt="Docker"></a>
  <a href="skills/self-evolve.md"><img src="https://img.shields.io/badge/自进化-反馈循环-10b981?style=flat-square" alt="自进化"></a>
  <a href="#"><img src="https://img.shields.io/badge/Thompson-多臂老虎机-EC4899?style=flat-square" alt="Thompson"></a>
  <a href="#"><img src="https://img.shields.io/badge/PID-自适应限速-F59E0B?style=flat-square" alt="PID"></a>
</p>

## 🧠 三层智能优化

> 验证引擎集成了三层优化：**DeepSeek 级效率** (MoE 门控 + KV 缓存)、**学者级置信** (Rule of Three 统计停止)、**混沌增强探索** (Rössler 扰动 + wildcard 发现)。
> 由 [eon-core](https://github.com/fangtaocai041/eon-core) 统一协调。

## 🔺 S-T-V-P₁-P₂ 架构角色: **Validation (V)**

> S-T-V-P₁-P₂ 生态: `fish(S) → cognitive(V)`，`porpoise(P₁)` + `coilia(P₂)` + `culter(P₃)` 为领域专研，`conflict-arbiter(C)` 为冲突仲裁。
> 验证搜索结果、提供权威可信度评分、维护共享知识图谱。
> **DirectLoader**: `importlib` 零 MCP 进程。**三角验证**: 每个核心声明 ≥3 独立源。

## 📊 自我评价

| 维度 | 评分 | 说明 |
|------|:--:|------|
| 🎯 搜索精度 | ⭐⭐⭐⭐⭐ | Hub-and-Spoke + OCR 变体生成 + 权威可信度评分 (0-100) |
| 🧠 认知架构 | ⭐⭐⭐⭐⭐ | BDI + ReAct 循环 + 矛盾驱动的策略选择 |
| 📊 验证严谨性 | ⭐⭐⭐⭐☆ | `validator.py` 实现跨项目独立性强制检查 |
| 🔬 物种覆盖 | ⭐⭐⭐⭐☆ | 图谱中约 10 个物种，通过自动回写可扩展 |
| ⚡ 运行效率 | ⭐⭐⭐⭐☆ | DirectLoader (importlib 零 MCP) + Thompson 采样 + PID 限速 |
| 🧪 测试覆盖 | ⭐⭐⭐⭐⭐ | 46 集成 + 94 鲁棒性 = 140 项测试 |

---

## 📋 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v5.4.0** | 2026-06-20 | 🆕 Thompson 采样多臂老虎机引擎选择 + PID 自适应 API 限速 + MPC 世界模型搜索成本优化 + LLM-as-Judge 四维评估 + validator.py 5级信任评分 + evolution_executor 7触发矛盾驱动自进化 + AsyncParallelSearch (aiohttp，3-5x 加速) |
| **v5.3.0** | 2026-06-12 | 🆕 inference_engine 缺口+矛盾检测（TAO 启发）+ agent_judge.py LLM裁判 |
| **v5.2.2** | 2026-06-09 | validator.py 提取 + evolution_executor + contradiction-driven meso_agent + 修复 25+ 静默吞错 |
| **v5.2.1** | 2026-06-07 | S-T-V 三角验证 + DirectLoader + Meso-Cosmos Agent v4.0 |
| **v5.2** | 2026-06-07 | Meso-Cosmos 协调层 + 中英双语图谱 |
| **v5.1** | 2026-06-07 | Hub-and-Spoke 搜索 + 权威可信度评分 |
| **v5.0** | 2026-06-07 | BDI + ReAct 认知架构 |

> **最新**: v5.4.0 · 2026-06-20

> **核心力量**: 从"字符串匹配"到"所指重建"——多条能指路径（精确名、OCR变体、作者网络、引用图谱、中文名）汇聚于同一所指（物种本身）。

## 🔗 关联项目

本引擎作为 git submodule 集成到以下项目：

| 项目 | 角色 | 说明 |
|------|:----:|------|
| [eon-core](https://github.com/fangtaocai041/eon-core) | **Coord** | 协调中枢 — EventBus · CAS · DAG 路由 · 6项目拓扑 |
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | **S** (State) | 鱼类生态 — 21 MCP · 28 skills · 长江 430 种鱼类知识库 |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | **P₁** (Porpoise) | 江豚专研 — NBHF 声学 · 栖息地建模 |
| [coilia-agent](https://github.com/fangtaocai041/coilia-agent) | **P₂** (Coilia) | 刀鲚专研 — 耳石微化学 · 洄游生态 |
| [culter-agent](https://github.com/fangtaocai041/culter-agent) | **P₃** (Culter) | 鲌类专研 — 营养生态 · 生长分析 |
| [conflict-arbiter](https://github.com/fangtaocai041/conflict-arbiter) | **C** (Arbiter) | 冲突仲裁 — 多源保护级冲突检测 |

> **协同进化**: 引擎代码更新 → 衍生项目通过 submodule 自动受益。
> 知识图谱进化 → 全项目共享。
> 完整协调规范: workspace 根目录 `coordination.yaml`。

### 🧠 eon-core 统一内核 (Workspace Level)

> **10层同心架构** — OriginKernel → YinYang → 5 Vertices → 8 Trigrams → Tetrahedron → Samsara → Sphere → Tendrils → Evolution。
> 由 [eon-core](https://github.com/fangtaocai041/eon-core) 统一协调。替代已删除的 meso-cosmos-agent (v7.1)。

```
理解 → 路由 → 执行 → 验证 → 合成 → 进化
(Macro) (Meso) (Micro) (Cross) (Merge) (Feedback)
```

---

## 🧠 v5.2: 中宇宙式 Agent — Meso-Cosmos 协调层

> **宏观(BDI) → 中宇宙(协调) → 微观(执行)** — 自动在宏观意图与微观工具调用之间搭建桥梁。

### 新增功能

| 功能 | 说明 | 模块 |
|:----|:-----|:-----|
| **MesoAgent** | 中宇宙式协调层 — 统一管理 WorldModel/SearchRuleEngine/MemorySystem/GraphUpdater | `src/meso_agent.py` |
| **动态图谱 v2.0** | 中英文感知自动更新 — 中文期刊自动填入 `authors_zh`，新作者/期刊自动注册，中英文双语去重 | `src/graph_updater.py` |
| **中英文文献规则** | 中文期刊走中文署名（杨计平），英文走英文名（Yang Jiping）；论文防双版本重复 | `project memory (high)` |
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
│       → 执行分发 → 图谱更新 → 中英规则               │
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

### 中英自动规则

| 情境 | 以前 | 现在 |
|:----|:----|:----|
| 中文期刊论文 | `authors: [Yang Jiping]` | `authors_zh: [杨计平]` ✅ |
| 英文期刊论文 | `authors: [Yang Jiping]` | `authors: [Yang Jiping]` ✅ (不变) |
| 中英文双版本 | 两个都保留 | DOI + title_zh 去重 → 保留中文版 |
| 发现新作者 | 手动添加 | 自动注册中文名 |
| 发现新期刊 | 手动输入 | 自动注册 |

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
| **5. 执行** | PubMed · Crossref · MCP (7 引擎) · 权威评分 · Thompson 采样 · PID 限速 | `rule_engine._http_search()` |

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

## 🔺 S-T-V-P₁-P₂ 架构 (跨项目)

> 六个项目: State(fish) → Validation(cognitive) → Coord(eon-core)，P₁(porpoise) + P₂(coilia) + P₃(culter) + C(arbiter)

| 组件 | 项目 | 功能 |
|:----:|------|------|
| **S** | fish-ecology-assistant | State — 知识、数据、发现 |
| **V** | cognitive-search-engine | Validation — 验证、信任评分 |
| **Coord** | eon-core | Coordination — EventBus, CAS, DAG 路由 |
| **P₁** | porpoise-agent | 江豚领域专家 |
| **P₂** | coilia-agent | 刀鲚领域专家 |
| **P₃** | culter-agent | 鲌类领域专家 |
| **C** | conflict-arbiter | 冲突仲裁 |

## 🔧 工程语言承诺

> **所有功能用可执行的工程语言表达 — 非自然语言。**
> `function(input: Type) → OutputType` | `WHEN condition THEN action` | `config.path.to.value`

| 格式 | 用途 |
|------|------|
| `search_rules.yaml` | 10 阶段结构化规则引擎 |
| `tools.json` | JSON Schema — DeepSeek+Gemini+OpenAI 通用 |
| `src/rule_engine.py` | Python 直接执行 |
| `config/evolution.yaml` | 7 触发参数自适应 |

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

---

## 🆕 v5.4.0 新增功能

| 功能 | 状态 | 说明 |
|------|:--:|------|
| 🧠 BDI MesoAgent | ✅ | Belief→Desire→Intention 自适应循环 |
| 🌐 15+ 数据源 | ✅ | PubMed, Crossref, OpenAlex, CNKI, 万方, 百度学术... |
| ⚡ 异步搜索 | ✅ | aiohttp AsyncParallelSearch, 3-5x 加速 |
| 🎯 Thompson 采样 | ✅ | 学习型多臂老虎机引擎选择 |
| 📊 PID 限速器 | ✅ | 自适应 API 速率控制 |
| 🎛️ MPC 世界模型 | ✅ | 搜索成本优化 |
| ⚖️ Agent 裁判 | ✅ | LLM 四维评估 |
| ✅ 5 级信任 | ✅ | DOI→PMID→物种→作者→期刊 层级评分 |
| 🔍 OCR 变体 | ✅ | 系统化学名变体安全网 |
| 🌊 中英双通道 | ✅ | 中英文文献分路由 |
| 🔄 自进化 | ✅ | 7 触发器参数自适应（矛盾驱动） |
| 🧠 推理引擎 | ✅ | 搜索后缺口分析 + 矛盾检测（TAO） |
| 🎯 verify_claims() | ✅ | IProjectAdapter 跨项目声明验证 |
| 🐛 错误日志 | ✅ | 修复 25+ 静默吞错 |
| 🧪 测试套件 | ✅ | 8 个测试文件，140 项测试通过 |

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
│   ├── agent.yaml                ← v5.0: 5层架构 + BDI 配置
│   ├── mcp_servers.yaml          ← 7 搜索引擎
│   ├── species_graph.yaml        ← 长期记忆 (16 条目 + 索引)
│   ├── component_registry.yaml   ← 活系统：12 组件生命周期
│   ├── evolution.yaml            ← 自进化：7 自适应触发
│   ├── search_rules.yaml         ← 阶段定义 (映射层)
│   ├── stv_protocol.yaml         ← 跨项目 STV 三角协议
│   ├── tao.yaml                  ← TAO 启发推理配置
│   └── wuxing.yaml               ← 五行流转
│
├── src/                          ← 15 模块 (5层认知智能体)
│   ├── agent_core.py             ← 🧠 CognitiveAgent — BDI + ReAct 循环
│   ├── memory_layer.py           ← 🗄️  MemorySystem — 短期+长期
│   ├── world_model.py            ← 🧬 BDI WorldModel — Belief/Desire/Intention
│   ├── rule_engine.py            ← ⚙️  SearchRuleEngine — 阶段+执行
│   ├── variant_generator.py      ← 🔤 OCR 变体自动生成
│   ├── graph_updater.py          ← 📊 图谱持久化 + 反向索引
│   ├── mcp_client.py             ← 🔌 MCP stdio 客户端 (7 服务器)
│   ├── parallel_search.py        ← ⚡ 多查询并行执行
│   ├── meso_agent.py             ← 🧠 中宇宙协调层
│   ├── validator.py              ← ✅ 5级信任评分 + 独立性检查
│   ├── thompson_selector.py      ← 🎰 Thompson 采样老虎机引擎选择
│   ├── pid_limiter.py            ← 📊 PID 自适应 API 限速
│   ├── mpc_world.py              ← 🎛️ MPC 搜索成本优化
│   ├── agent_judge.py            ← ⚖️ LLM裁判四维评估
│   ├── inference_engine.py       ← 🧠 搜索后缺口+矛盾检测
│   ├── evolution_executor.py     ← 🔄 7触发自进化（矛盾驱动）
│   └── adapter.py                ← 🔗 IProjectAdapter + verify_claims()
│
├── skills/
│   ├── graph-search-engine.md    ← v4 核心：图谱遍历 + 能效最优
│   ├── cognitive-species-search.md ← v3：符号学 + 语言学 + 语音学
│   ├── chinese-academic-search.md  ← 中文期刊搜索 (8 种期刊)
│   ├── meso-orchestrator.md      ← 🧠 中宇宙协调
│   └── self-evolve.md            ← 🧬 搜索后反馈 → 自动调参
│
├── docs/
│   ├── ARCHITECTURE.md           ← 5层智能体架构 (完整文档)
│   ├── STV_TRIANGLE_ARCHITECTURE.md ← 跨项目三角架构
│   └── UNIFIED_EVOLUTION.md      ← 多项目协同进化架构
│
├── tests/
│   ├── test_validator.py           ← 信任评分测试
│   ├── test_variant_generator.py   ← 变体生成测试
│   ├── test_credibility_scorer.py  ← 可信度评分测试
│   ├── test_unified_search.py      ← 统一搜索测试
│   ├── test_world_model.py         ← MPC 世界模型测试
│   └── test_search_integration.py  ← 搜索集成测试
│
└── .github/workflows/
    └── validate.yml              ← CI/CD
```

---

## 🔬 工作原理

### 自适应搜索深度（三模式）

```
搜索前先估算文献量：
  ncbi_esearch → pubmed_count
  scholar_search_literature_graph(limit=5) → scholar_count
  web_search(中文名 + " 论文 OR 综述") → chinese_hits
  estimated = MAX(pubmed_count, scholar_count, chinese_hits * 0.5)

穷举模式 (estimated < 20)
  → Hub-and-Spoke 全方向展开，每篇论文加载完整元数据

分类归纳模式 (estimated 20–100)
  → STEP 0: 先搜综述 → STEP 1: 构建分类图谱 → STEP 2: 用户选择展开

大规模模式 (estimated > 100)
  → STEP 0: 必搜综述 → STEP 1: 分类概览 → STEP 2: 每方向精选 5-8 篇
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

---

## 📡 内置搜索引擎

| 引擎 | 用途 | 模糊匹配 |
|------|------|:------:|
| Google Scholar | 主力 — 模糊匹配最强 | ✅✅✅ |
| Europe PMC + PubMed | 生物医学文献 | ✅ |
| OpenAlex + Semantic Scholar | 跨学科学术搜索 | ✅✅ |
| CNKI + 万方 + 百度学术 | 中文学术数据库 | ✅ |
| Tavily | 网络搜索（灰色文献、报告） | ✅✅ |
| Exa | 语义网络搜索 | ✅ |

---

## 🗺️ 后续计划

### ⚠️ 已知限制

| 方面 | 限制 | 影响 |
|------|------|------|
| **用户界面** | 仅 CLI，依赖 Reasonix 运行时 | 非 Reasonix 用户无法直接使用 |
| **部署方式** | 无 Docker 镜像，无 REST API | 无法独立部署 |
| **基准测试** | 仅在鳤（12 篇）上验证 | 对其他物种的 recall 未知 |
| **中文数据库** | web_search + web_fetch 降级方案 | 频率限制 |

### 🎯 里程碑 1：独立产品化

- Web UI (Streamlit / Gradio) → 输入物种名 → 输出知识图谱
- REST API (FastAPI) → POST /search
- Docker 镜像 → `docker pull fangtaocai/cognitive-search-engine`
- pip 安装 → `python -m cognitive_search.search "鳤"`

### 🎯 里程碑 2：多物种基准测试

- 整理 50 种中国淡水鱼类的已知论文列表
- 基线: PubMed / Google Scholar / Semantic Scholar 的 recall
- 对比: 本引擎的 recall、precision、每物种 token 成本

### 🎯 里程碑 3：学术论文发表

- 目标期刊: BMC Bioinformatics / 水生生物学报 / Scientific Data
- 贡献: Hub-and-Spoke 协议、权威可信度评分、OCR 变体安全网、中文优先搜索

### 💡 正在探索的想法

- **多 Agent 协作**：每个学科方向一个 agent Hub，合并结果
- **本地 LLM 推理**：将 DeepSeek API 替换为 Ollama (Qwen2.5-7B)
- **CNKI 直连 API**：如有机构访问权限
- **多模态搜索**：鱼类图片 → 物种鉴定 → 论文检索

---

## 📋 README 变更记录

| 版本 | 日期 | 主题 | 变更内容 |
|:------|:-----|:------|:-------------|
| **v7.1** | 2026-06-20 | README 复原 | 从历史会话记录恢复: 中宇宙架构、Hub-and-Spoke 协议、权威评分公式、五大突破、工程语言、README 变更记录、Thompson+PID 徽标 |
| **v5.4.0** | 2026-06-20 | 智能优化 | Thompson 采样老虎机, PID 自适应限速, MPC 世界模型, AsyncParallelSearch (aiohttp), LLM-as-Judge, validator.py 5级信任, evolution_executor 7触发 |
| **v5.3.0** | 2026-06-12 | TAO 推理 | inference_engine 缺口+矛盾检测, TAO 启发推理 |
| **v5.2.2** | 2026-06-09 | 错误基础设施 | 修复 25+ 静默吞错, validator.py, evolution_executor |
| **v5.2.1** | 2026-06-07 | 跨项目同步 | + S-T-V 三角角色, + DeepWiki/Docker/自进化徽标, + 关联项目协同进化 |
| **v5.2** | 2026-06-06 | 中宇宙式 Agent | + MesoAgent, + 动态图谱 v2.0 (中英自动), + 中英文献规则, + MCP 15秒超时 |
| **v5.1** | 2026-06-06 | Hub-and-Spoke 协议 | + Hub-and-Spoke (3阶段10调用), + 权威可信度评分, + 综述优先策略, + 懒加载图谱 |
| **v5.0** | 2026-06-06 | 5层智能体架构 | + BDI WorldModel, + CognitiveAgent (ReAct循环), + MemorySystem |
| **v4.3** | 2026-06-06 | 工程语言化 | + YAML 规则引擎 (10阶段), + JSON Schema tools.json, + rule_engine.py |
| **v4.2** | 2026-06-06 | 活系统 | + component_registry (12组件), + evolution.yaml, + self-evolve Skill |
| **v4.1** | 2026-06-06 | 自适应深度 | + 自适应搜索深度 (穷举/分类/满意), + Phase 1.5 综述挖掘 |
| **v4.0** | 2026-06-06 | 图谱引擎 | 初始发布 — 知识图谱遍历, 12 搜索层, 5 搜索引擎 |

---

## 📜 许可证

MIT © 2026 fangtaocai041

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
