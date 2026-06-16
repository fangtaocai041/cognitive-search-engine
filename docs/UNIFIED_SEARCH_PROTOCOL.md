# 🔍 19引擎统一搜索协议 — UnifiedSpeciesSearch v3.0

> **三角闭环**: fish(V0知识库) → cognitive(V1搜索) → eon-core(协调)
> **三生万物**: P₁(porpoise) · P₂(coilia) · ... 从三角闭环衍生
> **解决**: Science 论文搜不到的问题 — 单引擎精确名搜索遗漏附带/政策/综述论文
> **策略**: 19引擎(7 MCP + 12 Native HTTP) → 合并去重 → 分类 → KB-First 两阶段
> **集成**: 图谱遍历 (graph-search-engine) + KB-First (fish-ecology-assistant 知识库预查)
> **同步**: 2026-07-17

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

## 2. MCP 优先搜索架构（v2.0）

```
MCP优先层 (6引擎, 并行):
  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
  │ scholar  │ article  │   ncbi   │  tavily  │   exa    │scholarly │
  │  MCP     │   MCP    │   MCP    │   MCP    │   MCP    │   MCP    │
  │ Google   │ EuropePMC│ E-utils  │  AI深度  │  语义    │  OpenAlex│
  │ Scholar  │+PubMed   │ API      │  网络    │  网络    │+Semantic │
  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
       │          │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼          ▼
     _parse_   _parse_   _parse_   _parse_   _parse_    (TBD)
    scholar   article     ncbi     tavily     exa

HTTP回退层 (5引擎, MCP不可用时):
  pubmed / europe_pmc / crossref / openalex / arxiv (+ cnki_web 中文)

去重管线:
  raw → _filter_by_genus (属名校验) → _deduplicate (DOI+标题) → classify + CN/EN label

MCP 预热: McpClient.warmup() 一次性启动全部 6 个 npx 子进程
失败回退: 任意 MCP 调用失败 → 整条管线回退到 HTTP
```
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

## 5. 鳤文献搜索 — 当前流程（v2.0）

```
search_api.py --species "鳤"
  │
  ├─ 分类学变体: Ochetobius + Ochetobibus + Ochetobus + Opsarius + 鳤
  │
  ├─ MCP优先搜索 (6引擎并行):
  │     scholar MCP → 7篇
  │     article MCP → 2篇 (EuropePMC + PubMed)
  │     ncbi MCP   → 6篇 (全部与scholar重复, 去重移除)
  │     exa MCP    → 1篇
  │     tavily MCP → Wikipedia (非论文格式)
  │     原始合计   → 74篇
  │
  ├─ 属名校验 (_filter_by_genus):
  │     标题不含 "Ochetobius" → 移除 51篇
  │     保留 23篇
  │
  ├─ DOI去重 (_deduplicate):
  │     DOI/标题重复 → 移除 13篇
  │     保留 10篇 (unique)
  │
  └─ CN/EN通道分类:
        🇨🇳 中文期刊: 4篇 (生物多样性2 + 水生生物学报 + 动物分类学报)
        🇬🇧 英文期刊: 7篇 (Animals×3 + Gene + SciData + MitDNA + IUCN)
        📐 分类: 形态2/遗传2/基因组1/生态4/保护2/食性1
```

---

> **关键增强 (v2.0)**:
> - MCP 6 引擎优先: 启动时间 5s，精确度远高于 HTTP 模糊搜索
> - 属名校验: 解决 Crossref "elongatus" 通配返回其他物种的噪音
> - OpenAlex 摘要: abstract_inverted_index → 可读文本
> - ncbi esummary: 兼容 `{"papers": [...]}` 格式
> - cnki_web: 中文不足 2 字自动过滤游戏广告
>
> **实现文件**:
> - `scripts/search_api.py` — search_mcp_priority() + 5个MCP解析器
> - `src/parallel_search.py` — HTTP 5引擎 + _filter_by_genus + OpenAlex抽象重建
> - `src/mcp_client.py` — 6 MCP 子进程管理 + call_tool server/tool 分离修复
> - `ZN_EN_RULES.md` — CN/EN 双通道 + 中文署名映射
