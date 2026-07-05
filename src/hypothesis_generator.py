"""
hypothesis_generator.py — LLM-as-Hypothesis-Generator (P0)
===========================================================
DeepSeek 增强的假说生成器。接收涌现引擎的中间结果，调用 LLM 生成
可证伪的理论假说、支持证据链、反例预测和实验设计方案。

用法:
    from hypothesis_generator import HypothesisGenerator, HypothesisResult

    gen = HypothesisGenerator()
    result = gen.generate(
        species="Coilia nasus",
        emergence_signals=engine.scan(data)["results"],
        theory_matches=tg.route("刀鲚资源下降原因"),
        knowledge_gaps=["缺乏幼鱼阶段的耳石微化学数据"],
        contradictions=["资源评估结论不一致: 论文A认为恢复中, 论文B认为持续下降"],
    )
    print(result.hypothesis)  # "刀鲚种群下降主要由入海通道阻断导致..."

架构:
    EmergenceEngine.scan() ──┐
    TheoryGraph.route() ─────┤
    InferenceEngine.infer() ─┤──→ HypothesisGenerator ──→ HypothesisResult
    (可选) 文献摘要 ─────────┘         │
                                    DeepSeek V3/R1
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field


@dataclass
class HypothesisResult:
    """结构化假说输出。"""
    species: str = ""

    # 核心假说
    hypothesis: str = ""                    # 可证伪的假说陈述
    null_hypothesis: str = ""               # 零假设 (H₀)
    mechanism: str = ""                     # 因果机制描述

    # 证据
    supporting_evidence: list[str] = field(default_factory=list)   # 支持证据链
    conflicting_evidence: list[str] = field(default_factory=list)  # 矛盾证据
    knowledge_gaps_identified: list[str] = field(default_factory=list)  # 知识空白

    # 可检验性
    testable_predictions: list[str] = field(default_factory=list)  # 可检验预测
    experiment_design: str = ""             # 实验/观测设计方案
    falsification_condition: str = ""       # 证伪条件 (什么情况下假说被推翻)

    # 元信息
    confidence: float = 0.0                 # 置信度 (0-1)
    cross_domain_connections: list[str] = field(default_factory=list)  # 跨学科关联
    suggested_next_steps: list[str] = field(default_factory=list)      # 建议下一步

    # 生成元数据
    model_used: str = ""
    generation_time_ms: int = 0
    raw_llm_response: str = ""


class HypothesisGenerator:
    """LLM 驱动的假说生成器。

    特性:
      - 接收涌现管道所有中间输出作为上下文
      - 调用 DeepSeek API 生成结构化假说
      - 无 API 时自动降级为模板生成
      - 输出包含可证伪性检查
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        disable_llm: bool = False,
    ):
        self._model = model or os.environ.get("LLM_MODEL", "deepseek-chat")
        self._disable_llm = disable_llm
        if disable_llm:
            self._api_key = None
        else:
            self._api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        self._api_base = api_base or os.environ.get("LLM_API_BASE", "https://api.deepseek.com/v1/chat/completions")
        self._temperature = temperature
        self._max_tokens = max_tokens

    # ── 公共 API ─────────────────────────────────────────

    def generate(
        self,
        species: str,
        emergence_signals: list[dict] | None = None,
        theory_matches: list[dict] | None = None,
        knowledge_gaps: list[str] | None = None,
        contradictions: list[str] | None = None,
        paper_abstracts: list[str] | None = None,
        domain_context: str = "淡水鱼类生态学",
    ) -> HypothesisResult:
        """生成理论假说。

        Args:
            species: 目标物种 (如 "Coilia nasus")
            emergence_signals: EmergenceEngine.scan() 的输出
            theory_matches: TheoryGraph.route() 的输出
            knowledge_gaps: InferenceEngine 检测到的知识空白
            contradictions: 矛盾发现
            paper_abstracts: 相关论文摘要 (可选, 最多5篇)
            domain_context: 领域上下文

        Returns:
            HypothesisResult 结构化假说
        """
        t0 = time.time()
        emergence_signals = emergence_signals or []
        theory_matches = theory_matches or []
        knowledge_gaps = knowledge_gaps or []
        contradictions = contradictions or []
        paper_abstracts = paper_abstracts or []

        # ── 构建 Prompt ──
        prompt = self._build_prompt(
            species=species,
            emergence_signals=emergence_signals,
            theory_matches=theory_matches,
            knowledge_gaps=knowledge_gaps,
            contradictions=contradictions,
            paper_abstracts=paper_abstracts,
            domain_context=domain_context,
        )

        # ── 调用 LLM ──
        raw_response = self._call_llm(prompt)

        # ── 解析响应 ──
        result = self._parse_response(raw_response, species)
        result.generation_time_ms = int((time.time() - t0) * 1000)
        result.raw_llm_response = raw_response or ""
        result.model_used = self._model

        return result

    def health(self) -> dict:
        return {
            "module": "hypothesis_generator",
            "llm_available": bool(self._api_key),
            "model": self._model,
            "api_base": self._api_base[:40] + "..." if self._api_base else "not set",
        }

    # ── 内部方法 ─────────────────────────────────────────

    def _build_prompt(
        self,
        species: str,
        emergence_signals: list[dict],
        theory_matches: list[dict],
        knowledge_gaps: list[str],
        contradictions: list[str],
        paper_abstracts: list[str],
        domain_context: str,
    ) -> str:
        """构建 LLM 提示词。"""

        parts = [
            f"你是一位{domain_context}领域的资深科学家。你的任务是基于以下研究证据，",
            f'提出一个关于物种 "{species}" 的可证伪理论假说。',
            "",
            "## 要求",
            "1. 假说必须是可以被实验或观测证伪的",
            "2. 必须包含因果机制，而不仅仅是相关性",
            "3. 必须给出零假设 H₀",
            "4. 支持证据必须引用具体的数据来源",
            "5. 必须预测在什么条件下假说会被推翻",
            "6. 输出严格 JSON 格式，不要额外文字",
            "",
        ]

        # ── 涌现信号 ──
        if emergence_signals:
            parts.append("## 数据异常信号 (EmergenceEngine 三层分析)")
            for sig in emergence_signals[:10]:
                dt = sig.get("detection_type", "unknown")
                desc = sig.get("description", str(sig))
                conf = sig.get("confidence", 0)
                theory = sig.get("suggested_theory", "")
                parts.append(f"- [{dt}] {desc}")
                if theory:
                    parts.append(f"  理论匹配: {theory} (置信度: {conf:.2f})")
            parts.append("")

        # ── 理论图谱路由 ──
        if theory_matches:
            parts.append("## 理论图谱匹配 (TheoryGraph)")
            for tm in theory_matches[:5]:
                name = tm.get("theory_name", tm.get("name", str(tm)))
                score = tm.get("score", tm.get("fitness", 0))
                domain = tm.get("domain", "")
                parts.append(f"- {name} (领域: {domain}, 匹配度: {score:.2f})")
            parts.append("")

        # ── 知识空白 ──
        if knowledge_gaps:
            parts.append("## 已知知识空白 (InferenceEngine)")
            for gap in knowledge_gaps[:8]:
                parts.append(f"- {gap}")
            parts.append("")

        # ── 矛盾发现 ──
        if contradictions:
            parts.append("## 矛盾与不一致发现")
            for c in contradictions[:5]:
                parts.append(f"- {c}")
            parts.append("")

        # ── 相关文献 ──
        if paper_abstracts:
            parts.append("## 相关文献摘要")
            for i, abstract in enumerate(paper_abstracts[:5], 1):
                parts.append(f"论文{i}: {abstract[:300]}")
            parts.append("")

        # ── 输出格式 ──
        parts.append("## 输出 JSON 格式")
        parts.append(json.dumps({
            "hypothesis": "可证伪的假说陈述 (一句话)",
            "null_hypothesis": "零假设 H₀",
            "mechanism": "因果机制 (2-3句)",
            "supporting_evidence": ["证据1", "证据2", "证据3"],
            "conflicting_evidence": ["矛盾证据或不足"],
            "knowledge_gaps_identified": ["识别到的知识空白"],
            "testable_predictions": ["预测1: 如果假说成立，我们应该观察到...", "预测2"],
            "experiment_design": "验证假说的实验/观测方案 (3-5句)",
            "falsification_condition": "在什么条件下假说被推翻",
            "confidence": 0.7,
            "cross_domain_connections": ["跨学科关联1"],
            "suggested_next_steps": ["建议下一步1", "建议下一步2"],
        }, ensure_ascii=False, indent=2))

        return "\n".join(parts)

    def _call_llm(self, prompt: str) -> str | None:
        """调用 DeepSeek API。"""
        if not self._api_key:
            return None

        try:
            import urllib.request
            payload = json.dumps({
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "You are a research scientist. Respond with valid JSON only, no markdown fences."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
            }).encode()

            req = urllib.request.Request(self._api_base, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            # 静默失败 — 调用方会使用降级逻辑
            return None

    def _parse_response(self, raw: str | None, species: str) -> HypothesisResult:
        """解析 LLM 响应或生成降级结果。"""
        if raw:
            try:
                # 尝试去 Markdown 代码块包装
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                parsed = json.loads(cleaned)
                return HypothesisResult(
                    species=species,
                    hypothesis=parsed.get("hypothesis", ""),
                    null_hypothesis=parsed.get("null_hypothesis", ""),
                    mechanism=parsed.get("mechanism", ""),
                    supporting_evidence=parsed.get("supporting_evidence", []),
                    conflicting_evidence=parsed.get("conflicting_evidence", []),
                    knowledge_gaps_identified=parsed.get("knowledge_gaps_identified", []),
                    testable_predictions=parsed.get("testable_predictions", []),
                    experiment_design=parsed.get("experiment_design", ""),
                    falsification_condition=parsed.get("falsification_condition", ""),
                    confidence=float(parsed.get("confidence", 0.0)),
                    cross_domain_connections=parsed.get("cross_domain_connections", []),
                    suggested_next_steps=parsed.get("suggested_next_steps", []),
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # 解析失败 → 降级

        # ── 降级: 模板生成 ──
        return self._fallback_generate(species)

    def _fallback_generate(self, species: str) -> HypothesisResult:
        """无 LLM 时的模板降级。"""
        return HypothesisResult(
            species=species,
            hypothesis=f"{species} 的种群动态受多尺度环境因子 (水文+营养+捕捞) 的交互作用主导",
            null_hypothesis=f"{species} 的种群变化与所测环境因子无显著因果关系",
            mechanism="多因子交互通过改变栖息地适宜度和食物网结构间接影响种群增长率和空间分布",
            supporting_evidence=["需连接 LLM (DeepSeek) 以获取具体证据链"],
            conflicting_evidence=[],
            knowledge_gaps_identified=[
                "缺乏长时间序列的高分辨率环境-种群耦合数据",
                "多因子交互的效应量未量化",
            ],
            testable_predictions=[
                "如假说成立，水文变异度应能解释 >40% 的种群波动方差",
                "移除捕捞压力后，种群应在 2-3 代内恢复到环境承载力上限的 70%",
            ],
            experiment_design="建议采用结构方程模型 (SEM) 分解各因子贡献，结合时间序列交叉验证",
            falsification_condition="如关键环境因子与种群动态的交叉相关不显著 (p > 0.05)，假说被推翻",
            confidence=0.3,
            cross_domain_connections=["可类比草地生态系统的放牧-降水交互模型"],
            suggested_next_steps=["收集 10 年以上逐月环境+种群数据", "建立 SEM 模型检验因果路径"],
            model_used="fallback (no LLM)",
        )
