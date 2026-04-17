"""Tier 0 sentiment: regex/lexicon pass for WSB slang + emoji.

Returns a decision in <1ms when the text has a strong short-form signal. The
motivation is that FinBERT and most financial-news-trained classifiers register
"tendies", "diamond hands", 🚀, 💀 as noise — a retail-focused app needs to
read those correctly before escalating to a heavier model.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

BULLISH = {
    # WSB / retail
    "moon", "mooning", "tendies", "diamond hands", "yolo",
    "calls", "call", "long", "buy", "bullish", "pump", "rocket",
    "bagholder rescued", "squeeze", "short squeeze", "ath", "breakout",
    # emoji
    "🚀", "🌙", "💎", "🙌", "📈", "🦍", "✨", "💰",
}
BEARISH = {
    "puts", "put", "short", "shorts", "bearish", "dump", "dumping",
    "tank", "tanking", "rekt", "rug", "rugged", "bagholder", "bagholding",
    "crater", "crashing", "crash", "bubble", "overvalued",
    "down big", "red", "bleeding", "💀", "📉", "🐻", "🧻", "🩸",
}

_WORD_RE = re.compile(r"[\w']+|[\U0001F300-\U0001FAFF]", re.UNICODE)


@dataclass
class LexResult:
    label: str       # "positive" | "negative" | "neutral"
    score: float     # |score| in [0, 1]; confidence
    hits_pos: int
    hits_neg: int


def lexicon_score(text: str) -> LexResult:
    if not text:
        return LexResult("neutral", 0.0, 0, 0)
    tokens = [t.lower() for t in _WORD_RE.findall(text)]
    pos = sum(1 for t in tokens if t in BULLISH)
    neg = sum(1 for t in tokens if t in BEARISH)
    # also catch multi-word phrases
    lower = text.lower()
    for phrase in ("diamond hands", "short squeeze", "down big", "all time high"):
        if phrase in lower:
            pos += 1
    total = pos + neg
    if total == 0:
        return LexResult("neutral", 0.0, 0, 0)
    score = (pos - neg) / max(total, 1)
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    confidence = min(1.0, abs(score) + 0.1 * total)
    return LexResult(label, confidence, pos, neg)


def is_strong_signal(text: str, threshold: float = 0.6) -> bool:
    """Return True when the lexicon produces a confident enough read to skip
    the heavier ONNX/LLM tiers."""
    r = lexicon_score(text)
    return r.score >= threshold and r.label != "neutral"
