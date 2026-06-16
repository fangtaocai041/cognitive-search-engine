# Changelog — cognitive-search-engine

> 版本变更记录。参见 ROADMAP.md 了解技术改进路线图。

## v5.9.0 — 2026-07-17
- 🧭 新增 **ROADMAP.md / ROADMAP.zh.md** — 6 项目×3 时间维度未来优化方向路线图
- 🗺️ README 双板同步: +「各项目未来优化方向」趋势表
- 🔧 恢复 ENGINE_REGISTRY (12引擎) + ENGINE_GROUPS (4组) + search_streaming()
- 📜 功能脚本化: +scripts/credibility_scorer.py (完整版), +scripts/kb_to_graph_sync.py, +scripts/self_evolve.py
- ⚙️ config/agent.yaml v4.0.0→v5.5.0: +gateway角色, +共享协议, +超时重连, +LLM配置
- 🤝 config/coordination.yaml 新建: 三角闭环架构声明 + 搜索网关

## v5.8.0 — 2026-07-11
- 🚀 21 引擎全线升级 — SerpAPI Baidu/Scholar/DuckDuckGo 突破中文反爬
- Exa API 语义搜索
- Europe PMC NCBI 500 故障转移
- HTTP 超时 15→8s, 全流程 112→25s

## v5.7.0 — 2026-06-20
- 🧬 KB-First 两阶段搜索
- `search_with_kb_first()` + `continue_full_search()`

## v5.6.0 — 2026-06-10
- 🔁 HTTP 重连 + 🚀 MCP 并行预热
- 🌐 中文三层搜索 + 🛑 停止机制重构

## v5.0.0 — 2026-06-07
- BDI + ReAct 认知架构初始发布
