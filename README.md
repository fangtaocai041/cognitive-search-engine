# Cognitive Search Engine 🔍

**多源并行文献搜索引擎** — Google Scholar 优先 + 中文期刊 + PubMed/Crossref + 可信度评分。

[中文版](README.zh.md) | [变更日志](CHANGELOG.md) | [参与贡献](CONTRIBUTING.md)

---

## 快速开始

`ash
pip install -e .
python -m src.credibility_scorer
`

## 核心功能

### 多源搜索
- Google Scholar 优先搜索（全球学术）
- CNKI / CQVIP 中文期刊搜索
- PubMed / Crossref 国际文献

### 可信度评分
`python
from src.credibility_scorer import score_papers, format_credibility

papers = [{"title": "...", "journal": "Nature", "citation_count": 100}]
scored = score_papers(papers)
for p in scored:
    print(p["title"], format_credibility(p["credibility_score"]))
`

## 项目架构

`
cognitive-search-engine/
├── src/
│   ├── __init__.py
│   ├── search_engine.py      # 搜索编排器
│   └── credibility_scorer.py # 可信度评分
├── scripts/                  # CLI 工具
├── config/                   # 搜索规则配置
├── tests/                    # 测试
├── pyproject.toml
└── CHANGELOG.md
`

## 三角角色

本系统是 Triangle Core 的 **V/V0 (搜索验证)** 层，接收来自 fish-ecology-assistant (S) 的委托搜索请求，执行全量文献搜索后返回评分结果。

## 许可证

MIT
