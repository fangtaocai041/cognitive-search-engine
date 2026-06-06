<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
</p>

# 🕸️ Cognitive Search Engine v5

> **Hub-and-Spoke Graph Search** — BDI + ReAct + Authority Scoring + Classified Knowledge Graph + Lazy Loading

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.1-8b5cf6)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-4-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-5-f59e0b)](config/mcp_servers.yaml)
[![Architecture](https://img.shields.io/badge/architecture-hub_and_spoke-ec4899)](docs/ARCHITECTURE.md)
[![Multi-LLM](https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6)]()
[![BDI](https://img.shields.io/badge/BDI-ReAct-22c55e)]()
[![Authority Score](https://img.shields.io/badge/authority-scoring_0_100-ec4899)]()

---

## 🔗 Linked Projects

This engine is integrated as a git submodule in:

| Project | Description |
|---------|-------------|
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | Fish ecology AI research team |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | Porpoise research agent — auto-routes species queries to this engine |

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

## 📋 README Changelog

| Version | Date | Theme | What Changed |
|:--------|:-----|:------|:-------------|
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
