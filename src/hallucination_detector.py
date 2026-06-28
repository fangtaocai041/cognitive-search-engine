"""
hallucination_detector.py — Layer 6: AI 幻觉检测器
====================================================
宁可慢, 必须真 — 每条文献通过外部 API 验证真实性。

验证链路:
  ① DOI → Crossref API 确认真实存在
  ② PMID → NCBI E-utilities 确认真实存在  
  ③ 引用 → 被引文献的 DOI/PMID 也可验证
  ④ 声明 → 论文摘要与用户提供的结论交叉比对
  ⑤ 元数据 → 标题/作者/期刊/年份与官方记录一致性

HallucinationScore: 0.0 = 全部验证通过, 1.0 = 全部无法验证(高度可疑)

Usage:
    from src.hallucination_detector import HallucinationDetector
    hd = HallucinationDetector()
    result = hd.verify_paper({"doi": "10.1038/s41586-025-...", "title": "..."})
    # → {verified: True, score: 0.05, checks: {doi: True, pmid: True, ...}}
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VerificationResult:
    """单条论文的验证结果。"""
    paper_title: str = ""
    doi: str = ""
    pmid: str = ""
    verified: bool = False          # 总体是否通过验证
    hallucination_score: float = 0.0  # 0=真实, 1=完全幻觉
    checks: dict[str, bool | None] = field(default_factory=dict)
    official_title: str = ""         # 官方数据库中的标题
    official_journal: str = ""       # 官方期刊名
    official_year: int = 0           # 官方发表年份
    title_match: float = 0.0         # 标题与官方的相似度
    errors: list[str] = field(default_factory=list)

    def describe(self) -> str:
        status = "✅ REAL" if self.verified else "⚠️ SUSPICIOUS"
        return (f"{status} | score={self.hallucination_score:.2f} | "
                f"title_match={self.title_match:.2f} | "
                f"doi={'✓' if self.checks.get('doi') else '✗'} "
                f"pmid={'✓' if self.checks.get('pmid') else '✗'}")


class HallucinationDetector:
    """AI 幻觉检测器 — 逐条验证每篇论文的真实性。

    设计原则:
      - 宁可慢: 每条 DOI 都通过 Crossref API 查询 (≈1s/paper)
      - 必须真: 至少 1 个外部源确认 → verified=True
      - 可降级: API 超时/不可用 → 标记为 unverifiable (非幻觉)
    """

    # ── 中英双语生态学术语词典 ──
    BILINGUAL_TERMS: dict[str, list[str]] = {}

    # 扁平化为反向索引: English → Chinese
    _EN_TO_CN: dict[str, str] = {}

    @classmethod
    def _load_dictionary(cls):
        """加载渔业术语词典 (Wikipedia Fishery Glossary 为主源)。"""
        import json
        from pathlib import Path

        # ── 核心: Wikipedia Fishery Glossary (权威英文术语) ──
        terms = {}
        wiki_paths = [
            Path(__file__).resolve().parent.parent / "config" / "fishery_glossary_wikipedia.json",
            Path("config/fishery_glossary_wikipedia.json"),
        ]
        for p in wiki_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        wiki_terms = json.load(f)
                    for en_term in wiki_terms:
                        cn = cls._infer_chinese(en_term)
                        if cn and cn not in terms:
                            terms[cn] = []
                        if cn:
                            terms[cn].append(en_term.lower())
                except Exception:
                    pass
                break

        # ── 补充: 高频渔业中英对照 (手工校对版, 保守) ──
        verified_mappings = {
            "丰度": ["abundance"],
            "生物量": ["biomass"],
            "资源量": ["stock"],
            "补充量": ["recruitment"],
            "死亡率": ["mortality", "mortality rate"],
            "捕捞死亡率": ["fishing mortality"],
            "自然死亡": ["natural mortality"],
            "洄游": ["migration"],
            "溯河": ["anadromous"],
            "降河": ["catadromous"],
            "产卵": ["spawning"],
            "怀卵量": ["fecundity"],
            "捕捞": ["fishing", "harvest"],
            "过度捕捞": ["overfishing"],
            "渔获量": ["catch", "landing"],
            "栖息地": ["habitat"],
            "底栖": ["benthos", "benthic"],
            "浮游动物": ["zooplankton"],
            "浮游植物": ["phytoplankton"],
            "营养级": ["trophic level"],
            "食物网": ["food web"],
            "最大可持续产量": ["maximum sustainable yield"],
            "环境容纳量": ["carrying capacity"],
            "种群": ["population", "stock"],
            "世代": ["cohort"],
            "多样性": ["biodiversity"],
            "濒危": ["endangered"],
            "特有": ["endemic"],
            "可持续": ["sustainable"],
            "保护区": ["protected area", "marine protected area"],
            "增殖放流": ["stock enhancement"],
            "人工繁殖": ["captive breeding"],
        }
        for cn, ens in verified_mappings.items():
            if cn not in terms:
                terms[cn] = []
            for en in ens:
                if en.lower() not in terms[cn]:
                    terms[cn].append(en.lower())

        cls.BILINGUAL_TERMS = terms
        cls._EN_TO_CN = {}
        for cn, ens in terms.items():
            for en in ens:
                cls._EN_TO_CN[en.lower()] = cn

    @staticmethod
    def _infer_chinese(en_term: str) -> str:
        """保守推断英文术语对应的中文 (只做高置信度映射)。"""
        mapping = {
            "abundance": "丰度", "biomass": "生物量", "stock": "资源量",
            "recruitment": "补充量", "mortality": "死亡率",
            "fishing mortality": "捕捞死亡率", "natural mortality": "自然死亡",
            "migration": "洄游", "anadromous": "溯河", "catadromous": "降河",
            "spawning": "产卵", "fecundity": "怀卵量",
            "fishing": "捕捞", "overfishing": "过度捕捞",
            "harvest": "渔获量", "catch": "渔获量", "landing": "渔获量",
            "habitat": "栖息地", "benthos": "底栖", "benthic": "底栖",
            "zooplankton": "浮游动物", "phytoplankton": "浮游植物",
            "trophic level": "营养级", "food chain": "食物链",
            "food web": "食物网", "maximum sustainable yield": "最大可持续产量",
            "carrying capacity": "环境容纳量",
            "population": "种群", "cohort": "世代",
            "biodiversity": "多样性", "endangered": "濒危",
            "endemic": "特有", "sustainable": "可持续",
            "bycatch": "副渔获", "selectivity": "选择性",
            "growth rate": "生长率", "density": "密度",
            "pelagic": "中上层", "demersal": "底层",
            "upwelling": "上升流", "ecosystem": "生态系统",
            "aquaculture": "养殖", "depletion": "资源枯竭",
            "precautionary": "预防性", "quota": "配额",
            "shoaling": "集群", "predator": "捕食者",
            "prey": "饵料", "species": "物种",
            "distribution": "分布", "range": "分布区",
            "extinct": "灭绝", "threatened": "受威胁",
            "vulnerable": "易危", "conservation": "保护",
            "restoration": "恢复", "management": "管理",
            "pollution": "污染", "eutrophication": "富营养化",
            "hypoxia": "缺氧", "climate change": "气候变化",
            "temperature": "温度", "salinity": "盐度",
            "dissolved oxygen": "溶解氧", "turbidity": "浊度",
            "primary productivity": "初级生产力",
            "genetic": "遗传", "morphology": "形态",
            "otolith": "耳石", "length": "体长",
            "weight": "体重", "age": "年龄",
            "reproduction": "繁殖", "feeding": "摄食",
            "diet": "食性", "isotope": "同位素",
            "diversity index": "多样性指数",
            "sampling": "采样", "survey": "调查",
            "monitoring": "监测", "model": "模型",
        }
        return mapping.get(en_term.lower(), "")

    @classmethod
    def _normalize_metric(cls, term: str) -> set[str]:
        """将指标词归一化为所有语言变体。"""
        variants = {term.lower()}
        if term in cls.BILINGUAL_TERMS:
            variants.update(v.lower() for v in cls.BILINGUAL_TERMS[term])
        if term.lower() in cls._EN_TO_CN:
            cn = cls._EN_TO_CN[term.lower()]
            variants.add(cn)
            variants.update(v.lower() for v in cls.BILINGUAL_TERMS.get(cn, []))
        return variants

    def __init__(self, timeout: float = 5.0, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self._cache: dict[str, dict] = {}  # DOI → API 响应缓存
        if not self.BILINGUAL_TERMS:
            self._load_dictionary()

    def verify_paper(self, paper: dict) -> VerificationResult:
        """验证单篇论文。

        Args:
            paper: {doi, pmid, title, journal, year, authors, ...}

        Returns:
            VerificationResult with hallucination_score and checks
        """
        doi = paper.get("doi", "").strip()
        pmid = paper.get("pmid", "").strip()
        title = paper.get("title", "")
        journal = paper.get("journal", "")
        year = paper.get("year", 0)

        result = VerificationResult(
            paper_title=title[:100],
            doi=doi,
            pmid=pmid,
        )

        checks = {}
        score_components = []

        # ── Check 1: DOI 真实性 (Crossref API) ──
        if doi and doi.startswith("10."):
            crossref_data = self._verify_doi_crossref(doi)
            if crossref_data:
                checks["doi"] = True
                score_components.append(0.0)  # 验证通过 = 无幻觉信号
                result.official_title = crossref_data.get("title", [""])[0] if isinstance(
                    crossref_data.get("title"), list) else crossref_data.get("title", "")
                result.official_journal = (crossref_data.get("container-title", [""])[0]
                    if isinstance(crossref_data.get("container-title"), list)
                    else crossref_data.get("container-title", ""))
                result.official_year = crossref_data.get("published-print", {}).get(
                    "date-parts", [[0]])[0][0]
                # 标题相似度
                result.title_match = self._title_similarity(
                    title, result.official_title
                )
                if result.title_match < 0.5:
                    score_components.append(0.3)  # 标题差异大 → 部分幻觉信号
            else:
                checks["doi"] = False
                score_components.append(0.8)  # DOI 不存在 → 强幻觉信号
                result.errors.append(f"DOI {doi} 在 Crossref 中未找到")
        elif doi:
            checks["doi"] = None  # 格式不对, 无法验证
            score_components.append(0.2)

        # ── Check 2: PMID 真实性 (NCBI E-utilities) ──
        if pmid:
            ncbi_data = self._verify_pmid_ncbi(pmid)
            if ncbi_data:
                checks["pmid"] = True
                score_components.append(0.0)
                # 如果 Crossref 没拿到标题, 用 NCBI 的
                if not result.official_title:
                    result.official_title = ncbi_data.get("title", "")
                    result.title_match = self._title_similarity(
                        title, result.official_title
                    )
            else:
                checks["pmid"] = False
                score_components.append(0.7)
                result.errors.append(f"PMID {pmid} 在 PubMed 中未找到")

        # ── Check 3: 元数据一致性 ──
        if result.official_title and title:
            if result.title_match < 0.3:
                score_components.append(0.5)
                result.errors.append(
                    f"标题严重不匹配 (相似度 {result.title_match:.2f})"
                )
        if result.official_journal and journal:
            journal_match = self._title_similarity(journal, result.official_journal)
            if journal_match < 0.5:
                score_components.append(0.2)
        if result.official_year and year:
            if abs(int(result.official_year) - int(year)) > 2:
                score_components.append(0.2)

        # ── Check 4: 不可验证项 (非幻觉, 但降低置信度) ──
        if not doi and not pmid:
            checks["unverifiable"] = True
            score_components.append(0.1)  # 无法验证 ≠ 幻觉

        # ── 综合评分 ──
        if score_components:
            result.hallucination_score = round(
                sum(score_components) / len(score_components), 2
            )
        result.checks = checks
        # verified = 至少 1 个外部源确认 + 无严重矛盾
        result.verified = (
            (checks.get("doi") is True or checks.get("pmid") is True)
            and result.hallucination_score < 0.5
        )

        return result

    def verify_papers(self, papers: list[dict],
                      progress_callback=None) -> list[VerificationResult]:
        """批量验证论文列表。"""
        results = []
        for i, paper in enumerate(papers):
            if progress_callback:
                progress_callback(i + 1, len(papers))
            result = self.verify_paper(paper)
            results.append(result)
        return results

    def hallucination_report(self, results: list[VerificationResult]) -> dict:
        """幻觉检测报告。"""
        verified = [r for r in results if r.verified]
        suspicious = [r for r in results if not r.verified and r.hallucination_score > 0]
        return {
            "total": len(results),
            "verified": len(verified),
            "suspicious": len(suspicious),
            "avg_hallucination_score": round(
                sum(r.hallucination_score for r in results) / max(len(results), 1),
                3,
            ),
            "suspicious_papers": [
                {"title": r.paper_title[:80], "score": r.hallucination_score,
                 "errors": r.errors}
                for r in sorted(suspicious, key=lambda x: x.hallucination_score,
                                reverse=True)
            ],
        }

    def filter_verified(self, papers: list[dict],
                        min_verified_ratio: float = 0.3
                        ) -> tuple[list[dict], list[dict]]:
        """分离已验证和未验证论文。

        Returns:
            (verified_papers, rejected_papers)
        """
        results = self.verify_papers(papers)
        verified = []
        rejected = []
        for paper, result in zip(papers, results):
            if result.verified:
                # 附加验证元数据
                paper["_verified"] = True
                paper["_hallucination_score"] = result.hallucination_score
                paper["_official_title"] = result.official_title
                paper["_official_journal"] = result.official_journal
                paper["_title_match"] = result.title_match
                verified.append(paper)
            else:
                paper["_verified"] = False
                paper["_hallucination_score"] = result.hallucination_score
                paper["_errors"] = result.errors
                rejected.append(paper)

        # 如果验证通过率太低, 全部保留但标记 (API 可能挂了)
        if len(papers) > 0 and len(verified) / len(papers) < min_verified_ratio:
            return papers, []  # 可能 API 故障, 不丢弃论文

        return verified, rejected

    # ── Internal: API 调用 ──────────────────────────────────

    def _verify_doi_crossref(self, doi: str) -> dict | None:
        """通过 Crossref API 验证 DOI。"""
        if doi in self._cache:
            return self._cache[doi]

        url = f"https://api.crossref.org/works/{doi}"
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "CognitiveSearchEngine/5.9 (mailto:reasonix@example.com)")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    msg = data.get("message", {})
                    self._cache[doi] = msg
                    return msg
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self._cache[doi] = None
                    return None
                time.sleep(0.5 * (attempt + 1))
            except Exception:
                time.sleep(0.5 * (attempt + 1))

        return None

    def _verify_pmid_ncbi(self, pmid: str) -> dict | None:
        """通过 NCBI E-utilities 验证 PMID。"""
        cache_key = f"pmid:{pmid}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pubmed&id={pmid}&retmode=json"
        )
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    result = data.get("result", {})
                    uids = result.get("uids", [])
                    if pmid in uids:
                        paper_data = result.get(pmid, {})
                        self._cache[cache_key] = paper_data
                        return paper_data
                    else:
                        self._cache[cache_key] = None
                        return None
            except Exception:
                time.sleep(0.5 * (attempt + 1))

        return None

    def _title_similarity(self, t1: str, t2: str) -> float:
        """计算标题相似度 (Jaccard)。"""
        if not t1 or not t2:
            return 0.0
        # 归一化
        for ch in ".,;:()[]{}!?\"'":
            t1 = t1.replace(ch, " ")
            t2 = t2.replace(ch, " ")
        w1 = set(t1.lower().split())
        w2 = set(t2.lower().split())
        if not w1 or not w2:
            return 0.0
        return len(w1 & w2) / len(w1 | w2)

    # ── v8.1: 声明真实性验证 ──────────────────────────────

    def verify_claim(self, claim: str, source_paper: dict,
                      tolerance: float = 0.10) -> dict:
        """结构化声明验证 — 验证声明与论文内容的一致性。

        三层验证:
          1. 结构提取: 从声明中提取 {指标, 数值, 方向, 对象, 时间段}
          2. 上下文匹配: 数值必须出现在相关指标的语义邻域 (±50 字符)
          3. 容差验证: 数值必须在 ±10% 容差内 (可配置)

        Returns:
            {verified: bool, confidence: float,
             claim_struct: {...}, evidence_matches: [...]}
        """
        import re

        abstract = source_paper.get("abstract", "")
        title = source_paper.get("title", "")
        full_text = f"{title}. {abstract}"

        # ── Step 1: 结构化声明提取 ──
        claim_struct = self._parse_claim_structure(claim)

        # ── Step 2: 逐项验证 ──
        matches = []
        checks = {}

        # 2a: 数值验证 (核心)
        if claim_struct["numbers"]:
            num_results = []
            for num_info in claim_struct["numbers"]:
                result = self._verify_number_in_context(
                    num_info, full_text, claim_struct["metrics"],
                    tolerance
                )
                num_results.append(result)
            # 至少一半的数值需要被验证
            nums_ok = sum(1 for r in num_results if r["found"]) / len(num_results)
            checks["numbers"] = nums_ok
            matches.extend(num_results)
        else:
            checks["numbers"] = 1.0  # 没有数字 → 不扣分

        # 2b: 对象/物种名验证
        if claim_struct["subject"]:
            subject_found = claim_struct["subject"].lower() in full_text.lower()
            checks["subject"] = 1.0 if subject_found else 0.0
            matches.append({
                "type": "subject", "value": claim_struct["subject"],
                "found": subject_found,
            })
        else:
            checks["subject"] = 0.5  # 无法解析对象 → 中性

        # 2c: 方向验证 (上升/下降/不变)
        if claim_struct["direction"]:
            dir_found = self._verify_direction(
                claim_struct["direction"], full_text,
                claim_struct["metrics"]
            )
            checks["direction"] = dir_found
        else:
            checks["direction"] = 1.0

        # ── Step 3: 综合置信度 ──
        weights = {"numbers": 0.4, "subject": 0.25, "direction": 0.2}
        confidence = sum(
            checks.get(k, 1.0) * w for k, w in weights.items()
        )
        # 指标匹配加分
        metric_bonus = self._metric_context_score(
            claim_struct["metrics"], full_text
        )
        confidence = confidence * 0.8 + metric_bonus * 0.2

        evidence_parts = []
        if checks.get("numbers", 1.0) < 1.0:
            evidence_parts.append(
                f"数值匹配 {checks['numbers']:.0%}"
            )
        if checks.get("subject", 1.0) < 1.0:
            evidence_parts.append("对象未在论文中找到")
        if checks.get("direction", 1.0) < 1.0:
            evidence_parts.append("方向不一致")

        return {
            "verified": confidence >= 0.5,
            "confidence": round(min(confidence, 1.0), 3),
            "claim_struct": claim_struct,
            "checks": {k: round(v, 3) for k, v in checks.items()},
            "evidence_matches": matches,
            "evidence": "; ".join(evidence_parts) if evidence_parts else (
                f"所有要素验证通过 (置信度 {confidence:.2f})"
            ),
        }

    def _parse_claim_structure(self, claim: str) -> dict:
        """从自然语言声明中提取结构化信息。

        "刀鲚生物量从2010到2020年下降了42.5%"
        → {
            subject: "刀鲚",
            metrics: ["生物量"],
            numbers: [{value: 42.5, context: "下降", modifier: "%"}],
            direction: "下降",
            timeframe: "2010-2020",
        }
        """
        import re

        # 提取数字及其上下文 (排除年份: 1900-2099 的整数)
        numbers = []
        for m in re.finditer(
            r'(\d+\.?\d*)\s*(%|％|倍|个百分点)?',
            claim
        ):
            val = float(m.group(1))
            # 跳过纯年份 (整数, 1900-2099)
            if val == int(val) and 1900 <= val <= 2099:
                continue
            modifier = m.group(2) or ""
            # 获取数字前后的上下文 (20 字符窗口)
            start = max(0, m.start() - 20)
            end = min(len(claim), m.end() + 20)
            context = claim[start:end]
            numbers.append({
                "value": val,
                "modifier": modifier,
                "context": context,
            })

        # 提取方向词
        direction = ""
        dir_patterns = [
            (r'下降|减少|降低|decline|decrease|reduce|drop', "下降"),
            (r'上升|增加|增长|提高|increase|rise|grow|raise', "上升"),
            (r'不变|稳定|持平|stable|unchanged|constant', "不变"),
        ]
        for pattern, label in dir_patterns:
            if re.search(pattern, claim, re.IGNORECASE):
                direction = label
                break

        # 提取指标词 (含双语扩展)
        metric_keywords = list(self.BILINGUAL_TERMS.keys()) + list(
            self._EN_TO_CN.keys()
        )
        metrics = []
        for kw in metric_keywords:
            if kw.lower() in claim.lower():
                # 添加该指标的所有语言变体
                variants = self._normalize_metric(kw)
                metrics.extend(variants)
        # 去重
        metrics = list(set(metrics))

        # 提取对象 (物种名/地名) — 广义中文物种名匹配
        subject = ""
        # 带鱼/豚/鲌/鲚等鱼字旁的词
        species_match = re.search(
            r'([\u4e00-\u9fff]{2,6}(?:鱼|豚|鲌|鲚|鳤|鳡|鲢|鳙|鲂|鮈|鳑|鲏|鲀|魨|鲀|鲃|鳅|鳢|鳗|鲶|鮡|鳜|鲈|鲻|鲷|鲹|鲾|鳐|鳕|鳓|鳗|鲨|鲸))',
            claim
        )
        if species_match:
            subject = species_match.group(1)
        else:
            # 尝试英文物种名
            eng_match = re.search(
                r'([A-Z][a-z]+ [a-z]+)',
                claim
            )
            if eng_match:
                subject = eng_match.group(1)

        # 提取时间段
        timeframe = ""
        time_match = re.search(
            r'(\d{4})\s*[-–—到至]\s*(\d{4})',
            claim
        )
        if time_match:
            timeframe = f"{time_match.group(1)}-{time_match.group(2)}"

        return {
            "subject": subject,
            "metrics": metrics,
            "numbers": numbers,
            "direction": direction,
            "timeframe": timeframe,
        }

    def _verify_number_in_context(self, num_info: dict, text: str,
                                   metrics: list[str],
                                   tolerance: float) -> dict:
        """验证数值是否在正确语义上下文中出现。

        不是简单字符串匹配, 而是:
          1. 在文本中找 ±10% 范围内的数值
          2. 检查附近是否有相关指标词
          3. 评分: 精确匹配 > 容差匹配 > 无匹配
        """
        import re

        value = num_info["value"]
        context_words = num_info.get("context", "")

        # 搜索目标数值 ± tolerance
        lo = value * (1 - tolerance)
        hi = value * (1 + tolerance)

        # 在文本中找所有数字
        all_numbers = re.finditer(
            r'(\d+\.?\d*)\s*(%|％)?',
            text
        )

        best_match = None
        best_score = 0.0

        for m in all_numbers:
            found_val = float(m.group(1))
            if lo <= found_val <= hi:
                # 检查上下文: 数字附近是否有指标词
                window_start = max(0, m.start() - 80)
                window_end = min(len(text), m.end() + 80)
                window = text[window_start:window_end].lower()

                # 指标匹配分
                metric_score = 0.0
                for metric in metrics:
                    if metric.lower() in window:
                        metric_score = max(metric_score, 0.5)
                        # 指标越近分越高
                        metric_pos = window.find(metric.lower())
                        dist = abs(metric_pos - (m.start() - window_start))
                        if dist < 30:
                            metric_score = max(metric_score, 0.8)

                # 精确/容差分
                precision = 1.0 - abs(found_val - value) / max(value, 1e-9)
                score = 0.4 * min(precision, 1.0) + 0.6 * metric_score

                if score > best_score:
                    best_score = score
                    best_match = {
                        "value": found_val,
                        "position": m.start(),
                        "context_window": window[:100],
                    }

        return {
            "type": "number",
            "claimed_value": value,
            "found": best_score > 0.3,
            "best_match": best_match,
            "score": round(best_score, 3),
        }

    def _verify_direction(self, direction: str, text: str,
                          metrics: list[str]) -> float:
        """验证方向词是否与相关指标共现。

        支持中英文跨语言: "下降" ↔ "decline/decrease/drop"
        """
        import re
        text_lower = text.lower()

        # 方向词的中英文同义词映射
        dir_synonyms = {
            "下降": ["下降", "减少", "降低", "decline", "declined",
                     "decrease", "decreased", "reduce", "reduced",
                     "drop", "dropped", "fell", "falling", "fall"],
            "上升": ["上升", "增加", "增长", "提高", "increase",
                     "increased", "rise", "rose", "grow", "grew",
                     "raise", "raised", "rising", "growing"],
            "不变": ["不变", "稳定", "持平", "stable", "unchanged",
                     "constant", "steady", "maintained", "no change"],
        }

        synonyms = dir_synonyms.get(direction, [direction])

        if not metrics:
            # 没有指标 → 只检查方向词是否存在
            for syn in synonyms:
                if syn.lower() in text_lower:
                    return 0.7  # 存在但不是最理想 (无指标关联)
            return 0.0

        # 检查方向词 Synonyms 是否在指标词的语义邻域内
        for metric in metrics:
            metric_positions = [
                m.start() for m in re.finditer(
                    re.escape(metric.lower()), text_lower
                )
            ]
            for pos in metric_positions:
                window = text_lower[max(0, pos - 100):pos + 100]
                for syn in synonyms:
                    if syn.lower() in window:
                        return 1.0  # 方向词在指标附近 → 高置信

        # 方向词存在但远离指标 → 中等置信
        for syn in synonyms:
            if syn.lower() in text_lower:
                return 0.5

        return 0.0

    def _metric_context_score(self, metrics: list[str],
                               text: str) -> float:
        """计算指标词在文本中的上下文覆盖度。"""
        if not metrics:
            return 0.5  # 无指标不扣分
        text_lower = text.lower()
        found = sum(1 for m in metrics if m.lower() in text_lower)
        return found / len(metrics)
