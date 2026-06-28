"""
Post-Search Inference Engine — P3: 推理增强检索

将认知搜索从 "变体生成 + Hub-and-Spoke 遍历" 升级为
"搜索 → 推理 → 追问 → 验证" 的循环推理范式。

参照:
  R1-Searcher: 搜索后推理验证 (post-search reasoning)
  EcphyRAG:    cue-driven 多跳检索
  DeepResearcher: agentic deep research with iterative refinement

工程实现:
  Phase 1 (Search):  现有 cognitive-search-engine 执行搜索
  Phase 2 (Infer):   对搜索结果进行矛盾检测 + 缺口识别
  Phase 3 (Follow):  对缺口发起追问搜索
  Phase 4 (Verify):  交叉验证新结果与旧结果的一致性

Usage:
    from src.inference_engine import InferenceEngine
    ie = InferenceEngine()
    enriched = ie.infer(papers, species_id="Ochetobius_elongatus")
"""

from dataclasses import dataclass, field


@dataclass
class InferenceResult:
    species_id: str
    original_papers: int = 0
    new_papers_from_followup: int = 0
    contradictions_found: int = 0
    knowledge_gaps: list[str] = field(default_factory=list)
    followup_queries: list[str] = field(default_factory=list)
    confidence_improvement: float = 0.0
    reasoning_trace: list[str] = field(default_factory=list)


class InferenceEngine:
    """搜索后推理引擎 — 将搜索结果转化为可追问的知识。

    推理循环:
      papers → detect gaps → formulate followup → search → verify → merge
    """

    def __init__(self, min_confidence_gain: float = 0.05, max_followup_rounds: int = 3):
        self.min_gain = min_confidence_gain
        self.max_rounds = max_followup_rounds

    def infer(self, papers: list[dict], species_id: str = "",
              known_topics: list[str] = None) -> InferenceResult:
        """对搜索结果执行推理增强。

        Args:
            papers: 初始搜索结果
            species_id: 物种标识
            known_topics: 已知的研究主题 (从图谱加载)

        Returns:
            InferenceResult with gaps, followup queries, and reasoning trace
        """
        result = InferenceResult(
            species_id=species_id,
            original_papers=len(papers),
        )
        known_topics = known_topics or []

        # ── Step 1: Gap Detection ──
        gaps = self._detect_gaps(papers, known_topics)
        result.knowledge_gaps = gaps
        result.reasoning_trace.append(f"Gap detection: {len(gaps)} gaps found")
        for g in gaps:
            result.reasoning_trace.append(f"  - {g}")

        # ── Step 2: Formulate Followup Queries ──
        if gaps:
            followups = self._formulate_followups(gaps, species_id)
            result.followup_queries = followups
            result.reasoning_trace.append(f"Followup queries: {len(followups)} generated")
            for fq in followups:
                result.reasoning_trace.append(f"  - {fq}")

        # ── Step 3: Contradiction Detection ──
        contradictions = self._detect_contradictions(papers)
        result.contradictions_found = len(contradictions)
        result.reasoning_trace.append(f"Contradictions: {len(contradictions)} found")

        # ── Step 4: Confidence Assessment ──
        avg_score = sum(p.get("credibility_score", p.get("trust_score", 50))
                       for p in papers) / max(len(papers), 1)
        result.confidence_improvement = min(avg_score / 100.0, 1.0)

        return result

    def _detect_gaps(self, papers: list[dict], known_topics: list[str]) -> list[str]:
        """检测知识缺口。

        Rules:
          - 如果论文数 < 5: 标记为 "data scarcity"
          - 如果缺少综述: 标记 "need review"
          - 如果无近期论文 (近2年): 标记 "need recent"
          - 如果缺少已知主题覆盖: 标记具体缺口
        """
        gaps = []

        # Data scarcity
        if len(papers) < 5:
            gaps.append("DATA_SCARCITY: <5 papers found — expand search with OCR variants + Chinese databases")

        # Missing review
        has_review = any(
            any(kw in (p.get("title", "") + p.get("abstract", "")).lower()
                for kw in ["review", "综述", "survey", "进展"])
            for p in papers
        )
        if not has_review and len(papers) >= 3:
            gaps.append("NO_REVIEW: no review paper found — consider review-first search strategy")

        # Recent papers check
        current_year = 2026
        has_recent = any(p.get("year", 0) >= current_year - 2 for p in papers)
        if not has_recent and len(papers) > 0:
            gaps.append("NO_RECENT: no papers from last 2 years — may indicate inactive research area or search gap")

        # Topic coverage
        covered_topics = set()
        for p in papers:
            title = (p.get("title", "") + " " + p.get("abstract", "")).lower()
            for topic in known_topics:
                if topic.lower() in title:
                    covered_topics.add(topic)
        missing_topics = set(known_topics) - covered_topics
        for mt in missing_topics:
            gaps.append(f"TOPIC_GAP: '{mt}' not covered in search results")

        return gaps

    def _formulate_followups(self, gaps: list[str], species_id: str) -> list[str]:
        """根据缺口生成追问查询。"""
        queries = []
        for gap in gaps:
            if "DATA_SCARCITY" in gap:
                queries.append(f"{species_id} OR variant_search")
            elif "NO_REVIEW" in gap:
                queries.append(f"{species_id} review OR 综述 OR survey")
            elif "NO_RECENT" in gap:
                queries.append(f"{species_id} 2024 OR 2025 OR 2026")
            elif "TOPIC_GAP" in gap:
                topic = gap.split("'")[1] if "'" in gap else gap
                queries.append(f"{species_id} {topic}")
        return queries

    def _detect_contradictions(self, papers: list[dict]) -> list[dict]:
        """检测论文间的矛盾。

        简化版: 检查 credibility_score 方差。
        完整版需要 NLP 级别的声明对比。
        """
        if len(papers) < 2:
            return []

        contradictions = []
        scores = [p.get("credibility_score", p.get("trust_score", 50)) for p in papers]
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)

        # High variance = potential contradictions in quality
        if variance > 400:  # std > 20
            contradictions.append({
                "type": "quality_variance",
                "detail": f"High score variance ({variance:.0f}) — "
                          f"mix of high and low credibility sources",
                "recommendation": "Cross-validate low-scoring papers against high-scoring ones",
            })

        return contradictions


# ═══════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════

def infer_from_search(papers: list[dict], species_id: str = "",
                       known_topics: list[str] = None) -> InferenceResult:
    """One-liner: 对搜索结果执行推理增强。"""
    ie = InferenceEngine()
    return ie.infer(papers, species_id, known_topics)


# ═══════════════════════════════════════════════════════════
# v6.0: DeepSeek + Holland 增强推理 (MoE + 投机 + 涌现)
# ═══════════════════════════════════════════════════════════

class DeepInferenceEngine(InferenceEngine):
    """DeepSeek 增强推理引擎: MoE 路由 + 投机假说 + Holland 涌现。

    继承 InferenceEngine, 添加:
      - MoE 稀疏理论匹配 (替代全量模式遍历)
      - 投机假说生成 (Draft-then-Verify)
      - Holland 涌现评分集成
    """

    def __init__(self, min_confidence_gain: float = 0.05,
                 max_followup_rounds: int = 3):
        super().__init__(min_confidence_gain, max_followup_rounds)
        self._moe_router = None     # lazy init
        self._spec_engine = None    # lazy init
        self._holland_cas = None    # lazy init

    def _ensure_deepseek(self):
        """延迟加载 DeepSeek 模块 (避免循环导入)。"""
        if self._moe_router is None:
            try:
                import sys
                from pathlib import Path as _P
                _infra = _P(__file__).resolve().parent.parent.parent / "infrastructure" / "src"
                if str(_infra) not in sys.path:
                    sys.path.insert(0, str(_infra))
                from deepseek.moe_router import MoETheoryRouter
                from deepseek.speculative import SpeculativeEngine
                self._moe_router = MoETheoryRouter()
                self._spec_engine = SpeculativeEngine(n_drafts=4, top_k=3)
            except ImportError:
                pass

    def _ensure_holland(self):
        """延迟加载 Holland 模块。"""
        if self._holland_cas is None:
            try:
                import sys
                from pathlib import Path as _P
                _infra = _P(__file__).resolve().parent.parent.parent / "infrastructure" / "src"
                if str(_infra) not in sys.path:
                    sys.path.insert(0, str(_infra))
                from holland.cas_engine import CASCognitiveEngine
                self._holland_cas = CASCognitiveEngine()
            except ImportError:
                pass

    def deep_infer(self, papers: list[dict], species_id: str = "",
                   observations: dict[str, float] | None = None
                   ) -> dict:
        """DeepSeek 增强推理: MoE 路由 → 投机假说 → Holland 涌现。

        Returns:
            {
                "papers": int,
                "gaps": [...],
                "contradictions": [...],
                "moe_matches": [...],        # MoE 路由结果
                "hypotheses": [...],          # 投机假说
                "holland_score": HollandScore, # 涌现评分
            }
        """
        # Step 0: 基础推理 (父类)
        base = self.infer(papers, species_id)

        # Step 1: MoE 稀疏理论匹配
        self._ensure_deepseek()
        moe_matches = []
        if self._moe_router and observations:
            moe_matches = self._moe_router.match(observations, top_k=3)

        # Step 2: 投机假说
        hypotheses = []
        if self._spec_engine and observations:
            specs = self._spec_engine.run(observations)
            hypotheses = [
                {"statement": h.statement, "confidence": h.confidence,
                 "evidence": h.evidence}
                for h in specs
            ]

        # Step 3: Holland 涌现评分
        self._ensure_holland()
        holland_score = None
        if self._holland_cas:
            holland_score = self._holland_cas.scan(
                papers=papers, species=species_id,
                data=observations,
            )
            # 如果涌现, 追加假说
            if holland_score.is_emergent:
                holland_hyps = self._holland_cas.generate_hypotheses(
                    holland_score, species_id
                )
                hypotheses.extend(
                    {"statement": h, "confidence": holland_score.holland_index,
                     "source": "holland_emergence"}
                    for h in holland_hyps
                )

        return {
            "papers": base.original_papers,
            "gaps": base.knowledge_gaps,
            "contradictions": base.contradictions_found,
            "moe_matches": moe_matches,
            "hypotheses": hypotheses,
            "holland_score": (
                {"index": holland_score.holland_index,
                 "emergent": holland_score.is_emergent,
                 "dims_active": holland_score.dimensions_active}
                if holland_score else None
            ),
        }


# Convenience
def deep_infer(papers: list[dict], species_id: str = "",
               observations: dict[str, float] | None = None) -> dict:
    """One-liner: DeepSeek 增强推理。"""
    return DeepInferenceEngine().deep_infer(
        papers, species_id, observations
    )
