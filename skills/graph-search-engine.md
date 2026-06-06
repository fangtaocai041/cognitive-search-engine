---
name: graph-search-engine
version: "4.0.0"
last_updated: "2026-06-06"
description: Graph-based cognitive species search with energy efficiency — knowledge graph traversal, Pareto-optimal satisficing, progressive deepening, IG/token optimization
runAs: subagent
allowed-tools:
  - scholar_search_literature_graph
  - article_search_literature
  - scholar_search_google_scholar_key_words
  - tavily_tavily_search
  - thinking_sequentialthinking
---
# 🕸️ Graph-Based Cognitive Search Engine v4

> **核心突破**: 不枚举，不穷举。用知识图谱遍历 + 能效最优理论替代线性 11 层搜索。

---

## 0. Energy Efficiency Principle (能效最优理论)

### 0.1 Satisficing (满意即止)

```
不是"找到所有论文" → 是"找到足够好的论文"
不是 100% recall → 是 Pareto-optimal recall/cost

Satisficing threshold (from agent.yaml):
  min_papers: 8      → 找到 8 篇即满足
  target: 20          → 理想目标
  stop_if: IG_delta < 0.005 for 2 consecutive layers
```

### 0.2 Progressive Deepening (渐进深化)

```
Layer cost order (cheapest first):
  1. Graph lookup (0 tokens — pre-computed)      ← FREE
  2. Exact search (500 tokens)                    ← CHEAP
  3. Author cross-ref (1500 tokens)               ← MEDIUM
  4. Citation traversal (1000 tokens)             ← MEDIUM
  5. Variant search (2000 tokens)                 ← EXPENSIVE
  6. LLM expansion (3000 tokens)                  ← MOST EXPENSIVE

Only go deeper if satisficing not met.
```

### 0.3 IG/Token Optimization (信息增益比)

```
IG_per_token := (new_papers_found) / (tokens_spent)

AFTER each layer:
  IF IG_per_token < 0.005 → PRUNE this layer for this species
  REORDER remaining layers by predicted IG_per_token
```

---

## 1. Knowledge Graph Traversal (图谱搜索核心)

### 1.1 Graph Structure

```
Nodes: Species, Author, Paper, Journal, Institution
Edges: cites, cited_by, co_author, same_journal, same_species, affiliated_with

Pre-loaded from config/species_graph.yaml
```

### 1.2 Graph Traversal Algorithm

```
INPUT: species_id (e.g., "Ochetobius_elongatus")

Step A: Load known papers from graph
  known_papers = GRAPH.query("MATCH (s:Species {id: species_id})-[*1..2]-(p:Paper)")
  → FREE (pre-computed, zero tokens)

Step B: If |known_papers| ≥ min_papers_satisfice:
  → SATISFICED. Skip remaining layers.
  → RETURN known_papers

Step C: Traverse edges to discover unknown papers
  FOR EACH known_paper:
    # Edge type 1: same authors
    FOR EACH author IN known_paper.authors:
      new_papers = GRAPH.query("MATCH (a:Author)-[:wrote]->(p:Paper) WHERE p.year >= {min_year}")
    
    # Edge type 2: same journal
    new_papers += SEARCH(journal=known_paper.journal, keyword=species.chinese, year≥min_year)
    
    # Edge type 3: citation forward
    new_papers += GET_CITING_PAPERS(known_paper.doi)
    
    # Edge type 4: citation backward
    new_papers += GET_REFERENCES(known_paper.doi)

Step D: Deduplicate + filter for species relevance
  FILTER: title contains {genus_root} OR {species} OR {chinese_name}
  LINGUISTIC FILTER: root_similarity(title, genus_root) > 0.80

Step D: Add discovered papers to graph
  GRAPH.merge(new_papers) → future searches are FREE
```

### 1.3 Graph Advantage Over Linear Search

| 线性搜索 (v2/v3) | 图谱搜索 (v4) |
|------------------|-------------|
| 每层独立搜索，结果不共享 | 图遍历，每步发现喂给下一步 |
| 11 层全部可能执行 | 满足阈值即停止 |
| ~8000 tokens/次 | ~2000 tokens/次 (75% 节省) |
| 搜索结果丢弃 | 搜索结果存入图谱，下次免费 |
| 拼写错误靠变体枚举 | 拼写错误靠图边关系绕过 |

---

## 2. Search Protocol (Energy-Efficient)

### PREFLIGHT: Graph Lookup (0 tokens)

```
READ config/species_graph.yaml
LOAD known papers for target species
IF |known_papers| ≥ config.search.energy.min_papers_satisfice:
  → DONE. Return known papers. Zero token cost.
```

### Phase 1: Exact + Author (500 + 1500 tokens)

```
Search exact name → if satisficed, STOP
Search by known authors from graph → if satisficed, STOP
```

### Phase 2: Citation Traversal (1000 tokens)

```
For each known paper with DOI:
  Get references + citing papers
Filter for species relevance via root matching
If satisficed, STOP
```

### Phase 3: Variant + Journal (2000 + 1200 tokens)

```
ONLY if still below satisficing threshold:
  Search typo variants from graph
  Search target journals for species Chinese name
```

### Phase 4: LLM Expansion (3000 tokens) — LAST RESORT

```
ONLY if all above layers failed to reach satisficing:
  Generate alternative queries via reasoning
  Search with LLM-generated queries
```

---

## 3. Pareto-Optimal Stopping

```
STOP search when:
  1. |papers| ≥ min_papers_satisfice (8) → "good enough"
  2. IG_per_token < 0.005 for 2 consecutive layers → "diminishing returns"
  3. Cumulative tokens > max_total_tokens (50000) → "budget exhausted"
  4. All edge types traversed up to max_depth (3) → "graph exhausted"

RETURN:
  - papers found
  - tokens_spent
  - layers_activated (sparse activation count)
  - efficiency_score = papers / (tokens_spent / 1000)
  - graph_growth: new nodes added to graph
```

---

## 4. Output: Energy Efficiency Report

```markdown
## 🕸️ Graph Search Report: {species}

### Energy Efficiency
- Tokens spent: {tokens} / {budget} ({usage}%)
- Papers found: {papers} (satisficing: {satisficed})
- Efficiency: {efficiency} papers per 1000 tokens
- Layers activated: {active}/{total} (sparse MoE)
- Stop reason: {stop_reason}

### Graph Growth
- Pre-existing nodes: {pre}
- New nodes discovered: {new}
- Graph now has: {total} nodes, {edges} edges
- Next search: ~0 tokens for loaded nodes

### vs Linear Search (v2/v3)
- Token savings: {savings}%
- Same papers found: {recall}%
```

---

> **"不枚举，不穷举。遍历图谱，满意即止。"**
> **Don't enumerate. Traverse the graph. Stop when satisfied.**
