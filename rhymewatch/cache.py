"""Upstash Redis wrapper with in-memory fallback for local dev.

All values stored as JSON strings. Keys are namespaced `rw:{kind}:{id}`.
TTLs follow the research doc: 1–6h for sentiment, 24h for predictions.
"""
from __future__ import annotations
import os
import json
import time
from typing import Any, Optional

_MEM: dict = {}
_MEM_EXPIRY: dict = {}


def _mem_get(k: str) -> Optional[Any]:
    exp = _MEM_EXPIRY.get(k)
    if exp and exp < time.time():
        _MEM.pop(k, None)
        _MEM_EXPIRY.pop(k, None)
        return None
    return _MEM.get(k)


def _mem_set(k: str, v: Any, ex: Optional[int] = None):
    _MEM[k] = v
    if ex:
        _MEM_EXPIRY[k] = time.time() + ex


def _client():
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis
        return Redis(url=url, token=token)
    except ImportError:
        return None


def get(key: str) -> Optional[Any]:
    r = _client()
    try:
        raw = r.get(key) if r else _mem_get(key)
    except Exception:
        raw = _mem_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return raw


def set(key: str, value: Any, ex: int = 3600):
    payload = json.dumps(value, default=str)
    r = _client()
    try:
        if r:
            r.set(key, payload, ex=ex)
        else:
            _mem_set(key, payload, ex=ex)
    except Exception:
        _mem_set(key, payload, ex=ex)
