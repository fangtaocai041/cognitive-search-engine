"""
memory_system — 短时/长时记忆系统 (MemorySystem v1.0)

提供搜索 Agent 的两层记忆管理：
  - 短时记忆 (Session): 当前搜索会话的临时缓存，按 species_id 索引
  - 长时记忆 (Persistent): 跨会话持久化的知识图谱状态

Usage:
    from src.memory_system import MemorySystem

    mem = MemorySystem()
    mem.store("Coilia_nasus", {"papers": [...], "timestamp": ...})
    data = mem.recall("Coilia_nasus")
    mem.forget("Coilia_nasus")
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ── 数据类 ──────────────────────────────────────────


@dataclass
class MemoryEntry:
    """单条记忆条目。"""
    species_id: str
    data: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
    access_count: int = 0

    @property
    def age_hours(self) -> float:
        """记忆存活时间（小时）。"""
        return (time.time() - self.created_at) / 3600

    @property
    def is_stale(self, max_hours: float = 24) -> bool:
        """是否过期。"""
        return self.age_hours > max_hours


# ── MemorySystem ────────────────────────────────────


class MemorySystem:
    """两层记忆系统：Session (内存) + Persistent (JSON 文件)。"""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        self._session: dict[str, MemoryEntry] = {}
        self._persist_dir: Path = (
            Path(persist_dir) if persist_dir
            else Path(__file__).resolve().parent.parent / "data" / "memory"
        )
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._loaded: set[str] = set()

    # ── Session 层 ──────────────────────────────────

    def store(self, species_id: str, data: dict[str, Any]) -> None:
        """写入短时记忆。"""
        now = time.time()
        if species_id in self._session:
            entry = self._session[species_id]
            entry.data.update(data)
            entry.updated_at = now
        else:
            self._session[species_id] = MemoryEntry(
                species_id=species_id,
                data=data,
                created_at=now,
                updated_at=now,
            )

    def recall(self, species_id: str) -> Optional[dict[str, Any]]:
        """读取短时记忆。"""
        entry = self._session.get(species_id)
        if entry is None:
            return None
        entry.access_count += 1
        return dict(entry.data)

    def forget(self, species_id: str) -> bool:
        """删除短时记忆。"""
        return self._session.pop(species_id, None) is not None

    def clear_session(self) -> None:
        """清空短时记忆（不影响持久层）。"""
        self._session.clear()

    def list_species(self) -> list[str]:
        """列出所有有缓存物种。"""
        return list(self._session.keys())

    # ── 持久层 (JSON) ───────────────────────────────

    def _species_path(self, species_id: str) -> Path:
        return self._persist_dir / f"{species_id}.json"

    def persist(self, species_id: str) -> None:
        """将短时记忆写入持久文件。"""
        entry = self._session.get(species_id)
        if entry is None:
            return
        path = self._species_path(species_id)
        payload = {
            "species_id": species_id,
            "data": entry.data,
            "created_at": entry.created_at,
            "updated_at": time.time(),
            "access_count": entry.access_count,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, species_id: str) -> Optional[dict[str, Any]]:
        """从持久层加载到短时记忆。"""
        path = self._species_path(species_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entry = MemoryEntry(
                species_id=payload["species_id"],
                data=payload.get("data", {}),
                created_at=payload.get("created_at", 0.0),
                updated_at=payload.get("updated_at", 0.0),
                access_count=payload.get("access_count", 0),
            )
            self._session[species_id] = entry
            self._loaded.add(species_id)
            return dict(entry.data)
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def persist_all(self) -> int:
        """持久化所有短时记忆。返回写入数。"""
        count = 0
        for species_id in list(self._session.keys()):
            self.persist(species_id)
            count += 1
        return count

    def load_all(self) -> int:
        """加载所有已有持久化文件。返回加载数。"""
        count = 0
        for path in self._persist_dir.glob("*.json"):
            species_id = path.stem
            if species_id not in self._session:
                if self.load(species_id):
                    count += 1
        return count

    # ── 统计 ────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """返回记忆系统统计。"""
        return {
            "session_species": len(self._session),
            "persisted_files": len(list(self._persist_dir.glob("*.json"))),
            "loaded_from_disk": len(self._loaded),
            "persist_dir": str(self._persist_dir),
        }

    def evict_stale(self, max_hours: float = 24) -> int:
        """清除过期短时记忆。返回清除数。"""
        stale = [sid for sid, entry in self._session.items() if entry.is_stale(max_hours)]
        for sid in stale:
            self.forget(sid)
        return len(stale)
