# 🔍 认知搜索引擎

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python) ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge) ![Version](https://img.shields.io/badge/Version-v5.9-blueviolet?style=for-the-badge) ![Engines](https://img.shields.io/badge/Engines-15%2B-success?style=for-the-badge) ![Thompson](https://img.shields.io/badge/Thompson-Sampling-orange?style=for-the-badge) ![PID](https://img.shields.io/badge/PID-Rate%20Limit-yellow?style=for-the-badge) ![MPC](https://img.shields.io/badge/MPC-Optimization-red?style=for-the-badge) ![Async](https://img.shields.io/badge/Async-aiohttp-9cf?style=for-the-badge) ![CN/EN](https://img.shields.io/badge/CN%2FEN-Dual%20Channel-ff69b4?style=for-the-badge) ![Agent](https://img.shields.io/badge/Agent-Judge-important?style=for-the-badge)

> ⚡ 搜索验证核心 — BDI认知搜索，15+引擎，Thompson采样，MPC优化。
> 你无法用昨天的搜索结果回答今天的问题。

[English](README.md) · [中文](README.zh.md) · [更新日志](CHANGELOG.md)

---

## 📖 目录

- [哲学](#-哲学)
- [快速开始](#-快速开始)
- [架构](#-架构)
- [功能特性](#-功能特性)
- [项目结构](#-项目结构)
- [生态体系](#-生态体系)

---

## 🎯 核心哲学

> 世界是动态的，知识是暂时的，涌现是常态。

这是三角之 **V（验证）**。S（知识）提出主张，V 负责验证——通过多源并行搜索、跨项目比对、三角验证评分，确保每一条写入知识库的信息都经过 ≥3 个独立来源的检验。

### 🔗 在三角中的角色

```
三生万物架构：
  S/V0  fish-ecology-assistant    → 知识供给（阴·静）
  V/V1  cognitive-search-engine   → 搜索验证（阳·动） ← 你在这里
  Coord eon-core                  → 协调内核（太极点）
```

---

## 🧩 这个项目是什么

它是一个搜索验证引擎。不存储知识，而是验证知识。

当 S 层说"鳤的科是鲤科"，V 层会去问 PubMed、Crossref、中文期刊、Google Scholar——它们都这么说吗？有没有不一致？如果有，谁是对的？

> 赫拉克利特说：人不能两次踏进同一条河流。
>
> 我们说：你也不能用昨天的搜索回答今天的问题。

---

## 🧩 这个项目是什么

它是一个搜索验证引擎。不存储知识，而是验证知识。

当 S 层说"鳤的科是鲤科"，V 层会去问 PubMed、Crossref、中文期刊、Google Scholar——它们都这么说吗？有没有不一致？如果有，谁是对的？

> 赫拉克利特说：人不能两次踏进同一条河流。
>
> 我们说：你也不能用昨天的搜索回答今天的问题。

---

## 📜 三谛

**🌊 万象流转** — R包迭代，物种迁徙，共识更迭，气候重塑生态。今日之确论，半载后或为陈迹。吾辈不视任何知识为永恒真理，而将其置于时间轴上，以动态眼光审之。

**🍂 真知若寄** — 科学之基石，在于可证伪（波普尔）。无发现乃终极真理——唯有「当下最佳解释」。吾辈用校准之语：「证据提示」而非「证明」，「Smith (2022) 发现」而非「研究表明」。每一条输出，皆镌刻时间之锚。

**🌟 涌现成章** — 生命、意识、生态、AI推理——莫非涌现。不可执一隅以窥全豹。当≥3个独立来源指向同一意外模式，系统不以其为噪声而弃之，乃标记为涌现信号而追踪之。

### ⚖️ 何以重要

| 事境 | 旧习 | 新观 |
|:-----|:----|:----|
| 引用 | 「研究证明」 | 「Smith(2022) 发现 X，Jones(2024) 补 Y」 |
| 异常 | 视为噪声弃之 | ≥3 来源 → 涌现信号，持续追踪 |
| 知识衰减 | 手册尘封不更 | 审查记录含「下次审查日期」 |
| 方法选择 | 流水线一成不变 | 择法动态，信心动态 |

> 道生一，一生二，二生三，三生万物。

此为三角之根，载 430 种长江鱼类。


## 📜 三大信条

**🌍 世界是动态的** — R包在更新，物种分布变化，科学共识在演进。今天正确的结论，六个月后可能过时。

**📖 知识是暂时的** — 科学的基石是可证伪（波普尔）。没有发现是终极真理——只有当前最佳解释。我们用校准语言：证据表明，而非证明。

**🌟 涌现是常态** — 生命、意识、生态系统、AI推理——都是涌现现象。当≥3个独立来源指向同一意外模式，系统标记为涌现信号。

### ⚖️ 为什么这对研究很重要

| 场景 | 传统做法 | 动态世界观 |
|:-----|:--------|:----------|
| 引用 | 研究证明 | Smith(2022)发现X，Jones(2024)补充Y |
| 异常值 | 当作噪声 | ≥3来源→涌现信号 |
| 知识衰减 | 手册冻结 | 含下次审查日期 |

> 道生一，一生二，二生三，三生万物。

这是三角之核心，承载 430 种长江鱼类。


## 🚀 快速开始

```bash
git clone git@github.com:fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine
pip install -e .
python src/main.py search "刀鲚 生态"
```

---

## 🏗️ 架构

```
cognitive-search-engine/
  src/
  ├── meso_agent.py          BDI 认知核心 (Belief→Desire→Intention)
  ├── parallel_search.py     15+ HTTP 数据源 (PubMed/Crossref/OpenAlex...)
  ├── AsyncParallelSearch     aiohttp 异步搜索 (3-5x 加速)
  ├── search_coordinator.py  KB-First 两阶段搜索协调器
  ├── unified_search.py      自适应模式: 全量/分类/饱和
  ├── validator.py           5级信任评分 + 源独立性检验
  ├── thompson_selector.py   Thompson采样多臂老虎机引擎选择
  ├── pid_limiter.py         PID自适应API速率限制
  ├── mpc_world.py           MPC搜索成本优化
  ├── agent_judge.py         LLM裁判结果评估
  ├── inference_engine.py    搜索后缺口+矛盾检测
  ├── evolution_executor.py  7触发器自进化
  └── variant_generator.py   OCR学名变体生成
```

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🧠 BDI 认知 | Belief→Desire→Intention 自适应搜索循环 |
| 🌐 15+ 搜索引擎 | PubMed, Crossref, OpenAlex, Semantic Scholar, CNKI, 万方... |
| ⚡ 异步搜索 | aiohttp AsyncParallelSearch, 3-5x 加速 |
| 🎯 Thompson 采样 | 学习型引擎选择替代规则剪枝 |
| 📊 PID 速率限制 | 自适应 API 请求速率控制 |
| 🎛️ MPC 优化 | 模型预测控制搜索成本优化 |
| ⚖️ Agent 裁判 | LLM 结果质量评估 (4维度) |
| ✅ 5级信任 | DOI→PMID→物种→作者→期刊评分 |
| 🔍 OCR 变体 | 系统化学名变体生成 |
| 🌊 中英双通道 | 中英文文献分路由 |
| 🔄 自进化 | 7 触发器自适应搜索参数 |

---

## 📁 项目结构

```
cognitive-search-engine/
  (见上方架构图)
```

---

## 🔗 生态体系

本项目是「三生万物」生态的 搜索验证核心 (V1)。

```
三角核心 (sealed 3):
  📦 fish-ecology-assistant    → 知识供给 (V0)
  🔍 cognitive-search-engine   → 搜索验证 (V1)
  ⚙️ eon-core                  → 协调内核 (Coord)

万物衍生 (open N):
  🐬 porpoise-agent    → P₁ 江豚专研
  🐟 coilia-agent      → P₂ 刀鲚专研
  🐟 culter-agent      → P₃ 鲌类专研
  🔥 conflict-arbiter  → C  冲突仲裁
```

> 🔥 和则无穷力量，分则顶尖专家引擎。

---
*SanShengWanWu Ecosystem · MIT License · fangtaocai041*
