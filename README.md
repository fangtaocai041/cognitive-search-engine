# 🕸️ Cognitive Search Engine

**它聪明地搜索物种文献，不遗漏一篇该看的论文，也不浪费一分钱搜无关的。**

[中文版](README.zh.md) · [更新日志](CHANGELOG.md) · [路线图](ROADMAP.md) · [怎么参与](CONTRIBUTING.md)

---

## 🔺 Triangle Core Role: **V1 (Validation)**

> **Part of Triangle Core (三角闭环)**, coordinated by [eon-core](https://github.com/fangtaocai041/eon-core).
> **三角闭环 (Triangle Core)**: fish(V0知识库) + cognitive(V1验证) + eon-core(协调器) — 缺一不可
> **三生万物 (Derived)**: P₁(porpoise) · P₂(coilia) · 无限衍生
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

### 11 搜索引擎（6 MCP 优先 + 5 HTTP 回退）

```
MCP 优先层 (npx 子进程):
  scholar    → Google Scholar / OpenAlex / Semantic Scholar
  article    → Europe PMC + PubMed + Crossref 全文
  ncbi       → PubMed E-utilities (esearch+esummary+efetch)
  tavily     → AI 深度网络搜索
  exa        → 语义网络搜索
  scholarly  → OpenAlex + Semantic Scholar (待集成)

HTTP 回退层 (直连 API):
  pubmed       → NCBI E-utilities REST
  europe_pmc   → Europe PMC REST API
  crossref     → Crossref REST API
  openalex     → OpenAlex REST API (含 abstract 重建)
  arxiv        → arXiv API (属名校验严格过滤)
  cnki_web     → Bing site:cnki.net (中文文献)

去重管线:
  raw → _filter_by_genus(属名校验) → _deduplicate(DOI+标题) → classify
```

### MCP 优先搜索（v5.9.1）

```
# MCP 6引擎并行 → 失败回退 HTTP
python scripts/search_api.py --species "鳤"

管线: 分类学变体 → MCP warmup(6引擎) → 并行搜索 →
      属名校验(_filter_by_genus) → DOI去重 → CN/EN分类
```

```python
from src.search_coordinator import kb_first, continue_full_search

# Stage 1: KB check (fast, no external API)
result = kb_first("珠星三块鱼")
# → KbFirstSearchResult { stage: "kb_check", kb_found: True, ... }

print(result.ask_user_prompt())
# → "📚 f项目知识库已收录… 留步 or 继续搜索?"

# Stage 2: full search (only if user continues)
result = continue_full_search(result, group="full")
# → KbFirstSearchResult { full_search: CoordinatedSearchResult }
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

## 🧭 Future Optimization Trends

| Project | Layer | Near-term (3mo) | Mid-term (6mo) | Long-term (12mo) |
|---------|:-----:|-----------------|-----------------|------------------|
| **cognitive-search-engine** | V1 | SerpAPI Baidu/DuckDuckGo anti-crawl bypass · Exa semantic expansion; target: 21→28 engines, p95 latency 25→15s | Cross-lingual retrieval (CN↔EN bidirectional) · Real-time graph update on search; target: zero cold-start | Self-tuning MoE router — per-species dynamic engine selection; target: 90% recall at 50% token cost |
| **fish-ecology-assistant** | V0 | Literature auto-classification · Contradiction detection pipeline; target: 95% auto-categorization | KB-Graph bidirectional sync · Automated annual review generation; target: 80% synthesis automated | Multi-modal knowledge base (text + image + genomic) · LLM-based research gap suggestion; target: suggest 3 actionable gaps per species |
| **eon-core** | Coord | EventBus throughput optimization · DAG routing with learned priorities; target: inter-project latency <200ms | Cross-project resource-aware scheduling · Distributed coordination across 5+ agents; target: zero-conf project onboarding | Self-healing coordination graph · Autonomous derived-project spawning (三生万物 auto P₃/P₄…); target: new project scaffold in <5min |
| **porpoise-agent** | P₁ | Acoustic monitoring data integration · Population trend dashboard; target: monthly update from field data | ML-based threat assessment (ship strike + fishing + pollution) · Real-time alerting; target: early warning 48h before risk event | Full digital twin — simulate management scenarios · Policy impact prediction; target: recommend optimal conservation action with 90% confidence |
| **coilia-agent** | P₂ | Otolith microchemistry automation pipeline · Migration route reconstruction from trace elements; target: 80% automated | Multi-year spawning ground prediction · Climate scenario simulation; target: forecast recruitment 2yr ahead | Full life-cycle digital twin (egg→adult) · Gene-flow metapopulation model; target: guide hatchery release with 85% recruitment success |
| **culter-agent** | P₃ | Chromosome-level genome assembly pipeline · Trophic niche inference from gut microbiome; target: genome annotation <2wk | Population genomics — adaptive loci discovery · Speciation genomics across Culterinae; target: identify 10+ adaptive loci | Eco-evolutionary simulation — predict species response to environmental change · Integrate genomic + trophic + distribution data; target: 5yr population forecast with 80% accuracy |

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
