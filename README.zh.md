# Cognitive Search Engine 🔍

**多源并行文献搜索引擎** — Google Scholar 优先 + 中文期刊 + PubMed/Crossref + 可信度评分。

[English](README.md) | [变更日志](CHANGELOG.md) | [参与贡献](CONTRIBUTING.md)

---

## 快速开始

`ash
pip install -e .
`

## 核心功能

### 多源搜索
- Google Scholar 优先搜索
- CNKI / CQVIP 中文期刊
- PubMed / Crossref 国际文献

### 可信度评分
`python
from src.credibility_scorer import score_papers, format_credibility
`

## 项目架构

`
cognitive-search-engine/
├── src/
│   ├── __init__.py
│   ├── search_engine.py
│   └── credibility_scorer.py
├── scripts/
├── config/
├── tests/
├── pyproject.toml
└── CHANGELOG.md
`

## 许可证

MIT
