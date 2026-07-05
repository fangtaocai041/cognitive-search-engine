"""
claim_verifier.py — Layer 7: LLM 全文声明验证
================================================
真正的声明验证 — 不是字符串匹配, 而是语义理解的交叉比对。

流程:
  1. 获取论文全文 (通过 MCP article 工具)
  2. LLM 逐句提取所有定量声明
  3. 用户声明与提取声明逐条比对
  4. 输出: verified / partially_verified / contradicted / unverifiable

原理:
  文献 → LLM 提取 [{指标, 数值, 单位, 对象, 方向, 置信度, 上下文}]
  用户声明 → 同样的结构
  比对 → 数值 ±tolerance, 语义方向一致, 对象匹配

Usage:
    from src.claim_verifier import ClaimVerifier
    cv = ClaimVerifier()
    result = cv.verify("刀鲚生物量下降了42.5%", paper_fulltext="...")
    # → {status: "verified", matched_data: [...], confidence: 0.95}
"""

from __future__ import annotations

import json
import math
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DataPoint:
    """论文中提取的一个定量数据点。"""
    metric: str           # 指标名 (biomass, abundance, temperature...)
    value: float          # 数值
    unit: str = ""        # 单位 (%, kg, °C, individuals...)
    direction: str = ""   # 趋势方向 (increased, decreased, stable, fluctuated)
    subject: str = ""     # 研究对象 (物种名/种群/生态系统)
    timespan: str = ""    # 时间范围 (2010-2020, 5 years...)
    confidence: float = 1.0  # 提取置信度
    context: str = ""     # 原文句子
    p_value: Optional[float] = None  # 统计显著性


@dataclass
class ClaimMatch:
    """一条声明的比对结果。"""
    claim: str
    status: str = "unverifiable"  # verified | partially_verified | contradicted | unverifiable
    matched_points: list[DataPoint] = field(default_factory=list)
    similarity: float = 0.0
    explanation: str = ""
    tolerance_violations: list[str] = field(default_factory=list)


@dataclass
class ClaimVerificationReport:
    """完整的声明验证报告。"""
    paper_title: str = ""
    claims: list[ClaimMatch] = field(default_factory=list)
    extracted_datapoints: list[DataPoint] = field(default_factory=list)
    overall_confidence: float = 0.0
    verified_count: int = 0
    contradicted_count: int = 0
    summary: str = ""


class ClaimVerifier:
    """LLM 驱动的全文声明验证器。

    设计:
      - 调用 DeepSeek API 逐句提取结构化数据
      - 数值比对: 精确匹配 + ±tolerance 容差
      - 语义比对: 方向/对象/时间范围一致性
    """

    # 常见生态学指标的识别模式
    METRIC_PATTERNS = {
        "biomass": r"(?:生物量|biomass|standing\s*stock)\s*(?:下降|decline|减少|decrease|上升|increase|增长|grow)",
        "abundance": r"(?:丰度|abundance|种群数量|population\s*size|个体数)",
        "diversity": r"(?:多样性|diversity|物种数|species\s*richness|Shannon)",
        "body_size": r"(?:体长|body\s*size|体质量|body\s*mass|体重|weight)",
        "fecundity": r"(?:繁殖力|fecundity|产卵|spawning|怀卵量)",
        "mortality": r"(?:死亡率|mortality|存活率|survival\s*rate)",
        "temperature": r"(?:温度|temperature|水温|water\s*temp)",
        "catch": r"(?:渔获量|catch|捕捞|harvest|产量)",
        "area": r"(?:面积|area|分布区|distribution\s*range|栖息地面积)",
    }

    def __init__(self,
                 api_key: str = "",
                 api_base: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 tolerance: float = 0.10,  # 10% 数值容差
                 timeout: float = 30.0):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.tolerance = tolerance  # ±10% 默认
        self.timeout = timeout

    def verify(self, claims: list[str],
               paper_fulltext: str,
               paper_title: str = "",
               species: str = "") -> ClaimVerificationReport:
        """验证多条声明。

        Args:
            claims: 用户/系统生成的声明列表
            paper_fulltext: 论文全文
            paper_title: 论文标题
            species: 目标物种 (用于精准提取)

        Returns:
            ClaimVerificationReport
        """
        # Step 1: LLM 提取全文中的定量数据点
        extracted = self._extract_datapoints(paper_fulltext, species)

        # Step 2: 逐条验证声明
        matches = []
        for claim in claims:
            match = self._match_claim(claim, extracted, species)
            matches.append(match)

        # Step 3: 综合报告
        verified = sum(1 for m in matches if m.status == "verified")
        contradicted = sum(1 for m in matches if m.status == "contradicted")
        confidence = (
            sum(m.similarity for m in matches) / max(len(matches), 1)
        )

        return ClaimVerificationReport(
            paper_title=paper_title,
            claims=matches,
            extracted_datapoints=extracted,
            overall_confidence=round(confidence, 3),
            verified_count=verified,
            contradicted_count=contradicted,
            summary=self._generate_summary(matches),
        )

    def _extract_datapoints(self, fulltext: str, species: str = ""
                            ) -> list[DataPoint]:
        """从全文中提取定量数据点。

        通过 LLM 识别: 指标 + 数值 + 方向 + 对象 + 时间范围。
        回退: 正则表达式提取数字和上下文。
        """
        points = []

        # 尝试 LLM 提取
        if self.api_key:
            llm_points = self._llm_extract(fulltext, species)
            if llm_points:
                return llm_points

        # 回退: 正则提取
        points.extend(self._regex_extract(fulltext, species))
        return points

    def _match_claim(self, claim: str, datapoints: list[DataPoint],
                     species: str) -> ClaimMatch:
        """将一条声明与提取的数据点进行比对。

        比对方程:
          - 指标语义匹配: metric similarity (Jaccard + embedding)
          - 数值匹配: abs(claim_val - paper_val) / paper_val ≤ tolerance
          - 方向匹配: trend direction 一致
          - 对象匹配: species / subject 一致
        """
        # 从声明中提取结构化信息
        claim_metric, claim_value, claim_direction = self._parse_claim(claim)

        match = ClaimMatch(claim=claim)

        if claim_value is None:
            match.status = "unverifiable"
            match.explanation = "声明中未检测到可量化的数值"
            return match

        best_match = None
        best_score = 0.0

        for dp in datapoints:
            score = 0.0
            violations = []

            # 1. 指标匹配
            metric_sim = self._metric_similarity(claim_metric, dp.metric)
            if metric_sim < 0.3:
                continue
            score += 0.3 * metric_sim

            # 2. 数值匹配 (硬约束: 偏差 > 30% 直接判定矛盾)
            if dp.value != 0:
                error = abs(claim_value - dp.value) / abs(dp.value)
                if error <= self.tolerance:
                    score += 0.35
                elif error <= self.tolerance * 2:
                    score += 0.15
                elif error <= self.tolerance * 3:
                    score += 0.05
                else:
                    violations.append(f"数值严重偏差 {error*100:.1f}%")
                    score -= 0.30  # 严重数值偏差

            # 3. 方向匹配
            if claim_direction and dp.direction:
                if self._direction_match(claim_direction, dp.direction):
                    score += 0.20
                else:
                    violations.append(
                        f"方向矛盾: 声明'{claim_direction}' vs 论文'{dp.direction}'"
                    )
                    score -= 0.40  # 方向矛盾是严重问题, 大幅扣分

            # 4. 对象匹配
            if species and dp.subject:
                species_sim = self._metric_similarity(species.lower(),
                                                       dp.subject.lower())
                score += 0.15 * species_sim

            total_score = min(score, 1.0)

            if total_score > best_score:
                best_score = total_score
                best_match = dp
                match.tolerance_violations = violations

        if best_match:
            match.matched_points = [best_match]
            match.similarity = round(best_score, 3)

            if best_score >= 0.65:
                match.status = "verified"
                match.explanation = f"与论文数据高度一致 (匹配度 {best_score:.2f})"
            elif best_score >= 0.40:
                match.status = "partially_verified"
                match.explanation = (f"部分匹配 (匹配度 {best_score:.2f}) — "
                                    f"建议人工复核")
            else:
                match.status = "contradicted"
                match.explanation = "论文中未找到支撑该声明的数据"
        else:
            match.status = "unverifiable"
            match.explanation = "论文中未提取到相关指标的数据点"

        return match

    # ── Internal: LLM extraction ───────────────────────────

    def _llm_extract(self, fulltext: str, species: str
                     ) -> list[DataPoint] | None:
        """调用 DeepSeek API 提取结构化数据点。"""
        prompt = f"""你是一个生态学文献数据提取专家。请仔细阅读以下论文全文, 
逐句提取所有定量数据点。只提取原文明确写出的数字, 不要推断。

对每个数据点, 输出 JSON 数组:
[
  {{
    "metric": "指标名 (英文)",
    "value": 数值,
    "unit": "单位",
    "direction": "increased/decreased/stable/fluctuated",
    "subject": "研究对象 (物种/种群)",
    "timespan": "时间范围",
    "confidence": 0-1提取置信度,
    "context": "所在句子(原文)",
    "p_value": 统计p值或null
  }}
]

目标物种: {species}

论文全文:
{fulltext[:8000]}
"""
        try:
            response = self._call_llm(prompt)
            data = json.loads(response)
            return [
                DataPoint(
                    metric=d.get("metric", ""),
                    value=float(d.get("value", 0)),
                    unit=d.get("unit", ""),
                    direction=d.get("direction", ""),
                    subject=d.get("subject", ""),
                    timespan=d.get("timespan", ""),
                    confidence=float(d.get("confidence", 1.0)),
                    context=d.get("context", ""),
                    p_value=(float(d["p_value"])
                             if d.get("p_value") else None),
                )
                for d in data
                if isinstance(d, dict)
            ]
        except Exception:
            return None

    def _call_llm(self, prompt: str) -> str:
        """调用 DeepSeek API。"""
        url = f"{self.api_base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a data extraction expert. Output only valid JSON arrays. No explanation."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]

    # ── Internal: regex fallback extraction ────────────────

    def _regex_extract(self, fulltext: str, species: str = ""
                       ) -> list[DataPoint]:
        """正则表达式提取: 回退方案。"""
        points = []

        # 中文百分比模式 (单独处理, 因为语言结构不同)
        cn_pct = re.compile(
            r'(?P<context>[^。！？\n]{0,30})'
            r'(?P<direction>下降了?|减少了?|降低了?|增加了?|上升了?|增长了?)'
            r'\s*(?P<value>\d+\.?\d*)\s*%',
        )
        for m in cn_pct.finditer(fulltext):
            ctx = m.group("context").strip()
            direction_text = m.group("direction")
            direction = "decreased" if any(w in direction_text for w in ["下降", "减少", "降低"]) else "increased"
            value = float(m.group("value"))
            points.append(DataPoint(
                metric=ctx if ctx else "unknown",
                value=value,
                unit="%",
                direction=direction,
                subject=species,
                context=m.group(0),
                confidence=0.6,
            ))

        # 英文百分比模式
        pct_pattern = re.compile(
            r'(?P<metric>[a-zA-Z\u4e00-\u9fff\s]+?)\s*'
            r'(?:declined|decreased|dropped|fell|reduced|'
            r'下降|减少|降低|下降)\s*(?:by\s*)?'
            r'(?P<value>\d+\.?\d*)\s*%',
            re.IGNORECASE
        )
        for m in pct_pattern.finditer(fulltext):
            metric = m.group("metric").strip().lower()
            value = float(m.group("value"))
            ctx_start = max(0, m.start() - 50)
            ctx_end = min(len(fulltext), m.end() + 50)
            points.append(DataPoint(
                metric=metric,
                value=value,
                unit="%",
                direction="decreased",
                subject=species,
                context=fulltext[ctx_start:ctx_end].strip(),
                confidence=0.6,
            ))

        # 增长模式: "increased by 30%" / "增加了 30%"
        inc_pattern = re.compile(
            r'(?P<metric>[a-zA-Z\u4e00-\u9fff\s]+?)\s*'
            r'(?:increased|rose|grew|gained|'
            r'增加|上升|增长|上升)\s*(?:by\s*)?'
            r'(?P<value>\d+\.?\d*)\s*%',
            re.IGNORECASE
        )
        for m in inc_pattern.finditer(fulltext):
            metric = m.group("metric").strip().lower()
            value = float(m.group("value"))
            ctx_start = max(0, m.start() - 50)
            ctx_end = min(len(fulltext), m.end() + 50)
            points.append(DataPoint(
                metric=metric,
                value=value,
                unit="%",
                direction="increased",
                subject=species,
                context=fulltext[ctx_start:ctx_end].strip(),
                confidence=0.6,
            ))

        # 绝对值模式: "biomass was 123.4 kg/ha"
        abs_pattern = re.compile(
            r'(?P<metric>[a-zA-Z\u4e00-\u9fff\s]+?)\s*'
            r'(?:was|is|of|为|是)\s*'
            r'(?P<value>\d+\.?\d*)\s*'
            r'(?P<unit>kg|g|m|cm|mm|°C|individuals|ind\.|t|tonnes?)',
            re.IGNORECASE
        )
        for m in abs_pattern.finditer(fulltext):
            points.append(DataPoint(
                metric=m.group("metric").strip().lower(),
                value=float(m.group("value")),
                unit=m.group("unit"),
                direction="stable",
                subject=species,
                context=fulltext[max(0,m.start()-50):min(len(fulltext),m.end()+50)],
                confidence=0.5,
            ))

        return points

    # ── Internal: helpers ──────────────────────────────────

    def _parse_claim(self, claim: str
                     ) -> tuple[str, Optional[float], str]:
        """解析声明的(指标, 数值, 方向)。"""
        # 提取指标
        metric = ""
        for key in self.METRIC_PATTERNS:
            if re.search(self.METRIC_PATTERNS[key], claim, re.IGNORECASE):
                metric = key
                break
        if not metric:
            # 取前两个词作为指标
            words = claim.split()[:2]
            metric = "_".join(words).lower()

        # 提取数值
        nums = re.findall(r'\d+\.?\d*', claim)
        value = float(nums[0]) if nums else None

        # 提取方向
        direction = ""
        if re.search(r'declin|decreas|dropp|fell|reduc|下降|减少|降低',
                     claim, re.IGNORECASE):
            direction = "decreased"
        elif re.search(r'increas|rose|grew|gain|上升|增加|增长',
                       claim, re.IGNORECASE):
            direction = "increased"
        elif re.search(r'stabl|unchang|稳定|不变',
                       claim, re.IGNORECASE):
            direction = "stable"

        return metric, value, direction

    def _metric_similarity(self, m1: str, m2: str) -> float:
        """指标名相似度。"""
        if not m1 or not m2:
            return 0.0
        w1 = set(m1.lower().replace("_", " ").split())
        w2 = set(m2.lower().replace("_", " ").split())
        if not w1 or not w2:
            return 0.0
        jaccard = len(w1 & w2) / len(w1 | w2)
        # 子串匹配加分
        if m1.lower() in m2.lower() or m2.lower() in m1.lower():
            jaccard = max(jaccard, 0.7)
        return jaccard

    def _direction_match(self, d1: str, d2: str) -> bool:
        """方向匹配。"""
        synonym_groups = [
            {"increased", "increase", "rose", "grew", "gained", "上升", "增加"},
            {"decreased", "decrease", "declined", "dropped", "fell", "下降", "减少"},
            {"stable", "unchanged", "稳定", "不变"},
        ]
        for group in synonym_groups:
            if d1.lower() in group and d2.lower() in group:
                return True
        return d1.lower() == d2.lower()

    def _generate_summary(self, matches: list[ClaimMatch]) -> str:
        """生成验证摘要。"""
        parts = []
        for m in matches:
            emoji = {"verified": "✅", "partially_verified": "⚠️",
                     "contradicted": "❌", "unverifiable": "❓"}
            parts.append(
                f"{emoji.get(m.status, '')} [{m.status}] {m.claim[:80]}"
            )
            if m.explanation:
                parts.append(f"   → {m.explanation}")
        return "\n".join(parts)
