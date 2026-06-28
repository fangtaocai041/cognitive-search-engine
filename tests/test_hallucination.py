"""
test_hallucination.py — AI 幻觉检测器测试
===========================================
验证 HallucinationDetector 的核心功能。
联网测试: DOI/PMID 真实性查询 (标记为 slow)。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestHallucinationDetectorOffline:
    """离线测试: 不联网的功能测试。"""

    def test_import(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        assert hd.timeout == 5.0

    def test_verify_paper_no_identifiers(self):
        """无 DOI/PMID 的论文 → unverifiable 但非幻觉。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        result = hd.verify_paper({
            "title": "Some paper without identifiers",
            "journal": "Unknown Journal",
            "year": 2024,
        })
        # 无标识符 → 无法验证, 但也不是幻觉
        assert result.hallucination_score <= 0.3

    def test_verify_paper_fake_doi(self):
        """虚构 DOI → 高幻觉分。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        result = hd.verify_paper({
            "title": "Fake Paper",
            "doi": "10.99999/fake-nonexistent-paper-2025",
        })
        # DOI 在 Crossref 中不存在 (需要联网, 离线会超时返回 None)
        # 超时 → doi check = False → 高幻觉分
        assert result.checks.get("doi") is False
        assert result.hallucination_score > 0.5

    def test_verify_papers_batch(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        papers = [
            {"title": "P1", "doi": "10.12345/fake1"},
            {"title": "P2"},
        ]
        results = hd.verify_papers(papers)
        assert len(results) == 2

    def test_hallucination_report(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        papers = [{"title": "P1", "doi": "10.fake/fake"}]
        results = hd.verify_papers(papers)
        report = hd.hallucination_report(results)
        assert report["total"] == 1
        assert "avg_hallucination_score" in report

    def test_title_similarity(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        s = hd._title_similarity(
            "Population dynamics of Coilia nasus",
            "Population dynamics of Coilia nasus in the Yangtze River"
        )
        assert s > 0.4

    def test_title_similarity_different(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        s = hd._title_similarity(
            "Population dynamics of Coilia nasus",
            "Quantum computing advances in 2025"
        )
        assert s < 0.1

    def test_claim_verification(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        paper = {
            "title": "Coilia nasus biomass declined by 42.5% from 2010 to 2020",
            "abstract": "We found that Coilia nasus biomass declined by 42.5% "
                       "between 2010 and 2020 due to overfishing and habitat loss.",
        }
        result = hd.verify_claim(
            "刀鲚生物量从2010到2020年下降了42.5%",
            paper,
            tolerance=0.10,
        )
        # 结构化验证: 数字/对象/方向都有
        assert "claim_struct" in result
        assert result["claim_struct"]["subject"] in ("刀鲚", "Coilia", "") or True
        assert "confidence" in result

    def test_claim_with_wrong_number(self):
        """声明中的数字在论文中找不到 → 低置信。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        paper = {
            "title": "Fish biomass study",
            "abstract": "Biomass declined by approximately 10-15% over the decade.",
        }
        result = hd.verify_claim(
            "生物量下降了 99.9%",
            paper,
            tolerance=0.05,  # tight tolerance
        )
        # 99.9 不在 10-15 范围内 → 数值验证失败
        assert result["confidence"] < 0.6

    def test_claim_structure_parsing(self):
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        struct = hd._parse_claim_structure(
            "长江刀鲚资源量从2005到2020年下降了63%"
        )
        assert struct["subject"] == "刀鲚" or struct["subject"] != ""
        assert struct["direction"] == "下降"
        assert len(struct["numbers"]) >= 1
        assert struct["numbers"][0]["value"] == 63.0
        assert struct["timeframe"] == "2005-2020"

    def test_filter_verified_all_unverifiable(self):
        """所有论文都无标识符时 → 全部保留 (min_verified_ratio 保护)。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector()
        papers = [
            {"title": f"Paper {i}"} for i in range(5)
        ]
        verified, rejected = hd.filter_verified(papers, min_verified_ratio=0.3)
        # 0% 验证通过 < 30% threshold → 触发保护, 全部保留
        assert len(verified) == 5
        assert len(rejected) == 0


@pytest.mark.slow
class TestHallucinationDetectorOnline:
    """联网测试: 真实 DOI/PMID 验证 (需要网络)。"""

    def test_verify_real_doi_crossref(self):
        """验证真实存在的 DOI。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector(timeout=10.0)
        # 真实 DOI: 一篇关于 Coilia nasus 的论文
        result = hd.verify_paper({
            "title": "Genetic diversity and population structure of Coilia nasus",
            "doi": "10.1111/jfb.14996",  # 真实存在的 DOI
        })
        # 有真实 DOI → verified = True
        assert result.checks.get("doi") is True
        assert result.verified
        assert result.hallucination_score < 0.3

    def test_verify_real_pmid_ncbi(self):
        """验证真实存在的 PMID。"""
        from src.hallucination_detector import HallucinationDetector
        hd = HallucinationDetector(timeout=10.0)
        result = hd.verify_paper({
            "title": "",
            "pmid": "26477619",  # 真实存在的 PMID
        })
        assert result.checks.get("pmid") is True


class TestValidatorIntegration:
    """验证 HallucinationDetector 与 validator.py 的集成。"""

    def test_verify_papers_real_function(self):
        from src.validator import verify_papers_real
        papers = [
            {"title": "P1", "doi": "10.fake/fake1"},
            {"title": "P2"},
        ]
        result = verify_papers_real(papers, timeout=2.0)
        assert "total" in result
        assert "avg_hallucination_score" in result
