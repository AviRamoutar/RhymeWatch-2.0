"""Tier 2 sentiment escalation via Gemini 2.5 Flash-Lite.

Called when the ONNX classifier is uncertain (<0.7 confidence), the text shows
sarcasm markers, contains multiple tickers (aspect analysis), or the caller
explicitly asks for aspect-based sentiment.

Cost: ~$0.000032 per short headline at Flash-Lite pricing. A sane cache
(Upstash Redis, 1–6h TTL) keeps a hobby project well under $5/mo.
"""
from __future__ import annotations
import os
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional

SARCASM_MARKERS = re.compile(
    r"\b(yeah right|sure jan|lmao|🤡|/s|obviously|this time for sure)\b", re.I
)


@dataclass
class AspectResult:
    sentiment: str          # "positive" | "negative" | "neutral"
    confidence: float
    aspect: str             # "earnings" | "guidance" | "management" | "macro" | "product" | "legal" | "M&A" | "rumor"
    targets: List[str]
    is_sarcastic: bool
    reasoning: str


def needs_escalation(text: str, tier1_confidence: float, n_tickers: int = 0) -> bool:
    if n_tickers >= 2:
        return True
    if SARCASM_MARKERS.search(text or ""):
        return True
    return tier1_confidence < 0.70


def escalate(text: str) -> Optional[AspectResult]:
    """Return None if GEMINI_API_KEY is not configured or the call fails."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not text:
        return None
    try:
        from google import genai
        from google.genai import types as gt
    except ImportError:
        return None
    client = genai.Client(api_key=api_key)
    prompt = (
        "Classify the financial sentiment of the text below. Output JSON only. "
        "Fields:\n"
        "  sentiment: one of positive, negative, neutral\n"
        "  confidence: 0-1 float\n"
        "  aspect: one of earnings, guidance, management, macro, product, legal, M&A, rumor\n"
        "  targets: array of ticker symbols mentioned (uppercase)\n"
        "  is_sarcastic: boolean\n"
        "  reasoning: one sentence\n\n"
        f"Text: {text}"
    )
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=gt.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=200,
            ),
        )
        raw = resp.text or "{}"
        data = json.loads(raw)
        return AspectResult(
            sentiment=data.get("sentiment", "neutral"),
            confidence=float(data.get("confidence", 0.5)),
            aspect=data.get("aspect", "rumor"),
            targets=list(data.get("targets", [])),
            is_sarcastic=bool(data.get("is_sarcastic", False)),
            reasoning=data.get("reasoning", ""),
        )
    except Exception:
        return None


def to_dict(r: Optional[AspectResult]) -> Optional[dict]:
    return asdict(r) if r else None
