# 🔍 Cognitive Search Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python) ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square) ![Version](https://img.shields.io/badge/Version-v5.9-blueviolet?style=flat-square) ![Engines](https://img.shields.io/badge/Engines-15%2B-success?style=flat-square) ![Thompson](https://img.shields.io/badge/Thompson-Sampling-orange?style=flat-square) ![PID](https://img.shields.io/badge/PID-Rate%20Limit-yellow?style=flat-square) ![MPC](https://img.shields.io/badge/MPC-Optimization-red?style=flat-square) ![Async](https://img.shields.io/badge/Async-aiohttp-9cf?style=flat-square) ![CN/EN](https://img.shields.io/badge/CN%2FEN-Dual%20Channel-ff69b4?style=flat-square) ![Agent](https://img.shields.io/badge/Agent-Judge-important?style=flat-square)

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

> The world is dynamic, knowledge is temporary, emergence is constant.

This is the **V-state (V1)** of the Triangle — Search Verification. Knowledge supplied by V0 is verified here through multi-source parallel search, credibility scoring, and source independence enforcement. The BDI cognitive architecture (Belief→Desire→Intention) adapts search strategy in real-time.

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
*SanShengWanWu Ecosystem · MIT License · fangtaocai041*
