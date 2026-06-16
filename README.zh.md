# 🕸️ Cognitive Search Engine

**它聪明地搜索物种文献，不遗漏一篇该看的论文，也不浪费一分钱搜无关的。**

[English](README.md) · [更新日志](CHANGELOG.md) · [怎么参与](CONTRIBUTING.md)

---

## 🔺 三角闭环角色: **V1 (验证)**

> **三角闭环 (V1/验证)**，由 [eon-core](https://github.com/fangtaocai041/eon-core) 协调。
> **三角闭环**: fish(V0知识库) + cognitive(V1验证) + eon-core(协调器) — 缺一不可
> **三生万物**: P₁(porpoise) · P₂(coilia) · 无限衍生
>
> 搜索验证、权威可信度评分、多重三角验证 (≥3源, ≥2项目独立验证)。
> **DirectLoader**: `importlib` 零 MCP 进程。**三角验证**: ≥3 来源, ≥2 独立项目。

---

## 这引擎能干嘛？

你输入一个物种名，它能：

1. **猜你要搜多少文献** — 先查 PubMed、Crossref、OpenAlex 估算文献量
2. **决定怎么搜** — 文献少就穷举，多就分类，太多了就综述锚定
3. **并行搜 21 个引擎** — SerpAPI·Exa·Europe PMC·NCBI·OpenAlex·Semantic Scholar·CNKI·更多
4. **去重打分** — 按期刊权威性给每篇论文打分（0~100）
5. **检测缺口** — 看看哪些方向还没人研究
6. **自我进化** — 搜得越多，参数越准

**关键词**: 物种 · 文献 · 多源搜索 · 可信度评分 · BDI 认知循环

---

## 怎么用

### 一行代码搜物种

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")

print(f"{len(result.papers)} 篇论文，耗时 {result.elapsed_s:.1f} 秒")
```

### 命令行搜

```bash
python scripts/search_api.py --species "鳤"
python scripts/search_api.py --species "Pseudaspius hakonensis" --max 20
```

### 给其他项目调用

```python
from src.adapter import CognitiveSearchAdapter

adapter = CognitiveSearchAdapter()
result = adapter.search("珠星三块鱼", mode="adaptive")
```

---

## 它怎么工作的

### 6+ 搜索通道 (MCP + HTTP)

```
MCP 通道 (需 npx/node):
  scholar    → 谷歌学术 / OpenAlex / Semantic Scholar
  article    → Europe PMC / PubMed / Crossref 全文
  tavily     → AI 深度网络搜索
  exa        → 语义网络搜索
  ncbi       → PubMed E-utilities 直连
  scholarly  → OpenAlex + Semantic Scholar

HTTP 通道 (无需装任何东西):
  pubmed     → NCBI E-utilities REST
  crossref   → Crossref REST API
  openalex   → OpenAlex REST API
  arxiv      → arXiv API
  europe_pmc → Europe PMC REST API
  cnki       → Bing 中文文献搜索
```

搜不到的时候还会自动生成 OCR 拼写变体（`Ochetobius` → `Ochetobibus`、`Ocheotbius`……），防止打字错误漏论文。

### 可信度评分

```
评分 = 50(基础) + 30(SCI期刊) + 25(CSCD核心) + 10(有DOI) + 10(有PMID)
       - 30(预印本) - 100(掠夺性期刊)
```

| 分数 | 标记 | 含义 |
|------|------|------|
| ≥80 | 🟢 | 高可信度，SCI/Q1 期刊论文 |
| 60–79 | 🟡 | 中等，一般同行评审期刊 |
| 40–59 | 🟠 | 低可信度，预印本/学位论文 |
| <40 | 🔴 | 不可信，掠夺性期刊 |

### 项目文件

```
cognitive-search-engine/
├── config/           # 配置文件（搜索规则、物种图谱、MCP 服务器）
├── src/              # Python 源码
│   ├── meso_agent.py       ← BDI 认知循环，搜索入口
│   ├── mcp_client.py       ← MCP 子进程管理 + 工具发现
│   ├── parallel_search.py  ← HTTP 直连搜索（6 源并行）
│   ├── unified_search.py   ← 搜索协议 + 分类学服务 + 引擎注册表
│   ├── search_coordinator.py ← 统一搜索协调器
│   ├── validator.py        ← 论文验证
│   ├── credibility_scorer.py ← 期刊白名单评分
│   ├── variant_generator.py  ← OCR 拼写变体
│   ├── inference_engine.py ← 推理增强（缺口检测）
│   ├── evolution_executor.py ← 自进化参数调整
│   ├── world_model.py      ← 预搜索仿真
│   ├── adapter.py          ← 跨项目接口
│   └── report_formatter.py ← 分类报告输出
├── scripts/          # CLI 工具 (search_api, credibility_scorer, kb_to_graph_sync, self_evolve)
├── skills/           # Reasonix AI 技能
└── tests/
```

---

## 和谁一起工作

```
三角闭环 + 衍生 (跨项目)
├── V0  fish-ecology-assistant   → 知识库 + 数据 + 矛盾分析
├── V1  cognitive-search-engine  → 搜索验证 ← 就是这个项目
├── Coord  eon-core              → EventBus + DAG 路由
│
├── P₁  porpoise-agent           → 衍生: 江豚种群监测
└── P₂  coilia-agent             → 衍生: 刀鲚洄游生态
```

本引擎是**整个工作区的唯一搜索网关**。所有外部搜索请求必须路由到此引擎。

---

## 先装啥

```bash
pip install pyyaml        # 配置文件读取
pip install requests      # HTTP 搜索（可选，默认用 urllib）
```

Python 3.10+。Windows/Linux/macOS 都行。

---

## 许可证

MIT © 2026 fangtaocai041
