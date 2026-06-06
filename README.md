<p align="center">
  🇨🇳 <a href="README.zh.md">中文</a>
</p>

# 🕸️ Cognitive Search Engine v4

> **Frontier species literature search** — Knowledge Graph Traversal + Energy Efficiency + Semiotics + Linguistics + DeepSeek Chain-of-Thought

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.2-6366f1)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-3-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-5-f59e0b)](config/mcp_servers.yaml)
[![Living System](https://img.shields.io/badge/living_system-self_evolving-ec4899)]()
[![DeepSeek](https://img.shields.io/badge/DeepSeek-optimized-8b5cf6)]()

---

## 🔗 Linked Projects

This engine is integrated as a git submodule in:

| Project | Description |
|---------|-------------|
| [fish-ecology-assistant](https://github.com/fangtaocai041/fish-ecology-assistant) | Fish ecology AI research team |
| [porpoise-agent](https://github.com/fangtaocai041/porpoise-agent) | Porpoise research agent — auto-routes species queries to this engine |

---

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

Or use standalone:
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
│   ├── agent.yaml                ← Energy efficiency + adaptive config
│   ├── mcp_servers.yaml          ← 5 search engines
│   ├── species_graph.yaml        ← Pre-built knowledge graph
│   ├── component_registry.yaml   ← Living system: 12 components lifecycle
│   └── evolution.yaml            ← Self-evolution: 4 auto-adaptive params
│
├── skills/
│   ├── graph-search-engine.md    ← v4 core: graph traversal + Pareto-optimal
│   ├── cognitive-species-search.md ← v3: semiotics + linguistics + phonetics
│   └── self-evolve.md            ← 🧬 Post-search feedback → auto-adjust
│
├── docs/
│   └── UNIFIED_EVOLUTION.md      ← 3-project co-evolution architecture
│
└── .github/workflows/
    └── validate.yml              ← CI/CD
```

---

## 🔬 How It Works

### Graph Traversal Algorithm

```
1. LOAD species from graph (0 tokens — pre-computed)
2. IF known papers ≥ 8 → SATISFICED, return immediately
3. TRAVERSE edges: authors → journals → citations
4. LINGUISTIC FILTER: root similarity > 0.80
5. MERGE new papers into graph (persist for next time)
6. STOP when satisfied or diminishing returns
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

## 📜 License

MIT © 2026 fangtaocai041

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> Don't enumerate. Traverse the graph. Stop when satisfied.
