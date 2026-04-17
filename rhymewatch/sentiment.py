"""Three-tier sentiment pipeline.

    Tier 0  regex/lexicon         <1ms          (WSB slang, emoji)
    Tier 1  ONNX-int8 finbert     ~20ms/text    (bulk)
    Tier 2  Gemini Flash-Lite      ~400ms/text   (sarcasm, aspects, multi-ticker)

Each result is cached in Upstash under `rw:sent:{hash(text)}` with a 4-hour TTL.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Optional

from . import cache, lexicon, llm

try:
    from .onnx_sentiment import ONNXSentiment
    _HAS_ONNX = True
except Exception:
    _HAS_ONNX = False


@dataclass
class SentimentResult:
    label: str              # positive | negative | neutral
    confidence: float
    tier: int               # 0, 1, 2
    aspect: Optional[str] = None
    targets: Optional[List[str]] = None
    is_sarcastic: Optional[bool] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _key(text: str) -> str:
    return "rw:sent:" + hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:16]


def classify_one(text: str, force_escalate: bool = False) -> SentimentResult:
    cached = cache.get(_key(text))
    if cached and not force_escalate:
        return SentimentResult(**cached)

    # Tier 0 — regex / lexicon
    lex = lexicon.lexicon_score(text)
    if lex.score >= 0.6 and lex.label != "neutral" and not force_escalate:
        r = SentimentResult(label=lex.label, confidence=lex.score, tier=0)
        cache.set(_key(text), r.to_dict(), ex=4 * 3600)
        return r

    # Tier 1 — ONNX
    tier1_label = lex.label
    tier1_conf = lex.score
    if _HAS_ONNX:
        try:
            m = ONNXSentiment.get()
            batch = m.classify([text])
            if batch:
                tier1_label = batch[0].label
                tier1_conf = batch[0].score
        except Exception:
            pass  # soft-fail to lexicon result

    n_tickers = sum(1 for tok in (text or "").split() if tok.isupper() and 2 <= len(tok) <= 5)

    # Tier 2 — LLM escalation
    if force_escalate or llm.needs_escalation(text, tier1_conf, n_tickers):
        aspect = llm.escalate(text)
        if aspect:
            r = SentimentResult(
                label=aspect.sentiment,
                confidence=aspect.confidence,
                tier=2,
                aspect=aspect.aspect,
                targets=aspect.targets,
                is_sarcastic=aspect.is_sarcastic,
            )
            cache.set(_key(text), r.to_dict(), ex=4 * 3600)
            return r

    r = SentimentResult(label=tier1_label, confidence=tier1_conf, tier=1)
    cache.set(_key(text), r.to_dict(), ex=4 * 3600)
    return r


def classify_many(texts: List[str]) -> List[SentimentResult]:
    return [classify_one(t) for t in texts]


def counts(results: List[SentimentResult]) -> dict:
    c = {"positive": 0, "neutral": 0, "negative": 0, "escalations": 0}
    for r in results:
        c[r.label] = c.get(r.label, 0) + 1
        if r.tier == 2:
            c["escalations"] += 1
    return c
