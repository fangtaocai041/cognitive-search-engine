<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
</p>

# 🕸️ Cognitive Search Engine v5

> **Meso-Cosmos Agent** — BDI + ReAct + Authority Scoring + ZN/EN Dynamic Graph + Lazy Loading

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.8.0-8b5cf6)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-5-22c55e)](skills/)
[![Auto-Retry](https://img.shields.io/badge/auto_retry-12s_window-22c55e)]()
[![Engines](https://img.shields.io/badge/engines-21-f59e0b)]()
[![Chinese Search](https://img.shields.io/badge/chinese_search-SerpAPI-ec4899)]()
[![SerpAPI](https://img.shields.io/badge/SerpAPI-Baidu+Scholar+DDG-8b5cf6)](config/agent.yaml)
[![Architecture](https://img.shields.io/badge/architecture-meso_cosmos-8b5cf6)](docs/ARCHITECTURE.md)
[![Multi-LLM](https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6)]()
[![BDI](https://img.shields.io/badge/BDI-ReAct-22c55e)]()
[![Authority Score](https://img.shields.io/badge/authority-scoring_0_100-ec4899)]()
[![DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/fangtaocai041/cognitive-search-engine)
[![Docker](https://img.shields.io/badge/Docker-planning-lightgrey)]()
[![Self-Evolve](https://img.shields.io/badge/self_evolve-feedback_loop-10b981)](skills/self-evolve.md)

## 🧠 Intelligent Optimization Layers

> 验证引擎集成了三层优化：**DeepSeek 级效率** (MoE 门控 + KV 缓存)、**学者级置信** (Rule of Three 统计停止)、**混沌增强探索** (Rössler 扰动 + wildcard 发现)。
> 协调由 [eon-core](https://github.com/fangtaocai041/eon-core) (10层统一内核) 统一调度。

## 🔺 S-T-V-P₁-P₂ Architecture Role: **Validation (V)**

> Part of the S-T-V-P₁-P₂ ecosystem, coordinated by [eon-core](https://github.com/fangtaocai041/eon-core) (10-layer unified kernel).
> Triangle Core: fish(Knowledge) + cognitive(Validation) + eon-core(Coordinator)
> Derived: P₁(porpoise) · P₂(coilia) · C(conflict)
> Validates search results, authority credibility scoring, enforces cross-project independence.
> **DirectLoader**: `importlib` zero MCP process. **Triangulation**: ≥3 sources, ≥2 independent projects.

## 📊 Self-Assessment

| Dimension | Rating | Notes |
|-----------|:-----:|-------|
| 🎯 Search Precision | ⭐⭐⭐⭐⭐ | Hub-and-Spoke + OCR variants + credibility scoring (0-100) |
| 🧠 Cognitive Architecture | ⭐⭐⭐⭐⭐ | BDI + ReAct loop + contradiction-driven strategy selection |
| 📊 Validation Rigor | ⭐⭐⭐⭐☆ | `validator.py` with cross-project independence enforcement |
| 🔬 Species Coverage | ⭐⭐⭐⭐☆ | ~10 species in graph, expandable via auto-writeback |
| ⚡ Efficiency | ⭐⭐⭐⭐☆ | DirectLoader (importlib, zero MCP) + MoE gating via T-layer |
| 🧪 Test Coverage | ⭐⭐⭐⭐⭐ | 46 integration + 94 robustness = 140 tests |

---

## 🗄️ v5.4: Living Database Catalog & Graph Router

> **65 databases · 8 domains · 4 tiers · self-evolving weights · tendril health awareness**

| Feature | Description | Module |
|:--------|:------------|:-------|
| **Database Catalog** | 65 databases across 8 domains, 4 tiers (general→specialized→institutional→raw data) | `config/database_catalog.yaml` |
| **Intent Detection** | `detect_intent(query)` → {literature \| data \| thesis \| comprehensive} | `catalog_loader.py` |
| **Graph Router** | `graph_route(query, health_aware=True)` — weighted topology + tendril health + complementarity | `catalog_loader.py` |
| **Progressive Search** | Tier 1 first → expandable Tier 2/3/4 — SM-2 retreat when satisficed | `catalog_loader.py` |
| **Taxonomic Unfolding** | L1(species)→L2(genus)→L3(family)→L4(Chinese+aliases) progressive search | `catalog_loader.py` |
| **Living System** | `record_search_result()` → feedback logs → `apply_feedback()` auto-tunes weights | `catalog_loader.py` |
| **Emergence Engine** | `emerge_domains()` — discovers cross-domain DB clusters from usage patterns | `catalog_loader.py` |

### Tiered Search Flow

```
"search Ochetobius literature"
  → intent=literature
  → Tier 1: PubMed, Scopus, WoS, CrossRef, Google Scholar, CNKI, 万方, 百度学术
  → [satisficed? → stop | expand → Tier 2: ASFA, FishBase, 水生生物学报...]

"download Ochetobius raw data"
  → intent=data
  → Tier 4: Dryad, GBIF, Zenodo, Figshare, PANGAEA, WorldClim...
```

### Engineering Language

```
graph_route(query: str, health_aware: bool) → List[Dict{id, _graph_score, _tendril}]
  Step 1: domain_scores = score_domains(query)
  Step 2: FOR EACH (domain, score) IN domain_scores:
            db_score[edge.from] = MAX(db_score[edge.from], edge.weight × score)
  Step 3: cross-domain propagation (decay 0.5)
  Step 4: complementarity boost (threshold 0.3, factor 0.15)
  Step 5: IF health_aware THEN tendril health filter (penalty 0.2)
  Step 6: RETURN sorted[:top_n]
```

---

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| **v5.8.0** | 2026-07-11 | 🚀 21引擎全线升级 — SerpAPI Baidu/Scholar/DuckDuckGo 突破中文反爬 · Exa API 语义搜索 · Europe PMC NCBI 500故障转移 · BDI修复(中文种强制全管线, consecutive_zero保护, stalled放宽) · HTTP超时15→8s · 全流程112→25s |
| **v5.7.0** | 2026-06-20 | 🧬 KB-First 两阶段搜索 — `search_with_kb_first()` + `continue_full_search()` + `KbFirstSearchResult` 跨项目聚合 · f项目知识库预查 · `kb_first()` 入口 |
| **v5.6.0** | 2026-06-10 | 🔁 HTTP重连 + 🚀 MCP并行预热 + 🌐 中文三层搜索 + 🛑 停止机制重构 |
| **v5.5.0** | 2026-06-09 | 🧬 Unified Search Protocol (自适应+附带过滤+CN/EN双通道) + 鲌类分类学修订(v2.2) + unified_search.py |
| **v5.4.0** | 2026-06-09 | 🗄️ Living DB Catalog (61 DBs, 8 domains, 4 tiers) + Graph Router + Progressive Search + Emergence Engine |
| **v5.3.0** | 2026-06-08 | 🆕 inference_engine + ☯️ TAO architecture (木) + 🔥 WUXING dynamics |
| **v5.2.2** | 2026-06-08 | validator.py extracted + evolution_executor + paper_health_check + contradiction-driven meso_agent |
| **v5.2.1** | 2026-06-07 | S-T-V triangulation + DirectLoader + eon-core coordination |
| **v5.2** | 2026-06-07 | Meso-Cosmos coordination layer + ZN/EN bilingual graph (→ deprecated, superseded by eon-core v7.1) |
| **v5.1** | 2026-06-07 | Hub-and-Spoke search + authority credibility scoring |
| **v5.0** | 2026-06-07 | BDI + ReAct cognitive architecture |

> **Latest**: v5.7.0 · 2026-06-20

> **Core Strength**: From "string matching" to "signified reconstruction" — multiple signifier paths (exact, OCR variant, author network, citation graph, Chinese name) converge on the same signified (the species itself).

## 🔁 v5.6.0: Production Hardening — Retry, Parallel MCP, Chinese Search

> **三化升级**：服务端不稳定不再是瓶颈。MCP 预热、HTTP 重连、中文三层发散确保每次搜索可靠覆盖。

### What's New

| Feature | Description | Module |
|:--------|:------------|:-------|
| **HTTP Auto-Retry** | PubMed/Crossref/OpenAlex 指数退避重试，60s 窗口，5 次尝试 | `src/rule_engine.py` |
| **MCP Parallel** | 7 搜索引擎并行启动，as_completed 先完成先返回，3min 超时 | `src/mcp_client.py` |
| **MCP Prewarm** | `__init__` 后台并行预热 + JSON-RPC `tools/list` 健康探测 | `src/mcp_client.py` |
| **Chinese 3-Layer Search** | Layer1 四中文源 → Layer2 Crossref/OpenAlex → Layer3 tavily 降级 | `src/rule_engine.py` |
| **Language Routing** | 每个 phase 标记 `language: en/zh/both`，分离中英文通道 | `config/search_rules.yaml` |
| **Stop Mechanism Fix** | `Desire.satisfied()` 不再因 `min_papers=8` 截断，diminishing returns 驱动 | `src/world_model.py` |

### HTTP Retry

```
每 API 调用:
  for attempt in 1..5:
      try: urlopen(timeout=15)
      except (URLError, TimeoutError, HTTPError):
          wait = min(2^attempt, 15)  # 指数退避
          retry
  raise → 记录错误，不影响其他源
```

文件：`rule_engine.py:586-612` · 配置：`agent.yaml → timeout.http_retry_max_s: 60`

### MCP Parallel + Prewarm

```
McpClient.__init__():
  Thread: prewarm_background()  # 不阻塞构造
    for server in [scholar, article, scholarly, tavily, exa]:
      Parallel: _get_or_start_process(name)
                _health_check(name)  # JSON-RPC tools/list
      → 标记 healthy/unhealthy

call_tools_parallel(tool_calls):
  ThreadPoolExecutor(max_workers=7)
  as_completed → 先完成先合并
```

文件：`mcp_client.py:68-138` · 总超时：`mcp_parallel_timeout_s: 180`

### Chinese 3-Layer Search

| Layer | Source | Query |
|:-----:|--------|-------|
| 1 | 百度学术/CNKI/万方/CAS | `web_search + site:` |
| 2 | Crossref/OpenAlex | `中文名 + 学名` UTF-8 |
| 3 | Tavily/Exa AI | `中文名 + 学术论文` |

先完成先统计，后完成的后合并，`dedup_merge` 阶段去重。

### Pipeline Evolution

```
v5.5 (之前)          v5.6 (之后)
─────────           ─────────
exact_search        graph_lookup
  ↓ (min=8 截断)    chinese_exact_search  ← 新增
  STOP               exact_search
                     author_crossref
                     review_mining
                       ↓ (diminishing returns)
                     STOP
```

### Config Reference

```yaml
# agent.yaml — timeout
timeout:
  http_retry_max_s: 60             # HTTP 重试总窗口
  http_retry_attempts: 5            # 最多重试 5 次
  http_per_call_timeout_s: 15       # 单次请求超时
  mcp_parallel_timeout_s: 180       # MCP 并行总超时 (3min)
  mcp_per_call_timeout_s: 30        # MCP 单次调用超时
  mcp_parallel_max_workers: 7       # 最大并行连接数
```

---

## 🧬 v5.7.0: KB-First 两阶段搜索 — f项目知识库优先

> **先查 f项目知识库，再决定是否启动全量搜索。** 不再无条件触发 7 引擎并行。

### 新 API

```python
from src.search_coordinator import kb_first, continue_full_search

# Stage 1: KB check (fast, no external API)
result = kb_first("珠星三块鱼")
# → KbFirstSearchResult {
#     stage: "kb_check",
#     kb_found: True,
#     kb_summary: "📚 三块鱼 / 鲤科 / 溯河洄游...",
#     suggested_next: "ask_user"
#   }

print(result.ask_user_prompt())
# → 询问用户：留步 or 继续搜索

# Stage 2: Full search (only if user continues)
result = continue_full_search(result, group="full")
# → KbFirstSearchResult {
#     stage: "full_search",
#     full_search: CoordinatedSearchResult { total_papers: 42, ... }
#   }
```

### 新增模块

| 模块 | 文件 | 功能 |
|------|------|------|
| `KbFirstResult` | `fish-ecology-assistant/src/orchestrator.py` | KB 查询结果结构体 (found/info/recommendation) |
| `KbFirstSearchResult` | `cognitive-search-engine/src/unified_search.py` | 两阶段搜索包装器 (ask_user_prompt / full_search) |
| `_load_fish_kb()` | `cognitive-search-engine/src/unified_search.py` | 跨项目 importlib 加载 f项目 orchestrator |
| `search_with_kb_first()` | `cognitive-search-engine/src/unified_search.py` | Stage 1 入口 (KB check + fallback) |
| `continue_full_search()` | `cognitive-search-engine/src/unified_search.py` | Stage 2 入口 (全量搜索 + KB 数据丰富) |
| `kb_first()` | `cognitive-search-engine/src/search_coordinator.py` | 薄委托入口 |
| `unified-species-search` v4.0 | `fish-ecology-assistant/.reasonix/skills/` | Skill 层 KB-First 流程 |

### 数据流

```
fish_species_kb.yaml (f项目)
  └─ kb_first_lookup()
       ├─ 精确匹配: scientific / chinese
       ├─ 别名匹配: aliases[]
       ├─ 同义名匹配: synonyms[]  ← NEW
       └─ 模糊匹配: genus + 中文字符
            │
            ▼
       ask_choice: 留步 | 继续搜索
            │
       [继续] → coordinated_search()
                (taxonomy check → mode → 7 engines → dedup → classify)
```

### 降级策略

```
IF f项目不可用:
  → 直接执行 coordinated_search() (自动降级)
IF KB 查询异常:
  → 记录错误 → 直接执行 coordinated_search()
IF KB 未命中:
  → 展示近缘候选 → 推荐 continue_to_c
```

: From "string matching" to "signified reconstruction" — multiple signifier paths (exact, OCR variant, author network, citation graph, Chinese name) converge on the same signified (the species itself).

## 🔗 Linked Projects

This engine is integrated as a git submodule in:

| Project | Role | Description |
|---------|:----:|-------------|
| [eon-core](https://github.com/fangtaocai041/eon-core) | **Coordinator** | 10-layer unified kernel — EventBus · Samsara karma · DAG routing |
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | **S / V0** (State) | Fish ecology — 21 MCP · 28 skills · Yangtze 443 species KB |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | **Derived P₁** (Porpoise) | Finless porpoise specialist — NBHF acoustics · habitat modeling |
| [coilia-agent](https://github.com/fangtaocai041/coilia-agent) | **Derived P₂** (Coilia) | Tapertail anchovy specialist — otolith microchemistry · migration ecology |

> **Co-evolution**: Engine code updated → fish & porpoise auto-benefit via submodule.
> Knowledge graph evolves → shared across all three projects.
> Full coordination spec: `coordination.yaml` at workspace root.

### 🧠 eon-core Unified Kernel (Workspace Level)

> **10-layer concentric architecture** — OriginKernel → YinYang → 4 Vertices → 8 Trigrams → Tetrahedron → WuXing → Samsara → Sphere → Tendrils → Evolution.
> Coordinated by [eon-core](https://github.com/fangtaocai041/eon-core). Replaces the now-deprecated meso-cosmos-agent (deleted v7.1).

```
User Question
     │
     ▼
┌────────────────────────────────────────────────┐
│  eon-core (workspace root — 10-layer kernel)    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ RECEIVE  │→│  ROUTE   │→│   EXECUTE     │ │
│  │(L7 API)  │  │(L0 DAG)  │  │(L2 Vertices) │ │
│  └──────────┘  └──────────┘  └──────┬───────┘ │
│                                     │          │
│  ┌──────────┐  ┌──────────┐  ┌─────▼───────┐ │
│  │  EVOLVE  │←─│  KARMA   │←─│   MONITOR   │ │
│  │(L9)      │  │(L6 Court)│  │(L5 WuXing)  │ │
│  └──────────┘  └──────────┘  └─────────────┘ │
└────────────────────────────────────────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
┌─────────┐      ┌──────────┐       ┌──────────────┐
│  fish   │      │ porpoise  │       │  cognitive    │
│(三角 V0)│      │(衍生 P₁)  │       │  (三角 V1)    │
└─────────┘      └──────────┘       └──────────────┘
```

> Config: `eon-core/config/taiji.yaml` · Kernel: `eon-core/src/kernel/origin.py`

---

## 🧠 v5.2: Meso-Cosmos Agent — 中宇宙式协调层

> **Macro(BDI) → Meso(Coordination) → Micro(Execution)** — 自动在宏观意图与微观工具调用之间搭建桥梁。

### What's New

| Feature | Description | Module |
|:--------|:------------|:-------|
| **MesoAgent** | 中宇宙式协调层 — 统一管理 WorldModel/SearchRuleEngine/MemorySystem/GraphUpdater | `src/meso_agent.py` |
| **Dynamic Graph v2.0** | ZN/EN-aware auto-update — 中文期刊自动填入 `authors_zh`，新作者/期刊自动注册，中英文双语去重 | `src/graph_updater.py` |
| **ZN/EN Literature Rule** | 中文期刊走中文署名（杨计平），英文走英文名（Yang Jiping）；论文防双版本重复 | `project memory (high)` |
| **MCP Timeout Protection** | 15 秒 threading 超时防止 MCP 子进程永久阻塞 | `src/mcp_client.py` |
| **Chinese Academic Search Skill** | 覆盖 8 种中文期刊的专用搜索策略 | `skills/chinese-academic-search.md` |

### Meso-Cosmos Architecture

```
┌─────────────────────────────────────────────────────┐
│              Macro-cosmos (BDI 意图层)               │
│  CognitiveAgent · WorldModel · Belief/Desire/Intention │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Meso-cosmos (协调层)                     │
│  MesoAgent.search(species_id)                       │
│                                                     │
│  Pipeline: BDI预测 → 模式选择(穷举/分类/轻量)          │
│          → 执行分发 → 图谱更新 → ZN/EN规则            │
│                                                     │
│  Components: WorldModel + SearchRuleEngine          │
│              + MemorySystem + GraphUpdater          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Micro-cosmos (执行层)                    │
│  PubMed E-utilities · Crossref · OpenAlex · MCP      │
│  11 search phases · 5 engines · Authority scoring    │
└─────────────────────────────────────────────────────┘
```

### ZN/EN Automatic Rules

| Context | Before | After |
|:--------|:-------|:------|
| Chinese journal paper | `authors: [Yang Jiping]` | `authors_zh: [杨计平]` ✅ |
| English journal paper | `authors: [Yang Jiping]` | `authors: [Yang Jiping]` ✅ (unchanged) |
| ZN/EN duplicate papers | Kept both versions | DOI + title_zh dedup → keep Chinese version |
| New author found | Manually add to graph | Auto-register with Chinese name |
| New journal found | Manual entry | Auto-register |

### Quick Start with MesoAgent

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")

print(f"Found {len(result.papers)} papers in {result.elapsed_sec}s")
print(f"New to graph: {result.new_papers}")
print(f"Stop reason: {result.stop_reason}")
```

---

## 🧠 v5.1: Hub-and-Spoke Search Protocol

> **From linear layers to directional hubs** — locate hub papers per sub-discipline, extract citation spokes, classify into knowledge graph.

### Search Protocol: Hub-and-Spoke (3 Phases)

| Phase | Action | Tools |
|:-----:|--------|-------|
| **1. Locate Hubs** | Parallel search across 5 sub-discipline directions (genetics/morphology/genomics/ecology/survey) | `scholar_search` + `web_search` |
| **2. Extract Spokes** | Pull citation graph from each hub paper | `article_get_references` |
| **3. Gap Detection** | OCR variant sweep + new paper detection (year ≥ current-1, PMID=NULL) | `scholar_search` variant queries |

### 5-Layer Agent Architecture

| Layer | Function | Module |
|:-----:|----------|--------|
| **1. Perception** | Input → species_id → genus/species/Chinese + volume estimation | `SearchRuleEngine.execute()` |
| **2. Cognitive** | BDI policy π(Belief,Desire) → Intention + ReAct loop | `src/agent_core.py` |
| **3. Memory** | Short-term + Long-term + **Classified Knowledge Graph** | `src/memory_layer.py` |
| **4. Mapping** | Direction routing → hub selection → `article_get_references` | `search_rules.yaml` |
| **5. Execution** | PubMed · Crossref · MCP (5 engines) · Authority scoring | `rule_engine._http_search()` |

### BDI + ReAct Cognitive Loop

```
Think → Act → Observe → Reflect
  │       │        │          │
  │  form_intention  count    compare
  │  (B,D)→I        papers   Belief vs
  │                          Desire
  ▼
Desire satisfied? → STOP
```

📖 Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🔺 S-T-V Triangle (Cross-Project)

> Three projects: State(fish) → Transition(porpoise) → Validation(cognitive) closed loop

| Component | Project | Function |
|:---------:|---------|----------|
| **S** | fish-ecology-assistant | State — knowledge, data, findings |
| **T** | porpoise-agent | Transition — execution, pipeline |
| **V** | cognitive-search-engine | Validation — verification, trust scoring |

Config: `config/stv_protocol.yaml` — `min_sources_core_claim = 3`, trust_score 5-level triangulation.

## 🔧 Engineering Language Commitment

> **Every feature is expressed in executable engineering language — not natural language.**
> `function(input: Type) → OutputType` | `WHEN condition THEN action` | `config.path.to.value`

| Format | Purpose | Example |
|--------|---------|---------|
| `search_rules.yaml` | Structured rule engine (10 phases) | `function: mine_review_references` + `tools: [article_get_references]` |
| `tools.json` | JSON Schema tool definitions | Compatible with DeepSeek + Gemini + OpenAI Function Calling |
| `src/rule_engine.py` | Python executor | `SearchRuleEngine("config/search_rules.yaml").execute(species_id)` |
| `config/evolution.yaml` | Self-adaptive parameters | `trigger: recall < 0.5 FOR 3 CONSECUTIVE → satisfice_threshold += 2` |

## 🧠 Core Innovation

**Not string matching — cognitive reconstruction.**

Traditional search matches strings. If a paper misspells "Ochetobius" as "Ochetobibus", it's invisible.
Our engine reconstructs the **signified** (the species itself) from multiple **signifier** paths simultaneously.

```
Signifier Paths → Signified (Species)
─────────────────────────────────────
Exact name      ─┐
Variant spell   ─┤
Author network  ─┼─→ Ochetobius elongatus (鳤)
Citation graph  ─┤
Journal context ─┤
Chinese name    ─┘
```

## 🏆 Why This Is the Most Advanced Species Search Engine

### vs Traditional Academic Search (Google Scholar, Web of Science, PubMed)

| Problem | Traditional | Cognitive Search Engine |
|---------|------------|------------------------|
| Species name typos | ❌ Misses "Ochetobibus" when searching "Ochetobius" | ✅ OCR variant sweep catches all (2 papers found: 2009 + 2026) |
| Chinese DB blind spot | ❌ PubMed/Crossref don't index 知网/万方/维普 | ✅ SerpAPI Baidu/Scholar/DuckDuckGo — 21 engines bypass Great Firewall |
| Cold-start (new species) | ❌ Zero results → stuck | ✅ Hub-and-Spoke: multi-direction hub location |
| Review paper blind trust | ❌ Cites ghosts/misattributions silently | ✅ Authority scoring 0-100 per paper, SCI/core-journal weighted |
| Search amnesia | ❌ Same search repeated, same cost | ✅ Classified knowledge graph persists, lazy-load on demand |
| One-size-fits-all depth | ❌ Same effort for 8 papers or 8000 | ✅ 3-mode: exhaustive(<20) / classified(20-100) / review-anchored(>100) |
| No cognitive model | ❌ Pure string matching | ✅ Semiotics + linguistics + phonetics + logic |

### vs AI Search (Gemini, Perplexity, Claude)

| Problem | AI Search | Cognitive Search Engine |
|---------|----------|------------------------|
| Transparency | ❌ Black box — can't verify completeness | ✅ 3-phase Hub-and-Spoke, each auditable |
| Cost | ❌ High token cost per search | ✅ Lazy-load knowledge graph, ~60% fewer calls |
| Domain knowledge | ❌ Generic — no species-specific logic | ✅ Latin grammar, IPA, OCR error models |
| Source authority | ❌ Mixes preprints with peer-reviewed equally | ✅ Credibility score 0-100, predatory journals excluded |
| Citation graph | ❌ Not leveraged | ✅ Multi-hub citation spokes → classified graph |
| Learning | ❌ Stateless — each search independent | ✅ Graph grows with each search |

### Unique Capabilities (No Other Tool Has)

| # | Capability | Why It Matters |
|:--|-----------|---------------|
| 1 | **Hub-and-Spoke Graph Search** | Multi-direction hubs → citation spokes → 10 calls cover 90%+ recall |
| 2 | **Authority Credibility Scoring** | SCI + CSCD核心 weighted +30, predatory journals -100 excluded |
| 3 | **Review-First Strategy** | For >20 papers: find review first → it IS the literature map |
| 4 | **Classified Knowledge Graph** | Lazy-load: output category counts first, expand only on user request |
| 5 | **OCR Variant Safety Net** | Ochetobius→Ochetobibus: caught 2 papers that exact-name search missed |

## ⚡ Five Breakthroughs

### 1. Hub-and-Spoke Graph (Not Linear Layers)

| Traditional (v4.1 14-layer) | Hub-and-Spoke (v5.0) |
|----------------------------|----------------------|
| 14 layers, sequential | 3 phases, parallel hubs |
| ~15+ tool calls/search | ~10 tool calls/search |
| Single linear path | Multi-direction spoke merge |
| Layers 0-13 all always executed | Gaps only filled when detected |

### 2. Authority Credibility Scoring

```
credibility = 50 + 30(SCI) + 25(CSCD核心) + 10(DOI) + 10(PMID) - 30(preprint) - 100(predatory)
→ 🟢 ≥80 高可信度  🟡 60-79 中  🟠 40-59 低  🔴 <40 不可信
```

### 3. Review-First Strategy (for medium/large fields)

```
IF estimated > 20 papers:
  Search review first → review references ≈ complete literature map
  Only then search for post-review papers
```

### 4. Classified Knowledge Graph with Lazy Loading

```
Output: category counts only → user picks direction → expand that subtree
Never load all papers into context at once.
```

### 5. Multi-Discipline Cognitive Engine

| Discipline | Method |
|-----------|--------|
| Semiotics | Signifier decomposition → signified reconstruction |
| Linguistics | Latin morphology, root extraction, OCR error models |
| Phonetics | IPA transcription, Soundex+Metaphone double-code |
| Logic | Deductive chain, abductive inference, inductive pattern |

---

## 🚀 Quick Start

```bash
git clone https://github.com/fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine
```

Add to your Reasonix project:
```yaml
# In your project's config/agent.yaml
skills:
  skill_dir: "../cognitive-search-engine/skills"
```

Or run directly with Python:
```bash
python src/rule_engine.py
```

Or use as a Skill:
```
/skill graph-search-engine species="Ochetobius elongatus"
```

---

## 📁 Project Structure

```
cognitive-search-engine/
├── README.md                     ← You are here
├── README.zh.md                  ← 中文
├── LICENSE
│
├── config/
│   ├── agent.yaml                ← v5.0: 5-layer architecture + BDI config
│   ├── mcp_servers.yaml          ← 5 search engines
│   ├── species_graph.yaml        ← Long-term memory (16 entries + indexes)
│   ├── component_registry.yaml   ← Living system: 12 components lifecycle
│   ├── evolution.yaml            ← Self-evolution: 4 auto-adaptive params
│   ├── search_rules.yaml         ← Phase definitions (mapping layer)
│   ├── stv_protocol.yaml         ← Cross-project STV triangle protocol
│   └── tools.json                ← JSON Schema: DeepSeek+Gemini+OpenAI tools
│
├── src/                          ← 18 modules (5-layer cognitive agent)
│   ├── adapter.py                ← 🔌 CognitiveSearchAdapter — DirectLoader entry
│   ├── agent_core.py             ← 🧠 CognitiveAgent — BDI + ReAct loop
│   ├── catalog_loader.py         ← 🗄️ DB catalog + graph router + emergence
│   ├── evolution_executor.py     ← 🦋 Self-evolution feedback executor
│   ├── graph_updater.py          ← 📊 Graph persistence + reverse indexes
│   ├── inference_engine.py       ← 🧮 TAO + WuXing inference engine
│   ├── mcp_client.py             ← 🔌 MCP stdio client (7 servers)
│   ├── memory_layer.py           ← 🗄️  MemorySystem — short-term + long-term
│   ├── meso_agent.py             ← 🧭 MesoAgent — coordination layer
│   ├── paper_health_check.py     ← 💓 Paper validity health checker
│   ├── parallel_search.py        ← ⚡ Multi-query parallel executor
│   ├── rule_engine.py            ← ⚙️  SearchRuleEngine — phases + execution
│   ├── search_coordinator.py     ← 🔀 SearchCoordinator — multi-engine orchestration
│   ├── unified_search.py         ← 🧬 UnifiedSearchProtocol — adaptive + CN/EN dual-channel
│   ├── validator.py              ← ✅ Cross-project independence validator
│   ├── variant_generator.py      ← 🔤 OCR variant auto-generation
│   └── world_model.py            ← 🧬 BDI WorldModel — Belief/Desire/Intention
│
├── skills/
│   ├── graph-search-engine.md    ← v4 core: graph traversal + Pareto-optimal
│   ├── cognitive-species-search.md ← v3: semiotics + linguistics + phonetics
│   ├── chinese-academic-search.md  ← 中文期刊搜索 (8 journals)
│   └── self-evolve.md            ← 🧬 Post-search feedback → auto-adjust
│
├── docs/
│   ├── ARCHITECTURE.md           ← 🆕 5-layer agent architecture (full docs)
│   └── UNIFIED_EVOLUTION.md      ← 3-project co-evolution architecture
│
└── .github/workflows/
    └── validate.yml              ← CI/CD
```

---

## 🔬 How It Works

### BDI + ReAct Cognitive Loop

```
1. INIT Belief: load known papers from graph (0 tokens)
2. THINK:   π(Belief, Desire) → Intention (select phases)
3. ACT:     Execute phase (PubMed, Crossref, MCP servers)
4. OBSERVE: Count new papers, compute IG, update Belief
5. REFLECT: Compare Belief vs Desire → continue / restructure / stop
6. PERSIST: Merge new papers into graph (long-term memory)
```

### Graph-First Efficiency

```
IF known papers ≥ 8 → SATISFICED, return immediately (0 tokens)
IF known papers < 8 → execute cheapest phases first
IF consecutive zeros ≥ 2 → STOP (diminishing returns)
```

### Energy Efficiency

| Metric | Value |
|--------|:----:|
| Satisficing threshold | 8 papers |
| Max token budget | 50,000 |
| IG/token prune threshold | 0.005 |
| Progressive deepening | Cheapest layers first |

---

## 📡 Search Engines (built-in)

| Engine | Purpose | Fuzzy Match |
|--------|---------|:----------:|
| Google Scholar | Primary — strongest fuzzy matching | ✅✅✅ |
| Europe PMC + PubMed | Biomedical literature | ✅ |
| OpenAlex + Semantic Scholar | Cross-disciplinary | ✅✅ |
| Tavily | Web search (grey lit, reports) | ✅✅ |
| Exa | Semantic web search | ✅ |

---

## 🗺️ 演进方向 (Personalized Roadmap)

> 以下方向根据实际研究需求排列，非通用路线图。每个方向对应一个具体痛点。

### 🔴 P0 — 本周可做

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 1 | **一键物种搜索** | 每次要手动输入学名+中文名 | `search("鳤")` → 自动查 species_graph → 中英双语并行 → 输出差距分析 |
| 2 | **CNKI/万方直连** | 当前用 web_search 兜底，慢且不全 | 如有机构账号 → 接入 CNKI API / 万方 API → 直接检索+下载摘要 |
| 3 | **付费论文自动 bypass** | 每次手动去 ResearchGate/小木虫搜 | `try_bypass()` 自动化 → 并行搜索 8 个共享渠道 → 返回可访问 URL |
| 4 | **搜索记录持久化** | 每次搜鳤都要重新来一遍 | `species_graph.yaml` 已有但未充分利用 → 搜索结果自动写回图谱 |

### 🟡 P1 — 本月

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 5 | **文献综述自动生成** | 搜完 15 篇还要人工分类写综述 | 按学科方向分类 → 提取摘要 → DeepSeek 生成结构化综述 |
| 6 | **研究差距自动检测** | 不知道国内vs国外研究到哪一步 | CN 5 篇 vs EN 7 篇 → `align_bilingual()` → "国内空白: 食性/基因组" |
| 7 | **物种对比搜索** | 搜完鳤还要搜鯮、鲥，重复劳动 | `compare_species(["鳤","鯮"])` → 并行搜索 → 对比表 |
| 8 | **新论文周报** | 不知道鳤最近有没有新论文 | 每日 NCBI/CNKI 自动检索 → 有新论文 → 推送通知 |

### 🟢 P2 — 本季度

| # | 方向 | 痛点 | 技术路径 |
|:--:|------|------|----------|
| 9 | **PDF 自动下载** | 找到论文还要手动下载、重命名 | 免费论文自动下载 → 按 `作者_年_期刊.pdf` 命名 → 本地存档 |
| 10 | **Zotero 集成** | 文献管理靠手工 | 搜索结果 → 自动导出 `.bib` → Zotero BetterBibTeX 同步 |
| 11 | **GIS 分布叠加** | 只有 GBIF 点数据，看不到环境背景 | GBIF 分布 + WorldClim 气候 + 水文图层 → 一张图看到栖息地全貌 |
| 12 | **机构库深度接入** | 中科院学位论文/报告找不到 | CAS IR + NSTL + 高校图书馆 → 学位论文/内部报告专属搜索 |

### 🔵 P3 — 未来

| # | 方向 | 痛点 |
|:--:|------|------|
| 13 | **微信小程序** | 野外调查时手机查物种文献 |
| 14 | **语音输入** | "帮我搜一下鳤的最新论文" |
| 15 | **多语种扩展** | 日文/韩文/俄文鱼类学论文 |
| 16 | **知识图谱可视化** | 作者合作网络 + 引用关系 → 交互式图谱 |

### ⚡ 技术债务 (持续)

- 触手健康状态从静态 YAML 改为运行时探针
- `species_graph.yaml` 自动从 NCBI Taxonomy 批量填充
- 反馈权重自进化从手动 `apply_feedback()` 改为后台定时任务
- 中文分词替代当前的字串匹配触发词检测

---

## 📋 README Changelog

| Version | Date | Theme | What Changed |
|:--------|:-----|:------|:-------------|
| **v5.2.1** | 2026-06-07 | Cross-Project Sync | + S-T-V triangle role declaration, + DeepWiki/Docker/Self-Evolve badges, + Linked Projects enhancement with co-evolution description, + alignment with fish/porpoise project conventions |
| **v5.2** | 2026-06-06 | Meso-Cosmos Agent | + MesoAgent (src/meso_agent.py), + Dynamic Graph v2.0 (ZN/EN auto authors_zh, auto-register, dedup), + ZN/EN Literature Rule, + MCP 15s Timeout Protection, + Chinese Academic Search Skill (4th skill), + architecture: meso_cosmos |
| **v5.1** | 2026-06-06 | Hub-and-Spoke Protocol | + Hub-and-Spoke (3-phase, 10 calls), + Authority Credibility Scoring (0-100), + Review-First Strategy, + Classified Knowledge Graph (lazy-load), + Chinese-academic-search Skill, + 3-mode adaptive depth (exhaustive/classified/review-anchored), + OCR variant safety net |
| **v5.0** | 2026-07-14 | 5-Layer Agent Architecture | + BDI WorldModel (Belief/Desire/Intention), + CognitiveAgent (ReAct loop), + MemorySystem (short-term + long-term), + agent_core.py, + memory_layer.py, + variant_generator.py, + graph_updater.py, + mcp_client.py, + ARCHITECTURE.md |
| **v4.3** | 2026-06-06 | Engineering Language | + YAML Rule Engine (10 structured phases), + JSON Schema tools.json, + rule_engine.py, + multi-provider config, + self-evolve feedback loop |
| **v4.2** | 2026-06-06 | Living System | + component_registry (12 components), + evolution.yaml (4 adaptive params), + self-evolve Skill, + UNIFIED_EVOLUTION.md |
| **v4.1** | 2026-06-06 | Adaptive Depth | + Adaptive search depth (exhaustive/classified/satisficing), + Phase 1.5 Review Mining, + Phase 1.6 Reference Verification (5-level trust scoring) |
| **v4.0** | 2026-06-06 | Graph Engine | Initial release — Knowledge Graph Traversal, 12 search layers, energy efficiency, 5 search engines |

---

## 📜 License

MIT © 2026 fangtaocai041

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
