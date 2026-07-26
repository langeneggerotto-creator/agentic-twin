#!/usr/bin/env python3
"""
APEX Article/Webpage Principles Extraction v0.1

Fetches a public webpage/article URL and extracts its clean main-content
text and metadata via trafilatura -- no login/paywall bypass, no video or
audio involved. Reuses the same LLM extraction, quote verification, dedupe,
and category/domain/alias labeling logic as pipeline.py (YouTube) so
articles produce principles tagged the same way and can be ingested into
the same principles knowledge base alongside video-sourced ones.

Truth boundary: this module only fetches a URL's publicly served HTML (the
same thing a browser would GET) and extracts readable text from it. It
never logs in, never bypasses a paywall, and reports 'unavailable' rather
than guessing when a page's real content can't be extracted (e.g. JS-only
rendering, paywalled content).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import trafilatura

try:
    from . import pipeline
except ImportError:  # allow loading/running this module standalone, not just as a package
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipeline  # type: ignore


@dataclass
class ArticleMeta:
    url: str
    title: str = "Unknown title"
    author: str = "Unknown author"
    site_name: str = ""


@dataclass
class ArticleContent:
    status: str  # "ok" | "unavailable" | "error"
    text: str = ""
    error: str = ""


def is_probably_url(text: str) -> bool:
    return text.strip().lower().startswith(("http://", "https://"))


def fetch_article(url: str) -> Tuple[ArticleMeta, ArticleContent]:
    """Fetch a public webpage and extract its clean article text + metadata."""
    meta = ArticleMeta(url=url)
    try:
        html = trafilatura.fetch_url(url)
    except Exception as exc:  # noqa: BLE001
        return meta, ArticleContent(status="error", error=f"{type(exc).__name__}: {exc}")

    if not html:
        return meta, ArticleContent(
            status="unavailable",
            error="Could not download this page (offline, blocked, or an invalid URL).",
        )

    try:
        raw = trafilatura.extract(html, url=url, output_format="json", with_metadata=True, include_comments=False)
    except Exception as exc:  # noqa: BLE001
        return meta, ArticleContent(status="error", error=f"{type(exc).__name__}: {exc}")

    if not raw:
        return meta, ArticleContent(
            status="unavailable",
            error="No extractable article text found (may be paywalled, JS-rendered, or not an article page).",
        )

    data = json.loads(raw)
    meta.title = data.get("title") or meta.title
    meta.author = data.get("author") or meta.author
    meta.site_name = data.get("source-hostname") or data.get("hostname") or ""
    text = (data.get("text") or "").strip()
    if not text:
        return meta, ArticleContent(status="unavailable", error="Extracted article text was empty.")
    return meta, ArticleContent(status="ok", text=text)


def chunk_plain_text(text: str, char_limit: int = pipeline.CHUNK_CHAR_LIMIT) -> List[pipeline.TranscriptChunk]:
    """Split plain article text into the same TranscriptChunk shape the video pipeline uses
    (start/end seconds are meaningless here and left at 0.0) so the shared extraction helpers
    don't need to know which source type they're operating on."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: List[pipeline.TranscriptChunk] = []
    buf: List[str] = []
    buf_len = 0
    for para in paragraphs:
        if buf_len + len(para) + 1 > char_limit and buf:
            chunks.append(pipeline.TranscriptChunk(len(chunks), " ".join(buf), 0.0, 0.0))
            buf, buf_len = [], 0
        buf.append(para)
        buf_len += len(para) + 1
    if buf:
        chunks.append(pipeline.TranscriptChunk(len(chunks), " ".join(buf), 0.0, 0.0))
    return chunks


def _qa_gates(content_status: str, principles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reuses pipeline.qa_gates' scoring, just relabeling 'transcript_*' to 'content_*'
    so the issue/pass names read correctly for a non-video source."""
    gates = pipeline.qa_gates(content_status, principles)
    gates["passes"] = [p.replace("transcript_fetched", "content_fetched") for p in gates["passes"]]
    gates["issues"] = [i.replace("transcript_", "content_") for i in gates["issues"]]
    return gates


def build_report(url: str, meta: ArticleMeta, content: ArticleContent, llm: pipeline.LLMClient) -> Dict[str, Any]:
    principles: List[Dict[str, Any]] = []
    summary = ""
    risk_flags = [
        "quotes_are_excerpts_verify_before_republishing",
        "verify_named_laws_against_primary_source",
    ]
    llm_errors: List[str] = []
    failed_chunk_count = 0

    if content.status == "ok":
        chunks = chunk_plain_text(content.text)
        full_text = " ".join(c.text for c in chunks)
        all_items: List[Dict[str, Any]] = []
        for chunk in chunks:
            try:
                items = llm.extract_principles(chunk.text, meta.title)
            except Exception as exc:  # noqa: BLE001 - one failed chunk should not sink the whole report
                failed_chunk_count += 1
                if len(llm_errors) < 3:
                    llm_errors.append(f"chunk {chunk.index}: {type(exc).__name__}: {exc}")
                continue
            for item in items:
                item["quote_verified"] = pipeline.verify_quote(item.get("quote", ""), chunk.text)
                item["approx_timestamp"] = ""
                item["source_chunk_index"] = chunk.index
                if item.get("category") not in pipeline.PRINCIPLE_CATEGORIES:
                    item["category"] = "principle"
                item["domains"] = pipeline.normalize_domains(item.get("domains"))
                item["aliases"] = pipeline.normalize_aliases(item.get("aliases"))
                all_items.append(item)
        if failed_chunk_count:
            risk_flags.append("llm_extraction_error")
        principles = pipeline.merge_candidates(all_items)
        try:
            summary = llm.summarize(full_text, meta.title)
        except Exception as exc:  # noqa: BLE001
            summary = "Summary unavailable (LLM call failed)."
            risk_flags.append("llm_summary_error")
            llm_errors.append(f"summary: {type(exc).__name__}: {exc}")
    else:
        risk_flags.append("no_content_available")

    report: Dict[str, Any] = {
        "artifact_type": "apex_principles_report_v01",
        "source_type": "article",
        "article": asdict(meta),
        "source_url": url,
        "content_status": content.status,
        "content_error": content.error,
        "summary": summary,
        "principles": principles,
        "principle_count": len(principles),
        "llm_failed_chunk_count": failed_chunk_count,
        "llm_error_samples": llm_errors,
        "risk_flags": sorted(set(risk_flags)),
        "qa_gates": _qa_gates(content.status, principles),
        "truth_status": {
            "VERIFIED": [
                "article fetched from the URL's own public HTML" if content.status == "ok" else "article fetch attempted",
            ],
            "INFERRED": ["principle categorization, domain tags, aliases, phrasing, and summary produced by an LLM"],
            "ASSUMED": ["extracted article text is a faithful, complete rendering of the page's main content"],
            "UNKNOWN": ["whether extracted quotes are precisely verbatim beyond the automated substring check"],
        },
        "next_3_plus_1": {
            "next_1": "Read the flagged unverified quotes against the original article before quoting publicly.",
            "next_2": "Cross-check named laws/theories against a primary source before treating them as fact.",
            "next_3": "Re-run with a stronger model if an article's principles feel thin or generic.",
            "plus_1_control": "This pipeline never logs in, bypasses paywalls, or scrapes beyond the page's own public HTML.",
        },
    }
    payload = json.dumps(report, sort_keys=True, ensure_ascii=False, default=str)
    report["manifest_hash_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return report


def analyze_url(url: str, llm: Optional[pipeline.LLMClient] = None) -> Dict[str, Any]:
    llm = llm or pipeline.OpenAIClient()
    if not is_probably_url(url):
        return {
            "artifact_type": "apex_principles_report_v01",
            "source_type": "article",
            "source_url": url,
            "error": "Not a fetchable http(s) URL.",
            "content_status": "error",
            "principles": [],
            "principle_count": 0,
            "risk_flags": ["invalid_url"],
        }
    meta, content = fetch_article(url)
    return build_report(url, meta, content, llm)


def analyze_urls(urls: List[str], llm: Optional[pipeline.LLMClient] = None) -> List[Dict[str, Any]]:
    llm = llm or pipeline.OpenAIClient()
    return [analyze_url(u, llm) for u in urls]
