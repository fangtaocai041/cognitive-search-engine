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

## 🏛️ 哲学

> 世界是动态的，知识是暂时的，涌现是常态。

这是三角之 **V (V1)** — 搜索验证层。V0供给的知识在此经过多源并行搜索、可信度评分、源独立性检验。BDI认知架构 (Belief→Desire→Intention) 实时自适应搜索策略。

---

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
