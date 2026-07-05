"""PerceptionBridge — 硅基生命感知物理世界的触角 (Tendrils).

Self-contained perception bridge using public APIs (PubMed E-utilities, GBIF).
No coordinator dependency. All tendrils work standalone.

Tendrils:
  🌍  Research Pulse  — 最新论文 (PubMed E-utilities)
  🧬  Species Pulse   — 物种信息 (GBIF API)
  📡  Aquatic Pulse   — 水域生态 (PubMed ecological keywords)

Usage:
    from cognitive_search_engine.src.perception_bridge import PerceptionBridge
    bridge = PerceptionBridge()
    report = bridge.scan_all()
    pulse = bridge.species_pulse("Coilia nasus")
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_USER_AGENT = "ReasonixPerceptionBridge/2.0 (fangtaocai041@gmail.com)"
_TIMEOUT = 10


@dataclass
class TendrilReading:
    tendril: str
    timestamp: float
    species: str = ""
    source: str = ""
    summary: str = ""
    signals: list = field(default_factory=list)
    alert_level: str = "info"
    confidence: float = 0.5


@dataclass
class PerceptionReport:
    timestamp: float = field(default_factory=time.time)
    tendrils: Dict[str, TendrilReading] = field(default_factory=dict)
    alerts: list = field(default_factory=list)


class PerceptionBridge:
    """感知桥梁 — 自包含感知触角控制器 (零 coordinator 依赖)."""

    def __init__(self, data_dir: str = "data/perception"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._data_dir / "perception_log.jsonl"
        self._last_scan: Dict[str, float] = {}

    def scan_all(self, force: bool = False) -> PerceptionReport:
        report = PerceptionReport()
        tendrils = [
            ("research_pulse", self._scan_research_pulse),
            ("species_pulse", self._scan_species_pulse),
            ("aquatic_pulse", self._scan_aquatic_pulse),
        ]
        for name, scanner in tendrils:
            try:
                reading = scanner(force=force)
                report.tendrils[name] = reading
                if reading.alert_level in ("warning", "critical"):
                    report.alerts.append({
                        "tendril": name, "level": reading.alert_level,
                        "summary": reading.summary, "signals": reading.signals,
                    })
                self._log(reading)
            except Exception as e:
                logger.warning(f"Tendril [{name}] failed: {e}")
        self._detect_convergence(report)
        return report

    def species_pulse(self, species: str) -> TendrilReading:
        """单物种脉搏 — GBIF API 查询."""
        reading = TendrilReading(
            tendril="species_pulse", timestamp=time.time(),
            species=species, source="gbif_api",
        )
        signals = []
        try:
            url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(species)}"
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                if data.get("usageKey"):
                    signals.append(f"GBIF match: {data.get('scientificName', species)}")
                    signals.append(f"Rank: {data.get('rank', 'unknown')}")
                    signals.append(f"Kingdom: {data.get('kingdom', 'unknown')}")
                    reading.confidence = data.get("confidence", 0) / 100.0
                else:
                    signals.append(f"No GBIF match for {species}")
                    reading.confidence = 0.2
        except Exception as e:
            signals.append(f"GBIF unavailable: {e}")
            reading.confidence = 0.1

        reading.signals = signals
        reading.summary = f"{species}: {'; '.join(signals[:2])}" if signals else "No data"
        self._log(reading)
        return reading

    def get_history(self, tendril: str = "", limit: int = 20) -> List[dict]:
        records = []
        if not self._log_path.exists():
            return records
        with open(self._log_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if not tendril or rec.get("tendril") == tendril:
                        records.append(rec)
                except json.JSONDecodeError:
                    continue
        return records[-limit:]

    # ── Tendrils ──

    def _scan_research_pulse(self, force: bool = False) -> TendrilReading:
        """📡 研究脉搏 — PubMed E-utilities 最新论文."""
        reading = TendrilReading(
            tendril="research_pulse", timestamp=time.time(),
            source="pubmed_esearch",
        )
        last = self._last_scan.get("research_pulse", 0)
        if not force and time.time() - last < 3600:
            reading.summary = "Skipped (cooldown 1h)"
            return reading
        self._last_scan["research_pulse"] = time.time()

        signals = []
        queries = [
            "fish+ecology+Yangtze+River",
            "freshwater+fish+conservation+China",
        ]
        for q in queries:
            try:
                url = (
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                    f"db=pubmed&term={q}&retmax=5&retmode=json"
                    f"&mindate=2024/01/01&maxdate=2025/12/31&datetype=pdat"
                )
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode())
                    count = int(data.get("esearchresult", {}).get("count", 0))
                    idlist = data.get("esearchresult", {}).get("idlist", [])
                    signals.append(f"[PubMed] '{q}': {count} papers (2024-2025)")
                    if idlist:
                        signals.append(f"  PMIDs: {', '.join(idlist[:3])}...")
            except Exception as e:
                signals.append(f"[PubMed] '{q}': unavailable ({e})")

        reading.signals = signals
        reading.summary = f"{len(signals)} research pulse signals"
        reading.confidence = 0.7 if signals else 0.2
        return reading

    def _scan_species_pulse(self, force: bool = False) -> TendrilReading:
        """🧬 物种脉搏 — 批量 GBIF 查询关键物种."""
        reading = TendrilReading(
            tendril="species_pulse", timestamp=time.time(),
            source="gbif_batch",
        )
        key_species = [
            "Neophocaena asiaeorientalis",  # 江豚
            "Acipenser sinensis",           # 中华鲟
            "Coilia nasus",                 # 刀鲚
            "Culter alburnus",              # 翘嘴鲌
        ]
        signals = []
        for sp in key_species:
            try:
                pulse = self.species_pulse(sp)
                signals.extend(pulse.signals[:1])
            except Exception:
                continue

        reading.signals = signals[:12]
        reading.summary = f"{len(key_species)} key species checked"
        reading.confidence = 0.6
        return reading

    def _scan_aquatic_pulse(self, force: bool = False) -> TendrilReading:
        """🌊 水域脉搏 — PubMed 水生生态关键词."""
        reading = TendrilReading(
            tendril="aquatic_pulse", timestamp=time.time(),
            source="pubmed_esearch",
        )
        signals = []
        queries = [
            "Yangtze+River+hydrology+fish",
            "freshwater+biodiversity+China+threats",
        ]
        for q in queries:
            try:
                url = (
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                    f"db=pubmed&term={q}&retmax=3&retmode=json"
                )
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode())
                    count = int(data.get("esearchresult", {}).get("count", 0))
                    signals.append(f"[Aquatic] '{q}': {count} papers")
            except Exception as e:
                signals.append(f"[Aquatic] '{q}': unavailable ({e})")

        reading.signals = signals[:5]
        reading.summary = f"{len(signals)} aquatic signals" if signals else "Aquatic data unavailable"
        reading.confidence = 0.5
        return reading

    # ── Convergence detection ──

    def _detect_convergence(self, report: PerceptionReport) -> None:
        all_signals = []
        for r in report.tendrils.values():
            all_signals.extend(r.signals)
        if len(all_signals) >= 5:
            report.alerts.append({
                "type": "convergence",
                "level": "info",
                "message": f"Cross-tendril: {len(all_signals)} signals across "
                          f"{sum(1 for t in report.tendrils.values() if t.signals)} tendrils",
            })

    # ── Persistence ──

    def _log(self, reading: TendrilReading) -> None:
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "tendril": reading.tendril,
                    "timestamp": reading.timestamp,
                    "datetime": datetime.fromtimestamp(reading.timestamp).isoformat(),
                    "species": reading.species,
                    "source": reading.source,
                    "summary": reading.summary,
                    "signals": reading.signals,
                    "alert_level": reading.alert_level,
                    "confidence": reading.confidence,
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
