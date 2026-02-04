# rerank/rerank.py
"""
Cross-encoder reranker helper.

Provides rerank_candidates(query, candidates, ...) which returns
candidates annotated with 'rerank_score' and 'final_score', sorted descending.
"""

import os
from typing import List, Dict, Any, Optional
import logging

# Lazy import - CrossEncoder is heavy (and depends on torch)
_MODEL_CACHE = {}

def _load_model(name: str):
    # Lazy import to avoid import-time heavy dependency
    try:
        from sentence_transformers.cross_encoder import CrossEncoder
    except Exception as e:
        raise RuntimeError(f"sentence-transformers CrossEncoder not available: {e}")

    # determine device
    use_cuda = os.environ.get("USE_CUDA", "0") in ("1", "true", "True")
    device = "cuda" if use_cuda else "cpu"
    logging.info(f"Loading CrossEncoder model {name} on device {device}")
    return CrossEncoder(name, device=device)

def _get_model(name: str):
    if name not in _MODEL_CACHE:
        _MODEL_CACHE[name] = _load_model(name)
    return _MODEL_CACHE[name]

def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    batch_size: int = 64,
    top_k: Optional[int] = None,
    rerank_weight: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Rerank `candidates` for `query` using a CrossEncoder model.
    candidates: list of dicts containing at least 'chunk_text' and optionally 'fused_score'
    rerank_weight: how much to favor reranker (0..1). final_score = rerank_weight*rerank_score + (1-re_rank_weight)*fused_score
    """
    if not candidates:
        return []

    if model_name is None:
        model_name = os.environ.get("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    try:
        model = _get_model(model_name)
    except Exception as e:
        # If we cannot load the model, fallback gracefully and return original top candidates
        logging.exception("Failed to load reranker model; falling back.")
        # ensure fused_score exists:
        for c in candidates:
            c.setdefault("rerank_score", None)
            c["final_score"] = c.get("fused_score", 0.0)
        # sort by fused_score and return top_k
        return sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)[:top_k] if top_k else sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)

    # build pairs and predict
    pairs = [[query, c.get("chunk_text","")] for c in candidates]
    try:
        scores = model.predict(pairs, batch_size=batch_size)
    except Exception as e:
        logging.exception("Reranker predict failed; falling back to fused scores.")
        for c in candidates:
            c.setdefault("rerank_score", None)
            c["final_score"] = c.get("fused_score", 0.0)
        return sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)[:top_k] if top_k else sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)

    # annotate candidates
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
        fused = float(c.get("fused_score", 0.0))
        c["final_score"] = float(rerank_weight) * float(s) + (1.0 - float(rerank_weight)) * fused

    sorted_c = sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)
    return sorted_c[:top_k] if top_k else sorted_c
