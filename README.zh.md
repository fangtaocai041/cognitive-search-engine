# Cognitive Search Engine 🕸️

**三角核心 V/V1 层** — 多源并行搜索 · 分类学验证 · 可信度评分。

> 🌊 万物皆变 · Panta Rhei
>
> 搜索不是一次性的查询——它是持续的验证循环。

[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![Reasonix](https://img.shields.io/badge/Reasonix-Code-brightgreen)](https://reasonix.ai)

[English](README.md) · [中文](README.zh.md) · [更新日志](CHANGELOG.md)

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

## ⚡ 快速上手

```bash
# 搜索物种
python scripts/search_api.py --species "Ochetobius elongatus"

# 分类学不一致检测
python scripts/search_api.py --species "Ochetobius elongatus" --check-taxonomy

# JSON 输出
python scripts/search_api.py --species "鳤" --format json
```

---

## 🚀 核心能力

| 🚀 能力 | 📝 说明 |
|:---------|:--------|
| **多源并行** | tavily / exa / scholar / article / scholarly，11 引擎可配置 |
| **分类学验证** | 跨项目比对 family/order，不一致自动标记 |
| **三角验证评分** | 每篇论文 ≥2 独立源，journal whitelist 加权 |
| **OCR 变体** | 学名 OCR 容错（u↔b, i↔l, n↔m） |
| **引用回溯** | 从中文论文提取英文参考文献，弥合语言鸿沟 |
| **结果去重** | 按 DOI 精确去重，按标题模糊去重 |
| **DirectLoader** | `importlib` 零进程加载，无 MCP 开销 |

---

## 📁 项目结构

```
cognitive-search-engine/
├── src/
│   ├── search_coordinator.py   ← 搜索编排
│   ├── unified_search.py       ← 统一搜索入口
│   └── search_api.py           ← API 层
├── scripts/
│   └── search_api.py           ← CLI 入口
└── config/
    └── evolution.yaml          ← 自适应参数
```---------|:--------:|:--------|
| [fish-ecology-assistant](../fish-ecology-assistant/) | V0 | 📦 知识供给 |
| [cognitive-search-engine](../cognitive-search-engine/) | V1 | 🔍 搜索验证 |
| [eon-core](../eon-core/) | Coord | ⚙️ 协调内核 |
| [porpoise-agent](../porpoise-agent/) | P₁ | 🐬 江豚专研 |
| [coilia-agent](../coilia-agent/) | P₂ | 🐟 刀鲚专研 |
| [culter-agent](../culter-agent/) | P₃ | 🐟 鲌类专研 |
| [conflict-arbiter](../conflict-arbiter/) | C | 🔥 冲突仲裁 |

---
---


## 🔗 生态体系

> 🔥 和则无穷力量，分则顶尖专家引擎。

本项目是「三生万物」生态的 V1。

`
三角核心 (sealed 3):
  📦 fish-ecology-assistant    → 知识供给 (V0)
  🔍 cognitive-search-engine   → 搜索验证 (V1)
  ⚙️ eon-core                  → 协调内核 (Coord)

万物衍生 (open N):
  🐬 porpoise-agent    → 江豚专研 (P₁)
  🐟 coilia-agent      → 刀鲚专研 (P₂)
  🐟 culter-agent      → 鲌类专研 (P₃)
  🔥 conflict-arbiter  → 冲突仲裁 (C)
`
> 🌊 万物皆变 · Panta Rhei
>
> 🏛️ 赫拉克利特说：人不能两次踏进同一条河流。
>
> 💻 我们说：你也不能用昨天的搜索回答今天的问题。
>
> **📅 最后更新: 2026-06-17 · 🖥️ Reasonix Code · ⚡ DeepSeek 驱动**

[⬆ 回到顶部](#)
