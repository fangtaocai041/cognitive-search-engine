# Architecture: 5-Layer Standard Agent Model

> **Cognitive Search Engine v5.0** — BDI + ReAct + Multi-Layer Memory

---

## Overview

The Cognitive Search Engine implements the **Standard Agent Architectural Model**
— a 5-layer architecture widely recognized in academic AI (BDI, ReAct, MDP/POMDP)
and industrial agent frameworks (LangChain, AutoGPT).

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1 · PERCEPTION                                    │
│  Input: species_id, genus+species, Chinese name, DOI     │
│  → Parse → Validate → Route to cognitive layer           │
├──────────────────────────────────────────────────────────┤
│  Layer 2 · COGNITIVE (BDI + ReAct)                       │
│  Think → Act → Observe → Reflect                         │
│  π(Belief, Desire) → Intention                           │
├──────────────────────┬───────────────────────────────────┤
│  Layer 3 · MEMORY    │  Layer 4 · MAPPING                │
│  Short-term: context │  Intention → tools → queries      │
│  Long-term: graph    │  NL → URL / JSON-RPC              │
├──────────────────────┴───────────────────────────────────┤
│  Layer 5 · EXECUTION                                     │
│  PubMed · Crossref · scholar-mcp · article-mcp           │
│  HTTP REST + MCP JSON-RPC stdio                          │
└──────────────────────────────────────────────────────────┘
```

---

## Layer 1: Perception (交互与感知层)

**Module:** `SearchRuleEngine.execute(species_id)`

Receives search requests and normalizes them into structured inputs.

| Input Type     | Example                          | Parsed To                        |
|----------------|----------------------------------|----------------------------------|
| Species ID     | `Ochetobius_elongatus`           | genus=`Ochetobius`, species=`elongatus` |
| Chinese name   | `鳤`                             | fetched from `species_graph.yaml` |
| DOI            | `10.1038/s41597-024-04223-x`     | direct paper lookup              |

**Future:** multimodal — image → species identification → search

---

## Layer 2: Cognitive (认知与决策层)

**Module:** `src/agent_core.py` → `CognitiveAgent`

### BDI Model

The classic Belief-Desire-Intention architecture maps directly to search:

| BDI      | Search Analog                                         |
|----------|-------------------------------------------------------|
| **Belief** | `WorldModel.current_belief()` — papers found, tokens spent, IG history, phase states |
| **Desire** | `WorldModel.desire()` — min 8 papers, ≤50000 tokens, precision ≥0.85 |
| **Intention** | `WorldModel.form_intention()` — which phases to execute, in what order |

**Formal policy:** `π(B_t, D) → I_t`

### ReAct Loop

Each search round follows the ReAct pattern:

```
Round i:
  1. THINK    → form_intention(belief, desire) → active_phases
  2. ACT      → execute phase (delegate to rule_engine._execute_phase)
  3. OBSERVE  → count new papers, compute IG, update belief
  4. REFLECT  → compare belief vs desire → continue | restructure | stop
```

### Stopping conditions
- Desire satisfied: `papers_found ≥ min_papers` (8)
- Budget exhausted: `tokens_spent ≥ max_tokens` (50000)
- Diminishing returns: 2 consecutive zero-yield phases
- Declining IG: 3-phase decreasing trajectory → restructure

### Future paradigms (planned)
- **Tree of Thoughts (ToT):** generate multiple phase candidates, heuristic evaluation, backtracking
- **Graph of Thoughts (GoT):** DAG-structured reasoning with branch merging

---

## Layer 3: Memory (记忆系统层)

**Module:** `src/memory_layer.py` → `MemorySystem`

### Short-term Memory: ContextTracker

```python
M_{t+1} = Φ(M_t, O_t, A_t)
```

- `M_t`: list of `PhaseTrace` objects (phase name, papers found, tokens, IG, errors)
- `O_t`: observation from last action (new paper count, IG value)
- `A_t`: action taken (phase name)
- `Φ`: append trace, update accumulators

Analogous to the **LLM context window** — tracks what the agent
"remembers" about the current task.

### Long-term Memory: GraphMemory

Persistent storage backed by `config/species_graph.yaml` with reverse indexes:

| Index       | Query Example                          |
|-------------|----------------------------------------|
| DOI → Paper | `get_paper_by_doi("10.1038/...")`      |
| Species → DOIs | `get_papers_by_species("Ochetobius_elongatus")` |
| Author → DOIs | `get_papers_by_author("Yang Jiping")`  |
| Journal → DOIs | `get_papers_by_journal("Animals")`     |

**Future:** vector index (sentence-transformers → Chroma/Qdrant) for semantic similarity search (RAG).

---

## Layer 4: Mapping (逻辑映射与转换层)

**Module:** `search_rules.yaml` + `PHASE_FUNCTIONS` registry

Bridges semantic intent to executable tool calls.

```
Intention: ["exact_search", "variant_search"]
     │
     ▼
PhaseSpec: { function: "search_scholar_article", tools: ["scholar_search_literature_graph"], budget: 500 }
     │
     ▼
Serialization: "Ochetobius elongatus" → URL-encoded PubMed E-utilities query
               or JSON-RPC: {"method": "tools/call", "params": {"name": "scholar_search_literature_graph", ...}}
```

### Activation conditions

Phases are activated based on context evaluation:

```yaml
activation: "len(all_papers) < config.search.energy.min_papers_satisfice"
```

Evaluated against current `ctx` + `belief` — if false, phase is skipped.

---

## Layer 5: Execution (工具与执行层)

**Module:** `rule_engine._http_search()`, `_mcp_search()`, `_mock_search()`

### Search tools

| Tool            | Protocol          | Description                       |
|-----------------|-------------------|-----------------------------------|
| PubMed E-utilities | HTTP REST      | NCBI ESearch + EFetch (XML)      |
| Crossref API    | HTTP REST         | `/works?query=...`               |
| scholar-mcp     | JSON-RPC stdio    | Google Scholar via MCP           |
| article-mcp     | JSON-RPC stdio    | Europe PMC + PubMed + Crossref   |
| scholarly-mcp   | JSON-RPC stdio    | OpenAlex + Semantic Scholar      |

### Precision gates

All external search results pass through `_matches_species_context()`:
- Title must contain target **genus** (e.g., "Ochetobius")
- OR title must contain **Chinese name** (e.g., "鳤")
- OR title must contain species epithet **plus biology keyword** (e.g., "elongatus" + "fish"/"genetic"/"conservation")

This prevents false matches like `Ophiodon elongatus` (a different fish genus).

### Error handling
- HTTP timeout → exception → empty result (no crash)
- MCP server unavailable → fallback to mock/HTTP
- XML parse error → skip malformed record → continue

---

## System Data Flow

```
User: "搜索 鳤 的文章"
  │
  ▼
[Layer 1 · Perception]
  Parse: species_id="Ochetobius_elongatus", genus="Ochetobius",
         species="elongatus", chinese="鳤"
  │
  ▼
[Layer 3 · Memory · Recall]
  GraphMemory.get_papers_by_species("Ochetobius_elongatus") → 11 papers
  ContextTracker.start_search()
  │
  ▼
[Layer 2 · Cognitive · BDI]
  Belief.init(known=11) → Desire(≥8 papers)
  │
  ▼
[Layer 2 · Cognitive · ReAct · Think]
  π(Belief, Desire) → Intention: ["exact_search"]
  │
  ▼
[Layer 4 · Mapping]
  Intention → PhaseSpec("exact_search") → tool="scholar_search_literature_graph"
  Serialize: query="Ochetobius elongatus" → URL-encoded
  │
  ▼
[Layer 5 · Execution]
  PubMed ESearch → 5 PMIDs → EFetch → 5 Paper records
  │
  ▼
[Layer 2 · Cognitive · ReAct · Observe]
  Belief.total_papers_found += 5 → 16
  │
  ▼
[Layer 2 · Cognitive · ReAct · Reflect]
  16 ≥ 8 → Desire satisfied → STOP
  │
  ▼
[Layer 3 · Memory · Persist]
  GraphMemory.add_papers_batch(new_papers) → save to YAML
  │
  ▼
[Layer 1 · Perception · Output]
  Return: { paper_count: 16, papers: [...], bdi_trace: {...}, memory_state: {...} }
```

---

## BDI Lifecycle

```
search_start
     │
     ▼
  init_belief(species_id, graph_known_count)
     │
     ▼
  ┌─────────────────────────────────────┐
  │          ReAct Loop                 │
  │                                     │
  │  belief  ← world.current_belief()   │
  │  desire  ← world.desire()           │
  │  intent  ← form_intention(b, d)     │  ← THINK
  │                                     │
  │  for phase in intent.active_phases: │
  │    result ← execute(phase)           │  ← ACT
  │    observe(phase, papers, tokens)    │  ← OBSERVE
  │    reflect(belief, desire)           │  ← REFLECT
  │                                     │
  │  if desire.satisfied(belief): break │
  └─────────────────────────────────────┘
     │
     ▼
  world.update(prediction, actual_papers, actual_tokens)
     │
     ▼
  memory.commit_to_long_term()
     │
     ▼
search_end
```

---

## Key Metrics

| Metric                  | Formula                                   |
|-------------------------|-------------------------------------------|
| Information Gain (IG)   | `new_papers / (tokens_used / 1000)`       |
| Precision               | `relevant_papers / total_papers`          |
| Prediction Accuracy     | `1.0 - mean(|predicted - actual| / predicted)` |
| Efficiency              | `papers_found / (tokens_spent / 1000)`    |

---

## Related Documents

- `config/agent.yaml` — full configuration with 5-layer parameters
- `config/search_rules.yaml` — phase definitions (mapping layer)
- `config/species_graph.yaml` — long-term memory store
- `config/evolution.yaml` — adaptive parameter auto-tuning
- `config/stv_protocol.yaml` — cross-project STV triangle protocol
- `docs/UNIFIED_EVOLUTION.md` — co-evolution across 3 projects
