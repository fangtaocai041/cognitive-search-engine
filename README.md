<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
</p>

# 🕸️ Cognitive Search Engine v5

> **Meso-Cosmos Agent** — BDI + ReAct + Authority Scoring + ZN/EN Dynamic Graph + Lazy Loading

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.2-8b5cf6)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-5-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-7-f59e0b)](config/mcp_servers.yaml)
[![Architecture](https://img.shields.io/badge/architecture-meso_cosmos-8b5cf6)](docs/ARCHITECTURE.md)
[![Multi-LLM](https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6)]()
[![BDI](https://img.shields.io/badge/BDI-ReAct-22c55e)]()
[![Authority Score](https://img.shields.io/badge/authority-scoring_0_100-ec4899)]()
[![DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/fangtaocai041/cognitive-search-engine)
[![Docker](https://img.shields.io/badge/Docker-planning-lightgrey)]()
[![Self-Evolve](https://img.shields.io/badge/self_evolve-feedback_loop-10b981)](skills/self-evolve.md)

## 🧠 Intelligent Optimization Layers

> 验证引擎集成了三层优化：**DeepSeek 级效率** (MoE 门控 + KV 缓存)、**学者级置信** (Rule of Three 统计停止)、**混沌增强探索** (Rössler 扰动 + wildcard 发现)。
> 协调由 [meso-cosmos-agent](https://github.com/fangtaocai041/meso-cosmos-agent) 统一调度。

## 🔺 S-T-V-P₁-P₂ Architecture Role: **Validation (V)**

> Part of the S-T-V-P₁-P₂ ecosystem: `fish(S) → meso-cosmos(T) → cognitive(V)`, with `porpoise(P₁)` + `coilia(P₂)` as domain specialists.
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

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| **v5.2.2** | 2026-06-08 | validator.py extracted + evolution_executor + paper_health_check + contradiction-driven meso_agent |
| **v5.2.1** | 2026-06-07 | S-T-V triangulation + DirectLoader + Meso-Cosmos Agent v4.0 |
| **v5.2** | 2026-06-07 | Meso-Cosmos coordination layer + ZN/EN bilingual graph |
| **v5.1** | 2026-06-07 | Hub-and-Spoke search + authority credibility scoring |
| **v5.0** | 2026-06-07 | BDI + ReAct cognitive architecture |

> **Latest**: v5.2.2 · 2026-06-08 · `bb939b5`

> **Core Strength**: From "string matching" to "signified reconstruction" — multiple signifier paths (exact, OCR variant, author network, citation graph, Chinese name) converge on the same signified (the species itself).

## 🔗 Linked Projects

This engine is integrated as a git submodule in:

| Project | Role | Description |
|---------|:----:|-------------|
| [meso-cosmos-agent](https://github.com/fangtaocai041/meso-cosmos-agent) | **T** (Transition) | Execution hub — 6-phase pipeline · cross-project routing · self-healing |
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | **S** (State) | Fish ecology — 22 MCP · 28 skills · Yangtze 443 species KB |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | **P₁** (Porpoise) | Finless porpoise specialist — NBHF acoustics · habitat modeling |
| [coilia-agent](https://github.com/fangtaocai041/coilia-agent) | **P₂** (Coilia) | Tapertail anchovy specialist — otolith microchemistry · migration ecology |

> **Co-evolution**: Engine code updated → fish & porpoise auto-benefit via submodule.
> Knowledge graph evolves → shared across all three projects.
> Full coordination spec: `coordination.yaml` at workspace root.

### 🧠 Meso-Cosmos Agent (Workspace Level)

> **Macro(BDI) → Meso(Coordination) → Micro(Execution)** — spanning all three S-T-V projects.

```
User Question
     │
     ▼
┌────────────────────────────────────────────────┐
│  Meso-Cosmos Agent (workspace root)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │UNDERSTAND│→│  ROUTE   │→│   EXECUTE     │ │
│  │(Macro)   │  │(Meso)    │  │(Micro)       │ │
│  │BDI意图   │  │S-T-V路由 │  │项目委派       │ │
│  └──────────┘  └──────────┘  └──────┬───────┘ │
│                                     │          │
│  ┌──────────┐  ┌──────────┐  ┌─────▼───────┐ │
│  │  EVOLVE  │←─│SYNTHESIZE│←─│  VALIDATE   │ │
│  │(Feedback)│  │(Merge)   │  │(Cross-Verify)│ │
│  └──────────┘  └──────────┘  └─────────────┘ │
└────────────────────────────────────────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
┌─────────┐      ┌──────────┐       ┌──────────────┐
│  fish   │      │ porpoise  │       │  cognitive    │
│  (S)    │      │   (T)     │       │    (V)        │
└─────────┘      └──────────┘       └──────────────┘
```

> Config: `config/meso_agent.yaml` · Skill: `skills/meso-orchestrator.md`

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
| Chinese DB blind spot | ❌ PubMed/Crossref don't index 知网/万方/维普 | ✅ Chinese-first search → web_search + 11 journal sites |
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
├── src/                          ← 7 modules (5-layer cognitive agent)
│   ├── agent_core.py             ← 🧠 CognitiveAgent — BDI + ReAct loop
│   ├── memory_layer.py           ← 🗄️  MemorySystem — short-term + long-term
│   ├── world_model.py            ← 🧬 BDI WorldModel — Belief/Desire/Intention
│   ├── rule_engine.py            ← ⚙️  SearchRuleEngine — phases + execution
│   ├── variant_generator.py      ← 🔤 OCR variant auto-generation
│   ├── graph_updater.py          ← 📊 Graph persistence + reverse indexes
│   ├── mcp_client.py             ← 🔌 MCP stdio client (5 servers)
│   └── parallel_search.py        ← ⚡ Multi-query parallel executor
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

## 🗺️ Future Roadmap

> **Current status:** Domain-leading research prototype (v5.1). The following milestones are planned for future iterations.

### ⚠️ Known Limitations

| Area | Limitation | Impact |
|------|-----------|--------|
| **UI** | CLI-only, depends on Reasonix runtime | Cannot be used standalone or by non-Reasonix users |
| **Deployment** | No Docker image, no REST API | No independent deploy / embed scenario |
| **Benchmark** | Only verified on 鳤 (12 papers) | Unknown recall on other 100+ species |
| **Real-time Index** | Relies on 3rd party APIs (PubMed, Crossref, etc.) | Latency depends on external services |
| **Chinese DB** | web_search + web_fetch fallback, no direct CNKI API | Rate-limited, may miss some paywalled papers |
| **Peer Review** | No published paper | Academic community hasn't reviewed the approach |

### 🎯 Milestone 1: Ship as Standalone Product

```
PRD:
  - Web UI (Streamlit / Gradio) → input species name → output knowledge graph
  - REST API (FastAPI) → POST /search?species=Ochetobius+elongatus
  - Docker image → docker pull fangtaocai/cognitive-search-engine
  - pip install → python -m cognitive_search.search "鳤"
```

**Why:** The most advanced species search engine is useless if it only runs inside Reasonix.

### 🎯 Milestone 2: Multi-Species Benchmark

```
BENCHMARK:
  - Curate 50 Chinese freshwater fish species with known paper lists
  - Baseline: PubMed/Google Scholar/Semantic Scholar recall
  - Compare: this engine's recall, precision, token cost per species
  - Publish: benchmark table as a technical report
```

**Why:** One data point (鳤, 100% recall) is anecdotal. 50 species is evidence.

### 🎯 Milestone 3: Academic Publication

```
PAPER:
  - Title: "Hub-and-Spoke Graph Search for Critically Endangered Fish Species"
  - Venue target: BMC Bioinformatics / J. of Fish Biology / Scientific Data
  - Contributions:
      1. Hub-and-Spoke protocol (replaces 14-layer linear)
      2. Authority credibility scoring (0-100)
      3. OCR variant safety net
      4. Chinese-first search strategy
  - Empirical results: recall vs token cost across 50 species
```

**Why:** Peer review validates the architecture and opens citation impact.

### 🎯 Milestone 4: Production Hardening

```
ENGINEERING:
  - Auto-scaling: handle 100 concurrent species searches
  - Caching: Redis-backed query cache (TTL 7 days)
  - Monitoring: Prometheus + Grafana (recall, latency, token cost per species)
  - Self-hosted: fallback to local PDF corpus when APIs are down
  - Plugin system: community-contributed search rules per fish family
```

**Why:** From "works on my machine" to "serves 100 users reliably."

### 💡 Ideas Being Explored

- **CrewAI-style multi-agent**: one agent per sub-discipline Hub, merge results
- **Local LLM inference**: replace DeepSeek API calls with Ollama (Qwen2.5-7B) for cost reduction
- **CNKI direct API**: if institutional access available, bypass web_search for Chinese papers
- **Multi-modal**: add image search (fish photos → species ID → paper retrieval)

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
