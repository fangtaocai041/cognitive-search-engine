#!/usr/bin/env python3
"""
self_evolve.py — 自进化反馈 (lit-search §3.3)

实现 lit-search §3.3 自进化反馈逻辑:
  每次搜索后评估效果, 根据触发条件自动调整搜索参数。

触发条件:
  - recall_drop:       连续3次 recall < 50% → 提高 satisfice 阈值
  - efficiency_gain:   连续5次 token_efficiency 提升 → 剪枝低 IG 层
  - false_positive_spike: 连续2次 FP > 15% → 提高信任阈值

用法:
  python scripts/self_evolve.py --metrics '{"recall_vs_expected":0.45,"token_efficiency":3.2}'
  python scripts/self_evolve.py --report
  python scripts/self_evolve.py --history
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


ENGINE_ROOT = Path(__file__).resolve().parent.parent
EVOLUTION_LOG_DIR = ENGINE_ROOT / ".evolution"
EVOLUTION_LOG_PATH = EVOLUTION_LOG_DIR / "evolution-log.jsonl"
CONFIG_PATH = ENGINE_ROOT / "config" / "evolution.yaml"


# ═══════════════════════════════════════════════════════
# 进化触发条件 (与 evolution.yaml 同步)
# ═══════════════════════════════════════════════════════

TRIGGERS = {
    "recall_drop": {
        "metric": "recall_vs_expected",
        "threshold": 0.5,
        "comparator": "<",
        "consecutive": 3,
        "action": "increase satisfice_threshold by 2 AND activate more layers",
        "param": "satisfice_threshold",
        "adjust": +2,
    },
    "efficiency_gain": {
        "metric": "token_efficiency",
        "threshold": 1.2,  # 相比 baseline 提升 20%
        "comparator": ">",
        "consecutive": 5,
        "action": "prune lowest-IG layer",
        "param": "ig_prune_threshold",
        "adjust": +0.001,
    },
    "false_positive_spike": {
        "metric": "false_positive_rate",
        "threshold": 0.15,
        "comparator": ">",
        "consecutive": 2,
        "action": "increase trust_score_threshold by 10",
        "param": "trust_score_threshold",
        "adjust": +10,
    },
    "new_species_discovered": {
        "metric": "graph_node_growth_pct",
        "threshold": 20,
        "comparator": ">",
        "consecutive": 1,
        "action": "log discovery + suggest building dedicated species_graph entry",
        "param": "",
        "adjust": 0,
    },
}


# ═══════════════════════════════════════════════════════
# 进化日志管理
# ═══════════════════════════════════════════════════════

def ensure_log_dir():
    EVOLUTION_LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> List[Dict]:
    """加载进化历史."""
    ensure_log_dir()
    if not EVOLUTION_LOG_PATH.exists():
        return []
    records = []
    try:
        with open(EVOLUTION_LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception:
        pass
    return records


def append_log(entry: Dict):
    """追加进化日志条目."""
    ensure_log_dir()
    with open(EVOLUTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════
# 进化评估
# ═══════════════════════════════════════════════════════

def _load_config() -> Dict:
    """加载 evolution.yaml 配置."""
    if yaml is None:
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_config(config: Dict):
    """保存 evolution.yaml."""
    if yaml is None:
        return
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"⚠️ 保存 evolution.yaml 失败: {e}")


def evaluate(metrics: Dict[str, float]) -> List[Dict]:
    """评估指标并执行进化.

    Args:
        metrics: 搜索后的效果指标, 如:
            {"recall_vs_expected": 0.45, "token_efficiency": 3.2, ...}

    Returns:
        触发的进化动作列表
    """
    history = load_history()
    config = _load_config()
    actions: List[Dict] = []

    # 记录本次指标
    entry = {
        "timestamp": datetime.now().isoformat(),
        **metrics,
    }
    append_log(entry)
    history.append(entry)
    if len(history) > 50:
        history = history[-50:]

    # 逐项检查触发条件
    for trigger_name, trigger in TRIGGERS.items():
        metric_key = trigger["metric"]
        if metric_key not in metrics:
            continue

        threshold = trigger["threshold"]
        comparator = trigger["comparator"]
        consecutive = trigger["consecutive"]

        # 检查最近 N 次历史
        if len(history) < consecutive:
            continue

        recent = history[-consecutive:]
        values = [r.get(metric_key) for r in recent]
        if any(v is None for v in values):
            continue

        # 判定条件
        triggered = all(
            v < threshold if comparator == "<" else
            v > threshold if comparator == ">" else
            v <= threshold if comparator == "<=" else
            v >= threshold
            for v in values
        )

        if triggered:
            param = trigger["param"]
            action = {
                "trigger": trigger_name,
                "metric": metric_key,
                "values": values,
                "action": trigger["action"],
                "timestamp": datetime.now().isoformat(),
            }

            # 执行参数调整
            if param and config:
                adaptive = config.get("evolution", {}).get("adaptive_params", {})
                if param in adaptive:
                    old_val = adaptive[param].get("current", adaptive[param].get("value", 0))
                    param_range = adaptive[param].get("range", [0, 100])
                    new_val = old_val + trigger["adjust"]
                    new_val = max(param_range[0], min(param_range[1], new_val))
                    if "current" in adaptive[param]:
                        adaptive[param]["current"] = new_val
                    else:
                        adaptive[param]["value"] = new_val
                    adaptive[param]["last_adjusted"] = datetime.now().isoformat()
                    action["param"] = param
                    action["old_value"] = old_val
                    action["new_value"] = new_val
                    _save_config(config)

            actions.append(action)

    return actions


def generate_report() -> str:
    """生成进化报告."""
    history = load_history()
    if not history:
        return "📭 无进化历史"

    total = len(history)
    last = history[-1] if history else {}
    triggered = [h for h in history if "trigger" in h]

    report = [
        "🧬 自进化报告",
        "=" * 40,
        f"总搜索轮次: {total}",
        f"进化事件: {len(triggered)}",
        f"最后指标: {json.dumps(last, ensure_ascii=False)[:100]}",
        "",
    ]

    if triggered:
        recent = triggered[-5:]
        report.append("近期进化事件:")
        for t in recent:
            report.append(
                f"  [{t.get('timestamp', '?')[:16]}] "
                f"{t.get('trigger', '?')}: {t.get('action', '?')}"
            )
            if t.get("param"):
                report.append(f"    {t['param']}: {t.get('old_value')} → {t.get('new_value')}")

    return "\n".join(report)


def print_history(limit: int = 10):
    """打印历史记录."""
    history = load_history()
    if not history:
        print("📭 无进化历史")
        return
    for h in history[-limit:]:
        ts = h.get("timestamp", "?")[:19]
        trigger = h.get("trigger", "metrics")
        vals = {k: v for k, v in h.items() if k not in ("timestamp", "trigger")}
        print(f"[{ts}] {trigger}: {json.dumps(vals, ensure_ascii=False)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="自进化反馈引擎")
    parser.add_argument("--metrics", help='搜索效果指标 JSON, e.g. \'{"recall":0.45}\'')
    parser.add_argument("--report", action="store_true", help="生成进化报告")
    parser.add_argument("--history", action="store_true", help="打印进化历史")
    parser.add_argument("--limit", type=int, default=10, help="历史记录条数")
    args = parser.parse_args()

    if args.metrics:
        metrics = json.loads(args.metrics)
        actions = evaluate(metrics)
        if actions:
            print(f"⚡ 触发了 {len(actions)} 个进化事件:")
            for a in actions:
                print(f"  [{a['trigger']}] {a['action']}")
                if a.get("param"):
                    print(f"    {a['param']}: {a['old_value']} → {a['new_value']}")
        else:
            print("✅ 无触发条件满足")
        print(json.dumps(actions, ensure_ascii=False, indent=2))

    elif args.report:
        print(generate_report())

    elif args.history:
        print_history(args.limit)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
