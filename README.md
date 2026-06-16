# 🕸️ Cognitive Search Engine

**它聪明地搜索物种文献，不遗漏一篇该看的论文，也不浪费一分钱搜无关的。**

[中文版](README.zh.md) · [更新日志](CHANGELOG.md) · [怎么参与](CONTRIBUTING.md)

---

## 🔺 Triangle Core Role: **V1 (Validation)**

> **Part of Triangle Core**, coordinated by [eon-core](https://github.com/fangtaocai041/eon-core).
> **Triangle Core**: fish(V0) + cognitive(V1) + eon-core(Coordinator)
> **Derived (三生万物)**: P₁(porpoise) · P₂(coilia) · ...
>
> Validates search results, authority credibility scoring, enforces triangulation (≥3 sources, ≥2 projects).
> **DirectLoader**: `importlib` zero MCP process. **Triangulation**: ≥3 sources, ≥2 independent projects.

---

## What It Does

Enter a species name, it:

1. **Estimates literature volume** — PubMed, Crossref, OpenAlex pre-flight
2. **Decides search strategy** — few → exhaustive, moderate → classified, many → review-anchored
3. **Searches 21 engines in parallel** — SerpAPI·Exa·Europe PMC·NCBI·OpenAlex·Semantic Scholar·CNKI·more
4. **Deduplicates + scores** — journal whitelist (0-100)
5. **Detects gaps** — which directions are under-studied
6. **Self-evolves** — more searches → better parameters

**Keywords**: species · literature · multi-source search · credibility scoring · BDI cognitive cycle

---

## Quick Start

### One-liner in code

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")

print(f"{len(result.papers)} papers, {result.elapsed_s:.1f}s")
```

### CLI

```bash
python scripts/search_api.py --species "鳤"
python scripts/search_api.py --species "Pseudaspius hakonensis" --max 20
```

### From other projects

```python
from src.adapter import CognitiveSearchAdapter

adapter = CognitiveSearchAdapter()
result = adapter.search("珠星三块鱼", mode="adaptive")
```

---

## How It Works

### 6+ Search Channels (MCP + HTTP)

```
MCP (requires npx/node):
  scholar    → Google Scholar / OpenAlex / Semantic Scholar
  article    → Europe PMC / PubMed / Crossref full-text
  tavily     → AI deep web search
  exa        → Semantic web search
  ncbi       → PubMed E-utilities direct
  scholarly  → OpenAlex + Semantic Scholar

HTTP (no dependencies):
  pubmed     → NCBI E-utilities REST
  crossref   → Crossref REST API
  openalex   → OpenAlex REST API
  arxiv      → arXiv API
  europe_pmc → Europe PMC REST API
  cnki       → Bing Chinese literature search
```

Auto-generates OCR spelling variants (`Ochetobius` → `Ochetobibus`, `Ocheotbius`…), preventing typo misses.

### Credibility Scoring

```
Score = 50(base) + 30(SCI journal) + 25(CSCD core) + 10(DOI) + 10(PMID)
        - 30(preprint) - 100(predatory)
```

| Score | Mark | Meaning |
|-------|------|---------|
| ≥80 | 🟢 | Highly credible, SCI/Q1 journal |
| 60–79 | 🟡 | Moderate, peer-reviewed |
| 40–59 | 🟠 | Low, preprint/thesis |
| <40 | 🔴 | Untrustworthy, predatory |

### Project Structure

```
cognitive-search-engine/
├── config/           # Config (search rules, species graph, MCP servers)
├── src/              # Python source
│   ├── meso_agent.py       ← BDI cognitive loop, search entry
│   ├── mcp_client.py       ← MCP subprocess management + tool discovery
│   ├── parallel_search.py  ← HTTP direct search (6 sources parallel)
│   ├── unified_search.py   ← Search protocol + taxonomy service + engine registry
│   ├── search_coordinator.py ← Unified search coordinator
│   ├── validator.py        ← Paper validation
│   ├── credibility_scorer.py ← Journal whitelist scoring
│   ├── variant_generator.py  ← OCR spelling variants
│   ├── inference_engine.py ← Inference enhancement (gap detection)
│   ├── evolution_executor.py ← Self-evolution parameter tuning
│   ├── world_model.py      ← Pre-search simulation
│   ├── adapter.py          ← Cross-project interface
│   └── report_formatter.py ← Categorized report output
├── scripts/          # CLI tools (search_api, credibility_scorer, kb_to_graph_sync, self_evolve)
├── skills/           # Reasonix AI playbooks
└── tests/
```

---

## Works With

```
Triangle Core + Derived (跨项目)
├── V0  fish-ecology-assistant   → Knowledge base + data + contradiction
├── V1  cognitive-search-engine  → Validation ← THIS PROJECT
├── Coord  eon-core              → EventBus + DAG routing
│
├── P₁  porpoise-agent           → Derived: 江豚种群监测
└── P₂  coilia-agent             → Derived: 刀鲚洄游生态
```

This engine is the **exclusive search gateway** for the entire workspace. All external search requests route through it first.

---

## Installation

```bash
pip install pyyaml        # Config reading
pip install requests      # HTTP (optional, uses urllib by default)
```

Python 3.10+. Windows/Linux/macOS.

---

## License

MIT © 2026 fangtaocai041
