from __future__ import annotations

import json
import logging
import random as _random_mod
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ─── User-Agent ──────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": "ReasonixCognitiveSearch/5.8 (fangtaocai041@gmail.com)",
    "Accept": "application/json",
}

_TIMEOUT_S = 45  # per-provider timeout (tuned for DeepSeek API + patience)

# ═══════════════════════════════════════════════════════════════
# Error Classification (4-tier, inspired by SearXNG)
# ═══════════════════════════════════════════════════════════════

class ErrorTier(Enum):
    """4 层错误分类 — 决定重试/熔断/跳过策略。"""
    RETRY = "retry"               # 瞬时故障 → 可重试 (timeout, 5xx, connection)
    RATE_LIMIT = "rate_limit"     # 被限流 → 等更久再重试 (429, 503)
    SUSPEND = "suspend"           # 需要熔断 → 暂停该引擎 (连续失败)
    FATAL = "fatal"               # 不可恢复 → 跳过不重试 (403, 404, auth)


def classify_error(exc: Exception) -> ErrorTier:
    """根据异常类型和内容分到 4 层。"""
    msg = str(exc).lower()
    exc_type = type(exc).__name__

    # FATAL: 认证/权限/不存在
    if any(k in msg for k in ("403", "401", "forbidden", "unauthorized", "not found", "404")):
        return ErrorTier.FATAL

    # RATE_LIMIT: 被限流
    if any(k in msg for k in ("429", "rate limit", "too many", "503")):
        return ErrorTier.RATE_LIMIT

    # RETRY: 瞬时网络/超时
    if any(k in msg for k in ("timeout", "timed out", "connection", "reset", "eof", "broken pipe",
                               "temporary failure", "name resolution")):
        return ErrorTier.RETRY
    if exc_type in ("TimeoutError", "ConnectionError", "ConnectionResetError",
                     "BrokenPipeError", "URLError", "RemoteDisconnected"):
        return ErrorTier.RETRY

    # SUSPEND: 其他一切
    return ErrorTier.SUSPEND


# ═══════════════════════════════════════════════════════════════
# Retry with Exponential Backoff + Jitter
# ═══════════════════════════════════════════════════════════════

def retry_call(
    fn: Callable,
    *args,
    max_retries: int = 2,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    backoff: float = 2.0,
    jitter: bool = True,
    **kwargs,
) -> Any:
    """带指数退避 + 抖动的重试调用。

    参考: tenacity + AWS SDK retry strategy
    - 瞬时故障 (RETRY): 退避重试
    - 限流 (RATE_LIMIT): 退避×2 重试
    - 熔断/致命: 不重试, 直接抛

    Args:
        fn: 要调用的函数
        max_retries: 最多重试次数
        base_delay: 基础延迟秒数
        max_delay: 最大延迟秒数
        backoff: 退避倍数
        jitter: 是否加随机抖动 (避免惊群)
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            tier = classify_error(e)

            if tier == ErrorTier.FATAL:
                raise  # 不重试致命错误

            if tier == ErrorTier.SUSPEND and attempt >= 1:
                raise  # 熔断类只重试 1 次

            if attempt == max_retries:
                raise  # 重试耗尽

            # 计算延迟
            delay = min(base_delay * (backoff ** attempt), max_delay)
            if tier == ErrorTier.RATE_LIMIT:
                delay *= 2  # 限流等更久

            if jitter:
                delay *= 0.5 + _random_mod.random()  # ±50% 抖动

            logger.debug(
                "[retry %d/%d] %s | %s | waiting %.1fs",
                attempt + 1, max_retries,
                fn.__name__ if hasattr(fn, "__name__") else str(fn),
                tier.value, delay,
            )
            time.sleep(delay)

    raise last_exc  # unreachable but safe


# ═══════════════════════════════════════════════════════════════
# Reciprocal Rank Fusion (RRF) — 学术金标准结果融合
# ═══════════════════════════════════════════════════════════════
# Reference: Cormack, Clarke, Buettcher (SIGIR 2009)
#   "Reciprocal Rank Fusion outperforms Condorcet and individual
#    rank learning methods" — scores = Σ 1/(k + rank)
# k=60 is the canonical value from the paper.

def rrf_fuse(
    ranked_lists: List[List[Dict]],
    k: int = 60,
    id_key: str = "doi",
    title_key: str = "title",
) -> List[Dict]:
    """Reciprocal Rank Fusion: 将多个排序列表融合为一个。

    原理: 论文在越多的搜索引擎中排位越靠前 → 最终得分越高。
    自动处理 DOI 缺失降级到标题匹配。

    Args:
        ranked_lists: 各搜索引擎返回的论文列表 (每个已按相关度排序)
        k: RRF 常数 (论文推荐 k=60)
        id_key: 主去重键 (默认 doi)
        title_key: 降级去重键 (DOI 缺失时用标题)

    Returns:
        融合后的论文列表, 按 RRF 分数降序, 附带来源信息
    """
    scores: Dict[str, float] = {}
    papers: Dict[str, Dict] = {}
    sources: Dict[str, List[str]] = {}

    for src_idx, paper_list in enumerate(ranked_lists):
        for rank, paper in enumerate(paper_list, start=1):
            # 主键: DOI; 降级: 归一化标题
            pid = (paper.get(id_key) or "").strip().lower()
            if not pid:
                pid = (paper.get(title_key) or "").strip().lower()[:100]
            if not pid:
                continue

            rrf_score = 1.0 / (k + rank)
            scores[pid] = scores.get(pid, 0.0) + rrf_score
            sources.setdefault(pid, []).append(paper.get("source", f"src_{src_idx}"))

            # 保留最完整的那条记录 (优先有 DOI 的)
            if pid not in papers or (
                paper.get(id_key) and not papers[pid].get(id_key)
            ):
                papers[pid] = dict(paper)

    # 按 RRF 分数降序排列, 附加元数据
    fused = []
    for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        entry = dict(papers[pid])
        entry["_rrf_score"] = round(score, 4)
        entry["_sources"] = list(set(sources.get(pid, [])))
        entry["_source_count"] = len(entry["_sources"])
        fused.append(entry)

    return fused


def combmnz_fuse(
    ranked_lists: List[List[Dict]],
    id_key: str = "doi",
    title_key: str = "title",
) -> List[Dict]:
    """CombMNZ 融合: 论文在多个引擎出现 → 得分乘以引擎数。

    原理: "被越多搜索引擎收录的论文越可信" — 奖励跨源共识。
    与 RRF 互补: RRF 看排名, CombMNZ 看共识度。

    Reference: Fox & Shaw (1994), "Combination of Multiple Searches"
      score(d) = Σ score_i(d) × count(sources_retrieving_d)

    在没有引擎内分数的场景, 每篇论文的 score_i = 1/rank_i
    """
    scores: Dict[str, float] = {}
    papers: Dict[str, Dict] = {}
    source_counts: Dict[str, int] = {}

    for paper_list in ranked_lists:
        for rank, paper in enumerate(paper_list, start=1):
            pid = (paper.get(id_key) or "").strip().lower()
            if not pid:
                pid = (paper.get(title_key) or "").strip().lower()[:100]
            if not pid:
                continue

            # 引擎内分数: 1/rank
            engine_score = 1.0 / rank
            scores[pid] = scores.get(pid, 0.0) + engine_score
            source_counts[pid] = source_counts.get(pid, 0) + 1

            if pid not in papers or paper.get(id_key):
                papers[pid] = dict(paper)

    # CombMNZ: 总分 × 出现引擎数
    fused = []
    for pid, raw_sum in scores.items():
        mnz_score = raw_sum * source_counts[pid]
        entry = dict(papers[pid])
        entry["_mnz_score"] = round(mnz_score, 4)
        entry["_source_count"] = source_counts[pid]
        fused.append(entry)

    fused.sort(key=lambda x: x["_mnz_score"], reverse=True)
    return fused


def fuse_results(
    ranked_lists: List[List[Dict]],
    method: str = "rrf",
) -> List[Dict]:
    """统一融合入口: rrf (默认) 或 combmnz。

    Args:
        ranked_lists: 各引擎返回的排序列表
        method: "rrf" (Reciprocal Rank Fusion) | "combmnz" (共识加权)
    """
    if method == "combmnz":
        return combmnz_fuse(ranked_lists)
    return rrf_fuse(ranked_lists)


# ═══════════════════════════════════════════════════════════════
# Per-Engine Circuit Breaker (SearXNG-inspired)
# ═══════════════════════════════════════════════════════════════

@dataclass
class EngineBreaker:
    """单引擎熔断器 — 连续失败 N 次后暂停 M 秒。

    参考 SearXNG SuspendedStatus:
      - 连续失败达到阈值 → 挂起 (skip)
      - 挂起期间任何请求直接跳过
      - 挂起时间到 → 放行一个探测请求
      - 探测成功 → 恢复; 失败 → 重新挂起
    """
    name: str
    max_failures: int = 5
    suspend_seconds: float = 60.0

    _failures: int = 0
    _suspend_until: float = 0.0

    def can_pass(self) -> bool:
        """是否可以放行请求。"""
        if self._suspend_until > 0:
            if time.time() < self._suspend_until:
                return False  # 仍在挂起
            # 挂起到期 → 放行一个探测
            self._suspend_until = 0.0
        return True

    def record_success(self):
        """请求成功 → 重置失败计数。"""
        self._failures = 0
        self._suspend_until = 0.0

    def record_failure(self):
        """请求失败 → 递增, 达到阈值则挂起。"""
        self._failures += 1
        if self._failures >= self.max_failures:
            self._suspend_until = time.time() + self.suspend_seconds
            logger.warning("[breaker] %s SUSPENDED for %.0fs (%d failures)",
                           self.name, self.suspend_seconds, self._failures)


# 全局引擎熔断器字典 (懒初始化)
_ENGINE_BREAKERS: Dict[str, EngineBreaker] = {}


def get_engine_breaker(name: str) -> EngineBreaker:
    """获取或创建指定引擎的熔断器。"""
    if name not in _ENGINE_BREAKERS:
        _ENGINE_BREAKERS[name] = EngineBreaker(name=name)
    return _ENGINE_BREAKERS[name]
