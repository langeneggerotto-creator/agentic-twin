#!/usr/bin/env python3
"""
Source-type dispatcher for the principles extraction pipeline.

Routes a URL to the YouTube pipeline (pipeline.py) if it looks like a
YouTube URL, otherwise to the generic article/webpage pipeline
(article_pipeline.py). Both return the same overall report shape --
artifact_type, source_type, source_url, principles, principle_count,
risk_flags, qa_gates, truth_status, next_3_plus_1, manifest_hash_sha256 --
differing only in the source-specific metadata key ('video' vs 'article')
and status field names ('transcript_status' vs 'content_status'). Callers
that need to branch on source type should key off report['source_type'].
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from . import article_pipeline, pipeline
except ImportError:  # allow loading/running this module standalone, not just as a package
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import article_pipeline, pipeline  # type: ignore

split_urls = pipeline.split_urls


def analyze_url(url: str, llm: Optional[pipeline.LLMClient] = None) -> Dict[str, Any]:
    llm = llm or pipeline.OpenAIClient()
    if pipeline.parse_video_id(url):
        return pipeline.analyze_url(url, llm)
    return article_pipeline.analyze_url(url, llm)


def analyze_urls(urls: List[str], llm: Optional[pipeline.LLMClient] = None) -> List[Dict[str, Any]]:
    llm = llm or pipeline.OpenAIClient()
    return [analyze_url(u, llm) for u in urls]
