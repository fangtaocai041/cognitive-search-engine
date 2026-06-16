# Cognitive Search Engine 🔍

**多源并行文献搜索引擎** — Google Scholar + 中文期刊 + PubMed/Crossref + 可信度评分。

[中文版](README.zh.md) | [变更日志](CHANGELOG.md)

---

## 项目简介

多源学术文献搜索引擎，为 fish-ecology-assistant 提供全量文献搜索和可信度验证。核心引擎支持 20+ 数据源并行搜索、OCR 拼写变体、引用回溯。

> **当前状态**：核心框架已恢复。搜索适配器（MCP 客户端、API 调用）处于重建阶段，通过 Reasonix MCP 工具提供搜索能力。

---

## 安装

```bash
pip install -e .
```

---

## 核心功能

### 多源并行搜索

通过 Reasonix MCP 协议调用多个搜索引擎：

- **PubMed / Europe PMC** — 生物医学文献
- **Crossref / OpenAlex** — 学术元数据
- **Semantic Scholar** — AI 增强搜索
- **Google Scholar** — 综合学术
- **CNKI / 万方 / 百度学术** — 中文期刊

### 可信度评分

```python
from src.credibility_scorer import score_papers

papers = [
    {"title": "Ochetobius elongatus mitochondrial genome", 
     "journal": "Animals", "doi": "10.3390/ani15010001", "pmid": "12345678"},
]

scored = score_papers(papers)
for p in scored:
    print(f"{p['credibility_score']}/100 {p['credibility_flag']} | {p['title']}")
```

**评分规则：**
- 基线 50 + SCI 期刊 +30 + 北大核心/CSCD +25
- DOI +10 · PMID +10 · 预印本 -30
- 80+ 🟢 高可信度 · 60-79 🟡 中可信度 · <60 🟠 需交叉验证

---

## 项目结构

```
cognitive-search-engine/
├── src/
│   ├── __init__.py              # 公共 API
│   ├── search_engine.py         # 搜索编排器
│   └── credibility_scorer.py    # 可信度评分引擎
├── config/
│   ├── engine_registry.yaml     # 搜索引擎注册
│   ├── component_registry.yaml  # 组件注册
│   ├── evolution.yaml           # 自进化参数
│   └── stv_protocol.yaml        # S-T-V 三角协议
├── pyproject.toml
└── CHANGELOG.md
```

---

## 架构角色

本系统为 **V/V1（搜索验证层）**，与 fish-ecology-assistant（S/V0 知识供给）和 eon-core（协调内核）构成三角闭环：

```
fish-ecology-assistant → 委托搜索 → cognitive-search-engine
cognitive-search-engine → 可信度评分 + 分类反馈 → fish-ecology-assistant
```

---

## 许可证

MIT License © 2026 fangtaocai041
