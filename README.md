<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
</p>

# 🕸️ Cognitive Search Engine v5

> **5-Layer Cognitive Agent** — BDI + ReAct + Multi-Layer Memory + Knowledge Graph Traversal + Semiotics

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0-8b5cf6)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-3-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-5-f59e0b)](config/mcp_servers.yaml)
[![Architecture](https://img.shields.io/badge/architecture-5_layer_agent-ec4899)](docs/ARCHITECTURE.md)
[![Multi-LLM](https://img.shields.io/badge/LLM-DeepSeek_%7C_Gemini_%7C_OpenAI-8b5cf6)]()
[![BDI](https://img.shields.io/badge/BDI-ReAct-22c55e)]()
[![Living System](https://img.shields.io/badge/living_system-self_evolving-ec4899)]()

---

## 🔗 Linked Projects

This engine is integrated as a git submodule in:

| Project | Description |
|---------|-------------|
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | Fish ecology AI research team |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | Porpoise research agent — auto-routes species queries to this engine |

---

## 🧠 v5.0: 5-Layer Standard Agent Architecture

> **BDI + ReAct + Memory** — aligning with academic AI (MDP/POMDP, ReAct, BDI) and industrial frameworks (LangChain, AutoGPT)

| Layer | Function | Module |
|:-----:|----------|--------|
| **1. Perception** | Input parsing: species_id → genus/species/Chinese | `SearchRuleEngine.execute()` |
| **2. Cognitive** | BDI policy π(Belief,Desire) → Intention + ReAct loop | `src/agent_core.py` |
| **3. Memory** | Short-term (ContextTracker) + Long-term (GraphMemory) | `src/memory_layer.py` |
| **4. Mapping** | Intention routing → tool selection → query serialization | `search_rules.yaml` + `PHASE_FUNCTIONS` |
| **5. Execution** | PubMed · Crossref · MCP servers (5 engines) | `rule_engine._http_search()` |

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
| Species name typos | ❌ Misses "Ochetobibus" when searching "Ochetobius" | ✅ 11-layer fuzzy protocol catches all variants |
| Cold-start (new species) | ❌ Zero results → stuck | ✅ Author graph + citation traversal finds papers |
| Review paper blind trust | ❌ Cites ghosts/misattributions silently | ✅ Phase 1.6: 5-level reference verification |
| Search amnesia | ❌ Same search repeated, same cost | ✅ Knowledge graph persists, known papers = 0 tokens |
| One-size-fits-all depth | ❌ Same effort for 8 papers or 8000 | ✅ Adaptive: exhaustive / classified / satisficing |
| Chinese + English gap | ❌ English-only misses Chinese papers | ✅ Layer 4: Chinese name search + author cross-ref |
| No cognitive model | ❌ Pure string matching | ✅ Semiotics + linguistics + phonetics + logic |

### vs AI Search (Gemini, Perplexity, Claude)

| Problem | AI Search | Cognitive Search Engine |
|---------|----------|------------------------|
| Transparency | ❌ Black box — can't verify completeness | ✅ 12 phases, each auditable |
| Cost | ❌ High token cost per search | ✅ 75% savings via graph persistence |
| Domain knowledge | ❌ Generic — no species-specific logic | ✅ Latin grammar, IPA, OCR error models |
| Citation graph | ❌ Not leveraged | ✅ Graph traversal: authors → journals → citations |
| Learning | ❌ Stateless — each search independent | ✅ Graph grows with each search |

### Unique Capabilities (No Other Tool Has)

| # | Capability | Why It Matters |
|:--|-----------|---------------|
| 1 | **Review Reference Mining + Verification** | 综述是"二手搜索" — 但先验证再信任 |
| 2 | **Semiotic Reconstruction** | 从拼写错误重建物种身份，而非匹配字符串 |
| 3 | **Adaptive Search Depth** | 8 篇穷举 vs 8000 篇满意即止 — 自动切换 |
| 4 | **Cross-Language Author Graph** | 中文作者发英文论文，英文作者引中文论文 — 全捕获 |
| 5 | **IPA Phonetic Distance** | Ochetobius=O231, Ochetobibus=O231 — 语音相同即相同 |

## ⚡ Three Breakthroughs

### 1. Knowledge Graph Traversal (Not Linear Search)

| Traditional (v2/v3) | Graph Search (v4) |
|---------------------|-------------------|
| 11 layers, sequential | Graph traversal, conditional |
| Results discarded each run | Results persist in graph |
| ~8000 tokens/search | ~2000 tokens/search |
| Every search starts from zero | Known papers: **0 tokens** |

### 2. Energy Efficiency (Satisficing, Not Exhausting)

```
Don't find ALL papers → Find ENOUGH papers.
Satisfice at 8 papers. Stop at diminishing returns.
Cheapest layers first. Only go deeper if needed.
```

### 3. Adaptive Search Depth (v4.1)

```
Volume < 20   → EXHAUSTIVE (e.g., 鳤 only 8 papers — find every single one)
Volume 20-200 → CLASSIFIED (classify first, drill down on demand)
Volume > 200  → SATISFICING (stop when enough representative papers found)
```

### 4. Multi-Discipline Cognitive Engine

| Discipline | Method |
|-----------|--------|
| Semiotics | Signifier decomposition → signified reconstruction |
| Linguistics | Latin morphology, root extraction, OCR error models |
| Phonetics | IPA transcription, Soundex+Metaphone double-code |
| Logic | Deductive chain, abductive inference, inductive pattern |
| DeepSeek CoT | Info-gain ordering, sparse MoE, entropy budget |

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
