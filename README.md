<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
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

# Python 依赖
pip install pyyaml
```

### 验证安装

```python
# 验证 adapter 加载
from src.adapter import CognitiveSearchAdapter
adapter = CognitiveSearchAdapter()
print(adapter.info())

# 验证图谱加载
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

三阶段协议：

```python
from src.unified_search import coordinated_search

# 全量搜索（自动选择模式）
result = coordinated_search("Pseudaspius hakonensis", mode="adaptive")
# mode: "adaptive" | "exhaustive" | "classified" | "satisficing"

print(f"总命中: {result.total_raw}")
print(f"去重后: {result.total_merged}")
```

搜索模式选择逻辑：

```
文献量 < 20  → 穷举模式（Hub-and-Spoke 全方向展开，100% recall）
文献量 20-200 → 分类归纳模式（先搜综述 → 分类计数 → 用户选方向展开）
文献量 > 200 → 大规模模式（仅输出分类概览，每方向精选 5-8 篇）
```

### 3. 权威可信度评分

```python
from scripts.credibility_scorer import score_papers

papers = [
    {"title": "Paper A", "journal": "水生生物学报", "year": 2024},
    {"title": "Paper B", "journal": "Scientific Reports", "year": 2023},
]
scored = score_papers(papers)

for p in scored:
    print(f"{p['_credibility_flag']} {p['_credibility_score']:3d} | {p['title'][:40]}")
```

评分公式：

```
credibility = 50 + 30(SCI) + 25(CSCD核心) + 10(DOI) + 10(PMID)
              - 30(预印本) - 100(掠夺性期刊)
评分范围: 0–100
🟢 ≥80 高 | 🟡 60-79 中 | 🟠 40-59 低 | 🔴 <40 不可信
```

### 4. 知识图谱（KB-First）两阶段搜索

```python
from src.search_coordinator import kb_first, continue_full_search

# Stage 1: 查 f项目知识库（无外部 API 调用）
result = kb_first("珠星三块鱼")
print(f"KB命中: {result.kb_found}")

# Stage 2: 全量搜索
result = continue_full_search(result, group="full")
print(f"总论文: {result.full_search.total_papers}")
```

### 5. OCR 拼写变体生成

```python
from src.variant_generator import generate_variants

variants = generate_variants("Ochetobius")
# → ["Ochetobius", "Ochetobibus", "Ocheotbius", "Ochetobiu", ...]
# 覆盖 OCR 常见混淆：u↔b, i↔l, n↔m 等
```

### 6. 自进化反馈

```python
from src.evolution_executor import record_search, get_evolution_history

record_search("tribolodon_brandti", {
    "mode": "satisficing",
    "papers_found": 18,
    "new_to_graph": 3,
    "elapsed_sec": 45,
})

history = get_evolution_history()
print(f"已记录 {len(history)} 次搜索")
```

---

## API 参考

### `src/meso_agent.py` — 中宇宙协调

| 函数/类 | 说明 |
|---------|------|
| `create_agent(mode)` | 创建搜索 agent（http / direct 模式） |
| `agent.search(species_id)` | 执行全量物种搜索 |
| `agent.search_with_kb_first(query)` | KB 优先搜索入口 |

### `src/unified_search.py` — 统一搜索协议

| 函数 | 说明 |
|------|------|
| `coordinated_search(name, mode, group, limit)` | 协调多引擎搜索 |
| `search_with_kb_first(query)` | KB-First 两阶段搜索 |
| `continue_full_search(kb_result)` | 后续全量搜索 |
| `detect_taxonomy_discrepancy(name)` | 跨项目分类一致性检测 |

### `src/mcp_client.py` — MCP 客户端

| 函数/类 | 说明 |
|---------|------|
| `McpClient()` | 管理 7 个 MCP 搜索引擎的并行客户端 |
| `client.search(name)` | 并行调用所有可用搜索工具 |
| `client.prewarm()` | 后台预热 + 健康探测 |

### `src/rule_engine.py` — 搜索规则引擎

| 方法 | 说明 |
|------|------|
| `SearchRuleEngine(config_path)` | 从 YAML 加载 10 阶段搜索规则 |
| `engine.execute(species_id)` | 执行搜索阶段序列 |

### `src/adapter.py` — 跨项目协议

| 方法 | 说明 |
|------|------|
| `CognitiveSearchAdapter.search(name, mode)` | 搜索入口 |
| `adapter.health()` | 健康检查 |
| `adapter.info()` | 版本能力信息 |

### `scripts/credibility_scorer.py` — 可信度评分

| 函数 | 说明 |
|------|------|
| `score_papers(papers, species_name)` | 批量评分（0–100） |
| `score_paper(paper)` | 单篇评分 |
| `format_credibility(paper)` | 格式化评分输出 |
| `detect_journal_tier(journal)` | 检测期刊层级 |
| `is_predatory(journal)` | 检查是否掠夺性期刊 |

---

## 命令行工具

| 脚本 | 用途 | 示例 |
|------|------|------|
| `scripts/search_api.py` | 搜索 API | `python scripts/search_api.py --species "Ochetobius"` |
| `scripts/check_rules.py` | 检查规则配置 | `python scripts/check_rules.py` |
| `scripts/credibility_scorer.py` | 评分测试 | `python -c "from scripts.credibility_scorer import score_papers; ..."` |
| `scripts/test_integration.py` | 集成测试 | `python scripts/test_integration.py` |
| `scripts/test_robustness.py` | 鲁棒性测试 | `python scripts/test_robustness.py` |
| `scripts/validate_cross_project.py` | 跨项目验证 | `python scripts/validate_cross_project.py` |

---

## 项目架构

```
cognitive-search-engine/
├── README.md                       ← 本文件
├── README.zh.md                    ← 中文 README
├── LICENSE
│
├── config/                         ← 配置文件
│   ├── agent.yaml                  ← Agent 配置（版本、超时、重试）
│   ├── search_rules.yaml           ← 10 阶段搜索规则引擎
│   ├── mcp_servers.yaml            ← MCP 服务器定义
│   ├── tools.json                  ← JSON Schema 工具定义
│   ├── species_graph.yaml          ← 预建物种知识图谱
│   ├── database_catalog.yaml       ← 65 个数据库目录（8 领域 4 层级）
│   ├── engine_registry.yaml        ← 引擎注册表
│   ├── component_registry.yaml     ← 组件生命周期
│   ├── evolution.yaml              ← 自进化参数
│   ├── stv_protocol.yaml           ← 跨项目协议
│   └── cnki_cookies.json           ← CNKI 登录态
│
├── src/                            ← Python 源码包
│   ├── adapter.py                  ← CognitiveSearchAdapter（跨项目协议）
│   ├── agent_core.py               ← CognitiveAgent（BDI + ReAct 循环）
│   ├── meso_agent.py               ← MesoAgent（中宇宙协调层）
│   ├── unified_search.py           ← 统一搜索协议（搜索编排器）
│   ├── rule_engine.py              ← SearchRuleEngine（10 阶段规则执行）
│   ├── mcp_client.py               ← MCP 并行客户端（7 服务器管理）
│   ├── world_model.py              ← BDI WorldModel（信念/愿望/意图）
│   ├── memory_layer.py             ← MemorySystem（短期 + 长期记忆）
│   ├── graph_updater.py            ← 图谱持久化 + 反向索引
│   ├── variant_generator.py        ← OCR 拼写变体生成器
│   ├── parallel_search.py          ← 多查询并行执行器
│   ├── catalog_loader.py           ← 数据库目录 + 图谱路由器 + 涌现引擎
│   ├── evolution_executor.py       ← 自进化反馈执行器
│   ├── inference_engine.py         ← TAO 推理引擎
│   ├── validator.py                ← 跨项目独立性验证器
│   ├── report_formatter.py         ← 报告格式化
│   ├── arbiter.py                  ← 搜索结果仲裁
│   ├── conflict_adapter.py         ← 冲突仲裁适配器
│   └── search_streaming.py         ← 流式搜索
│
├── scripts/                        ← 可执行脚本
│   ├── search_api.py               ← 搜索 API 入口
│   ├── credibility_scorer.py       ← 可信度评分
│   ├── test_integration.py         ← 46 个集成测试
│   ├── test_robustness.py          ← 94 个鲁棒性测试
│   ├── validate_cross_project.py   ← 跨项目验证
│   ├── check_rules.py              ← 规则配置检查
│   └── run_all.py                  ← 全部测试运行
│
├── skills/                         ← Reasonix AI Skills
│
├── logs/                           ← 运行日志
└── tests/                          ← 测试套件
```

### 模块职责

| 模块 | 职责 | 关键类/函数 |
|------|------|-------------|
| `src/meso_agent.py` | 中宇宙协调层 | `MesoAgent`, `create_agent()` |
| `src/unified_search.py` | 搜索编排 | `coordinated_search()`, `search_with_kb_first()` |
| `src/agent_core.py` | BDI 认知循环 | `CognitiveAgent` |
| `src/rule_engine.py` | 搜索规则执行 | `SearchRuleEngine` |
| `src/mcp_client.py` | MCP 服务器管理 | `McpClient` |
| `src/world_model.py` | BDI 世界模型 | `WorldModel` |
| `src/variant_generator.py` | OCR 变体 | `generate_variants()` |

---

## 配置文件说明

### `config/agent.yaml`

```yaml
timeout:
  http_retry_max_s: 60
  http_retry_attempts: 5
  http_per_call_timeout_s: 15
  mcp_parallel_timeout_s: 180
  mcp_parallel_max_workers: 7
```

### `config/search_rules.yaml`

10 阶段搜索规则引擎，每阶段定义搜索工具、查询模板和停止条件：

```yaml
phases:
  - id: phase1_graph_lookup
    function: graph_lookup
    tools: []
    stop_if: papers_found > 0

  - id: phase2_exact_search
    function: exact_search
    tools: [scholar_search, ncbi_esearch]
    stop_condition: diminishing_returns
```

---

## 搜索引擎一览

| 引擎 | 用途 | 模糊匹配 |
|------|------|:--------:|
| Google Scholar | 主力学术搜索 | ✅✅✅ |
| Europe PMC + PubMed | 生物医学文献 | ✅ |
| OpenAlex + Semantic Scholar | 跨学科学术搜索 | ✅✅ |
| SerpAPI Baidu | 百度学术（突破反爬） | ✅ |
| SerpAPI Scholar | Google Scholar 增强 | ✅✅ |
| SerpAPI DuckDuckGo | 通用搜索兜底 | ✅ |
| Exa | 语义级网络搜索 | ✅✅ |
| Tavily | AI 深度搜索 | ✅✅ |
| CrossRef | DOI 元数据解析 | ✅ |
| NCBI E-utilities | PubMed 直接查询 | ✅ |

---

## 多项目协作

```python
from src.adapter import CognitiveSearchAdapter

adapter = CognitiveSearchAdapter()
print(adapter.health())

# 跨项目搜索
result = adapter.search("珠星三块鱼", mode="adaptive")

# 跨项目委托
adapter.delegate_to("fish-ecology-assistant", "提供鳤的KB数据")
```

| 关联项目 | 角色 | 依赖关系 |
|---------|:----:|---------|
| fish-ecology-assistant | S/V0 知识供给 | 提供 KB 数据，本引擎查询 |
| eon-core | 协调器 | 提供 DAG 路由 |
| porpoise-agent | P₁ 江豚 | 本引擎提供文献搜索结果 |
| coilia-agent | P₂ 刀鲚 | 本引擎提供文献搜索结果 |

---

## 贡献指南

- Python 遵循 PEP 8
- 新引擎需在 `config/engine_registry.yaml` 注册
- 新增搜索规则需在 `config/search_rules.yaml` 添加阶段
- 所有公开 API 需 docstring + 类型注解

```bash
# 运行测试
python scripts/run_all.py

# 检查规则配置
python scripts/check_rules.py
```

---

## 许可证

MIT License © 2026 fangtaocai041

---

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)。
