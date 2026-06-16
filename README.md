# Cognitive Search Engine 🔍

**多源并行文献搜索引擎** — 7 引擎并行 + 图谱遍历 + 可信度评分 + 分类学变体。

[变更日志](CHANGELOG.md)

---

## 项目简介

Cognitive Search Engine 是 eon-workspace 生态系统的 **V/V1 搜索验证层**，为 fish-ecology-assistant 提供全量文献搜索和可信度验证。

### 核心能力

| 能力 | 说明 |
|------|------|
| 🔍 **多源并行搜索** | PubMed · Europe PMC · Crossref · OpenAlex · CNKI · 万方 · Google Scholar |
| 📊 **可信度评分** | 期刊白名单 + 引用量 → 0–100 评分 + 掠夺性期刊检测 |
| 🧬 **分类学变体** | OCR 拼写纠错 · 同义名展开 · 属名变更追踪 |
| 📈 **知识图谱** | 48 物种 / 176 篇论文的结构化图谱 |
| 🔗 **跨项目协作** | 接收 fish-ecology-assistant 委托搜索 → 评分 + 分类反馈回写 |

---

## 安装

```bash
pip install pyyaml
```

---

## 快速开始

### CLI 搜索

```bash
# 基本搜索
python scripts/search_api.py --species "Ochetobius elongatus"

# 指定结果数
python scripts/search_api.py --species "珠星三块鱼" --max 10

# 仅分类学检查（不搜索）
python scripts/search_api.py --species "鳤" --taxonomy-only

# JSON 输出
python scripts/search_api.py --species "Acipenser sinensis" --format json
```

### Python API

```python
from src.search_engine import CognitiveSearchEngine
from src.credibility_scorer import score_papers, format_credibility

# 搜索引擎
engine = CognitiveSearchEngine()
print(engine.health())  # {'project': 'cognitive-search-engine', 'status': 'HEALTHY'}

# 可信度评分
papers = [
    {"title": "长江鱼类群落研究", "journal": "水生生物学报", "citation_count": 15},
    {"title": "Fish diversity in Yangtze", "journal": "Scientific Reports", "citation_count": 42},
]

scored = score_papers(papers)
for p in scored:
    print(f"{p['credibility_score']:3d} | {format_credibility(p['credibility_score'])} | {p['title'][:50]}")
```

---

## 核心功能

### 1. 搜索管线（search_api.py）

```bash
python scripts/search_api.py --species "Pseudaspius hakonensis"
```

**输出结构：**
```json
{
  "status": "ok",
  "species": {
    "query": "Pseudaspius hakonensis",
    "scientific": "Tribolodon brandti",
    "chinese": "珠星三块鱼",
    "family": "鲤科",
    "variants": ["Tribolodon brandti", "Pseudaspius hakonensis", "珠星三块鱼"]
  },
  "taxonomy_discrepancy": null,
  "papers": [{ "doi": "...", "title": "...", "year": 2024, "journal": "..." }],
  "stats": { "total_raw": 45, "total_merged": 32, "elapsed_s": 2.3 }
}
```

**搜索管线流程：**
1. 分类学检查 → 获取所有变体（OCR 纠错 + 同义名）
2. 跨项目不一致检测（与 fish-ecology-assistant 比对）
3. 并行 HTTP 搜索（PubMed + Europe PMC + Crossref + OpenAlex + CN）
4. DOI 去重 + 学科分类 + 语言标注

### 2. 可信度评分

```python
from src.credibility_scorer import score_paper, score_papers, detect_journal_tier, is_predatory

# 单篇评分
score = score_paper({"journal": "Nature", "citation_count": 100})
print(score)  # 55

# 期刊分级
tier = detect_journal_tier("水生生物学报")  # "core"
print(is_predatory("WASET Journal"))       # True
```

**评分规则：**

| 期刊 | 分数 | 分级 |
|------|:---:|:---:|
| Nature / Science / PNAS | 45–50 | top |
| BMC Biology / Scientific Reports / PLOS ONE | 30 | core |
| 水生生物学报 / 水产学报 / 中国水产科学 | 25 | core |
| 普通期刊 | 10 | standard |
| 掠夺性期刊 | — | 标记预警 |

引用量加成：>50 引用 +5，>20 引用 +3，>5 引用 +1。

### 3. CNKI 学术搜索

```bash
python scripts/cnki_xue_search.py "鳤 遗传多样性"
```

### 4. 报告格式化

```python
from src.report_formatter import format_search_report

report = format_search_report(papers, species_name="Ochetobius elongatus")
print(report)  # 结构化文本报告
```

### 5. 知识图谱

```bash
# 查询物种在图谱中的论文
python -c "
import yaml
with open('config/species_graph.yaml', encoding='utf-8') as f:
    graph = yaml.safe_load(f)
papers = [p for p in graph['graph']['papers'] if 'ochetobius_elongatus' in p.get('species', [])]
print(f'{len(papers)} papers')
"
```

---

## 项目结构

```
cognitive-search-engine/
├── src/                          # 源代码
│   ├── __init__.py               # 公共 API（版本 3.2.0）
│   ├── search_engine.py          # CognitiveSearchEngine — 搜索编排器
│   ├── credibility_scorer.py     # 论文可信度评分 + 期刊分级 + 掠夺性检测
│   ├── search_coordinator.py     # 搜索协调器（96 行）
│   ├── world_model.py            # 世界模型（102 行）
│   ├── agent_core.py             # Agent 核心逻辑
│   ├── report_formatter.py       # 报告格式化（507 行）
│   └── _utils.py                 # 内部工具
│
├── scripts/                      # CLI 工具
│   ├── search_api.py             # 搜索 API（289 行，供 f 项目调用）
│   └── cnki_xue_search.py        # CNKI 学术搜索（256 行）
│
├── config/                       # 配置
│   ├── species_graph.yaml        # 物种知识图谱（48 种 / 176 篇）
│   ├── agent.yaml                # Agent 行为配置
│   ├── engine_registry.yaml      # 搜索引擎注册表
│   ├── component_registry.yaml   # 组件注册表
│   ├── search_rules.yaml         # 搜索规则
│   ├── evolution.yaml            # 自进化参数
│   └── stv_protocol.yaml         # S-T-V 三角协议
│
├── config/                       # 部分恢复（.py.partial）
│   ├── adapter.py.partial        # 适配器代码片段
│   ├── mcp_client.py.partial     # MCP 客户端片段
│   ├── meso_agent.py.partial     # Meso Agent 片段
│   ├── unified_search.py.partial # 统一搜索片段
│   ├── rule_engine.py.partial    # 规则引擎片段
│   └── catalog_loader.py.partial # 目录加载器片段
│
├── tests/                        # 测试
│   └── test_configs.py           # 配置文件测试
│
├── skills/                       # Reasonix 技能
│   ├── graph-search-engine.md    # 图谱搜索
│   ├── cognitive-species-search.md # 认知物种搜索
│   └── self-evolve.md            # 自进化
│
├── docs/                         # 文档
│   ├── STV_TRIANGLE_ARCHITECTURE.md
│   ├── UNIFIED_EVOLUTION.md
│   ├── UNIFIED_SEARCH_PROTOCOL.md
│   └── DIMENSIONAL_EVOLUTION.md
│
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 配置文件说明

### `config/species_graph.yaml`

物种知识图谱，包含 48 种鱼类和 176 篇论文的结构化数据：

```yaml
graph:
  species:
    - id: ochetobius_elongatus
      name: "Ochetobius elongatus"
      chinese: "鳤"
      family: "鲤科"
      aliases: ["Ochetobibus elongatus"]
      variants: ["Ochetobius elongates"]
  papers:
    - doi: "10.3390/ani15010001"
      title: "..."
      species: ["ochetobius_elongatus"]
      year: 2026
      journal: "Animals"
```

### `config/engine_registry.yaml`

```yaml
engines:
  pubmed:    { priority: 1 }
  crossref:  { priority: 2 }
  openalex:  { priority: 3 }
  cnki:      { priority: 2 }
```

---

## 跨项目角色

本系统为 Triangle Core 的 **V/V1（搜索验证层）**：

```
fish-ecology-assistant (S/V0 知识供给)
        ↓ 委托搜索
cognitive-search-engine (V/V1 搜索验证)  ← 本项目
        ↓ 可信度评分 + 分类反馈
fish-ecology-assistant (知识库回写)
```

---

## 许可证

MIT License © 2026 fangtaocai041
