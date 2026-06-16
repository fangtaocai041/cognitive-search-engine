├── src/                          ← 15 modules (5-layer cognitive agent)
│   ├── adapter.py                ← 🔌 CognitiveSearchAdapter — DirectLoader entry
│   ├── agent_core.py             ← 🧠 CognitiveAgent — BDI + ReAct loop
│   ├── catalog_loader.py         ← 🗄️ DB catalog + graph router + emergence
│   ├── evolution_executor.py     ← 🦋 Self-evolution feedback executor
│   ├── graph_updater.py          ← 📊 Graph persistence + reverse indexes
│   ├── inference_engine.py       ← 🧮 TAO + WuXing inference engine
│   ├── mcp_client.py             ← 🔌 MCP stdio client (7 servers)
│   ├── memory_layer.py           ← 🗄️  MemorySystem — short-term + long-term
│   ├── meso_agent.py             ← 🧭 MesoAgent — coordination layer
│   ├── paper_health_check.py     ← 💓 Paper validity health checker
│   ├── parallel_search.py        ← ⚡ Multi-query parallel executor
│   ├── rule_engine.py            ← ⚙️  SearchRuleEngine — phases + execution
│   ├── validator.py              ← ✅ Cross-project independence validator
│   ├── variant_generator.py      ← 🔤 OCR variant auto-generation
│   └── world_model.py            ← 🧬 BDI WorldModel — Belief/Desire/Intention