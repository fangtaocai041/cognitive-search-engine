<p align="center">
  🇬🇧 <a href="README.md">English</a>
</p>

<div align="center">
  <h1>🕸️ Cognitive Search Engine v5</h1>
  <p><strong>多引擎物种文献搜索验证引擎</strong> — BDI + ReAct + 权威评分 + Hub-and-Spoke 图谱搜索</p>
  <p>Python 3.10+ · 21 引擎 · 5 层架构 · Triangle Core V/V1 层</p>
</div>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-5.8.0-8b5cf6" alt="v5.8.0"></a>
  <a href="#"><img src="https://img.shields.io/badge/engines-21-f59e0b" alt="21 engines"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/changelog-v5.8.0-22c55e" alt="Changelog"></a>
</p>

---

## 目录

- [项目简介](#项目简介)
- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [API 参考](#api-参考)
- [命令行工具](#命令行工具)
- [项目架构](#项目架构)
- [配置文件说明](#配置文件说明)
- [搜索引擎一览](#搜索引擎一览)
- [多项目协作](#多项目协作)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

**Cognitive Search Engine** 是一个面向物种文献的多引擎搜索验证引擎，作为 [eon-core](https://github.com/fangtaocai041/eon-core) 生态系统的 **V/V1 搜索验证层**（三角核心成员）运行。

### 核心能力

| 能力 | 说明 |
|------|------|
| 🔍 **21 引擎并行搜索** | Google Scholar + PubMed + CNKI + 万方 + 百度学术 + Exa + Tavily 等 |
| 🧠 **BDI + ReAct 认知架构** | Belief-Desire-Intention 推理循环，自适应停止 |
| ⭐ **权威可信度评分** | 0–100 分：SCI/CSCD 加权，掠夺性期刊排除 |
| 🔗 **Hub-and-Spoke 图谱搜索** | 多方向 Hub 定位 → 引用轮辐 → 分类图谱 |
| 🔤 **OCR 拼写变体安全网** | 自动生成拉丁名 OCR 常见错误变体 |
| 🌐 **中文三层搜索** | 百度学术→CNKI→万方→中科院，SerpAPI 突破反爬 |
| 🔄 **知识图谱持久化** | 搜索成果写回 `species_graph.yaml`，跨项目共享 |

### 生态系统角色

```
三角核心（密闭三元组）
├── S/V0  fish-ecology-assistant  ← 知识供给
├── V/V1  cognitive-search-engine  ← 本项目：搜索验证
└──         eon-core              ← 协调内核
```

---

## 快速开始

### 安装

```bash
git clone https://github.com/fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine
pip install pyyaml
```

### 验证安装

```python
from src.adapter import CognitiveSearchAdapter
adapter = CognitiveSearchAdapter()
print(adapter.info())
```

```bash
python -c "
import yaml
from pathlib import Path
graph = yaml.safe_load(Path('config/species_graph.yaml').read_text())
print(f'图谱中物种数: {len(graph[\"graph\"][\"species\"])}')
print(f'图谱中论文数: {len(graph[\"graph\"][\"papers\"])}')
"
```

---

## 核心功能

### 1. 多引擎并行搜索

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")

print(f"论文数: {len(result.papers)}, 耗时: {result.elapsed_sec}s")
print(f"新增图谱: {result.new_papers}")
print(f"停止原因: {result.stop_reason}")
```

### 2. Hub-and-Spoke 图谱搜索

```python
from src.unified_search import coordinated_search

result = coordinated_search("Pseudaspius hakonensis", mode="adaptive")
print(f"总命中: {result.total_raw}")
print(f"去重后: {result.total_merged}")
```

搜索模式选择逻辑：

```
文献量 < 20   → 穷举模式（全方向展开，100% recall）
文献量 20-200  → 分类归纳模式（先搜综述 → 分类计数 → 按需展开）
文献量 > 200  → 大规模模式（仅概览，精选 5-8 篇/方向）
```

### 3. 权威可信度评分

```python
from scripts.credibility_scorer import score_papers

papers = [
    {"title": "长江鱼类研究", "journal": "水生生物学报", "year": 2024},
    {"title": "Fish diversity", "journal": "Scientific Reports", "year": 2023},
]
scored = score_papers(papers)

for p in scored:
    flag = p["_credibility_flag"]      # 🟢 🟡 🟠 🔴
    label = p["_credibility_label"]    # 高 / 中 / 低 / 不可用
    score = p["_credibility_score"]    # 0–100
    print(f"{flag} {score:3d} | {p['title'][:40]}")
```

评分标准：

| 评级 | 分数范围 | 标识 |
|:----:|:--------:|:----:|
| 高 | 80–100 | 🟢 SCI Q1/Q2 或 CSCD 核心 |
| 中 | 60–79 | 🟡 一般 SCI 或统计源 |
| 低 | 40–59 | 🟠 普通期刊 |
| 不可用 | 0–39 | 🔴 掠夺性/无来源 |

### 4-6 其余功能详见英文版

---

## API 参考

| 模块 | 关键类/函数 | 说明 |
|------|-------------|------|
| `src/meso_agent.py` | `create_agent()`, `MesoAgent.search()` | 中宇宙协调入口 |
| `src/unified_search.py` | `coordinated_search()`, `search_with_kb_first()` | 搜索编排 |
| `src/mcp_client.py` | `McpClient` | MCP 并行客户端 |
| `src/rule_engine.py` | `SearchRuleEngine.execute()` | 搜索规则引擎 |
| `src/adapter.py` | `CognitiveSearchAdapter` | 跨项目协议 |
| `scripts/credibility_scorer.py` | `score_papers()`, `score_paper()` | 可信度评分 |

---

## 项目架构

```
cognitive-search-engine/
├── README.md / README.zh.md       ← 文档
├── config/                        ← 11 个配置文件
│   ├── agent.yaml                 ← 超时/重试
│   ├── search_rules.yaml          ← 10 阶段搜索规则
│   ├── mcp_servers.yaml           ← MCP 定义
│   ├── species_graph.yaml         ← 知识图谱
│   ├── database_catalog.yaml      ← 65 数据库目录
│   └── evolution.yaml             ← 自进化参数
│
├── src/                           ← 20+ 模块
│   ├── adapter.py                 ← 跨项目协议
│   ├── meso_agent.py              ← 中宇宙协调层
│   ├── unified_search.py          ← 搜索编排器
│   ├── agent_core.py              ← BDI + ReAct 循环
│   ├── rule_engine.py             ← 规则引擎
│   ├── mcp_client.py              ← MCP 客户端
│   └── ...（13 个更多模块）
│
├── scripts/                       ← 可执行脚本
│   ├── search_api.py              ← 搜索 API
│   ├── credibility_scorer.py      ← 评分
│   ├── test_integration.py        ← 集成测试
│   └── test_robustness.py         ← 鲁棒性测试
│
├── skills/                        ← Reasonix Skills
└── logs/                          ← 运行日志
```

---

## 配置文件说明

### `config/agent.yaml` — 超时配置

```yaml
timeout:
  http_retry_max_s: 60           # HTTP 重试总窗口
  http_retry_attempts: 5         # 最多重试 5 次
  http_per_call_timeout_s: 15    # 单次请求超时
  mcp_parallel_timeout_s: 180    # MCP 并行总超时
```

### `config/search_rules.yaml` — 搜索阶段定义

```yaml
phases:
  - id: phase1_graph_lookup
    function: graph_lookup
    stop_if: papers_found > 0

  - id: phase2_exact_search
    function: exact_search
    tools: [scholar_search, ncbi_esearch]
    stop_condition: diminishing_returns
```

---

## 搜索引擎一览

| 引擎 | 用途 |
|------|------|
| Google Scholar | 主力学术搜索 |
| Europe PMC + PubMed | 生物医学文献 |
| OpenAlex + Semantic Scholar | 跨学科学术 |
| SerpAPI (Baidu/Scholar/DDG) | 中文+通用 |
| Exa | 语义搜索 |
| Tavily | AI 深度搜索 |
| CrossRef | DOI 元数据 |
| NCBI E-utilities | PubMed 直接查询 |

---

## 多项目协作

```python
from src.adapter import CognitiveSearchAdapter

adapter = CognitiveSearchAdapter()
result = adapter.search("珠星三块鱼", mode="adaptive")
```

| 关联项目 | 角色 | 关系 |
|---------|:----:|------|
| fish-ecology-assistant | S/V0 | 提供 KB 数据 |
| eon-core | 协调器 | DAG 路由 |
| porpoise-agent | P₁ | 消费本引擎搜索结果 |
| coilia-agent | P₂ | 消费本引擎搜索结果 |

---

## 贡献指南

- PEP 8 编码规范
- 新引擎注册到 `config/engine_registry.yaml`
- 新规则添加到 `config/search_rules.yaml`
- 公开 API 必须 docstring + 类型注解

```bash
python scripts/run_all.py        # 全部测试
python scripts/check_rules.py    # 规则检查
```

---

## 许可证

MIT License © 2026 fangtaocai041

---

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)。
