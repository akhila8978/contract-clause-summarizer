"""Pure-Python persistent vector store (no native deps).

Replaces ChromaDB to avoid the chroma-hnswlib C++ build requirement on
Windows. Stores vectors + documents + metadata as JSON+NPZ per collection
on disk. Cosine similarity search is done with numpy.
"""
from __future__ import annotations
import os
import json
import logging
import threading
from typing import List, Dict, Any, Optional
import numpy as np

log = logging.getLogger("vs")
STORE_DIR = os.getenv("CHROMA_DIR", ".vectorstore")

COLLECTIONS = ["policies", "contracts", "renewals", "requirements", "change_requests"]

_lock = threading.RLock()
_cache: Dict[str, Dict[str, Any]] = {}


def _paths(name: str):
    os.makedirs(STORE_DIR, exist_ok=True)
    return (
        os.path.join(STORE_DIR, f"{name}.json"),
        os.path.join(STORE_DIR, f"{name}.npy"),
    )


def _load(name: str) -> Dict[str, Any]:
    if name in _cache:
        return _cache[name]
    meta_p, vec_p = _paths(name)
    if os.path.exists(meta_p) and os.path.exists(vec_p):
        try:
            with open(meta_p, "r", encoding="utf-8") as f:
                meta = json.load(f)
            vecs = np.load(vec_p)
            data = {
                "ids": meta.get("ids", []),
                "docs": meta.get("docs", []),
                "metas": meta.get("metas", []),
                "vecs": vecs,
            }
        except Exception as e:
            log.warning("failed to load %s: %s", name, e)
            data = {"ids": [], "docs": [], "metas": [], "vecs": np.zeros((0, 0))}
    else:
        data = {"ids": [], "docs": [], "metas": [], "vecs": np.zeros((0, 0))}
    _cache[name] = data
    return data


def _save(name: str):
    data = _cache.get(name)
    if not data:
        return
    meta_p, vec_p = _paths(name)
    with open(meta_p, "w", encoding="utf-8") as f:
        json.dump(
            {"ids": data["ids"], "docs": data["docs"], "metas": data["metas"]},
            f,
        )
    np.save(vec_p, data["vecs"])


def get_collection(name: str):
    if name not in COLLECTIONS:
        raise ValueError(f"unknown collection {name}")
    return _load(name)


def add(
    collection: str,
    ids: List[str],
    docs: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
):
    with _lock:
        data = _load(collection)
        new_vecs = np.array(embeddings, dtype=np.float32)
        if new_vecs.ndim == 1:
            new_vecs = new_vecs.reshape(1, -1)
        id_to_idx = {i: k for k, i in enumerate(data["ids"])}
        for i, doc, meta, vec in zip(ids, docs, metadatas, new_vecs):
            if i in id_to_idx:
                k = id_to_idx[i]
                data["docs"][k] = doc
                data["metas"][k] = meta
                if data["vecs"].shape[0] > 0 and data["vecs"].shape[1] == vec.shape[0]:
                    data["vecs"][k] = vec
                else:
                    # dim mismatch -> rebuild
                    data["vecs"] = np.vstack([data["vecs"], vec.reshape(1, -1)]) if data["vecs"].size else vec.reshape(1, -1)
            else:
                data["ids"].append(i)
                data["docs"].append(doc)
                data["metas"].append(meta)
                if data["vecs"].size == 0:
                    data["vecs"] = vec.reshape(1, -1)
                elif data["vecs"].shape[1] == vec.shape[0]:
                    data["vecs"] = np.vstack([data["vecs"], vec.reshape(1, -1)])
                else:
                    log.warning("embedding dim mismatch in %s; skipping vector", collection)
                    data["vecs"] = np.vstack([data["vecs"], np.zeros((1, data["vecs"].shape[1]), dtype=np.float32)])
        _save(collection)


def query(
    collection: str,
    query_embeddings: List[List[float]],
    n_results: int = 5,
) -> List[List[Dict[str, Any]]]:
    with _lock:
        data = _load(collection)
        out: List[List[Dict[str, Any]]] = []
        if not data["ids"] or data["vecs"].size == 0:
            return [[] for _ in query_embeddings]
        mat = data["vecs"]
        norms = np.linalg.norm(mat, axis=1) + 1e-12
        for q in query_embeddings:
            qv = np.array(q, dtype=np.float32)
            if qv.shape[0] != mat.shape[1]:
                out.append([])
                continue
            sims = (mat @ qv) / (norms * (np.linalg.norm(qv) + 1e-12))
            top = np.argsort(-sims)[:n_results]
            out.append(
                [
                    {"id": data["ids"][k], "doc": data["docs"][k], "meta": data["metas"][k]}
                    for k in top
                ]
            )
        return out


def count(collection: str) -> int:
    try:
        return len(_load(collection)["ids"])
    except Exception:
        return 0
