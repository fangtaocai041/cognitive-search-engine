"""SanShengWanWu Ecosystem — Canonical Shared Types.

Cross-project type system for the entire 三生万物 ecosystem.
Single source of truth for all 7 projects (Triangle Core + Derived).

Sources merged:
  - fish-ecology-assistant/src/types.py      (V0: PipelinePhase, ConfidenceLevel, ...)
  - eon-core/scripts/shared_types.py         (Coord: VerificationStatus, ContradictionType)
  - porpoise-agent/src/cognitive/bdi.py      (P1: BDI states)
  - cognitive-search-engine/src/validator.py (V1: Paper, ValidationResult)

Usage from any project:
    import sys
    sys.path.insert(0, 'D:/Reasonix/eon-core')
    from scripts.shared_types import PipelinePhase, ConfidenceLevel, IProjectAdapter

v8.0 — canonical unified types for ecosystem cross-pollination.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# Pipeline & Research Enums (from fish-ecology-assistant V0)
# ═══════════════════════════════════════════════════════════════

class PipelinePhase(str, Enum):
    """Five-stage research pipeline (V0 canonical)."""
    PLANNING = "planning"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    WRITING = "writing"
    REVIEWING = "reviewing"


class ConfidenceLevel(str, Enum):
    """Calibrated confidence levels (V0 canonical)."""
    VERIFIED = "verified"       # Multi-source consistent, data publicly available
    INFERRED = "inferred"       # Logically extended from verified data
    UNCERTAIN = "uncertain"     # Single source, not reproduced
    NO_SOURCE = "no_source"     # Untraceable — forbidden from storage


class EvidenceQuality(str, Enum):
    """Evidence quality weighting (V0 canonical)."""
    HIGH = "high"       # Data + code public + reproducible
    MEDIUM = "medium"   # Credible but not reproducible
    LOW = "low"         # Insufficient information
    GREY = "grey"       # Grey literature


class ReviewResult(str, Enum):
    """Review outcome (V0 canonical)."""
    PASS = "pass"
    NEEDS_REVISION = "needs_revision"
    FAIL = "fail"


# ═══════════════════════════════════════════════════════════════
# Verification & Contradiction Enums (from eon-core Coord)
# ═══════════════════════════════════════════════════════════════

class VerificationStatus(str, Enum):
    """Verification outcome for a pipeline phase result (Coord canonical)."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    NEEDS_REVIEW = "needs_review"
    STALE = "stale"


class ContradictionType(str, Enum):
    """Type of contradiction detected between sources (Coord canonical)."""
    FACTUAL = "factual"
    METHODOLOGICAL = "methodological"
    TEMPORAL = "temporal"
    SOURCE_QUALITY = "source_quality"
    INTERPRETIVE = "interpretive"
    NON_ANTAGONISTIC = "non_antagonistic"
    ANTAGONISTIC = "antagonistic"
    STRUCTURAL = "structural"
    PHASIC = "phasic"


# ═══════════════════════════════════════════════════════════════
# BDI Cognitive States (from porpoise-agent P1)
# ═══════════════════════════════════════════════════════════════

class CognitiveState(str, Enum):
    """BDI cognitive states (P1 canonical, used by P2/P3)."""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    DELIBERATING = "deliberating"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    DONE = "done"


# ═══════════════════════════════════════════════════════════════
# Core Dataclasses (from fish-ecology-assistant V0)
# ═══════════════════════════════════════════════════════════════

@dataclass
class ResearchContext:
    """Research context — carried through entire pipeline."""
    research_question: str
    phase: PipelinePhase = PipelinePhase.PLANNING
    target_species: str = ""
    study_area: str = ""
    time_range: tuple[str, str] = ("", "")
    keywords_en: List[str] = field(default_factory=list)
    keywords_cn: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceEntry:
    """Literature source entry."""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    url: str = ""
    relevance: str = "medium"
    quality: EvidenceQuality = EvidenceQuality.MEDIUM
    key_findings: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


@dataclass
class AnalysisFinding:
    """Analysis finding with confidence label."""
    statement: str
    confidence: ConfidenceLevel = ConfidenceLevel.UNCERTAIN
    supporting_sources: List[str] = field(default_factory=list)
    contradicting_sources: List[str] = field(default_factory=list)
    quality_score: int = 0


@dataclass
class EmergenceSignal:
    """Emergence signal — >=3 independent sources pointing to unexpected pattern."""
    pattern: str
    sources: List[str] = field(default_factory=list)
    source_count: int = 0
    potential_explanation: str = ""
    confidence: str = "medium"
    timestamp: str = ""

    def __post_init__(self):
        self.source_count = len(self.sources)


@dataclass
class ReviewReport:
    """Review report with retry logic."""
    result: ReviewResult = ReviewResult.PASS
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    revision_notes: List[str] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 3

    @property
    def passed(self) -> bool:
        return self.result == ReviewResult.PASS

    @property
    def can_retry(self) -> bool:
        return self.iteration < self.max_iterations


@dataclass
class PipelineStats:
    """Pipeline statistics."""
    stage: PipelinePhase
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    search_query_count: int = 0
    source_count: int = 0
    finding_count: int = 0
    emergence_signal_count: int = 0

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class SessionResult:
    """Session result — complete pipeline output."""
    research_question: str
    phases_completed: List[PipelinePhase] = field(default_factory=list)
    findings: List[AnalysisFinding] = field(default_factory=list)
    emergence_signals: List[EmergenceSignal] = field(default_factory=list)
    sources: List[SourceEntry] = field(default_factory=list)
    pipeline_stats: Dict[str, PipelineStats] = field(default_factory=dict)
    final_report: str = ""
    review_result: Optional[ReviewReport] = None
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PhaseResult:
    """Cross-project phase result (Coord canonical)."""
    phase: str = ""
    status: str = "ok"
    papers_found: int = 0
    data_points: int = 0
    tokens_used: int = 0
    findings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    contradictions: List[ContradictionType] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Cross-project pipeline result (Coord canonical)."""
    question: str = ""
    phases_executed: List[str] = field(default_factory=list)
    phase_results: Dict[str, PhaseResult] = field(default_factory=dict)
    total_papers: int = 0
    total_tokens: int = 0
    synthesis: str = ""
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# IProjectAdapter Protocol (ecosystem standard interface)
# ═══════════════════════════════════════════════════════════════

class IProjectAdapter(ABC):
    """Standard interface every project adapter must implement.

    Implemented by:
      V0: FishEcologyAdapter     (fish-ecology-assistant)
      V1: CognitiveSearchAdapter (cognitive-search-engine)
      Coord: EonCoreAdapter      (eon-core)
      P1: PorpoiseAdapter        (porpoise-agent)
      P2: CoiliaAdapter          (coilia-agent)
      P3: CulterAdapter          (culter-agent)
      C:  ConflictArbiterAdapter (conflict-arbiter)
    """

    @abstractmethod
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute a search/analysis request."""
        ...

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return health status."""
        ...

    @abstractmethod
    def info(self) -> Dict[str, Any]:
        """Return project metadata and capabilities."""
        ...


# ═══════════════════════════════════════════════════════════════
# Ecosystem Architecture Constants
# ═══════════════════════════════════════════════════════════════

TRIANGLE_CORE: Dict[str, Dict[str, str]] = {
    "V0": {
        "project": "fish-ecology-assistant",
        "role": "Knowledge Supply Core",
        "symbol": "S/V0",
        "wuxing": "土 (EARTH)",
        "adapter": "FishEcologyAdapter",
    },
    "V1": {
        "project": "cognitive-search-engine",
        "role": "Search Verification Core",
        "symbol": "V/V1",
        "wuxing": "金 (METAL)",
        "adapter": "CognitiveSearchAdapter",
    },
    "Coord": {
        "project": "eon-core",
        "role": "Coordination Hub",
        "symbol": "Coordinator",
        "wuxing": "水 (WATER)",
        "adapter": "EonCoreAdapter",
    },
}

DERIVED_PROJECTS: Dict[str, Dict[str, str]] = {
    "P1": {
        "project": "porpoise-agent",
        "role": "Porpoise Domain Expert Engine",
        "species": "Neophocaena asiaeorientalis",
        "wuxing": "木 (WOOD)",
        "adapter": "PorpoiseAdapter",
    },
    "P2": {
        "project": "coilia-agent",
        "role": "Coilia Domain Expert Engine",
        "species": "Coilia nasus",
        "wuxing": "木 (WOOD)",
        "adapter": "CoiliaAdapter",
    },
    "P3": {
        "project": "culter-agent",
        "role": "Culter Domain Expert Engine",
        "species": "Culter alburnus",
        "wuxing": "木 (WOOD)",
        "adapter": "CulterAdapter",
    },
    "C": {
        "project": "conflict-arbiter",
        "role": "Conflict Arbitration Expert Engine",
        "species": "all",
        "wuxing": "火 (FIRE)",
        "adapter": "ConflictArbiterAdapter",
    },
}

ECOSYSTEM_TAGLINE_CN = "和则无穷力量，分则顶尖专家引擎。"
ECOSYSTEM_TAGLINE_EN = "Together infinite power, apart top expert engines."
ECOSYSTEM_NAME = "三生万物 (SanShengWanWu)"
ECOSYSTEM_VERSION = "v8.0"
