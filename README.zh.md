# 🕸️ 认知搜索引擎 v4.4 — 中文说明

> **前沿物种文献搜索** — 知识图谱遍历 + 能效最优 + 符号学 + 语言学 + DeepSeek 思维链

## 🧠 核心创新

**不是字符串匹配 — 是认知重建。**

传统搜索匹配字符串。如果论文把"Ochetobius"拼成"Ochetobibus"，传统搜索找不到。
本引擎从多条**能指路径**同时重建**所指**（物种本身）。

## ⚡ 三大突破

### 1. 知识图谱遍历（非线性搜索）

| 传统 (v2/v3) | 图谱搜索 (v4) |
|-------------|-------------|
| 11 层顺序执行 | 图谱条件遍历 |
| 结果每次丢弃 | 结果存入图谱，下次免费 |
| ~8000 tokens/次 | ~2000 tokens/次 |

### 2. 能效最优（满意即止，不穷举）

找到 8 篇即满足。边际收益递减时停止。便宜层先跑。

### 3. 多学科认知引擎

符号学 (能指→所指) + 语言学 (拉丁词根) + 语音学 (IPA) + 逻辑学 (演绎+溯因+归纳) + DeepSeek CoT

## 🚀 快速上手

```bash
git clone https://github.com/fangtaocai041/cognitive-search-engine.git
```

## 📡 内置搜索引擎

Google Scholar · Europe PMC · PubMed · OpenAlex · Semantic Scholar · Tavily · Exa

## 📜 许可证

MIT © 2026 fangtaocai041
