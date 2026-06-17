# 🔍 Cognitive Search Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge) ![License](https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge) ![Version](https://img.shields.io/badge/Version-v5.9-blueviolet?style=for-the-badge) ![Engines](https://img.shields.io/badge/Engines-15%2B-success?style=for-the-badge) ![Thompson](https://img.shields.io/badge/Thompson-Sampling-important?style=for-the-badge) ![PID](https://img.shields.io/badge/PID-Rate%20Limit-critical?style=for-the-badge) ![MPC](https://img.shields.io/badge/MPC-Optimization-informational?style=for-the-badge) ![Async](https://img.shields.io/badge/Async-aiohttp-ff69b4?style=for-the-badge) ![CN/EN](https://img.shields.io/badge/CN%2FEN-Dual-orange?style=for-the-badge) ![Agent](https://img.shields.io/badge/Agent-Judge-red?style=for-the-badge)

> ⚡ Search Verification Core — BDI cognitive search with 15+ engines, Thompson Sampling, and MPC optimization.
> You cannot answer today's question with yesterday's search.

[English](README.md) · [中文](README.zh.md) · [CHANGELOG](CHANGELOG.md)

---

## 📖 Table of Contents

- [Philosophy](#-philosophy)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Ecosystem](#-ecosystem)

---

## 🏛️ Philosophy

> The river flows, knowledge drifts, emergence patterns.

This is not a slogan. It is the operating system running through every line of code, every search, every analysis.

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


## 📜 Three Tenets

**🌍 The world is dynamic** — R packages update, species distributions shift, scientific consensus evolves, climate change reshapes ecosystems. A correct conclusion today may be outdated in six months.

**📖 Knowledge is temporary** — The foundation of science is falsification (Popper). No discovery is ultimate truth—only the best current explanation. We use calibrated language: evidence suggests not proves.

**🌟 Emergence is the norm** — Life, consciousness, ecosystems, AI reasoning—all are emergent phenomena. When >=3 independent sources point to the same unexpected pattern, the system flags it as an emergence signal.

### ⚖️ Why This Matters

| Scenario | Traditional | Dynamic Worldview |
|:---------|:-----------|:------------------|
| Citations | Studies prove it | Smith (2022) found X, Jones (2024) added Y |
| Outliers | Ignore as noise | >=3 sources → emergence signal |
| Knowledge decay | Handbook frozen | Review records include Next review date |

> 道生一，一生二，二生三，三生万物。

This is the **S-state (V0)** of the Triangle — Knowledge Supply, holding 430 Yangtze fish species.


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

```
cognitive-search-engine/
  src/
  ├── meso_agent.py          BDI cognitive core (Belief→Desire→Intention)
  ├── parallel_search.py     15+ HTTP providers (PubMed/Crossref/OpenAlex...)
  ├── AsyncParallelSearch     aiohttp-based async search (3-5x faster)
  ├── search_coordinator.py  KB-first two-stage search coordinator
  ├── unified_search.py      Adaptive mode: EXHAUSTIVE/CLASSIFIED/SATURATED
  ├── validator.py           5-level trust scoring + source independence
  ├── thompson_selector.py   Thompson Sampling multi-armed bandit engine selector
  ├── pid_limiter.py         PID adaptive API rate limiting
  ├── mpc_world.py           MPC search cost optimization
  ├── agent_judge.py         LLM-as-Judge result evaluation
  ├── inference_engine.py    Post-search gap + contradiction detection
  ├── evolution_executor.py  7-trigger self-evolution
  └── variant_generator.py   OCR scientific name variants
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 BDI Cognitive | Belief→Desire→Intention adaptive search loop |
| 🌐 15+ Search Engines | PubMed, Crossref, OpenAlex, Semantic Scholar, CNKI, Wanfang... |
| ⚡ Async Search | aiohttp-based AsyncParallelSearch, 3-5x faster |
| 🎯 Thompson Sampling | Learned engine selection replacing rule-based pruning |
| 📊 PID Rate Limiting | Adaptive API request rate control |
| 🎛️ MPC Optimization | Model Predictive Control for search cost optimization |
| ⚖️ Agent-as-Judge | LLM-based result quality evaluation (4 dimensions) |
| ✅ 5-level Trust | DOI→PMID→Species→Author→Journal scoring |
| 🔍 OCR Variants | Systematic scientific name variant generation |
| 🌊 CN/EN Dual Channel | Chinese + English literature separate routing |
| 🔄 Self-Evolution | 7 triggers auto-adapt search parameters |

---

## 📁 Project Structure

```
cognitive-search-engine/
  (see Architecture section above)
```

---

## 🔗 Ecosystem

This project is the Search Verification Core (V1) in the SanShengWanWu ecosystem.

```
Triangle Core (sealed 3):
  📦 fish-ecology-assistant    → Knowledge Supply (V0)
  🔍 cognitive-search-engine   → Search Verification (V1)
  ⚙️ eon-core                  → Coordination Hub (Coord)

Derived Projects (open N):
  🐬 porpoise-agent    → P₁ Porpoise Expert
  🐟 coilia-agent      → P₂ Coilia Expert
  🐟 culter-agent      → P₃ Culter Expert
  🔥 conflict-arbiter  → C  Conflict Arbitration
```

> 🔥 Together infinite power, apart top expert engines.

---

🌱 **Everything Flows · Panta Rhei**

> Heraclitus said: No man ever steps in the same river twice.
>
> We say: You cannot analyze today''s ecological data with last month''s code.

This project is not a fixed toolset — it is a **living system**. Every component has built-in expiration mechanisms, version tracking, and emergence awareness. As your research deepens, packages update, and new methods emerge, it evolves with you.

*Last updated: 2026-06-17　|　Environment: Reasonix Code · DeepSeek Powered*

