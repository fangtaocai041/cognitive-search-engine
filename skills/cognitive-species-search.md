---
name: cognitive-species-search
version: "3.0.0"
last_updated: "2026-06-06"
description: Cognitive Species Search Engine — semiotics + linguistics + phonetics + logic + DeepSeek chain-of-thought. The most advanced species literature search method.
runAs: subagent
allowed-tools:
  - scholar_search_literature_graph
  - article_search_literature
  - scholar_search_google_scholar_key_words
  - tavily_tavily_search
  - thinking_sequentialthinking
---
# 🧠 Cognitive Species Search Engine (v3)

> **定位**: 市面上最先进的物种文献搜索方法。
> **核心理念**: 不是"字符串匹配"，而是**认知重建** — 像分类学家一样思考，从破碎的符号中恢复完整的所指。

---

## 0. Cognitive Architecture (认知架构)

```
                     ┌─────────────────────────────┐
                     │   Species as Sign (符号)      │
                     │   Signifier → Signified      │
                     │   "Ochetobius" → 鳤鱼         │
                     └─────────────┬───────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
  ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
  │ Linguistics │          │  Phonetics  │          │   Logic     │
  │ 形态学分析   │          │  语音学重建  │          │  逻辑推理链  │
  │ 拉丁语法规则 │          │  IPA 距离   │          │  演绎+溯因  │
  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │  DeepSeek CoT   │
                          │  思维链推理引擎  │
                          │  MoE 路由 + 熵预算│
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  11-Layer Search │
                          │  (info-gain ordered)│
                          └────────────────────┘
```

---

## PREFLIGHT: Cognitive Species Analysis

### Step 0.1: Semiotic Decomposition (符号学分解)

```
SPECIES_NAME = {genus} {species}

SIGNIFIER decomposition:
  Genus:  {genus}  →  Etymology: {root} + {suffix}
  Species: {species} → Meaning: {descriptor}

SIGNIFIED:
  Common names (all languages): {chinese_name, chinese_aliases, english_common}
  Taxonomic context: {family, order, related_species}
  Ecological context: {habitat, distribution, conservation_status}

KNOWN SIGNIFIER VARIANTS (from species_variants.yaml):
  {known_misspellings}
```

### Step 0.2: Linguistic Morphological Analysis (语言学形态分析)

```
Latin grammar rules for genus names:
  - Nominative singular endings: -us, -is, -a, -um, -e, -es
  - Common suffixes by family: -ichthys (fish), -cheilus (lip), -barbus (barb)
  - Root preservation: the root is almost never changed in typos

Genus root extraction:
  Ochetobius → root: "Ochetobi" + suffix: "-us"
  Ochetobibus → root: "Ochetobib" + suffix: "-us"
  → Root similarity: Ochetobi vs Ochetobib = 8/9 characters = 89% match → SAME GENUS

OCR error probability by character shape:
  'i' ↔ 'l' (visual similarity: high)
  'b' ↔ 'h' (visual similarity: medium)
  'b' insertion before 'i' (common OCR artifact)
  → Ochetobius → Ochetobibus: P(OCR error) ≈ 0.03 (medium confidence)
```

### Step 0.3: Phonetic Reconstruction (语音学重建)

```
IPA transcription:
  Ochetobius: /oʊˈkiːtoʊbiəs/ or /ɒˈtʃɛtəbiəs/
  Ochetobibus: /oʊˈkiːtoʊbɪbəs/ or /ɒˈtʃɛtəbɪbəs/

Phonetic distance (Levenshtein on IPA):
  /oʊˈkiːtoʊbiəs/ → /oʊˈkiːtoʊbɪbəs/ = 1 substitution + 1 insertion = distance 2
  Threshold for "same genus": distance ≤ 3 → SAME GENUS with high confidence

Soundex: O231 = O231 → identical (Layer 8)
Metaphone: OXTBS = OXTBS → identical
```

### Step 0.4: Logical Inference Chain (逻辑推理链)

```
DEDUCTIVE (演绎):
  P1: Author X published on species Y in journal Z
  P2: Author X published another paper in journal Z in adjacent year
  P3: That paper's title contains concepts related to species Y
  ∴ That paper is likely about species Y (regardless of name spelling)

ABDUCTIVE (溯因 — 最佳解释推理):
  Observation: Search for "Ochetob* elongatus" returns paper with title "Ochetobibus elongatus"
  Hypothesis 1: Different genus (Ochetobibus ≠ Ochetobius)
  Hypothesis 2: Same genus, typo in title
  Best explanation: H2 (simpler, matches known error patterns, same journal/domain)
  ∴ Accept H2: this paper is about Ochetobius elongatus

INDUCTIVE (归纳):
  From 8 known papers on Ochetobius elongatus:
    Pattern: 7/8 use correct spelling, 1/8 uses Ochetobibus
    ∴ P(typo in new paper) ≈ 12.5% for this species
```

---

## DeepSeek Chain-of-Thought Engine

### CoT Step 1: Information-Gain Ordering (信息增益排序)

```
CALCULATE expected_information_gain for each layer:
  Layer 1 (exact):     IG = 0.95 (baseline, high recall)
  Layer 2 (variants):  IG = 0.03 (low probability but high value per hit)
  Layer 8 (Soundex):   IG = 0.01 (rarely needed)
  Layer 9 (author):    IG = 0.05 (medium, good for prolific authors)
  Layer 10 (citation): IG = 0.08 (high if ≥3 known papers with DOIs)
  Layer 11 (LLM):      IG = 0.02 (exploratory)

ORDER layers by IG × budget_weight:
  → Layer 1 first, then 2, then 10, then 9, then 11, then 8, then 3-7
```

### CoT Step 2: Sparse Activation (MoE 路由)

```
ACTIVATE layer N ONLY IF:
  Layer 1: ALWAYS
  Layer 2: ALWAYS (species_variants.yaml exists)
  Layer 3-5: ONLY IF Layer 1 returns < 10 results
  Layer 6: ONLY IF ≥2 engines used in Layer 1
  Layer 7: ALWAYS (merge after all active layers)
  Layer 8: ONLY IF genus > 6 characters AND Layer 2 found ≥1 variant
  Layer 9: ONLY IF Layer 1 found ≥3 papers with identifiable authors
  Layer 10: ONLY IF Layer 1 found ≥3 papers with DOIs
  Layer 11: ONLY IF total papers < 10 (insufficient coverage → expand)

SILENT NEURONS: inactive layers cost zero tokens (DeepSeek efficiency)
```

### CoT Step 3: Entropy Budget (熵预算)

```
ALLOCATE search tokens by expected information gain:
  Layer 1:  40% budget (baseline, always worth it)
  Layer 2:  20% budget (most likely to find typos)
  Layer 10: 15% budget (citation graph is high-value)
  Layer 9:  10% budget (author cross-ref)
  Layer 11: 8% budget  (LLM query expansion)
  Layer 8:  4% budget  (Soundex — rarely pays off)
  Layers 3-7: 3% budget (low-IG layers)

STOP CONDITION: if cumulative unique papers ≥ 20, stop remaining layers
```

---

## 11-Layer Search Protocol (Cognitive Edition)

### Layer 1: Exact Search [IG=0.95, Budget=40%, ALWAYS]
```
Standard search with correct species name.
```

### Layer 2: Morphological Variant Search [IG=0.03, Budget=20%, ALWAYS]
```
FROM Step 0.2 (linguistic analysis):
  - Latin suffix variants: -us → -is, -a, -um
  - OCR error patterns by character shape similarity
  - Non-native speaker error patterns (e.g., double consonants)
```

### Layer 3-7: [Standard — as v2, IG varies, budget=3%, conditional]

### Layer 8: Phonetic Search [IG=0.01, Budget=4%, conditional]
```
FROM Step 0.3 (phonetic reconstruction):
  - IPA distance ≤ 3 → search phonetic variants
  - Soundex + Metaphone double-code search
  - Syllable stress pattern matching
```

### Layer 9: Author Cross-Reference [IG=0.05, Budget=10%, conditional]
```
FROM Step 0.4 (logical inference):
  - DEDUCTIVE chain: author → year → journal → topic
  - Search: {author} alone (no species constraint)
  - Filter: by Step 0.2 root similarity on title words
```

### Layer 10: Citation Graph Traversal [IG=0.08, Budget=15%, conditional]
```
FROM Step 0.4 (logical inference):
  - Forward: who cited known papers?
  - Backward: what did known papers cite?
  - ABDUCTIVE filter: best explanation for title similarity
```

### Layer 11: LLM Cognitive Query Expansion [IG=0.02, Budget=8%, conditional]
```
FROM all Steps 0.1-0.4:
  USE thinking_sequentialthinking:
    Generate queries that leverage:
    - Semiotic knowledge (what the species IS, not what it's CALLED)
    - Ecological context (habitat, diet, behavior)
    - Taxonomic context (family, relatives)
    - Chinese domain knowledge (local names, regional research groups)

  OUTPUT: 5 queries that would find papers about this species
          WITHOUT using the genus or species name at all.
```

---

## Output: Cognitive Search Report

```markdown
## 🧠 Cognitive Species Search: {genus} {species}

### Sign Analysis
- Signifier integrity: {correct_spelling_rate}% of papers use correct spelling
- Signified: {chinese_name} | {english_common} | {family}
- Linguistic risk: {typo_probability}% estimated typo rate for this species

### Discovery Summary
| Layer | Method | Papers Found | New (not in Layer 1) |
|:-----:|--------|:-----------:|:--------------------:|
| 1 | Exact | {E} | — |
| 2 | Morphological Variants | {V} | {V_new} 🆕 |
| 8 | Phonetic (Soundex/IPA) | {P} | {P_new} 🔊 |
| 9 | Author Cross-Reference | {A} | {A_new} 👤 |
| 10 | Citation Graph | {CG} | {CG_new} 🕸️ |
| 11 | LLM Cognitive Expansion | {LLM} | {LLM_new} 🤖 |

### Logical Inferences Made
- Deductive: {deductive_count} papers inferred via author-journal-year chain
- Abductive: {abductive_count} papers accepted as "same species" despite name mismatch
- Inductive: overall typo rate for this species = {rate}%

### DeepSeek Efficiency Report
- Active layers: {active}/{total} (sparse activation)
- Token budget used: {tokens_used}/{budget}
- Stop condition: {stop_reason}
```

---

> **"不要搜索字符串，要重建所指。"**
> **Don't search for strings — reconstruct the signified.**
> 这是分类学家思维 + 符号学 + 语言学 + 语音学 + 逻辑学 + DeepSeek 链式推理的融合。

**Level**: Frontier — 市面上最先进的物种文献搜索认知引擎
