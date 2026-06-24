---
name: chinese-academic-search
version: "1.0.0"
last_updated: "2026-06-06"
description: 搜索中文期刊数据库（百度学术/知网/万方/水生生物学报/生物多样性等），返回中文论文元数据 + 提取作者中文名。弥补 PubMed/Crossref 不索引中文期刊的系统性盲区。
runAs: inline
---

# Chinese Academic Search — 中文期刊搜索

## 定位
弥补 PubMed/Crossref 不索引中文期刊的系统性盲区。

## 覆盖的期刊
- 生物多样性 (Biodiversity Science)
- 水生生物学报 (Acta Hydrobiologica Sinica)
- 南方水产科学 (South China Fisheries Science)
- 中国水产科学 (Journal of Fishery Sciences of China)
- 水产学报 (Journal of Fisheries of China)
- 湖泊科学 (Journal of Lake Sciences)
- 生态学报 (Acta Ecologica Sinica)
- 生态科学 (Ecological Science)

## 搜索策略

```
FOR EACH target_journal IN journal_list:
  web_search(species_chinese_name + " " + target_journal, limit=5)
  IF web_search result MATCHES species:
    EXTRACT: metadata → 中文标题, 作者(中文), 期刊, 年份, DOI
    ADD authors_zh field with Chinese author names
```

## 输出格式

```yaml
- doi: 10.xxx/xxx
  title_zh: 中文标题
  authors: [拼音名]
  authors_zh: [中文名]        # 必须！中文名非机翻
  journal: 期刊全名
  year: 2024
```

## 关键规则
1. 中文作者名用汉字，不机翻（杨计平 ≠ Yang Jiping）
2. 中文期刊名用原名，不替换为英文（生物多样性 ≠ Biodiversity Science）
3. 中英文双版本发表 → 只保留中文版本（信息更全）
