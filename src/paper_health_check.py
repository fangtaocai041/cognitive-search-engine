"""
Paper Health Check — Detects expired/stale papers in knowledge bases.

Implements the "Panta Rhei → knowledge is provisional → papers have expiration"
philosophy as executable code.  Runs periodic checks on knowledge base files
and flags papers that need review.

Usage:
    from src.paper_health_check import PaperHealthCheck

    checker = PaperHealthCheck("D:\\Reasonix\\porpoise-agent\\data\\knowledge_base")
    report = checker.check_all()
    # report.expired: papers past their expiration_date
    # report.stale: papers with no expiration_date (needs annotation)
    # report.healthy: recently verified papers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


# ═══════════════════════════════════════════════════════════════
# Default expiration rules
# ═══════════════════════════════════════════════════════════════

DEFAULT_MAX_AGE_DAYS = 365 * 2  # 2 years — general research papers
REVIEW_MAX_AGE_DAYS = 365 * 3   # 3 years — review papers age slower
METHODS_MAX_AGE_DAYS = 365 * 5  # 5 years — methods papers age slowest
FAST_MOVING_TOPICS = ["genomics", "genome", "CRISPR", "AI", "machine learning",
                       "deep learning", "transcriptomics", "single-cell"]
FAST_MOVING_MAX_AGE = 180       # 6 months for fast-moving fields


@dataclass
class PaperHealthRecord:
    """Health status of a single paper."""
    doi: str = ""
    title: str = ""
    year: Optional[int] = None
    expiration_date: Optional[str] = None
    last_verified: Optional[str] = None
    days_until_expiry: Optional[int] = None
    days_overdue: Optional[int] = None
    status: str = "unknown"  # "healthy" | "expiring_soon" | "expired" | "stale" | "no_expiry"
    needs_review: bool = False
    reason: str = ""


@dataclass
class PaperHealthReport:
    """Aggregate health report for a knowledge base."""
    total_papers: int = 0
    healthy: int = 0
    expiring_soon: int = 0       # within 90 days
    expired: int = 0              # past expiration_date
    stale: int = 0                # no expiration_date set
    no_expiry: int = 0            # no expiration_date field at all
    papers: list[PaperHealthRecord] = field(default_factory=list)
    summary: str = ""


class PaperHealthCheck:
    """Checks knowledge base papers for expiration and staleness."""

    def __init__(self, kb_path: str, max_age_days: int = DEFAULT_MAX_AGE_DAYS):
        self.kb_path = Path(kb_path)
        self.max_age_days = max_age_days
        self.now = datetime.now()

    def check_all(self) -> PaperHealthReport:
        """Scan all markdown files in the knowledge base and check paper health."""
        report = PaperHealthReport()

        if not self.kb_path.exists():
            report.summary = f"Knowledge base path not found: {self.kb_path}"
            return report

        md_files = list(self.kb_path.rglob("*.md"))
        for md_file in md_files:
            records = self._scan_file(md_file)
            report.papers.extend(records)

        report.total_papers = len(report.papers)
        for p in report.papers:
            if p.status == "healthy":
                report.healthy += 1
            elif p.status == "expiring_soon":
                report.expiring_soon += 1
            elif p.status == "expired":
                report.expired += 1
            elif p.status == "no_expiry":
                report.no_expiry += 1
            else:
                report.stale += 1

        report.summary = (
            f"{report.total_papers} papers: {report.healthy} healthy, "
            f"{report.expiring_soon} expiring soon, {report.expired} expired, "
            f"{report.stale} stale, {report.no_expiry} without expiration date"
        )
        return report

    def _scan_file(self, filepath: Path) -> list[PaperHealthRecord]:
        """Extract paper health records from a markdown file.

        Looks for YAML frontmatter or inline paper metadata with:
          - expiration_date: ISO date
          - last_verified: ISO date
          - doi: paper DOI
          - year: publication year
          - title: paper title
        """
        records = []
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return records

        # Try YAML frontmatter first
        if content.startswith("---") and yaml:
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if isinstance(frontmatter, dict):
                        record = self._record_from_dict(frontmatter)
                        if record:
                            records.append(record)
            except Exception:
                pass

        # Also scan for inline paper references with expiration
        for line in content.split("\n"):
            record = self._parse_inline_paper(line)
            if record:
                records.append(record)

        return records

    def _record_from_dict(self, data: dict) -> Optional[PaperHealthRecord]:
        """Create a health record from a dict (YAML frontmatter or JSON)."""
        if not data.get("title") and not data.get("doi"):
            return None  # Not a paper entry

        record = PaperHealthRecord(
            doi=data.get("doi", ""),
            title=data.get("title", ""),
            year=data.get("year"),
            expiration_date=data.get("expiration_date"),
            last_verified=data.get("last_verified"),
        )

        self._evaluate_health(record)
        return record

    def _parse_inline_paper(self, line: str) -> Optional[PaperHealthRecord]:
        """Parse inline paper references like:
        - `expiration_date: 2026-12-31 | doi: 10.xxx/yyy | title: Foo`
        """
        if "expiration_date:" not in line:
            return None
        # Simple key-value extraction
        data = {}
        for part in line.split("|"):
            part = part.strip().lstrip("-").strip()
            if ":" in part:
                key, _, val = part.partition(":")
                data[key.strip()] = val.strip()
        if not data:
            return None
        return self._record_from_dict(data)

    def _evaluate_health(self, record: PaperHealthRecord):
        """Determine paper health status based on expiration and age.

        Sets record.status and record.needs_review.
        """
        # Determine max age based on topic
        max_age = self._topic_max_age(record.title)

        if record.expiration_date:
            try:
                exp_date = datetime.fromisoformat(record.expiration_date)
                days_remaining = (exp_date - self.now).days
                record.days_until_expiry = days_remaining

                if days_remaining < 0:
                    record.status = "expired"
                    record.days_overdue = -days_remaining
                    record.needs_review = True
                    record.reason = f"Expired {record.days_overdue} days ago"
                elif days_remaining <= 90:
                    record.status = "expiring_soon"
                    record.needs_review = True
                    record.reason = f"Expires in {days_remaining} days"
                else:
                    record.status = "healthy"
            except (ValueError, TypeError):
                record.status = "stale"
                record.needs_review = True
                record.reason = "Invalid expiration_date format"
        elif record.last_verified:
            try:
                last = datetime.fromisoformat(record.last_verified)
                days_since = (self.now - last).days
                if days_since > max_age:
                    record.status = "expired"
                    record.days_overdue = days_since - max_age
                    record.needs_review = True
                    record.reason = f"Last verified {days_since} days ago (max {max_age})"
                elif days_since > max_age * 0.75:
                    record.status = "expiring_soon"
                    record.needs_review = True
                    record.reason = f"Last verified {days_since} days ago"
                else:
                    record.status = "healthy"
            except (ValueError, TypeError):
                record.status = "stale"
                record.needs_review = True
                record.reason = "Invalid last_verified format"
        elif record.year:
            # No expiration_date, estimate from publication year
            paper_age = self.now.year - record.year
            if paper_age > max_age / 365:
                record.status = "stale"
                record.needs_review = True
                record.reason = f"Published {record.year} ({paper_age} years ago) — no expiration_date set"
            else:
                record.status = "no_expiry"
                record.needs_review = False
        else:
            record.status = "no_expiry"
            record.needs_review = True
            record.reason = "No expiration_date, last_verified, or year — cannot determine health"

    def _topic_max_age(self, title: str) -> int:
        """Determine max age based on research topic."""
        title_lower = (title or "").lower()
        for fast_topic in FAST_MOVING_TOPICS:
            if fast_topic.lower() in title_lower:
                return FAST_MOVING_MAX_AGE
        if any(kw in title_lower for kw in ["review", "综述", "survey", "overview"]):
            return REVIEW_MAX_AGE_DAYS
        if any(kw in title_lower for kw in ["method", "protocol", "pipeline", "方法"]):
            return METHODS_MAX_AGE_DAYS
        return self.max_age_days


# ═══════════════════════════════════════════════════════════════
# Convenience
# ═══════════════════════════════════════════════════════════════

def check_kb_health(kb_path: str) -> dict:
    """One-liner: check knowledge base health, return summary dict."""
    checker = PaperHealthCheck(kb_path)
    report = checker.check_all()
    return {
        "total": report.total_papers,
        "healthy": report.healthy,
        "expiring_soon": report.expiring_soon,
        "expired": report.expired,
        "stale": report.stale,
        "no_expiry": report.no_expiry,
        "needs_review": [p.title[:80] for p in report.papers if p.needs_review],
        "summary": report.summary,
    }
