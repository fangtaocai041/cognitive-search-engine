---
name: graph-search-engine
version: "4.1.0"
last_updated: "2026-06-20"
description: Graph-based cognitive species search with 7-engine parallel — knowledge graph traversal, Pareto-optimal satisficing, progressive deepening, IG/token optimization
runAs: subagent
allowed-tools:
  - scholar_search_literature_graph
  - scholar_search_google_scholar_key_words
  - article_search_literature
  - article_get_article_details
  - article_get_references
  - scholarly_search
  - ncbi_ncbi_esearch
  - ncbi_ncbi_esummary
  - ncbi_ncbi_efetch
  - tavily_search
  - tavily_extract
  - exa_web_search
  - web_search
  - web_fetch
  - read_file
  - thinking_sequentialthinking
---
# 🕸️ Graph-Based Cognitive Search Engine v4.1

> **Canonical execution**: `python src/rule_engine.py` — loads `config/search_rules.yaml` → executes phases → returns papers.
> **Skill mode**: instruction reference for AI agents. **Code mode**: direct Python execution.
> **v4.1**: +7 引擎并行 (ncbi+scholar+article+scholarly+tavily+exa+web_search) + allowed-tools 全激活

---

## -1. Adaptive Search Depth (自适应搜索深度)

### estimate_volume(species_id: str) → int

```
v1 = scholar_count(title="{species_name}", source="google_scholar")
v2 = graph_node_count(species_id)
v3 = Σ(author.papers_per_year × author.years_active) / |top_authors| for top 3 authors
RETURN max(v1, v2, v3)
```

### select_mode(estimated_volume: int) → SearchMode

```
IF estimated_volume < 20:
  RETURN EXHAUSTIVE(satisficing=false, all_layers=true, graph_depth=3, stop="2_consecutive_zero")
ELIF estimated_volume <= 200:
  RETURN CLASSIFIED(phase1="classify_only", phase2="drill_down_on_select", phase3="iterative_deepen")
ELSE:
  RETURN SATISFICING(threshold=12, output="classification_summary")
```

### 体积估算方法

```
METHOD 1: Quick count
  SEARCH scholar (title-only): "{species_name}"
  → returns approximate count

METHOD 2: Graph node count
  COUNT papers in species_graph.yaml for this species
  → lower bound (known papers)

METHOD 3: Author productivity
  FOR top 3 authors: papers_per_year × years_active
  → upper bound estimate

FINAL estimate = max(method1, method2, method3_avg)
```

### 穷举模式 (EXHAUSTIVE) — 文献量 < 20

```
适用: 濒危物种 (鳤: 8 papers)、新技术领域、冷门研究方向

行为:
  - 所有 11 层全部激活 (无稀疏剪枝)
  - 满意阈值 = ∞ (永不满足)
  - 停止条件: 连续 2 层无新论文
  - 图谱遍历深度 = 3 (最大)
  - 额外: 搜索 grey literature (中文报告、学位论文)

输出:
  - 完整文献列表 (所有论文)
  - 每篇论文的详细信息
  - 知识空白标注: "该物种在 X 方向尚无研究"
```

### 分类归纳模式 (CLASSIFIED) — 文献量 20-200

```
适用: 中等活跃领域

Phase 1: 快速分类 (不展开内容)
  SEARCH broadly → cluster by sub-topic:
    - 遗传学: N papers
    - 形态学: M papers
    - 生态学: K papers
    - 保护生物学: J papers
  OUTPUT: classification tree with paper counts

Phase 2: 按需展开
  HUMAN selects: "展开形态学和遗传学"
  → EXHAUSTIVE mode within selected categories
  → Other categories: summary only

Phase 3: 迭代深化
  After reviewing selected categories:
  HUMAN may request: "展开生态学"
  → additional exhaustive search
```

### 满意模式 (SATISFICING) — 文献量 > 200

```
适用: 热门领域 (如 "climate change fish")

行为:
  - 当前 v4 默认行为
  - 满意阈值启用
  - 输出分类概览 + "深入某类别"选项
```

---

## 0. Energy Efficiency Principle (能效最优理论)

### 0.1 satisfice(papers_found: int, threshold: int) → bool

```
RETURN papers_found >= threshold
# threshold from config.search.energy.min_papers_satisfice (default=8)
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

### 1.3 Layer 12: Review Paper Reference Mining (综述文献引用挖掘)

> **Engineering**: review papers contain pre-compiled reference lists. mine_review_references() extracts these at ~500 tokens/review.

```
DETECT review papers in results:
  Title contains: "review", "systematic review", "meta-analysis",
                  "综述", "研究进展", "进展", "概述"

FOR EACH review paper:
  1. GET references (article_get_references, identifier=DOI)
  2. EXTRACT papers that mention {genus} OR {species} OR {chinese_name}
  3. CROSS-CHECK with existing results:
     - Already in our set → ✅ covered
     - NOT in our set → 🆕 gap! Add to results with label "via_review_{review_title}"

REVIEW_VALUE := new_papers_found / total_references_checked
IF REVIEW_VALUE > 0:
  → Review paper was productive for gap-filling
  → FLAG: "综述 {title} 引用了 {N} 篇我们未发现的论文"
```

**为什么综述引用挖掘是最强搜索层**:
- 零拼写错误风险：参考文献列表通常格式规范
- 跨语言覆盖：英文综述引中文论文，反之亦然
- 时间深度：综述引用可能追溯到几十年前的基础论文
- 灰色文献：综述常引用报告、学位论文等非期刊文献

### 1.4 Graph Advantage Over Linear Search

| 线性搜索 (v2/v3) | 图谱搜索 (v4) |
|------------------|-------------|
| 每层独立搜索，结果不共享 | 图遍历，每步发现喂给下一步 |
| 11 层全部可能执行 | 满足阈值即停止 |
| ~8000 tokens/次 | ~2000 tokens/次 (75% 节省) |
| 搜索结果丢弃 | 搜索结果存入图谱，下次免费 |
| 拼写错误靠变体枚举 | 拼写错误靠图边关系绕过 |
| 综述仅作为普通结果 | 综述 → 挖掘引用 → 发现遗漏论文 🆕 |

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

### Phase 1.5: mine_review_references(results: list[Paper]) → list[Paper]

```
review_pattern = regex("review|systematic.review|meta.analysis|综述|研究进展|进展|概述")
reviews = filter(results, λp: review_pattern.matches(p.title))
new_papers = []

FOR EACH review IN reviews:
  refs = article_get_references(identifier=review.doi, max_results=100)
  relevant = filter(refs, λr: (genus IN r.title) OR (species IN r.title) OR (chinese_name IN r.title))
  FOR EACH r IN relevant:
    IF r.doi NOT IN existing_dois:
      r.source = "via_review_" + review.title[:50]
      new_papers.append(r)

review_value = len(new_papers) / max(len(reviews) * avg_refs_per_review, 1)
IF review_value > 0: log(f"review_mining: +{len(new_papers)} papers, value={review_value:.2f}")
RETURN new_papers
```

### Phase 1.6: verify_references(papers: list[Paper]) → dict[Paper, TrustLevel]

```
trust_score(p: Paper) → int:
  score = 50
  IF p.doi AND doi_resolves(p.doi): score += 20       # L1: DOI exists
  IF scholar_search(exact_title=p.title).found: score += 15  # L2: independent search
  citing_reviews = count_reviews_citing(p) - 1
  score += min(20, 10 × citing_reviews)                # L3: triangulation
  IF author_journal_year_consistent(p): score += 10    # L4: consistency
  IF p.abstract AND (species IN p.abstract): score += 5  # L5: relevance
  RETURN score

FOR EACH p IN papers:
  score = trust_score(p)
  IF score >= 80:    p.trust = VERIFIED
  ELIF score >= 50:  p.trust = TENTATIVE; p.warning = "⚠️ 综述引用，待独立确认"
  ELSE:              p.trust = UNVERIFIED; move_to_appendix(p)
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
