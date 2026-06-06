# 🕸️ Cognitive Search Engine v4

> **Frontier species literature search** — Knowledge Graph Traversal + Energy Efficiency + Semiotics + Linguistics + DeepSeek Chain-of-Thought

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-6366f1)](config/agent.yaml)
[![Skills](https://img.shields.io/badge/skills-2-22c55e)](skills/)
[![MCP](https://img.shields.io/badge/MCP-5-f59e0b)](config/mcp_servers.yaml)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-optimized-8b5cf6)]()
[![submodule](https://img.shields.io/badge/git-submodule-ec4899)]()

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
│   ├── agent.yaml                ← Energy efficiency config
│   ├── mcp_servers.yaml          ← 5 search engines (Scholar, Article, Tavily, Exa, Scholarly)
│   └── species_graph.yaml        ← Pre-built knowledge graph
│
├── skills/
│   ├── graph-search-engine.md    ← v4 core: graph traversal + Pareto-optimal
│   └── cognitive-species-search.md ← v3: semiotics + linguistics + phonetics
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
