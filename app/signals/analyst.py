"""
Open-source LLM portfolio signal generator.

Uses the OpenAI-compatible chat completions API, which every major
open-source inference server implements:
  - Ollama   (local, default)  http://localhost:11434/v1
  - Groq     (hosted, free)    https://api.groq.com/openai/v1
  - Together AI                https://api.together.xyz/v1
  - OpenRouter                 https://openrouter.ai/api/v1
  - vLLM / LM Studio           http://localhost:8000/v1

Configure via .env: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import openai

from app.config import settings
from app.edgar.client import FilingSnapshot
from app.portfolio.diff import DiffOut
from app.portfolio.models import PortfolioAnalysis, TradingSignal
from app.sentiment.analyzer import TickerSentiment

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert institutional portfolio analyst with 20+ years of experience analysing \
13F filings and generating actionable investment intelligence.

Your task: analyse quarter-over-quarter changes in a celebrity investor's 13F holdings, \
incorporate news-sentiment signals, and produce institutional-quality trading intelligence.

Scoring criteria
- NEW position sizing > 1% of portfolio → HIGH conviction BUY
- INCREASED > 25% → ADD; > 50% → strong ADD
- DECREASED > 25% → TRIM; > 50% or full EXIT → SELL
- Sentiment SUPPORTS a bullish action → raise confidence by 0.1
- Sentiment CONTRADICTS a bullish action → lower confidence by 0.15

Output requirements
You MUST respond with a single valid JSON object and nothing else — no markdown fences, \
no prose outside the JSON. The object must match this exact schema:

{
  "executive_summary": "<2-3 sentence overview>",
  "strategy_style": "<e.g. Value rotation, AI infrastructure concentration>",
  "key_themes": ["<theme1>", "<theme2>", "<theme3>"],
  "signals": [
    {
      "ticker": "<TICKER or CUSIP>",
      "company_name": "<name>",
      "action": "<BUY|ADD|HOLD|TRIM|SELL>",
      "confidence": <0.0-1.0>,
      "rationale": "<specific reasoning grounded in the data>",
      "sentiment_alignment": "<SUPPORTS|NEUTRAL|CONTRADICTS>",
      "institutional_conviction": "<HIGH|MEDIUM|LOW>"
    }
  ],
  "risk_factors": ["<risk1>", "<risk2>", "<risk3>"]
}
"""


def _build_user_message(
    diff: DiffOut,
    snapshot: FilingSnapshot,
    sentiment: dict[str, TickerSentiment],
) -> str:
    total = snapshot.total_value_thousands or 1
    lines = [
        f"## Portfolio Analysis: {diff.investor_name}",
        f"**Period shift:** {diff.previous_period} → {diff.current_period}",
        f"**AUM change:** {diff.total_value_change_pct:+.1f}%",
        f"**Total AUM:** ${total / 1_000_000:.2f}B   |   **Holdings:** {snapshot.holding_count}",
        "",
    ]

    def _sent(ticker: Optional[str]) -> str:
        if not ticker:
            return ""
        s = sentiment.get(ticker)
        if not s:
            return ""
        return f"  [Sentiment: {s.label} score={s.score:+.3f} from {s.headline_count} headlines]"

    if diff.summary.new_positions:
        lines.append("### NEW POSITIONS")
        for c in [x for x in diff.changes if x.action == "NEW"][:12]:
            lines.append(
                f"- **{c.ticker or c.company_name}** ${(c.curr_value_thousands or 0)/1000:.1f}M "
                f"({c.curr_pct_of_portfolio or 0:.2f}% portfolio){_sent(c.ticker)}"
            )

    if diff.summary.increased_positions:
        lines.append("\n### INCREASED POSITIONS")
        for c in [x for x in diff.changes if x.action == "INCREASED"][:12]:
            lines.append(
                f"- **{c.ticker or c.company_name}** shares {c.shares_change_pct:+.1f}% | "
                f"portfolio weight {c.prev_pct_of_portfolio or 0:.2f}% → {c.curr_pct_of_portfolio or 0:.2f}%"
                f"{_sent(c.ticker)}"
            )

    if diff.summary.decreased_positions:
        lines.append("\n### DECREASED POSITIONS")
        for c in [x for x in diff.changes if x.action == "DECREASED"][:12]:
            lines.append(
                f"- **{c.ticker or c.company_name}** shares {c.shares_change_pct:+.1f}% | "
                f"portfolio weight {c.prev_pct_of_portfolio or 0:.2f}% → {c.curr_pct_of_portfolio or 0:.2f}%"
                f"{_sent(c.ticker)}"
            )

    if diff.summary.exited_positions:
        lines.append("\n### EXITED POSITIONS")
        for c in [x for x in diff.changes if x.action == "EXITED"][:10]:
            lines.append(
                f"- **{c.ticker or c.company_name}** fully exited "
                f"(was ${(c.prev_value_thousands or 0)/1000:.1f}M, "
                f"{c.prev_pct_of_portfolio or 0:.2f}% of portfolio)"
            )

    lines.append("\n### CURRENT TOP 10 HOLDINGS (context)")
    for i, h in enumerate(snapshot.holdings[:10], 1):
        pct = h.value_thousands / total * 100
        lines.append(f"{i}. **{h.ticker or h.company_name}** ${h.value_thousands/1000:.1f}M ({pct:.1f}%)")

    lines.append(
        "\nGenerate signals for the top 15 most significant positions. "
        "Be specific — ground rationale in the numbers above, not generic market commentary. "
        "Remember: respond with JSON only."
    )
    return "\n".join(lines)


def _parse_response(text: str) -> dict:
    text = text.strip()
    # Strip accidental markdown fences from models that ignore instructions
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in model response: {text[:200]}")
    return json.loads(text[start:end])


class AIAnalyst:
    def __init__(self):
        self._client = openai.OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
        self._model = settings.llm_model

    def analyze(
        self,
        diff: DiffOut,
        snapshot: FilingSnapshot,
        sentiment: dict[str, TickerSentiment],
    ) -> PortfolioAnalysis:
        user_msg = _build_user_message(diff, snapshot, sentiment)

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )

        raw = _parse_response(response.choices[0].message.content or "")
        signals = [TradingSignal(**s) for s in raw.get("signals", [])]

        return PortfolioAnalysis(
            investor_name=diff.investor_name,
            period=f"{diff.previous_period} → {diff.current_period}",
            executive_summary=raw.get("executive_summary", ""),
            strategy_style=raw.get("strategy_style", ""),
            key_themes=raw.get("key_themes", []),
            signals=signals,
            risk_factors=raw.get("risk_factors", []),
            model_used=self._model,
        )

    def generate_commentary(self, prompt: str, max_tokens: int = 512) -> str:
        """General-purpose text generation for ad-hoc commentary (e.g. insider signal narrative)."""
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
