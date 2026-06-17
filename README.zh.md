<p align="center">
  🇬🇧 <a href="README.md">English</a>
</p>

# 🕸️ 认知搜索引擎 v5

> **Meso-Cosmos Agent** — BDI + ReAct + 权威评分 + 中英文动态图谱 + 懒加载

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.4.0-8b5cf6)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-5-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-7-f59e0b)](config/mcp_servers.yaml)
[![Architecture](https://img.shields.io/badge/architecture-meso_cosmos-8b5cf6)](docs/ARCHITECTURE.md)
[![Multi-LLM](https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6)]()
[![BDI](https://img.shields.io/badge/BDI-ReAct-22c55e)]()
[![Authority Score](https://img.shields.io/badge/authority-scoring_0_100-ec4899)]()
[![Self-Evolve](https://img.shields.io/badge/self_evolve-feedback_loop-10b981)](skills/self-evolve.md)
[![Thompson](https://img.shields.io/badge/Thompson_Sampling-bandit-EC4899)]()
[![PID](https://img.shields.io/badge/PID_control-adaptive-F59E0B)]()

## 🧠 智能优化层

> 验证引擎集成三层优化：**DeepSeek 级效率**（MoE 门控 + KV 缓存）、**学者级置信度**（三法则统计停步）、**混沌增强探索**（Rössler 扰动 + 通配符发现）。
> 由 [eon-core](https://github.com/fangtaocai041/eon-core) 统一调度。

## 🔺 三角核心 + 衍生角色：**V/V1（验证）**

> 三生万物生态体系的一部分：三角核心（`S/V0`、`V/V1`、`Coord`）+ 衍生（`P₁`、`P₂`、`P₃`、`C`）。
> 验证搜索结果，权威可信度评分，跨项目独立性保障。
> **DirectLoader**：`importlib` 零 MCP 进程。**三角验证**：≥3 个来源，≥3 个独立项目。

## 📊 自我评价

| 维度 | 评分 | 说明 |
|------|:----:|------|
| 🎯 搜索精度 | ⭐⭐⭐⭐⭐ | Hub-and-Spoke + OCR 变体 + 可信度评分（0-100） |
| 🧠 认知架构 | ⭐⭐⭐⭐⭐ | BDI + ReAct 循环 + 矛盾驱动策略选择 |
| 📊 验证严谨 | ⭐⭐⭐⭐⭐ | `validator.py` 跨项目独立性保障 |
| 🔬 物种覆盖 | ⭐⭐⭐⭐ | 图谱中约 10 种，通过自动回写可扩展 |
| ⚡ 效率 | ⭐⭐⭐⭐⭐ | DirectLoader + MoE 门控 + Thompson 采样 |
| 🧪 测试覆盖 | ⭐⭐⭐⭐⭐ | 46 集成 + 94 鲁棒 = 140 测试 |

## 📋 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v5.4.0** | 2026-06-18 | 🆕 Thompson 采样多臂老虎机引擎选择器 + PID 自适应 API 限速器 + MPC 世界模型搜索成本优化 + LLM-as-Judge 四维评估 + validator.py 五级信任评分 + evolution_executor 7 触发矛盾驱动自进化 + AsyncParallelSearch（aiohttp，3-5 倍加速） |
| **v5.3.0** | 2026-06-12 | 🆕 inference_engine 空白与矛盾检测（TAO 启发）+ agent_judge.py LLM-as-Judge |
| **v5.2.2** | 2026-06-09 | validator.py 提取 + evolution_executor + paper_health_check + 修复 25+ 静默异常捕获 |
| **v5.2.1** | 2026-06-07 | 三角核心三角验证 + DirectLoader + Meso-Cosmos Agent v4.0 |
| **v5.2** | 2026-06-07 | Meso-Cosmos 协调层 + 中英文双语图谱 |
| **v5.1** | 2026-06-07 | Hub-and-Spoke 搜索 + 权威可信度评分 |
| **v5.0** | 2026-06-07 | BDI + ReAct 认知架构 |

> **最新**：v5.4.0 · 2026-06-18

> **核心优势**：从"字符串匹配"到"所指重建"——多条能指路径（精确、OCR 变体、作者网络、引用图谱、中文名）汇聚于同一所指（物种本身）。

## 🔗 关联项目

本引擎作为 git submodule 集成于：

| 项目 | 角色 | 说明 |
|------|:----:|------|
| [eon-core](https://github.com/fangtaocai041/eon-core) | **Coord** | 协调中枢 — EventBus · CAS · DAG 路由 · 6 项目拓扑 |
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | **S/V0**（知识供给） | 鱼类生态 · 21 MCP · 28 技能 · 长江 430 物种知识库 |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | **P₁**（衍生） | 江豚专研 · NBHF 声学 · 栖息地建模 |
| [coilia-agent](https://github.com/fangtaocai041/coilia-agent) | **P₂**（衍生） | 刀鲚专研 · 耳石微化学 · 洄游生态 |
| [culter-agent](https://github.com/fangtaocai041/culter-agent) | **P₃**（衍生） | 鲌类专研 · 营养生态 · 生长分析 |
| [conflict-arbiter](https://github.com/fangtaocai041/conflict-arbiter) | **C**（衍生） | 冲突仲裁 · 多源保护级别检测 |

> **协同进化**：引擎代码更新 → 衍生项目通过 submodule 自动受益。知识图谱进化 → 全项目共享。

## 🧠 核心创新

**不是字符串匹配——是认知重建。**

传统搜索匹配字符串。如果论文把"Ochetobius"错拼成"Ochetobibus"，就搜不到。
我们的引擎从多条**能指**路径同时重建**所指**（物种本身）：精确名、OCR 变体、作者网络、引用图谱、中文名汇聚于同一物种。

## 🏆 为什么这是最先进的物种搜索引擎

### vs 传统学术搜索

| 问题 | 传统搜索 | 认知搜索引擎 |
|------|---------|------------|
| 物种名拼写错误 | 搜不到 | OCR 变体扫描全覆盖 |
| 中文数据库盲区 | PubMed/Crossref 不索引知网万方 | 中文优先搜索 + 11 期刊站点 |
| 冷启动（新物种） | 零结果卡死 | Hub-and-Spoke 多方向 Hub 定位 |
| 综述论文盲信 | 静默引用错误归属 | 权威评分 0-100，SCI/核心期刊加权 |
| 搜索遗忘 | 重复搜索相同成本 | 分类知识图谱持久化，按需懒加载 |
| 一刀切深度 | 8 篇或 8000 篇同等投入 | 三模式：穷举(<20) / 分类(20-100) / 综述锚定(>100) |
| 无认知模型 | 纯字符串匹配 | 符号学 + 语言学 + 语音学 + 逻辑学 |

### vs AI 搜索

| 问题 | AI 搜索 | 认知搜索引擎 |
|------|--------|------------|
| 透明度 | 黑盒，无法验证完整性 | 三阶段 Hub-and-Spoke，每步可审计 |
| 成本 | 单次搜索高 token 消耗 | 懒加载知识图谱，约 60% 更少调用 |
| 领域知识 | 通用，无物种特定逻辑 | 拉丁语法、IPA、OCR 错误模型 |
| 来源权威 | 预印本与同行评审同等对待 | 可信度评分 0-100，掠食性期刊排除 |
| 引用图谱 | 未利用 | 多 Hub 引用辐条，分类图谱 |
| 学习能力 | 无状态，每次搜索独立 | 图谱随每次搜索增长 |

## 🆕 v5.4.0 新特性

| 特性 | 状态 | 说明 |
|------|:----:|------|
| 🧠 BDI MesoAgent | ✅ | Belief→Desire→Intention 自适应循环 |
| 🌐 15+ 数据源 | ✅ | PubMed、Crossref、OpenAlex、CNKI、万方、百度学术… |
| ⚡ 异步搜索 | ✅ | aiohttp AsyncParallelSearch，3-5 倍加速 |
| 🎯 Thompson 采样 | ✅ | 多臂老虎机引擎选择器 |
| 📊 PID 限速器 | ✅ | 自适应 API 速率控制 |
| 🎛️ MPC 世界模型 | ✅ | 搜索成本优化 |
| ⚖ Agent Judge | ✅ | LLM 四维评估 |
| 🔒 五级信任 | ✅ | DOI→PMID→物种→作者→期刊 层级 |
| 🔍 OCR 变体 | ✅ | 系统科学名变体安全网 |
| 🌊 中英文通道 | ✅ | 独立中英文文献路由 |
| 🔄 自进化 | ✅ | 7 触发矛盾驱动自适应参数 |
| 🧠 推理引擎 | ✅ | 搜索后空白分析 + 矛盾检测（TAO） |
| 🎯 verify_claims() | ✅ | IProjectAdapter 跨项目声明验证 |
| 🧪 测试套件 | ✅ | 8 测试文件，140 测试通过 |

## 🚀 快速开始

```bash
git clone https://github.com/fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine
```

添加到 Reasonix 项目：
```yaml
# 在项目的 config/agent.yaml 中
skills:
  skill_dir: "../cognitive-search-engine/skills"
```

或直接用 Python 运行：
```bash
python src/rule_engine.py
```

或作为 Skill 调用：
```
/skill graph-search-engine species="Ochetobius elongatus"
```

## 📋 README 变更记录

| 版本 | 日期 | 主题 | 变更内容 |
|:-----|:-----|:-----|:---------|
| **v7.1** | 2026-06-18 | README 恢复 | Meso-Cosmos 架构、Hub-and-Spoke 协议、权威评分公式、五大突破、工程语言 |
| **v5.4.0** | 2026-06-18 | 智能优化 | Thompson 采样、PID 限速、MPC 世界模型、异步搜索、LLM-as-Judge |
| **v5.3.0** | 2026-06-12 | TAO 推理 | inference_engine 空白与矛盾检测 |
| **v5.2.2** | 2026-06-09 | 错误基础设施 | 修复 25+ 静默异常 |
| **v5.2** | 2026-06-06 | Meso-Cosmos | MesoAgent、动态图谱 v2.0、中英文规则 |
| **v5.1** | 2026-06-06 | Hub-and-Spoke | 三阶段搜索、权威评分、综述优先策略 |
| **v5.0** | 2026-06-06 | 五层架构 | BDI WorldModel、CognitiveAgent |
| **v4.0** | 2026-06-06 | 图谱引擎 | 知识图谱遍历、12 搜索层 |

## 📜 License

MIT © 2026 fangtaocai041

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.

---

## 🌱 万物皆变 · Panta Rhei

> 赫拉克利特说：人不能两次踏进同一条河流。
>
> 我们说：知识会老去，但人类对世界的追问永不落幕。昨日之真理为今日之基石，今日之未知为明日之征途。我们的目光，从不囿于已知的疆界；我们的脚步，终将踏上那片星光璀璨的浩瀚征途。

这个项目不是一套固定的工具集——它是一个**活的系统**。每个组件都内置了过期机制、版本追踪和涌现感知。随着你的研究深入、R包更新、新方法涌现，它会和你一起进化。

*最后更新: 2026-06-18 | Reasonix Code · DeepSeek 驱动*
