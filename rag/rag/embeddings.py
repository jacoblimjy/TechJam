# rag/embeddings.py
from __future__ import annotations
from typing import List
import threading
import numpy as np
import torch

from langchain_core.embeddings import Embeddings
from FlagEmbedding import BGEM3FlagModel

# Thread-safe singleton loader for BGEM3
__BGE_LOCK = threading.Lock()
__BGE_MODEL = None

def _auto_use_fp16() -> bool:
    # Use fp16 only if CUDA is available; otherwise False for CPU
    return bool(torch.cuda.is_available())

def _load_bge(model_name: str = "BAAI/bge-m3", use_fp16: bool | None = None):
    global __BGE_MODEL
    if use_fp16 is None:
        use_fp16 = _auto_use_fp16()
    with __BGE_LOCK:
        if __BGE_MODEL is None:
            __BGE_MODEL = BGEM3FlagModel(
                model_name,
                use_fp16=use_fp16,   # safe on GPU; False on CPU
                devices=None,        # auto
            )
    return __BGE_MODEL

def _l2_normalize(vecs: List[List[float]]) -> List[List[float]]:
    arr = np.asarray(vecs, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    arr = arr / norms
    return arr.tolist()

class BGEM3DenseEmbeddings(Embeddings):
    """
    Dense embeddings using BGE-M3 via FlagEmbedding.
    Output dim = 1024.
    """
    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool | None = None, do_normalize: bool = True):
        self.model_name = model_name
        self.use_fp16 = _auto_use_fp16() if use_fp16 is None else use_fp16
        self.do_normalize = do_normalize
        self.model = _load_bge(model_name, self.use_fp16)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # NOTE: Do NOT pass normalize_embeddings to encode(); normalize ourselves.
        enc = self.model.encode(
            texts,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vecs = enc["dense_vecs"]  # List[List[float]]
        return _l2_normalize(vecs) if self.do_normalize else vecs

    def embed_query(self, text: str) -> List[float]:
        enc = self.model.encode(
            [text],
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vec = enc["dense_vecs"][0]
        if self.do_normalize:
            n = float(np.linalg.norm(vec) + 1e-12)
            vec = [v / n for v in vec]
        return vec
