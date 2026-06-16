# 🧭 Project Roadmap — Future Optimization Trends

> **Triangle Core + Derived**: Built-in optimization direction for all 6 projects.
> Updated: 2026-07-17

---

## 1. Overview

This roadmap defines the **unified optimization direction** across the entire eon-workspace.
Each project has 3 time horizons with **quantified targets**.

### Legend

| Symbol | Meaning |
|--------|---------|
| 🟢 | Achieved / Baseline |
| 🟡 | In progress |
| 🔴 | Not started |
| 🎯 | Milestone target |

---

## 2. Project Roadmaps

### 2.1 cognitive-search-engine (V1 — Validation)

**Current baseline**: 21 engines, p95 latency 25s, ~2500 tokens/search

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | SerpAPI Baidu/DuckDuckGo anti-crawl bypass | 21→28 engines, p95 25→15s | 🟡 |
| | Exa semantic search expansion | +3 semantic engines | 🟡 |
| | HTTP connection pool reuse | Reduce reconnect overhead 60% | 🟡 |
| | Chinese journal direct API (CNKI/Wanfang) | +2 native Chinese engines | 🔴 |
| **Mid (6mo)** | Cross-lingual CN↔EN bidirectional retrieval | Translate queries + cross-match results | 🔴 |
| | Real-time graph update on search | Zero cold-start for re-searched species | 🔴 |
| | Adaptive engine pruning per species | Skip irrelevant engines, save 30% tokens | 🔴 |
| | 🎯 **Baseline: 28 engines, p95 15s** | | 🟡 |
| **Long (12mo)** | Self-tuning MoE router per species | Dynamic engine selection per species | 🔴 |
| | 🎯 **90% recall at 50% token cost** | | 🔴 |
| | Fully automated gap analysis | "Species X has no papers on Y" | 🔴 |

---

### 2.2 fish-ecology-assistant (V0 — Knowledge)

**Current baseline**: Manual categorization, basic contradiction detection

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | Literature auto-classification pipeline | 95% auto-categorization accuracy | 🔴 |
| | Contradiction detection (same paper, conflicting data) | Flag 90% of real contradictions | 🔴 |
| **Mid (6mo)** | KB-Graph bidirectional sync | Push new papers to species_graph.yaml automatically | 🔴 |
| | Automated annual review generation | Species status summary from latest 20 papers | 🔴 |
| | 🎯 **80% synthesis automated** | | 🔴 |
| **Long (12mo)** | Multi-modal knowledge base (text + image + genomic) | Unified query across data types | 🔴 |
| | LLM-based research gap suggestion | Per species: 3 actionable research directions | 🔴 |
| | 🎯 **Self-updating knowledge base** | | 🔴 |

---

### 2.3 eon-core (Coord — Coordination)

**Current baseline**: Basic EventBus, DAG routing, 3-project coordination

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | EventBus throughput optimization | 10,000 events/s sustained | 🟡 |
| | DAG routing with learned priorities | Reduce idle agent wait by 40% | 🔴 |
| | 🎯 **Inter-project latency <200ms** | | 🔴 |
| **Mid (6mo)** | Cross-project resource-aware scheduling | Prioritize critical-path agents | 🔴 |
| | Distributed coordination 5+ agents | Plug-and-play new project onboarding | 🔴 |
| | 🎯 **Zero-config project onboarding** | | 🔴 |
| **Long (12mo)** | Self-healing coordination graph | Auto-detect and bypass failed agents | 🔴 |
| | Autonomous derived-project generation | Scaffold P₃/P₄... from template in <5min | 🔴 |
| | 🎯 **Triple-core fully autonomous** | | 🔴 |

---

### 2.4 porpoise-agent (P₁ — 江豚监测)

**Current baseline**: Field survey data, manual threat assessment

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | Acoustic monitoring data integration | Real-time passive acoustic feed | 🔴 |
| | Population trend dashboard | Monthly update from field data | 🔴 |
| | 🎯 **Monthly population update** | | 🔴 |
| **Mid (6mo)** | ML-based threat assessment | Ship strike + fishing + pollution risk scores | 🔴 |
| | Real-time alerting system | 🎯 **Early warning 48h before risk event** | 🔴 |
| **Long (12mo)** | Full digital twin | Simulate management scenarios (reserve design, fishing ban) | 🔴 |
| | Policy impact prediction | 🎯 **Recommend optimal action with 90% confidence** | 🔴 |

---

### 2.5 coilia-agent (P₂ — 刀鲚洄游)

**Current baseline**: Manual otolith analysis, basic migration mapping

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | Otolith microchemistry automation pipeline | Sr:Ca, Ba:Ca auto-analysis | 🟡 |
| | Migration route reconstruction | From trace element profiles | 🔴 |
| | 🎯 **80% automated otolith analysis** | | 🟡 |
| **Mid (6mo)** | Multi-year spawning ground prediction | Identify spawning sites from larval surveys | 🔴 |
| | Climate scenario simulation | Water temp + flow → spawning success | 🔴 |
| | 🎯 **Forecast recruitment 2yr ahead** | | 🔴 |
| **Long (12mo)** | Full life-cycle digital twin (egg→adult) | Individual-based model | 🔴 |
| | Gene-flow metapopulation model | Guide hatchery release strategy | 🔴 |
| | 🎯 **85% recruitment success from guided release** | | 🔴 |

---

### 2.6 culter-agent (P₃ — 鲌类基因组)

**Current baseline**: (Project initialized — minimal tooling)

| Horizon | Goals | Targets | Status |
|---------|-------|---------|--------|
| **Near (3mo)** | Chromosome-level genome assembly pipeline | Standardized assembly + annotation workflow | 🔴 |
| | Trophic niche inference from gut microbiome | 16S + stomach content analysis pipeline | 🔴 |
| | 🎯 **Genome annotation <2 weeks** | | 🔴 |
| **Mid (6mo)** | Population genomics — adaptive loci discovery | Selection scans across Culterinae | 🔴 |
| | Speciation genomics | Phylogenomic analysis of genus-level relationships | 🔴 |
| | 🎯 **Identify 10+ adaptive loci** | | 🔴 |
| **Long (12mo)** | Eco-evolutionary simulation | Predict species response to environmental change | 🔴 |
| | Integrate genomic + trophic + distribution | Multi-layer species vulnerability assessment | 🔴 |
| | 🎯 **5yr population forecast with 80% accuracy** | | 🔴 |

---

## 3. Cross-Project Dependencies

```
Near-term (3mo): Independent — each project builds own pipeline
                      │
Mid-term (6mo):   V0 ⟷ V1 (KB ↔ Graph sync)
                  V1 ⟶ P₁/P₂/P₃ (Search feeds into all derived)
                          │
Long-term (12mo): Coord orchestrates V0-V1-P₁-P₂-P₃ as unified system
                  V0 knowledge base is single source of truth
                  V1 search is the only external gateway
                  Derived projects consume both
```

---

## 4. Tracking

- Progress tracked in `CHANGELOG.md` (per-release)
- Detailed evolution log in `.evolution/evolution-log.jsonl`
- Component health in `config/component_registry.yaml`

---

> **"道生一，一生二，二生三，三生万物"**
> All 6 projects evolve together as one system.
