# 🀄 ZN/EN 文献通道规则 (Chinese/English Literature Channel Rules)

> **核心原则**: 中文文献走中文通道（署名、标题、期刊名用中文），英文文献走英文通道。去重后保留原文。
> **位置**: cognitive-search-engine 项目根目录
> **同步**: 2026-06-09

---

## 1. 通道分离规则

```
WHEN paper.journal IN ChineseJournals:
  → 走 CN 通道:
    authors = paper.authors_zh        // 中文署名（杨计平，非 Yang Jiping）
    title   = paper.title_zh          // 中文标题
    journal = paper.journal_zh        // 中文期刊名

WHEN paper.journal IN EnglishJournals:
  → 走 EN 通道:
    authors = paper.authors           // 英文署名（Yang Jiping）
    title   = paper.title             // 英文标题
    journal = paper.journal           // 英文期刊名
```

## 2. 中文期刊 → 中文署名映射

| 中文刊名 | 英文刊名 | 中文署名 | 英文署名 |
|---------|---------|---------|---------|
| 生物多样性 | Biodiversity Science | 杨计平 蔡方陶 翟东东 | — |
| 水生生物学报 | Acta Hydrobiologica Sinica | 翟东东 蔡方陶 | — |
| 南方水产科学 | South China Fisheries Science | 陈蔚涛 杨计平 | — |
| 湖泊科学 | Journal of Lake Sciences | — | — |
| 中国水产科学 | J. Fishery Sciences of China | — | — |
| 水产学报 | J. Fisheries of China | — | — |
| 生态学报 | Acta Ecologica Sinica | — | — |
| 生态科学 | Ecological Science | — | — |

## 3. 去重规则

```
// 方法1: DOI 精确匹配
IF paper_cn.doi == paper_en.doi:
  keep = paper_cn  // 保留中文版
  mark(paper_en, "_duplicate_of", paper_cn.doi)

// 方法2: 标题相似度 ≥ 0.8
similarity = SequenceMatcher(paper_cn.title_zh, paper_en.title).ratio()
IF similarity >= 0.8:
  keep = paper_cn  // 保留中文版
  mark(paper_en, "_title_match", similarity)

// 方法3: 作者+年份匹配
IF same_authors(paper_cn, paper_en) AND paper_cn.year == paper_en.year:
  IF paper_cn.journal IN ChineseJournals:
    keep = paper_cn
  ELSE:
    keep = paper_en
```

## 4. 中文期刊权威白名单

| 期刊 | 索引 | 权重 |
|------|------|:--:|
| 水生生物学报 | CSCD 核心 | +25 |
| 中国水产科学 | CSCD 核心 | +25 |
| 水产学报 | CSCD 核心 | +25 |
| 生物多样性 | CSCD 核心 | +25 |
| 湖泊科学 | CSCD 核心 | +25 |
| 南方水产科学 | 北大核心 | +25 |
| 生态科学 | 中国科技核心 | +20 |
| 生态学报 | CSCD 核心 | +25 |

## 5. 鳤文献 CN/EN 通道示例

```
CN 通道（中文期刊 → 中文署名）:
  #2  杨计平 等. 西江中下游鳤的遗传多样性与种群动态历史. 生物多样性. 2018.
  #4  陈蔚涛 等. 多基因解析长江与珠江鳤的遗传结构. 南方水产科学. 2022.
  #5  翟东东 等. 长江中游鳤的遗传多样性. 水生生物学报. 2024.
  #8  蔡方陶 等. 长江中下游鳤不同群体的多变量形态学特征. 生物多样性. 2025.
  #10 —. 五强溪水库鱼类资源历史变化. 湖泊科学. 2016.
  #13 —. 禁渔初期长江中游沅水流域鱼类群落结构. 水生生物学报. 2025.

EN 通道（英文期刊 → 英文署名）:
  #1  Yang JP et al. Complete mitochondrial genome... Mitochondrial DNA. 2015.
  #3  Yang JP et al. Development of 26 SNP markers... Conserv Genet Resour. 2018.
  #6  Li LK et al. A chromosome-level genome assembly... Scientific Data. 2024.
  #7  Cai FT et al. Revealing Phenotypic Differentiation... Animals. 2025.
  #9  Gao F et al. Analysis of Ochetobibus elongatus Dietary Habits... Animals. 2026.
  #11 Chen WT et al. Temporal species-level composition... Gene. 2021.
  #12 Kong CP et al. Post-Fishing Ban Period... Animals. 2025.
  #14 Cao WX (指导). Yangtze fishing ban... Science. 2026.
  #15 Wang J et al. PFAS toxicity... Environ Res. 2026.
```

## 6. OCR 变体 CN/EN 交叉

```
⚠️ Ochetobibus elongatus (拼写错误 → 应为 Ochetobius):
  中文通道: 鳤 → 搜 "鳤 食性 消化道" → 命中 #9
  英文通道: Ochetobibus → 搜 scholar → 命中 #9
  注: 精确名 "Ochetobius" 搜索无法命中此论文
```

---

> **铁律**: 中文期刊 ≠ 英文名。英文期刊 ≠ 中文名。去重后保留原文。
> **实现**: cognitive-search-engine/src/graph_updater.py (ZN/EN 自动填充)
> **配置**: cognitive-search-engine/config/species_graph.yaml (authors_zh 字段)
