"""AgentJudge — LLM-based evaluation of search/agent output quality.

Uses an LLM as a judge to score and rank search results.
Evaluates: relevance, credibility, novelty, completeness.
Replaces static rule-based credibility scoring with semantic evaluation.

Usage:
    judge = AgentJudge()
    scores = judge.evaluate(query, papers)
    ranked = sorted(papers, key=lambda p: scores.get(p['doi'], 0), reverse=True)
"""

import json, logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvalDimension:
    name: str
    score: float  # 0-10
    reasoning: str = ""

@dataclass
class PaperEval:
    doi: str = ""
    total_score: float = 0.0
    dimensions: List[EvalDimension] = field(default_factory=list)
    summary: str = ""


class AgentJudge:
    """LLM-as-Judge for search result evaluation."""

    EVAL_PROMPT = """Evaluate this research paper for query relevance:

Query: {query}
Title: {title}
Journal: {journal}
Year: {year}

Score each dimension 0-10:
- Relevance: How well does this paper answer the query?
- Credibility: Journal reputation and methodology quality
- Novelty: Is this recent, cutting-edge research?
- Completeness: Does it provide comprehensive data?

Return JSON: {{"relevance": X, "credibility": X, "novelty": X, "completeness": X, "reasoning": "..."}}"""

    def __init__(self, model_func: Callable = None):
        self._model = model_func  # LLM call function

    def evaluate(self, query: str, papers: List[Dict]) -> Dict[str, PaperEval]:
        """Evaluate a list of papers and return scores."""
        results = {}
        for paper in papers:
            prompt = self.EVAL_PROMPT.format(
                query=query,
                title=paper.get('title', 'Unknown'),
                journal=paper.get('journal', 'Unknown'),
                year=paper.get('year', 'Unknown')
            )
            try:
                if self._model:
                    response = self._model(prompt)
                    scores = json.loads(response) if isinstance(response, str) else response
                else:
                    scores = self._heuristic_score(query, paper)

                eval_result = PaperEval(
                    doi=paper.get('doi', ''),
                    total_score=sum(scores.get(d, 5) for d in 
                                   ['relevance','credibility','novelty','completeness']) / 4,
                    dimensions=[
                        EvalDimension("relevance", scores.get('relevance', 5)),
                        EvalDimension("credibility", scores.get('credibility', 5)),
                        EvalDimension("novelty", scores.get('novelty', 5)),
                        EvalDimension("completeness", scores.get('completeness', 5)),
                    ],
                    summary=scores.get('reasoning', '')
                )
            except Exception:
                eval_result = PaperEval(doi=paper.get('doi', ''), total_score=5.0)

            results[paper.get('doi', paper.get('title', ''))] = eval_result

        return results

    def _heuristic_score(self, query: str, paper: Dict) -> Dict:
        """Fallback heuristic when LLM unavailable."""
        title = (paper.get('title', '') or '').lower()
        query_lower = query.lower()
        relevance = 8 if any(w in title for w in query_lower.split()) else 4
        journal = paper.get('journal', '') or ''
        credibility = 8 if any(j in journal.lower() for j in 
                               ['nature','science','ecology','biology','fisheries']) else 5
        year = paper.get('year', 2000) or 2000
        novelty = 8 if year >= 2023 else 6 if year >= 2020 else 4
        return {"relevance": relevance, "credibility": credibility,
                "novelty": novelty, "completeness": 5, "reasoning": "heuristic"}

    def rank(self, query: str, papers: List[Dict]) -> List[Dict]:
        """Evaluate and rank papers by quality."""
        scores = self.evaluate(query, papers)
        for paper in papers:
            key = paper.get('doi', paper.get('title', ''))
            paper['judge_score'] = scores.get(key, PaperEval()).total_score
        return sorted(papers, key=lambda p: p.get('judge_score', 0), reverse=True)
