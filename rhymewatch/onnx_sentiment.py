"""Tier 1 sentiment: ONNX-int8 quantized finbert-tone.

Loads from a remote URL (e.g. Vercel Blob, Cloudflare R2) into /tmp on the
first call. Uses `onnxruntime` + `tokenizers` directly — no `torch`, no
`transformers`, which is what keeps us under the Vercel 250MB Python limit.

Export the model once locally with:

    from optimum.onnxruntime import ORTModelForSequenceClassification, ORTQuantizer
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    m = ORTModelForSequenceClassification.from_pretrained(
        "yiyanghkust/finbert-tone", export=True)
    q = ORTQuantizer.from_pretrained(m)
    q.quantize(save_dir="./fin_q",
        quantization_config=AutoQuantizationConfig.avx512_vnni(
            is_static=False, per_channel=False))

Then upload `fin_q/model.onnx` + tokenizer files to Vercel Blob and set
ONNX_SENTIMENT_MODEL_URL / ONNX_SENTIMENT_TOKENIZER_URL.
"""
from __future__ import annotations
import os
import tempfile
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass
import urllib.request
import numpy as np

_TMP = Path(tempfile.gettempdir()) / "rhymewatch_onnx"
_TMP.mkdir(exist_ok=True)

_LABELS = ["neutral", "positive", "negative"]  # finbert-tone label order


@dataclass
class ONNXResult:
    label: str
    score: float


class ONNXSentiment:
    """Lazy ONNX sentiment model loader. Holds a singleton per process."""
    _instance = None

    def __init__(self):
        self.session = None
        self.tokenizer = None

    @classmethod
    def get(cls) -> "ONNXSentiment":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _download(self, url: str, name: str) -> Path:
        dest = _TMP / name
        if not dest.exists():
            urllib.request.urlretrieve(url, dest)
        return dest

    def load(self):
        if self.session is not None:
            return
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as e:
            raise RuntimeError(
                "onnxruntime + tokenizers required for tier-1 sentiment: %s" % e
            )
        model_url = os.getenv("ONNX_SENTIMENT_MODEL_URL")
        tok_url = os.getenv("ONNX_SENTIMENT_TOKENIZER_URL")
        if not model_url or not tok_url:
            raise RuntimeError(
                "ONNX_SENTIMENT_MODEL_URL and ONNX_SENTIMENT_TOKENIZER_URL "
                "must be set. Upload the quantized model to Vercel Blob."
            )
        model_path = self._download(model_url, "finbert_tone_int8.onnx")
        tok_path = self._download(tok_url, "finbert_tone_tokenizer.json")
        self.session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
            sess_options=ort.SessionOptions(),
        )
        self.tokenizer = Tokenizer.from_file(str(tok_path))
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(length=128)

    def classify(self, texts: List[str]) -> List[ONNXResult]:
        if not texts:
            return []
        self.load()
        enc = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in enc], dtype=np.int64)
        attention = np.array([e.attention_mask for e in enc], dtype=np.int64)
        # finbert-tone was trained with token_type_ids, many exports omit them
        inputs = {"input_ids": input_ids, "attention_mask": attention}
        if "token_type_ids" in {i.name for i in self.session.get_inputs()}:
            inputs["token_type_ids"] = np.zeros_like(input_ids)
        logits = self.session.run(None, inputs)[0]
        probs = _softmax(logits)
        out = []
        for p in probs:
            idx = int(np.argmax(p))
            out.append(ONNXResult(label=_LABELS[idx], score=float(p[idx])))
        return out


def _softmax(x: np.ndarray) -> np.ndarray:
    ex = np.exp(x - x.max(axis=-1, keepdims=True))
    return ex / ex.sum(axis=-1, keepdims=True)
