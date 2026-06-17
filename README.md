![Python 3.10+](https://img.shields.io/badge/Python%203.10%2B-3776AB?style=flat-square)
  ![MIT](https://img.shields.io/badge/MIT-34D058?style=flat-square)
  ![v5.4.0](https://img.shields.io/badge/v5.4.0-8A4FCE?style=flat-square)
  ![15+ engines](https://img.shields.io/badge/15%2B%20engines-007EC6?style=flat-square)
  ![7 MCP](https://img.shields.io/badge/7%20MCP-FE7D37?style=flat-square)
  ![5 skills](https://img.shields.io/badge/5%20skills-D73A4A?style=flat-square)
  ![140 tests](https://img.shields.io/badge/140%20tests-0EA5E9?style=flat-square)
  ![Thompson](https://img.shields.io/badge/Thompson-EC4899?style=flat-square)
  ![PID control](https://img.shields.io/badge/PID%20control-F59E0B?style=flat-square)
  ![CN/EN](https://img.shields.io/badge/CN%2FEN-6B7280?style=flat-square)
</p>

[English](README.md) · [中文](README.zh.md)

<div align="center"><h3>🌊 Everything flows.</h3></div>

The world is dynamic, knowledge is temporary, emergence is the norm.

---

## 📖 Table of Contents

- [Philosophy](#-philosophy)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Features](#-features)
- [Unique Innovations](#-unique-innovations)
- [Project Structure](#-project-structure)
- [Version History](#-version-history)
- [Self-Assessment](#-self-assessment)
- [Ecosystem](#-ecosystem)

---

## 🏛️ Philosophy

> The river flows, knowledge drifts, emergence patterns.

This is not a slogan. It is the operating system running through every line of code, every search, every analysis.

This is the **Search Verification Core (V/V1)** in the SanShengWanWu S-T-V-P₁-P₂ architecture, coordinated by **eon-core**. S (Knowledge) proposes claims; V (Verification) validates them — through multi-source parallel search, cross-project comparison, and triangulation scoring, ensuring every piece of knowledge entering the system passes ≥3 independent source checks.

### 📜 Three Tenets

**🌊 The River Flows** — Packages update, species migrate, consensus shifts, climate reshapes. Today's certainty is tomorrow's footnote. We place knowledge on a timeline and view it dynamically.

**🍂 Knowledge Drifts** — The foundation of science is falsifiability (Popper). No discovery is final — only the best current explanation. We speak in calibrated language: evidence suggests, not proves.

**🌟 Emergence Patterns** — Life, consciousness, ecosystems, AI reasoning — all emergent. When three or more independent sources converge on the same unexpected pattern, the system flags emergence — never dismisses it as noise.

### ⚖️ Why This Matters

| Scenario | Traditional | Dynamic Worldview |
|:---------|:-----------|:-------------------|
| Citations | Studies prove | Smith (2022) found X; Jones (2024) added Y |
| Outliers | Dismiss as noise | Three or more sources → emergence signal |
| Knowledge Decay | Handbook frozen | Review records include next review date |
| Method | Fixed pipeline | Dynamic selection, dynamic confidence |

> 道生一，一生二，二生三，三生万物。

From One comes Two, from Two comes Three, from Three come all things.

---

## 🧩 What This Is

A search verification engine. It does not store knowledge — it verifies knowledge.

When the S-layer says "Ochetobius elongatus belongs to Cyprinidae," the V-layer asks PubMed, Crossref, Chinese journals, Google Scholar — do they all agree? Is there disagreement? If so, who is right?

> Heraclitus said: No man ever steps in the same river twice.
>
> We say: You cannot answer today's question with yesterday's search.

---

## 🚀 Quick Start

```bash
# Clone
git clone git@github.com:fangtaocai041/cognitive-search-engine.git
cd cognitive-search-engine

# Install
pip install -e .

# Run
python src/main.py search "Coilia nasus ecology"
```

---

## 🏗️ Architecture

### S-T-V-P₁-P₂ Role

```
S-T-V-P₁-P₂ Architecture (coordinated by eon-core):

  S/V0  fish-ecology-assistant    → Knowledge Supply
  V/V1  cognitive-search-engine   → Search Verification ← this project
  Coord  eon-core                  → Coordination Hub
```

### Internal Architecture

```
cognitive-search-engine/
  src/
  ├── meso_agent.py          BDI cognitive core (Belief→Desire→Intention)
  ├── parallel_search.py     15+ HTTP providers (PubMed/Crossref/OpenAlex...)
  ├── AsyncParallelSearch     aiohttp-based async search (3-5x faster)
  ├── search_coordinator.py  KB-first two-stage search coordinator
  ├── unified_search.py      Adaptive mode: EXHAUSTIVE/CLASSIFIED/SATURATED
  ├── validator.py           5-level trust scoring + source independence check
  ├── thompson_selector.py   Thompson Sampling multi-armed bandit engine selector
  ├── pid_limiter.py         PID adaptive API rate limiting
  ├── mpc_world.py           MPC search cost optimization
  ├── agent_judge.py         LLM-as-Judge 4-dimension result evaluation
  ├── inference_engine.py    Post-search gap + contradiction detection (TAO-inspired)
  ├── evolution_executor.py  7-trigger self-evolution (contradiction-driven)
  ├── variant_generator.py   OCR scientific name variant safety net
  └── adapter.py             IProjectAdapter + verify_claims() method
  config/
  ├── coordination.yaml      Cross-project coordination (shared with ecosystem)
  ├── evolution.yaml         Self-evolution parameters + feedback loop
  └── taiji.yaml             DAG topology definition
  tests/
  ├── test_validator.py           Trust scoring tests
  ├── test_variant_generator.py   Variant generation tests
  ├── test_credibility_scorer.py  Credibility scoring tests
  ├── test_unified_search.py      Unified search tests
  ├── test_world_model.py         MPC world model tests
  ├── test_configs.py             Config loading tests
  ├── test_imports.py             Import chain tests
  └── test_search_integration.py  Search integration tests
```

---

## ✨ Features

| Feature | Status | Description |
|---------|:------:|-------------|
| 🧠 BDI MesoAgent | ✅ | Belief→Desire→Intention adaptive loop |
| 🌐 15+ Providers | ✅ | PubMed, Crossref, OpenAlex, Semantic Scholar, CNKI, Wanfang, Baidu Scholar... |
| ⚡ Async Search | ✅ | aiohttp-based, 3-5x faster |
| 🎯 Thompson Sampling | ✅ | Learned engine selection via multi-armed bandit |
| 📊 PID Rate Limiter | ✅ | Adaptive API rate control |
| 🎛️ MPC World Model | ✅ | Search cost optimization |
| ⚖️ Agent Judge | ✅ | LLM-based 4-dimension evaluation |
| ✅ 5-Level Trust | ✅ | DOI→PMID→Species→Author→Journal hierarchy |
| 🔍 OCR Variants | ✅ | Systematic scientific name variant safety net |
| 🌊 CN/EN Channels | ✅ | Separate ZH/EN literature routing |
| 🔄 Self-Evolution | ✅ | 7 triggers auto-adapt parameters (contradiction-driven) |
| 🧠 Inference Engine | ✅ | Post-search gap analysis + contradiction detection (TAO) |
| 🎯 verify_claims() | ✅ | IProjectAdapter cross-project claim verification |
| 🐛 Error Logging | ✅ | Fixed 25+ silent except:pass |
| 🧪 Test Suite | ✅ | 8 test files, 140 tests passing |

---

## 💡 Unique Innovations

### 1. Hub-and-Spoke Search Architecture
All search requests route through this engine as the single gateway. Derived projects (P₁, P₂, P₃) call cognitive-search-engine — never raw APIs directly.

### 2. Authority Scoring (5-Level Trust)
```
DOI match > PMID match > Species name match > Author match > Journal match
```
Each result receives a weighted trust score. Cross-source disagreement triggers deeper verification.

### 3. OCR Variant Safety Net
`variant_generator.py` systematically generates OCR-prone scientific name variants (e.g., *Coilia nasus* → *Coilia nasus*, *Coilia nasus*, *Collia nasus*) to catch mis-scanned literature.

### 4. Taxonomic Knowledge Graph (Lazy-Loaded)
Species taxonomy relationships are loaded on-demand, never pre-cached. The graph evolves as new species relationships are discovered.

### 5. Five-Discipline Cognitive Engines
Each search category (taxonomy, ecology, genetics, conservation, morphology) has its own tuned cognitive engine with discipline-specific relevance scoring.

---

## 📁 Project Structure

```
cognitive-search-engine/
  (see Architecture section above)
```

---

## 📜 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **v5.4.0** | 2026-06-17 | validator.py 5-level trust, evolution_executor 7-trigger, contradiction-driven evolution |
| v5.3.0 | 2026-06-12 | inference_engine gap+contradiction detection, TAO-inspired reasoning |
| v5.2.2 | 2026-06-09 | Fixed 25+ silent except:pass, error logging infrastructure |
| v5.2.1 | 2026-06-07 | MPC world model search cost optimization |
| v5.2.0 | 2026-06-06 | Thompson Sampling engine selector, PID adaptive rate limiter |
| v5.1.0 | 2026-06-05 | AsyncParallelSearch (aiohttp), 3-5x speed improvement |
| v5.0.0 | 2026-06-01 | BDI MesoAgent, 15+ providers, unified search modes |

---

## 🪞 Self-Assessment

### Strengths
- **Verification-first**: Every claim passes through ≥3 independent source validation
- **Engine diversity**: 15+ providers spanning Western (PubMed/Crossref) and Chinese (CNKI/Wanfang) academic databases
- **Self-healing**: PID limiter prevents API abuse; OCR variants catch scanning errors
- **Contradiction-aware**: inference_engine actively hunts disagreements, not just confirmations
- **Cross-project integration**: verify_claims() enables any derived project to validate against the full search arsenal

### Current Limitations
- Some Chinese academic APIs (CNKI, Wanfang) have unstable access patterns
- Thompson Sampling cold-start requires ~50 queries per engine for convergence
- MPC world model assumes linear cost functions (adequate for current scale)
- No streaming search yet (batch-only)

### Roadmap
- [ ] Streaming search with progressive result delivery
- [ ] Bayesian truth serum for multi-rater claim validation
- [ ] Automated retraction watch integration
- [ ] Graph neural network for species co-occurrence prediction

---

## 🔗 Ecosystem

This project is the **Search Verification Core (V/V1)** in the SanShengWanWu ecosystem.

```
S-T-V-P₁-P₂ Architecture (coordinated by eon-core):

  S/V0  📦 fish-ecology-assistant    → Knowledge Supply
  V/V1  🔍 cognitive-search-engine   → Search Verification ← this project
  Coord ⚙️ eon-core                  → Coordination Hub

  Derived:
    P₁  🐬 porpoise-agent    → Porpoise Domain Expert
    P₂  🐟 coilia-agent      → Coilia Domain Expert
    P₃  🐟 culter-agent      → Culter Domain Expert
    C   🔥 conflict-arbiter  → Conflict Arbitration
```

> 🔥 Together infinite power, apart top expert engines.

---

🌱 **Everything Flows · Panta Rhei**

> Heraclitus said: No man ever steps in the same river twice.
>
> We say: You cannot analyze today's ecological data with last month's code.

This project is not a fixed toolset — it is a **living system**. Every component has built-in expiration mechanisms, version tracking, and emergence awareness. As your research deepens, packages update, and new methods emerge, it evolves with you.

*Last updated: 2026-06-20　|　Environment: Reasonix Code · DeepSeek Powered*
