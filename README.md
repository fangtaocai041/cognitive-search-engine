# Cognitive Search Engine 🔍

**多源并行文献搜索引擎** — Google Scholar 优先 + 中文期刊 + PubMed/Crossref + 可信度评分。

[中文版](README.zh.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md)

---

## 快速开始

```bash
pip install pyyaml
python scripts/search_api.py --species "鳤"
```

```python
from src.meso_agent import create_agent

agent = create_agent(mode="http")
result = agent.search("Ochetobius_elongatus")
print(f"{len(result.papers)} 篇论文，{result.elapsed_s:.1f} 秒")
```

## 核心功能

### 多源搜索
- Google Scholar 优先搜索（全球学术）
- PubMed / Europe PMC / Crossref 国际文献
- 中文期刊（CNKI / Bing 中文搜索）
- AI 网络搜索（Tavily / Exa）

### 可信度评分
```python
from src.credibility_scorer import score_paper

paper = {"title": "...", "journal": "Nature", "citation_count": 100}
scored = score_paper(paper)
# 🟢 ≥80 高 | 🟡 60-79 中 | 🟠 40-59 低 | 🔴 <40 不可信
```

### 其它能力
- **BDI 认知循环** — 先估算文献量，再决定怎么搜，搜完评分进化
- **OCR 变体** — 拉丁名打错了也能搜到（`Ochetobius` → `Ochetobibus`）
- **KB-First** — 搜之前先查知识库有没有，避免重复
- **S-T-V 闭环** — 和 fish-ecology-assistant / porpoise-agent 协同工作

## 项目架构

```
cognitive-search-engine/
├── src/
│   ├── meso_agent.py         ← BDI 搜索入口
│   ├── mcp_client.py         ← MCP 并行客户端
│   ├── parallel_search.py    ← HTTP 6 源并行搜索
│   ├── unified_search.py     ← 搜索协议 + 分类学
│   ├── adapter.py            ← 跨项目接口
│   ├── credibility_scorer.py ← 可信度评分
│   ├── validator.py          ← 论文验证
│   ├── variant_generator.py  ← 拼写变体生成
│   ├── inference_engine.py   ← 推理增强
│   └── evolution_executor.py ← 自进化
├── config/                   # 配置文件
├── scripts/                  # CLI 工具
└── tests/
```

## 三角角色

本系统是 Triangle Core 的 **V/V1 (搜索验证)** 层，接收来自 fish-ecology-assistant (S) 的委托搜索请求，执行全量文献搜索后返回评分结果。

## 许可证

MIT © 2026 fangtaocai041
