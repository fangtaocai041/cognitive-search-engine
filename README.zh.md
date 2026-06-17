![Python 3.10+](https://img.shields.io/badge/Python%203.10%2B-3776AB?style=flat-square)
  ![MIT](https://img.shields.io/badge/MIT-34D058?style=flat-square)
  ![v5.4.0](https://img.shields.io/badge/v5.4.0-8A4FCE?style=flat-square)
  ![15+ engines](https://img.shields.io/badge/15%2B%20引擎-007EC6?style=flat-square)
  ![7 MCP](https://img.shields.io/badge/7%20MCP-FE7D37?style=flat-square)
  ![5 skills](https://img.shields.io/badge/5%20技能-D73A4A?style=flat-square)
  ![140 tests](https://img.shields.io/badge/140%20测试-0EA5E9?style=flat-square)
  ![Thompson](https://img.shields.io/badge/Thompson-EC4899?style=flat-square)
  ![PID control](https://img.shields.io/badge/PID%20控制-F59E0B?style=flat-square)
  ![CN/EN](https://img.shields.io/badge/中英双语-6B7280?style=flat-square)
</p>

[English](README.md) · [中文](README.zh.md)

<div align="center"><h3>🌊 万物皆流。</h3></div>

世界是动态的，知识是暂时的，涌现是常态。

---

## 📖 目录

- [哲学](#-哲学)
- [快速开始](#-快速开始)
- [架构](#-架构)
- [功能特性](#-功能特性)
- [独特创新](#-独特创新)
- [项目结构](#-项目结构)
- [版本历史](#-版本历史)
- [自我评估](#-自我评估)
- [生态体系](#-生态体系)

---

## 🏛️ 哲学

> 万象流转，真知若寄，涌现成章。

此非口号。乃贯穿每一行代码、每一次检索、每一份分析之操作系统。

这是三生万物 S-T-V-P₁-P₂ 五体架构中的**搜索验证核心（V/V1）**，由 **eon-core** 统一协调。S（知识）提出主张，V（验证）负责检验——通过多源并行搜索、跨项目比对、三角验证评分，确保每一条写入系统的知识都经过 ≥3 个独立来源的检验。

### 📜 三谛

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

---

## 🧩 这个项目是什么

一个搜索验证引擎。不存储知识，而是验证知识。

当 S 层说"鳤的科是鲤科"，V 层会去问 PubMed、Crossref、中文期刊、Google Scholar——它们都这么说吗？有没有不一致？如果有，谁是对的？

> 赫拉克利特说：人不能两次踏进同一条河流。
>
> 我们说：你也不能用昨天的搜索回答今天的问题。

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

### S-T-V-P₁-P₂ 角色

```
S-T-V-P₁-P₂ 架构（由 eon-core 协调）：

  S/V0  fish-ecology-assistant    → 知识供给
  V/V1  cognitive-search-engine   → 搜索验证 ← 本项目
  Coord  eon-core                  → 协调内核
```

### 内部架构

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
  ├── agent_judge.py         LLM裁判四维结果评估
  ├── inference_engine.py    搜索后缺口+矛盾检测（TAO启发）
  ├── evolution_executor.py  7触发器自进化（矛盾驱动）
  ├── variant_generator.py   OCR学名变体安全网
  └── adapter.py             IProjectAdapter + verify_claims() 方法
  config/
  ├── coordination.yaml      跨项目协调配置（生态共享）
  ├── evolution.yaml         自进化参数 + 反馈循环
  └── taiji.yaml             DAG 拓扑定义
  tests/
  ├── test_validator.py           信任评分测试
  ├── test_variant_generator.py   变体生成测试
  ├── test_credibility_scorer.py  可信度评分测试
  ├── test_unified_search.py      统一搜索测试
  ├── test_world_model.py         MPC 世界模型测试
  ├── test_configs.py             配置加载测试
  ├── test_imports.py             导入链测试
  └── test_search_integration.py  搜索集成测试
```

---

## ✨ 功能特性

| 功能 | 状态 | 说明 |
|------|:--:|------|
| 🧠 BDI MesoAgent | ✅ | Belief→Desire→Intention 自适应循环 |
| 🌐 15+ 数据源 | ✅ | PubMed, Crossref, OpenAlex, CNKI, 万方, 百度学术... |
| ⚡ 异步搜索 | ✅ | aiohttp, 3-5x 加速 |
| 🎯 Thompson 采样 | ✅ | 学习型多臂老虎机引擎选择 |
| 📊 PID 限速器 | ✅ | 自适应 API 速率控制 |
| 🎛️ MPC 世界模型 | ✅ | 搜索成本优化 |
| ⚖️ Agent 裁判 | ✅ | LLM 四维评估 |
| ✅ 5级信任 | ✅ | DOI→PMID→物种→作者→期刊 层级评分 |
| 🔍 OCR 变体 | ✅ | 系统化学名变体安全网 |
| 🌊 中英双通道 | ✅ | 中英文文献分路由 |
| 🔄 自进化 | ✅ | 7 触发器参数自适应（矛盾驱动） |
| 🧠 推理引擎 | ✅ | 搜索后缺口分析 + 矛盾检测（TAO） |
| 🎯 verify_claims() | ✅ | IProjectAdapter 跨项目声明验证 |
| 🐛 错误日志 | ✅ | 修复 25+ 静默吞错 |
| 🧪 测试套件 | ✅ | 8 个测试文件，140 项测试通过 |

---

## 💡 独特创新

### 1. Hub-and-Spoke 搜索架构
所有搜索请求通过本引擎作为单一网关路由。衍生项目（P₁、P₂、P₃）调用 cognitive-search-engine——从不直接访问原始 API。

### 2. 权威评分（5 级信任）
```
DOI 匹配 > PMID 匹配 > 物种名匹配 > 作者匹配 > 期刊匹配
```
每个结果获得加权信任分。跨源不一致触发更深层验证。

### 3. OCR 变体安全网
`variant_generator.py` 系统生成 OCR 易错的学名变体（如 *Coilia nasus* → *Coilia nasus*, *Coilia nasus*, *Collia nasus*），捕获扫描错误的文献。

### 4. 分类知识图谱（懒加载）
物种分类关系按需加载，从不预缓存。图谱随新物种关系发现而进化。

### 5. 五学科认知引擎
每个搜索类别（分类学、生态学、遗传学、保护学、形态学）拥有自己的调优认知引擎，使用学科特定的相关性评分。

---

## 📁 项目结构

```
cognitive-search-engine/
  （见上方架构图）
```

---

## 📜 版本历史

| 版本 | 日期 | 重要更新 |
|------|------|----------|
| **v5.4.0** | 2026-06-17 | validator.py 5级信任，evolution_executor 7触发器，矛盾驱动进化 |
| v5.3.0 | 2026-06-12 | inference_engine 缺口+矛盾检测，TAO 启发推理 |
| v5.2.2 | 2026-06-09 | 修复 25+ 静默吞错，错误日志基础设施 |
| v5.2.1 | 2026-06-07 | MPC 世界模型搜索成本优化 |
| v5.2.0 | 2026-06-06 | Thompson 采样引擎选择器，PID 自适应限速器 |
| v5.1.0 | 2026-06-05 | AsyncParallelSearch (aiohttp)，3-5x 速度提升 |
| v5.0.0 | 2026-06-01 | BDI MesoAgent，15+ 数据源，统一搜索模式 |

---

## 🪞 自我评估

### 优势
- **验证优先**：每条声明经过 ≥3 个独立来源验证
- **引擎多样性**：15+ 数据源覆盖西方（PubMed/Crossref）和中国（CNKI/万方）学术数据库
- **自愈能力**：PID 限速器防 API 滥用；OCR 变体捕获扫描错误
- **矛盾感知**：inference_engine 主动搜寻分歧，而非仅确认
- **跨项目集成**：verify_claims() 使任何衍生项目可调用完整搜索武器库进行验证

### 当前局限
- 部分中文学术 API（CNKI、万方）访问不稳定
- Thompson 采样冷启动需约 50 次查询/引擎才能收敛
- MPC 世界模型假设线性成本函数（当前规模足够）
- 尚无流式搜索（仅批量模式）

### 路线图
- [ ] 流式搜索与渐进式结果交付
- [ ] 贝叶斯真言血清多评估者声明验证
- [ ] 自动撤稿监控集成
- [ ] 图神经网络物种共现预测

---

## 🔗 生态体系

本项目是「三生万物」生态的 **搜索验证核心（V/V1）**。

```
S-T-V-P₁-P₂ 架构（由 eon-core 协调）：

  S/V0  📦 fish-ecology-assistant    → 知识供给
  V/V1  🔍 cognitive-search-engine   → 搜索验证 ← 本项目
  Coord ⚙️ eon-core                  → 协调内核

  衍生项目：
    P₁  🐬 porpoise-agent    → 江豚领域专家
    P₂  🐟 coilia-agent      → 刀鲚领域专家
    P₃  🐟 culter-agent      → 鲌类领域专家
    C   🔥 conflict-arbiter  → 冲突仲裁
```

> 🔥 和则无穷力量，分则顶尖专家引擎。

---

🌱 **万物皆变 · Panta Rhei**

> 赫拉克利特说：人不能两次踏进同一条河流。
>
> 我们说：你也不能用上个月的代码分析今天的生态数据。

这个项目不是一套固定的工具集——它是一个**活的系统**。每个组件都内置了过期机制、版本追踪和涌现感知。随着你的研究深入、R包更新、新方法涌现，它会和你一起进化。

*最后更新：2026-06-20　|　适用环境：Reasonix Code · DeepSeek 驱动*
