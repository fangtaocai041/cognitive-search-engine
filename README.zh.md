<p align="center">
  🇬🇧 <a href="README.md">English</a>
</p>

<div align="center">
  <h1>🕸️ 认知搜索引擎 v4</h1>
  <p><strong>前沿物种文献搜索</strong> — 知识图谱遍历 + 能效最优 + 符号学 + 语言学 + DeepSeek 思维链</p>
  <p>3 Skills · 5 搜索引擎 · 预建知识图谱 · 自适应搜索深度 · 活系统自进化</p>
</div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-4.1.0-6366f1?style=flat-square" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/skills-3-22c55e?style=flat-square" alt="Skills"></a>
  <a href="#"><img src="https://img.shields.io/badge/MCP-5-f59e0b?style=flat-square" alt="MCP"></a>
  <a href="#"><img src="https://img.shields.io/badge/活系统-自进化-ec4899?style=flat-square" alt="活系统"></a>
  <a href="#"><img src="https://img.shields.io/badge/DeepSeek-优化-8b5cf6?style=flat-square" alt="DeepSeek"></a>
</p>

---

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
| 物种名拼写错误 | ❌ 搜"Ochetobius"找不到"Ochetobibus" | ✅ 11 层模糊协议捕获所有变体 |
| 冷启动（新物种） | ❌ 零结果 → 卡住 | ✅ 作者图谱 + 引用遍历找到论文 |
| 综述引用盲信 | ❌ 幽灵引用/错误归因直接纳入 | ✅ Phase 1.6: 5 级引用验证 |
| 搜索健忘症 | ❌ 同样搜索重复同样成本 | ✅ 知识图谱持久化，已知论文 = 0 tokens |
| 一刀切搜索深度 | ❌ 8 篇和 8000 篇同样策略 | ✅ 自适应：穷举/分类/满意三模式 |
| 中英文断层 | ❌ 纯英文搜索漏掉中文论文 | ✅ Layer 4: 中文名 + 作者交叉引用 |
| 无认知模型 | ❌ 纯字符串匹配 | ✅ 符号学 + 语言学 + 语音学 + 逻辑学 |

### vs AI 搜索 (Gemini, Perplexity, Claude)

| 问题 | AI 搜索 | 认知搜索引擎 |
|------|--------|------------|
| 透明度 | ❌ 黑箱 — 无法验证完整性 | ✅ 12 个阶段，每步可审计 |
| 成本 | ❌ 每次高 token 消耗 | ✅ 图谱持久化节省 75% |
| 领域知识 | ❌ 通用 — 无物种特定逻辑 | ✅ 拉丁语法、IPA、OCR 错误模型 |
| 引用图谱 | ❌ 未利用 | ✅ 图谱遍历：作者→期刊→引用 |
| 学习能力 | ❌ 无状态 — 每次独立 | ✅ 图谱随每次搜索增长 |

### 独有能力（无其他工具具备）

| # | 能力 | 为什么重要 |
|:--|------|-----------|
| 1 | **综述引用挖掘 + 验证** | 综述是"二手搜索" — 但先验证再信任 |
| 2 | **符号学重建** | 从拼写错误重建物种身份，而非匹配字符串 |
| 3 | **自适应搜索深度** | 8 篇穷举 vs 8000 篇满意即止 — 自动切换 |
| 4 | **跨语言作者图谱** | 中文作者发英文论文，英文作者引中文论文 — 全捕获 |
| 5 | **IPA 语音距离** | Ochetobius=O231, Ochetobibus=O231 — 语音相同即相同 |

## ⚡ 三大突破

### 1. 知识图谱遍历（非线性搜索）

| 传统线性搜索 (v2/v3) | 图谱搜索 (v4) |
|---------------------|-------------|
| 11 层顺序执行 | 图谱条件遍历 |
| 结果每次丢弃 | 结果持久化到图谱 |
| ~8000 tokens/次 | ~2000 tokens/次（节省 75%） |
| 每次从头开始 | 已知论文：**0 tokens** |

### 2. 能效最优（满意即止，不穷举）

```
文献量 < 20 → 穷举模式（如鳤仅 8 篇，一篇不漏）
文献量 20-200 → 分类归纳（先分类不展开，人选后穷举）
文献量 > 200 → 满意模式（找到代表性样本即停止）
```

### 3. 多学科认知引擎

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

### 自适应搜索深度

```
搜索前先估算文献量（Scholar 计数 + 图谱节点 + 作者产出率）

文献量 < 20   → 穷举模式
  • 11 层全激活，永不早停
  • 图谱遍历深度 = 3
  • 额外搜索灰色文献（中文报告、学位论文）
  • 输出知识空白标注

文献量 20-200 → 分类归纳模式
  • Phase 1: 按子主题快速分类（不展开内容）
  • Phase 2: 用户选择类别后穷举展开
  • Phase 3: 可迭代深化其他类别

文献量 > 200  → 满意模式
  • 找到 8-12 篇代表性论文即满足
  • 输出分类概览 + "深入某类别"选项
```

### 图谱遍历算法

```
1. 从图谱加载已知论文（0 tokens — 预计算）
2. 若已知论文 ≥ 8 → 满意，立即返回
3. 遍历图谱边：作者 → 期刊 → 引用
4. 语言学过滤：词根相似度 > 0.80
5. 新论文合并入图谱（持久化，下次免费）
6. 边际收益递减时停止
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

| 项目 | 用途 |
|------|------|
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | 鱼类生态学 AI 研究助手 |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | 江豚研究智能体 |

porpoise-agent 的 orchestrator 自动检测查询中的物种名，自动路由到 graph-search-engine。

---

## 📜 许可证

MIT © 2026 fangtaocai041

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
>
> **"不要搜索字符串，要重建所指。"**
> Don't search for strings — reconstruct the signified.
