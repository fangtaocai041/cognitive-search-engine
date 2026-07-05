"""
test_claim_verifier.py — 声明验证器测试
=========================================
验证 ClaimVerifier 的核心比对逻辑 (不依赖 LLM API)。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.claim_verifier import (
    ClaimVerifier, ClaimMatch, DataPoint, ClaimVerificationReport,
)


class TestRegexExtraction:
    """正则提取: 不依赖 LLM 的提取逻辑。"""

    def test_extract_percentage_decline(self):
        cv = ClaimVerifier(api_key="")  # no LLM → uses regex fallback
        text = "The biomass of Coilia nasus declined by 42.5% between 2010 and 2020."
        points = cv._regex_extract(text, species="Coilia nasus")
        assert len(points) >= 1
        assert points[0].value == 42.5
        assert points[0].unit == "%"
        assert points[0].direction == "decreased"

    def test_extract_percentage_increase(self):
        cv = ClaimVerifier(api_key="")
        text = "Water temperature increased by 3.2% annually."
        points = cv._regex_extract(text)
        increase = [p for p in points if p.direction == "increased"]
        assert len(increase) >= 1

    def test_extract_chinese_text(self):
        cv = ClaimVerifier(api_key="")
        text = "刀鲚生物量下降了42.5%，同时丰度减少了18.3%。"
        points = cv._regex_extract(text, species="刀鲚")
        assert len(points) >= 1


class TestClaimMatching:
    """声明比对: 核心匹配逻辑。"""

    def test_exact_match(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        points = [
            DataPoint(metric="biomass", value=42.5, unit="%",
                      direction="decreased", subject="Coilia nasus",
                      context="biomass declined by 42.5%", confidence=0.9),
        ]
        match = cv._match_claim(
            "Coilia nasus biomass decreased by 42.5%",
            points,
            species="Coilia nasus",
        )
        assert match.status == "verified"
        assert match.similarity >= 0.65

    def test_within_tolerance(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        points = [
            DataPoint(metric="biomass", value=42.5, unit="%",
                      direction="decreased", subject="Coilia nasus",
                      context="declined by 42.5%", confidence=0.9),
        ]
        match = cv._match_claim(
            "Coilia nasus biomass decreased by 43.0%",  # 0.5/42.5 = 1.2% < 10%
            points, species="Coilia nasus",
        )
        assert match.status == "verified"

    def test_outside_tolerance(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        points = [
            DataPoint(metric="biomass", value=42.5, unit="%",
                      direction="decreased", subject="Coilia nasus",
                      context="declined by 42.5%", confidence=0.9),
        ]
        match = cv._match_claim(
            "Coilia nasus biomass decreased by 60.0%",  # 17.5/42.5 = 41% > 30%
            points, species="Coilia nasus",
        )
        # 偏差 41% > 30% → contradicted
        assert match.status == "contradicted"

    def test_direction_contradiction(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        points = [
            DataPoint(metric="biomass", value=42.5, unit="%",
                      direction="decreased", subject="Coilia nasus",
                      context="declined by 42.5%", confidence=0.9),
        ]
        match = cv._match_claim(
            "Coilia nasus biomass increased by 42.5%",  # 方向相反!
            points, species="Coilia nasus",
        )
        # 方向矛盾 → 扣分 → contradicted
        assert match.status == "contradicted"

    def test_unverifiable(self):
        cv = ClaimVerifier(api_key="")
        points: list[DataPoint] = []  # no data points
        match = cv._match_claim(
            "Something happened by 50%", points, species="Test"
        )
        assert match.status == "unverifiable"


class TestFullVerify:
    """完整验证流程。"""

    def test_verify_with_regex(self):
        cv = ClaimVerifier(api_key="")  # regex fallback
        fulltext = """
        We studied Coilia nasus in the Yangtze River.
        Results showed that biomass declined by 42.5% over the study period.
        Abundance also decreased by 18.3 per year.
        """
        report = cv.verify(
            claims=["Coilia nasus biomass decreased by 42.5%",
                    "Coilia nasus abundance decreased by 15%"],
            paper_fulltext=fulltext,
            paper_title="Coilia nasus population study",
            species="Coilia nasus",
        )
        assert report.verified_count >= 1
        assert len(report.claims) == 2

    def test_correct_title_extraction(self):
        cv = ClaimVerifier(api_key="")
        text = "刀鲚生物量下降了42.5%。长江刀鲚丰度减少了18.3%。"
        points = cv._regex_extract(text, species="刀鲚")
        assert len(points) >= 1
        values = [p.value for p in points]
        assert 42.5 in values

    def test_tolerance_10_percent(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        # Paper says 42.5, claim says 45.0 → error = 2.5/42.5 ≈ 5.9% < 10%
        points = [DataPoint(metric="biomass", value=42.5, unit="%",
                           direction="decreased", subject="Test",
                           context="declined 42.5%")]
        match = cv._match_claim("biomass decreased 45.0%", points, species="Test")
        assert match.status == "verified"  # within 10%

    def test_tolerance_10_percent_fail(self):
        cv = ClaimVerifier(api_key="", tolerance=0.10)
        # Paper says 42.5, claim says 50.0 → error = 7.5/42.5 ≈ 17.6% > 10%
        # But still within 2x tolerance (20%) → partially_verified
        points = [DataPoint(metric="biomass", value=42.5, unit="%",
                           direction="decreased", subject="Test")]
        match = cv._match_claim("biomass decreased 50.0%", points, species="Test")
        assert match.status != "contradicted"  # 偏差在 2x 容差内, 非矛盾
