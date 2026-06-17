<div align="center">
  <h1>🔍 Cognitive Search Engine</h1>
  <p><em>Search Verification Core — BDI cognitive search · 15+ engines · Thompson Sampling · MPC optimization</em></p>
</div>

<p align="center">
  ![Python 3.10+](https://img.shields.io/badge/Python%203.10%2B-3776AB?style=flat-square)
  ![MIT](https://img.shields.io/badge/MIT-34D058?style=flat-square)
  ![v5.9](https://img.shields.io/badge/v5.9-8A4FCE?style=flat-square)
  ![15+ engines](https://img.shields.io/badge/15%2B%20engines-007EC6?style=flat-square)
  ![Thompson](https://img.shields.io/badge/Thompson-FE7D37?style=flat-square)
  ![PID control](https://img.shields.io/badge/PID%20control-D73A4A?style=flat-square)
  ![aiohttp](https://img.shields.io/badge/aiohttp-0EA5E9?style=flat-square)
  ![CN/EN](https://img.shields.io/badge/CN%2FEN-EC4899?style=flat-square)
  ![BDI agent](https://img.shields.io/badge/BDI%20agent-F59E0B?style=flat-square)
</p>

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

| Feature | Status | Description |
|---------|:------:|-------------|
| 🧠 BDI MesoAgent | ✅ | Belief→Desire→Intention adaptive loop |
| 🌐 15+ Providers | ✅ | PubMed, Crossref, OpenAlex, Semantic Scholar, CNKI... |
| ⚡ Async Search | ✅ | aiohttp-based, 3-5x faster |
| 🎯 Thompson Sampling | ✅ | Learned engine selection |
| 📊 PID Rate Limiter | ✅ | Adaptive API rate control |
| 🎛️ MPC World Model | ✅ | Search cost optimization |
| ⚖️ Agent Judge | ✅ | LLM-based 4-dimension evaluation |
| ✅ 5-level Trust | ✅ | DOI→PMID→Species→Author→Journal |
| 🔍 OCR Variants | ✅ | Systematic name variant generation |
| 🌊 CN/EN Channels | ✅ | Separate ZH/EN literature routing |
| 🔄 Self-Evolution | ✅ | 7 triggers auto-adapt parameters |
| 🐛 Error Logging | ✅ | Fixed 25+ silent except:pass |

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

