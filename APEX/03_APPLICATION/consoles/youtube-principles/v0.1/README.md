# APEX YouTube Principles Extraction Console v0.1

## Purpose

Paste one or more YouTube URLs into a single web page and get back, for
each video: its title/channel, a short summary, and every core law,
principle, theory, framework, mental model, and heuristic the video
teaches or references -- each with a plain-language explanation, how to
apply it, a supporting quote, and an approximate timestamp.

## Architecture

```
web/index.html       Single-page frontend: paste URLs, view/download results
backend/pipeline.py   Ingestion + extraction pipeline (framework-independent)
backend/server.py     FastAPI app: serves web/index.html and POST /api/analyze
```

Flow for each submitted URL:

1. Parse the YouTube video ID from the URL.
2. Fetch public oEmbed metadata (title, channel, thumbnail) -- no API key needed.
3. Fetch the official caption/transcript track via `youtube-transcript-api`.
4. Split the transcript into chunks and send each chunk to an LLM
   (OpenAI Chat Completions, `OPENAI_API_KEY` required) asking it to pull
   out every principle/law/theory/framework/mental model/heuristic in
   that chunk, with a supporting quote copied from the transcript.
5. Every returned quote is automatically checked against the transcript
   chunk text; quotes that do not match are flagged `unverified` rather
   than silently trusted.
6. Duplicate principles across chunks are merged, an overall summary is
   generated, and the result is returned as one JSON report per video
   with QA gates and a Truth Status block.

## Truth Boundary

This pipeline never downloads video or audio files, never bypasses
YouTube login/paywalls/terms of service, and never scrapes anything
beyond two public endpoints: the oEmbed metadata endpoint and the
official caption/transcript track YouTube already serves for the video.
Auto-generated captions can contain transcription errors, and the LLM's
categorization/phrasing is inferred, not verified fact -- named laws and
theories should be checked against a primary source before you rely on
or republish them.

## Run it

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # required for extraction/summary
uvicorn backend.server:app --reload --app-dir "APEX/03_APPLICATION/consoles/youtube-principles/v0.1"
```

Then open http://127.0.0.1:8000/ and paste YouTube URLs, one per line.

Without `OPENAI_API_KEY` set, `/api/analyze` still fetches metadata and
transcripts, but each report will carry an `llm_extraction_error` /
`llm_summary_error` risk flag instead of principles.

## Heart Core

- **Status**: Prototype -- not production-ready.
- **Truth labels**: metadata and transcript fetch are VERIFIED against
  public endpoints; principle extraction and summaries are INFERRED by
  an LLM and must be spot-checked; quote verbatim-ness beyond the
  automated substring check is UNKNOWN.
- **User controls**: nothing is downloaded, stored server-side, or
  published automatically; every report can be downloaded as JSON so the
  user can review it before use.
- **Next step**: add a "verify against source" checklist UI for
  unverified quotes before allowing export/sharing.
- **Review needed**: yes -- treat extracted principles as a first draft,
  not a citation.

## Known limits (v0.1)

- Videos without captions (disabled or none available) return a
  `disabled`/`unavailable` transcript status and no principles.
- Long videos are processed as multiple sequential LLM calls, which can
  take a while and cost more tokens; there is no caching yet.
- No YouTube Data API key is used or required -- only the public oEmbed
  endpoint, so metadata is limited to title/channel/thumbnail.
- Requests are processed sequentially, one video at a time.
