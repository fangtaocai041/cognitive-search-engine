# Changelog — cognitive-search-engine

> 版本变更记录。参见 ROADMAP.md 了解技术改进路线图。

## v5.10.0 — 2026-06-27

### 🔍 verify_claims() + 测试扩展

- 🎯 **verify_claims() adapter 方法**: `IProjectAdapter.verify_claims(claims)` — 跨项目声明验证端点
- 🧪 **测试套件扩展 5→8**: 新增 `test_credibility_scorer.py`、`test_world_model.py`、`test_configs.py`
- 全量 8 测试文件覆盖 validator / variant / credibility / unified search / world model / configs / imports / integration

---

## v5.9.1 — 2026-06-17
- 🔍 **MCP 优先搜索**: `search_mcp_priority()` — 6 MCP 引擎并行(scholar/article/ncbi/tavily/exa/scholarly) → 失败回退 HTTP 5引擎
- 🧹 **属名校验过滤**: `_filter_by_genus()` — 移除 Crossref/arXiv 标题不含目标属名的噪音论文
- 📝 **OpenAlex 摘要修复**: `abstract_inverted_index` 倒排索引 → 可读文本重建
- 🇨🇳 **cnki_web 垃圾过滤**: 中文不足2字自动丢弃(游戏广告)
- 🩹 **McpClient.call_tool() 修复**: server/tool 名 `/` 分离在 `_get_or_start_process` 之前执行
- 🔬 **ncbi MCP 全链路**: esearch→esummary 适配 `{"papers": [...]}` 格式
- 📋 **5 个 MCP 响应解析器**: `_parse_scholar/article/tavily/exa/ncbi_response`
- 🏷️ **图谱增强**: 鳤 12 篇论文补全 `authors_zh` + `affiliations`

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
