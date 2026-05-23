"""Shared AsyncOpenAI client for the GenAILab gateway with robust fallbacks."""
from __future__ import annotations
import os
import logging
import traceback
from functools import lru_cache
from typing import Any, List, Dict, Optional
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

from utils.sanitizer import sanitize_for_llm

load_dotenv()
log = logging.getLogger("llm")

BASE_URL = os.getenv("GENAI_BASE_URL", "https://genailab.tcs.in/v1")
API_KEY = os.getenv("GENAI_API_KEY", "")
EMBED_MODEL = os.getenv("GENAI_EMBED_MODEL", "azure/genailab-maas-text-embedding-3-large")
# text-embedding-3-large = 3072 dims. Make configurable in case the gateway
# returns a different size; everything is stored consistently in chroma.
EMBED_DIM = int(os.getenv("GENAI_EMBED_DIM", "3072"))


@lru_cache(maxsize=1)
def get_client() -> AsyncOpenAI:
    transport = httpx.AsyncHTTPTransport(verify=False)
    return AsyncOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        http_client=httpx.AsyncClient(transport=transport, verify=False, timeout=120.0),
    )


async def chat(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.2,
    response_format: Optional[Dict[str, Any]] = None,
    max_tokens: int = 1500,
) -> str:
    client = get_client()
    kwargs: Dict[str, Any] = dict(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    if response_format:
        kwargs["response_format"] = response_format
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggressively sanitize all message content for a retry."""
    out: List[Dict[str, Any]] = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            out.append({**m, "content": sanitize_for_llm(c)})
        else:
            out.append(m)
    return out


async def run_with_fallback(
    primary: str,
    fallback: str,
    messages: List[Dict[str, Any]],
    **kwargs: Any,
) -> str:
    """Run primary model; on any exception fall back. On 403 content-filter
    errors, retry once with sanitized messages before giving up."""
    try:
        return await chat(primary, messages, **kwargs)
    except Exception as e:  # noqa: BLE001
        err = str(e)
        log.warning("Primary model %s failed: %s — falling back to %s", primary, err[:200], fallback)
        log.debug(traceback.format_exc())
        # if content blocked, try sanitizing harder
        msgs2 = _sanitize_messages(messages) if "Content blocked" in err or "403" in err else messages
        try:
            return await chat(fallback, msgs2, **kwargs)
        except Exception as e2:  # noqa: BLE001
            err2 = str(e2)
            log.error("Fallback %s also failed: %s", fallback, err2[:200])
            # last-ditch: sanitize and retry primary
            if "Content blocked" in err2 or "403" in err2:
                try:
                    return await chat(primary, _sanitize_messages(messages), **kwargs)
                except Exception as e3:  # noqa: BLE001
                    log.error("Sanitized retry also failed: %s", str(e3)[:200])
            return ""


async def embed(texts: List[str]) -> List[List[float]]:
    """Embed in batches with per-batch and per-text fallback. Always returns
    vectors of EMBED_DIM length so the downstream vector store has a stable
    dimensionality."""
    client = get_client()
    out: List[List[float]] = []
    zero = [0.0] * EMBED_DIM
    BATCH = 32

    async def _embed_one_batch(batch: List[str]) -> List[List[float]]:
        resp = await client.embeddings.create(model=EMBED_MODEL, input=batch)
        return [list(d.embedding) for d in resp.data]

    for i in range(0, len(texts), BATCH):
        batch = [t if t else " " for t in texts[i : i + BATCH]]
        try:
            embs = await _embed_one_batch(batch)
            out.extend(embs)
        except Exception as e:  # noqa: BLE001
            log.warning("Embedding batch failed (%d items): %s — retrying sanitized", len(batch), str(e)[:200])
            # try sanitized
            try:
                embs = await _embed_one_batch([sanitize_for_llm(t) for t in batch])
                out.extend(embs)
                continue
            except Exception as e2:
                log.warning("Sanitized batch also failed: %s — embedding texts individually", str(e2)[:200])
            # individual fallback
            for t in batch:
                try:
                    e_one = await _embed_one_batch([sanitize_for_llm(t)])
                    out.append(e_one[0])
                except Exception as e3:  # noqa: BLE001
                    log.error("Embedding error for one chunk: %s", str(e3)[:200])
                    out.append(list(zero))
    # safety: normalize dims (in case gateway returns variable length)
    if out:
        d = len(out[0])
        if d != EMBED_DIM:
            # adopt observed dim so future calls match — but ensure all rows same length
            for k in range(len(out)):
                v = out[k]
                if len(v) != d:
                    out[k] = (v + [0.0] * d)[:d]
    return out
