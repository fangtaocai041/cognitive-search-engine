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

## 7. 附带论文标注规则

```
定义: 附带论文 = 鳤非主要研究对象，仅作为调查物种之一出现。

标注规则:
  WHEN paper 中目标物种仅出现在物种名录/调查结果中
  AND paper 的研究主题不是该物种本身
  THEN mark(paper, "附带", reason="仅出现在调查名录中，非专题研究")

  WHEN paper 的研究主题直接是该物种（遗传/形态/食性/基因组/保护）
  THEN mark(paper, "专题", reason="该物种为主要研究对象")

输出格式:
  专题论文: 编号 + 标题 + 作者 + 期刊 (正常格式)
  附带论文: 编号 + 📎 标题 + "(附带: 仅名录记录)" + 作者 + 期刊 (灰色标记)

去重合并:
  IF 附带论文的物种记录与专题论文重复
  THEN 保留专题论文，附带论文降级为引用来源
```

## 8. 鳤文献完整分级列表 (专题 vs 附带)

### 🔴 专题论文 (10篇) — 鳤为主要研究对象

| # | 年份 | 标题 | 作者 | 期刊 | 通道 | DOI/PMID |
|:--:|:--:|------|------|------|:--:|------|
| 1 | 2026 | ⚠️ 鳤食性 (Ochetobibus) | 高峰 | Animals | EN | PMID:42121788 |
| 2 | 2025 | 几何形态学表型分化 | Cai FT | Animals | EN | PMID:41096465 |
| 3 | 2025 | **多变量形态学特征** | **蔡方陶** | **生物多样性** | CN | 10.17520/biods.2025136 |
| 4 | 2024 | 染色体级别基因组 | Li LK | Scientific Data | EN | PMID:39702392 |
| 5 | 2024 | **长江中游遗传多样性** | **翟东东** | **水生生物学报** | CN | 10.7541/2024.2024.0056 |
| 6 | 2022 | **长江珠江遗传结构** | **陈蔚涛** | **南方水产科学** | CN | 10.12131/20220007 |
| 7 | 2018 | **西江遗传多样性** | **杨计平** | **生物多样性** | CN | 10.17520/biods.2018121 |
| 8 | 2018 | 26 SNP标记 (RAD-seq) | Yang JP | Conserv Genet Resour | EN | 10.1007/s12686-018-1075-3 |
| 9 | 2015 | 完整线粒体基因组 | Yang JP | Mitochondrial DNA | EN | PMID:26477619 |
| 10 | 2010 | IUCN红色名录评估 | IUCN | IUCN Red List | EN | 10.2305/IUCN.UK.2013-1 |

### ⭐ 专题论文 (续) — 重大保护政策论文

| # | 年份 | 标题 | 第一作者 | 指导 | 期刊 | 通道 | DOI |
|:--:|:--:|------|:--|:--|------|:--:|------|
| S1 | 2026 | ⭐ **Fishing ban halts seven decades of biodiversity decline in the Yangtze River** (鳤列入恢复物种) | **Xiong FY** 熊芳园 | 曹文宣(院士) 陈宇顺 | ***Science*** | EN | 10.1126/science.adu5160 |

> 注: 鳤(*O. elongatus*) 被列入禁渔后种群恢复的旗舰物种之一。这是鳤研究史上最高级别发表。

### 📎 附带论文 (5篇) — 鳤仅出现在调查名录中

| # | 年份 | 标题 | 作者 | 期刊 | 通道 | 鳤出现形式 |
|:--:|:--:|------|------|------|:--:|------|
| 11 | 2025 | 📎 Post-Fishing Ban: Poyang Lake Fish Diversity | Kong CP | Animals | EN | 120种鱼类之一 |
| 12 | 2025 | 📎 **禁渔初期沅水流域鱼类群落** | — | **水生生物学报** | CN | 物种名录 |
| 13 | 2021 | 📎 Pearl River larvae resources | Chen WT | Gene | EN | 附带采样 |
| 14 | 2016 | 📎 **五强溪水库鱼类资源历史变化** | — | **湖泊科学** | CN | 历史记录 |
| 15 | 2009 | 📎 赣江中游峡江段鱼类资源 | 齐华 | 江西科学 | CN | Ochetobibus 变体 |

### 📊 分级统计

```
专题论文: 10+1 篇 (CN 4篇 + EN 6+1篇) [含 Science ⭐]
附带论文:  5 篇 (CN 3篇 + EN 2篇)
总计:     16 篇 (CN 7篇 + EN 9篇)
OCR变体:   1 篇 (Ochetobibus #1)
Science:   1 篇 (S1 — 熊芳园, 曹文宣指导)
IUCN评估:  1 篇 (#10)
```

---

## 9. 鲌类分类学修订 (2024)

```
科级: 鲤科 Cyprinidae → Xenocyprididae
属级: Culter (鲌属) → Chanodichthys (原鲌属) [6种移出]
      Culter 保留 2种: 翘嘴鲌 + 扁体鲌

中文名以中国鱼类学实际使用为准 (非Wikipedia翻译):

  拉丁名 (现)           中文名        旧名/别名
  ─────────────         ─────        ──────────
  Culter alburnus       翘嘴鲌        —
  Culter compressocorpus 扁体鲌        —
  Ch. mongolicus        蒙古鲌        蒙古红鲌, 蒙古原鲌
  Ch. dabryi            达氏鲌        青梢鲌, 达氏原鲌
  Ch. erythropterus     红鳍原鲌      红鳍鲌
  Ch. oxycephalus       拟尖头鲌      尖头原鲌, Culter oxycephaloides
  Ch. abramoides        壮体鲌        壮体原鲌

⚠️ 拟尖头鲌搜索策略:
  必须同时搜索: "Chanodichthys oxycephalus" + "Culter oxycephaloides"
  中文: "拟尖头鲌" + "尖头原鲌"
  原因: 2024年确认 senior synonym, 但老文献全部使用旧名

## 10. 珠星三块鱼属名修订 (2020)

```
属级: Tribolodon → Pseudaspius (2020)
科级: Cyprinidae → Leuciscidae (雅罗鱼科)

⚠️ 搜索策略:
  必须同时搜索: "Pseudaspius hakonensis" + "Tribolodon hakonensis"
  新论文(2020后)使用 Pseudaspius; 老论文(1987-2019)使用 Tribolodon
  中文: "珠星三块鱼" + "珠星雅罗鱼"

教训: 2026.3 徐子悦论文(Pseudaspius hakonensis, Genes)因只用旧名搜索而遗漏
```

---

> **铁律**: 中文期刊 ≠ 英文名。英文期刊 ≠ 中文名。去重后保留原文。
> **附带规则**: 专题论文在前，附带论文在后。附带论文仅列出物种出现形式，不展开摘要。
> **实现**: cognitive-search-engine/src/graph_updater.py (ZN/EN 自动填充)
> **配置**: cognitive-search-engine/config/species_graph.yaml (authors_zh 字段)
