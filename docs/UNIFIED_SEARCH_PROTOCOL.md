# 🔍 多引擎统一搜索协议 — UnifiedSpeciesSearch v1.0

> **解决**: Science 论文搜不到的问题 — 单引擎精确名搜索遗漏附带/政策/综述论文
> **策略**: 多引擎并行 → 合并去重 → 分类别 → 按需展开
> **集成**: 图谱遍历 (graph-search-engine) → 引用链发现
> **同步**: 2026-06-09

---

## 1. 为什么 Science 论文没搜到？

```
❌ 单引擎精确名搜索: "Ochetobius elongatus"
   → PubMed/Crossref 返回论文中标题含 "Ochetobius" 的
   → Science 论文标题: "Fishing ban halts seven decades..."
   → 标题不含 "Ochetobius" → 搜索遗漏 ❌

✅ 多引擎宽网搜索:
   "Yangtze fishing ban 2026 fish recovery"
   → 命中 Science 论文
   → 论文内容提到 Ochetobius elongatus 作为恢复物种之一
```

## 2. 多引擎并行策略

```
Step 1: 精确名搜索 (Primary)
  PARALLEL:
    scholar_search("Ochetobius elongatus", limit=15)
    ncbi_esearch("Ochetobius elongatus", maxResults=20)
    web_search("鳤 论文 site:cnki.net OR site:biodiversity-science.net")

Step 2: 宽网搜索 (Secondary — 补漏)
  PARALLEL:
    web_search("Ochetobius elongatus Yangtze conservation fishing ban 2024 2025 2026")
    scholar_search("Yangtze fishing ban endangered fish recovery 2026", limit=5)

Step 3: OCR变体搜索 (Safety net)
  FOR EACH variant IN ["Ochetobibus elongatus", "Ochetobus elongatus"]:
    scholar_search(variant, limit=3)

Step 4: 合并去重
  merged = merge_by_doi(all_results)
  merged = deduplicate_by_title(merged)
  merged = deduplicate_cn_en(merged)  // ZN_EN_RULES

Step 5: 分类
  categories = {
    "🧬 遗传与分子": [],
    "🧪 基因组学": [],
    "📐 形态与表型": [],
    "🍽️ 食性与生理": [],
    "🌊 生态与资源": [],
    "📢 保护政策": [],
    "⚠️ 低可信度/变体": [],
  }

Step 6: 输出 (懒加载)
  print("📊 总计 N 篇 | 专题 M 篇 | 附带 K 篇")
  print("分类 | 计数 | 最新")
  // 不展开摘要 — 用户选择分类后再展开
```

## 3. 图谱遍历集成

```
graph-search-engine 已存在于 cognitive-search-engine/skills/

集成方式:
  WHEN 某篇论文有 DOI:
    references = article_get_references(doi, max_results=50)
    FOR EACH ref IN references:
      IF ref 关于目标物种 AND ref 不在已有列表中:
        ADD ref WITH flag = "🔄 引用发现"

  WHEN 某篇论文有已知作者:
    FOR EACH author IN paper.authors:
      more_papers = scholar_search(author.name + " " + species_name)
      IF new_paper NOT IN existing:
        ADD new_paper WITH flag = "👤 作者回溯"

遍历深度:
  L1: 直接引用 (from known papers)
  L2: 二级引用 (from L1 papers)
  停止条件: 连续2层无新论文 OR 达到 budget
```

## 4. 工程合约

```
unified_search(species_name: str, mode: str = "auto") → SearchReport

  模式:
    auto:     IF estimated < 20 → exhaustive (全量)
              ELIF 20-100 → classified (分类)
              ELSE → review_anchored (综述锚定)

    quick:    仅精确名 + 变体 (5-8篇, 快速)
    full:     精确名 + 宽网 + 变体 + 引用 (穷举)

  输出:
    SearchReport {
      total: int,
      papers: List[Paper],
      categories: Dict[str, List[Paper]],
      gaps: List[str],        // 发现的缺口
      variants_used: List[str],
      new_from_graph: int,    // 图谱遍历新发现
    }
```

## 5. 鳤文献搜索 — 正确流程示例

```
unified_search("Ochetobius elongatus", mode="exhaustive")

Step 1: 精确名 → 10篇 (PubMed/Crossref/OpenAlex)
Step 2: 宽网搜索 → +2篇 (Science禁渔 + NSR评论)
Step 3: OCR变体 → +2篇 (Ochetobibus 2009+2026)
Step 4: 引用遍历 → +1篇 (从Yang2018引用链发现)
Step 5: 作者回溯 → +1篇 (从Cai FT作者回溯)
────────────────────────────────
总计: 16篇 (专题11 + 附带5)
```

---

> **教训**: 单引擎精确名搜索 = 系统性盲区。多引擎 + 宽网 + 变体 + 引用 + 作者 = 接近全量。
> **实现**: `cognitive-search-engine/src/parallel_search.py` (多引擎) + `skills/graph-search-engine.md` (图谱)
