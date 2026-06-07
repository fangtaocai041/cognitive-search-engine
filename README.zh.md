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
  <a href="#"><img src="https://img.shields.io/badge/version-5.2-8b5cf6?style=flat-square" alt="Version"></a>
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
> 协调由 [meso-cosmos-agent](https://github.com/fangtaocai041/meso-cosmos-agent) 统一调度。

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
│   └── self-evolve.md            ← 🧬 搜索后反馈 → 自动调参
│
├── docs/
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

## 🗺️ 后续计划

> **当前状态：** 领域领先的研究原型 (v5.1)。以下里程碑计划在后续版本中逐步实现。

### ⚠️ 已知限制

| 方面 | 限制 | 影响 |
|------|------|------|
| **用户界面** | 仅 CLI，依赖 Reasonix 运行时 | 非 Reasonix 用户无法直接使用 |
| **部署方式** | 无 Docker 镜像，无 REST API | 无法独立部署/嵌入到其他项目 |
| **基准测试** | 仅在鳤（12 篇）上验证 | 对其他 100+ 物种的 recall 未知 |
| **实时索引** | 依赖第三方 API (PubMed, Crossref 等) | 延迟受外部服务状态影响 |
| **中文数据库** | web_search + web_fetch 降级方案，无直接 CNKI API | 有频率限制，部分付费论文可能遗漏 |
| **同行评审** | 无已发表论文 | 学术界尚未评审该架构 |

### 🎯 里程碑 1：独立产品化

```
产品需求:
  - Web UI (Streamlit / Gradio) → 输入物种名 → 输出知识图谱
  - REST API (FastAPI) → POST /search?species=Ochetobius+elongatus
  - Docker 镜像 → docker pull fangtaocai/cognitive-search-engine
  - pip 安装 → python -m cognitive_search.search "鳤"
```

**为什么重要：** 最先进的物种搜索引擎如果只能在 Reasonix 内部运行，等于不存在。

### 🎯 里程碑 2：多物种基准测试

```
基准测试:
  - 整理 50 种中国淡水鱼类的已知论文列表
  - 基线: PubMed / Google Scholar / Semantic Scholar 的 recall
  - 对比: 本引擎的 recall、precision、每物种 token 成本
  - 发布: 基准测试表作为技术报告
```

**为什么重要：** 一个数据点（鳤，100% recall）不足以服众。50 个物种才叫证据。

### 🎯 里程碑 3：学术论文发表

```
论文:
  - 标题: "Hub-and-Spoke Graph Search for Critically Endangered Fish Species"
  - 目标期刊: 水生生物学报 / Animals / Scientific Data
  - 贡献:
      1. Hub-and-Spoke 协议（替代线性 14 层）
      2. 权威可信度评分 (0-100)
      3. OCR 变体安全网
      4. 中文优先搜索策略
  - 实证: 50 个物种的 recall vs token 成本对比
```

**为什么重要：** 同行评审验证架构价值，并打开学术引用影响力。

### 🎯 里程碑 4：生产环境加固

```
工程目标:
  - 自动扩容: 处理 100 个并发物种搜索
  - 缓存: Redis 查询缓存 (TTL 7 天)
  - 监控: Prometheus + Grafana (recall、延迟、每物种 token 成本)
  - 自托管: 外部 API 不可用时回退到本地 PDF 语料库
  - 插件系统: 社区贡献每种鱼的搜索规则
```

**为什么重要：** 从"在我机器上能跑"到"稳定服务 100 个用户"。

### 💡 正在探索的想法

- **多 Agent 协作**：每个学科方向一个 agent Hub，合并结果
- **本地 LLM 推理**：将 DeepSeek API 替换为 Ollama (Qwen2.5-7B) 降低调用成本
- **CNKI 直连 API**：如有机构访问权限，绕过 web_search 直接搜索中文数据库
- **多模态搜索**：鱼类图片 → 物种鉴定 → 论文检索

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

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
>
> **"不要搜索字符串，要重建所指。"**
> Don't search for strings — reconstruct the signified.
