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

## 4. 自适应搜索模式 — 按文献量+濒危等级

```
estimate_literature_volume(species_name) → {
  estimated: int,
  conservation: CR | EN | VU | NT | LC,
  mode: exhaustive | classified | review_anchored,
  include_incidental: bool,
}

模式决策矩阵:

  CR + <20篇    → 穷举 (100%): 精确+宽网+变体+引用+附带
                  附带论文 = 每一条记录都珍贵, 全部保留

  EN/VU + <50   → 穷举 (100%): 含附带, 但附带仅列不展开

  20-100篇      → 分类 (80%):  专题全量, 附带标注📎过滤

  >100篇        → 综述锚定 (20%): 先搜综述→精选5-8篇
                  附带论文 = 噪音 ❌ 全部跳过

  鲤/鲫/草鱼等   → 饱和模式: 附带论文 = 噪音 ❌ 全部过滤
  研究热门物种      仅保留专题核心

附带论文过滤规则:
  IF conservation IN [CR, EN] AND estimated < 50:
    include_incidental = True   // 濒危+少文献: 每条记录珍贵
  ELSE:
    include_incidental = False  // 文献充裕: 附带=噪音, 过滤
```

## 5. 工程合约

```
unified_search(species_name: str) → SearchReport

  自适应决策:
    estimate = estimate_literature_volume(species_name)
    mode = estimate.mode

  输出:
    SearchReport {
      total: int,              // 去重后总数
      mode: str,               // exhaustive | classified | review_anchored
      conservation: str,       // CR | EN | VU | NT | LC
      include_incidental: bool,
      papers: List[Paper],     // 专题论文
      incidental: List[Paper], // 附带论文 (仅穷举模式)
      incidental_skipped: int, // 非穷举模式跳过的附带数
      categories: Dict[str, List[Paper]],
      gaps: List[str],
    }
```

## 6. 鳤 (CR, <20篇) — 穷举模式示例

```
unified_search("Ochetobius elongatus")
  → conservation=CR, estimated≈16 → mode=exhaustive

Step 1: 精确名 → 10篇
Step 2: 宽网补漏 → +2篇 (Science禁渔 + NSR)
Step 3: OCR变体 → +2篇 (Ochetobibus)
Step 4: 引用遍历 → +1篇
Step 5: 作者回溯 → +1篇
Step 6: 附带纳入 → +5篇 (调查名录)
────────────────────────────────
总计: 21篇 (专题11 + 附带5 + 变体2 + 宽网2 + 图谱1)
去重后: 16篇 (专题10+Science1 + 附带5)
```

## 7. 鲤鱼 (LC, >1000篇) — 综述锚定模式

```
unified_search("Cyprinus carpio")
  → conservation=LC, estimated>1000 → mode=review_anchored

Step 1: 先搜综述 → "Cyprinus carpio review" → 精选5篇综述
Step 2: 从综述参考文献提取研究方向分类
Step 3: 每个方向精选3-5篇最高引论文
Step 4: 附带论文全部跳过 ❌ (噪音)
────────────────────────────────
总计: 25-40篇 (各方向精选)
附带跳过: >200篇
```

---

> **教训**: 单引擎精确名搜索 = 系统性盲区。多引擎 + 宽网 + 变体 + 引用 + 作者 = 接近全量。
> **实现**: `cognitive-search-engine/src/parallel_search.py` (多引擎) + `skills/graph-search-engine.md` (图谱)
