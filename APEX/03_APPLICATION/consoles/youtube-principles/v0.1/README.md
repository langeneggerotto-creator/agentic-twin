# APEX Principles Extraction Console v0.1

## Purpose

Paste one or more URLs -- YouTube videos and/or articles/webpages, any mix
-- into a single web page (or the command line) and get back, for each
one: its title/byline, a short summary, and every core law, principle,
theory, framework, mental model, and heuristic it teaches or references --
each with a plain-language explanation, how to apply it, and a supporting
quote. Reports are labeled richly enough (category + domain tags +
aliases) to feed directly into the companion `principles-kb` knowledge
base repo, which other projects can query across every source, not just
one video at a time.

## Architecture

```
web/index.html               Single-page frontend: paste URLs, view/download results
backend/pipeline.py           YouTube ingestion + shared extraction/labeling helpers
backend/article_pipeline.py   Article/webpage ingestion, reusing pipeline.py's shared helpers
backend/dispatch.py           Routes each URL to the right pipeline by source type
backend/server.py             FastAPI app: serves web/index.html and POST /api/analyze
backend/cli.py                Command-line entry point: no server, no browser required

backend/av_craft_pipeline.py    Separate tool: cinematography/color-grading/tempo analysis (see below)
backend/av_craft_cli.py         Its command-line entry point
backend/lyric_scene_pipeline.py  Separate tool: correlates lyrics against scenes from an av_craft report (see below)
backend/lyric_scene_cli.py      Its command-line entry point
```

`pipeline.py` holds both the YouTube-specific ingestion (oEmbed metadata,
`youtube-transcript-api`) and the source-agnostic pieces every extractor
shares: the category/domain taxonomy, the LLM extraction prompt, quote
verification, cross-chunk dedupe, and QA scoring. `article_pipeline.py`
imports those shared pieces rather than duplicating them, so YouTube and
article reports use identical principle labeling. `dispatch.py` is the one
entry point both `cli.py` and `server.py` call -- it looks at each URL,
picks the right pipeline, and returns the same overall report shape either
way (see "Multi-source reports" below).

Flow for each submitted URL:

1. Detect source type: a YouTube URL routes to `pipeline.py`; any other
   `http(s)://` URL routes to `article_pipeline.py`.
2. Fetch public metadata (YouTube: oEmbed title/channel/thumbnail, no API
   key needed. Articles: page title/author/site name via `trafilatura`).
3. Fetch the actual content: YouTube's official caption/transcript track
   via `youtube-transcript-api`, or the article's own readable text via
   `trafilatura` (which strips nav/ads/boilerplate) -- no video/audio
   download, no login, no paywall bypass, in either case.
4. Split the content into chunks and send each chunk to an LLM (OpenAI
   Chat Completions, `OPENAI_API_KEY` required) asking it to pull out
   every principle/law/theory/framework/mental model/heuristic in that
   chunk, tagged with categories and domains, with a supporting quote
   copied from the source text.
5. Every returned quote is automatically checked against the source chunk
   text; quotes that do not match are flagged `unverified` rather than
   silently trusted.
6. Duplicate principles across chunks are merged (unioning any domains
   and aliases found in each duplicate sighting), an overall summary is
   generated, and the result is returned as one JSON report per URL with
   QA gates and a Truth Status block.

## Multi-source reports

Every report carries `source_type` (`"youtube_video"` or `"article"`,
more to come -- books and audio/podcasts are planned next). The two
current shapes differ only in their source-specific metadata key and
status field name:

| | YouTube | Article |
|---|---|---|
| metadata key | `video` (`video_id`, `title`, `channel`, `thumbnail_url`) | `article` (`title`, `author`, `site_name`) |
| status field | `transcript_status` / `transcript_error` | `content_status` / `content_error` |
| `approx_timestamp` on each principle | `"04:12"` style | `""` (articles have no timeline) |

Everything else -- `principles`, `principle_count`, `summary`,
`risk_flags`, `qa_gates`, `truth_status`, `next_3_plus_1`,
`manifest_hash_sha256` -- is identical, so downstream tooling (the CLI,
the web console, and `principles-kb`'s ingestion tool) can branch on
`source_type` once and otherwise treat every report the same way.

## Principle labeling

Every extracted principle carries, in addition to `name`/`description`/
`application`/`quote`:

- `category` -- one of `law`, `principle`, `theory`, `framework`,
  `mental_model`, `heuristic`, `rule_of_thumb`, `key_quote`.
- `domains` -- 1-3 topic tags chosen by the LLM from a fixed controlled
  vocabulary (`DOMAIN_TAGS` in `backend/pipeline.py`, e.g.
  `productivity-time-management`, `business-strategy`, `psychology-behavior`,
  `decision-making-cognition`, `finance-investing`...), kept in sync with
  `schema/domains.json` in the companion `principles-kb` repo so labels
  line up for cross-project querying.
- `aliases` -- other names the same principle is commonly known by (e.g.
  "80/20 Rule" as an alias of "Pareto Principle"), unioned across every
  chunk/source it's seen in.

This category+domain+alias labeling is what makes reports from this
pipeline directly ingestible into a categorized knowledge base (see
`principles-kb`) instead of just a flat list per source. That knowledge
base is also where cross-source consolidation happens: when the same
idea shows up under different names across several videos/articles, or
when enough related principles accumulate to suggest a genuinely new
higher-order pattern, that reconciliation and synthesis work lives in
`principles-kb`'s ingestion tool, not here -- this pipeline's job stops at
producing one clean, well-labeled report per source.

## Audiovisual craft analysis (av_craft_pipeline.py) -- a separate tool with a different Truth Boundary

Everything above only ever reads text (captions/transcripts, article
HTML). That's fine for a talking-head video or a written piece, but it
is fundamentally blind to cinematography, editing, color grading,
lighting, costume/set design, visual effects, choreography, and
tempo/rhythm -- none of that exists in a caption track. `av_craft_pipeline.py`
and its CLI (`av_craft_cli.py`) exist specifically to analyze that, and
they work differently on purpose:

- **It temporarily downloads the video** (via `yt-dlp`, moderate quality)
  strictly for local frame sampling (via `ffmpeg`) and audio-signal
  analysis (via `librosa`). The downloaded video, extracted frames, and
  extracted audio are **deleted immediately after the report is built**
  (see the `finally` block in `analyze_url`) -- nothing is stored,
  uploaded, redistributed, or included in the output report itself. This
  is a deliberate, narrow exception to the "never downloads video/audio"
  rule the rest of this console follows, made because there is no way to
  see cinematography or measure tempo from text alone. You are
  responsible for ensuring your use complies with the source platform's
  terms of service and applicable law for your situation -- this is built
  for personal, transient, non-commercial analysis, not for keeping or
  redistributing the source video.
- **Two clearly separated kinds of output**: `audio_analysis` (tempo/BPM,
  duration, beat count, energy) is **measured** via real digital signal
  processing (`librosa.beat.beat_track`, RMS energy) -- not an LLM guess.
  `craft_elements` (cinematography, editing, color grading, lighting, set/
  costume design, visual effects, choreography, narrative devices) is
  **inferred** by a vision-capable LLM (`gpt-4o-mini` by default) looking
  at sampled still frames -- qualitative, and only as good as what's
  visible in the frames actually sampled at the chosen interval. The
  report's `truth_status` block keeps these two apart explicitly.
- **Separate category/domain taxonomy**: `CRAFT_CATEGORIES` (`cinematography`,
  `editing`, `color_grading`, `lighting`, `set_design`, `costume_design`,
  `visual_effects`, `choreography`, `narrative_device`, `sound_design`,
  `music_production`) and `CRAFT_DOMAIN_TAGS` are intentionally distinct
  from the law/principle/theory taxonomy above -- craft technique isn't a
  "principle" in that sense, and forcing it into the same schema would
  blur two very different kinds of claims. Not yet wired into
  `principles-kb`; that would need its own schema extension there first.

Run it:

```bash
pip install yt-dlp librosa openai
# ffmpeg must also be installed and on PATH (not pip-installable)
export OPENAI_API_KEY=sk-...
python3 av_craft_cli.py "https://youtu.be/VIDEO_ID"
python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --frame-interval 4 --max-frames 60  # denser sampling for fast cuts
python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --out-dir reports/
```

Known limits: only the sampled frames are seen (a coarse interval can
miss fast cuts/transitions between samples -- lower `--frame-interval`
for fast-paced editing); tempo/BPM detection is algorithmic and not
infallible on complex mixes; the vision LLM describes what's visible in
low-detail frame previews (`detail: "low"`), not full-resolution frame
analysis, to keep cost/latency reasonable.

## Lyric-scene correlation (lyric_scene_pipeline.py)

A "making of" commentary video explains *why* a creative choice was
made; this tool answers a related but different question: *what is the
song actually saying at the moment a given visual scene happens?* It
reads the video's real caption track (lyrics + timestamps -- no
video/audio download) and cross-references it against an existing
`av_craft_pipeline.py` report's scenes (matched by timestamp overlap),
then asks an LLM to describe the thematic/emotional relationship --
literalizing the lyric, contrasting with it, using metaphor, or (often,
for instrumental passages) no meaningful connection at all, which it's
explicitly told to say plainly rather than invent.

Run `av_craft_cli.py` first to produce the scene data this needs:

```bash
python3 av_craft_cli.py "https://youtu.be/VIDEO_ID" --out-dir reports/
python3 lyric_scene_cli.py "https://youtu.be/VIDEO_ID" --craft-report reports/av_craft_VIDEOID.json --out-dir reports/
```

Requires `OPENAI_API_KEY` for the correlation commentary; the lyric/
timestamp data itself needs no API key, only `youtube-transcript-api`
(already a dependency). The `--craft-report` must be for the *same*
video (checked by `video_id`) -- a mismatched report is rejected rather
than silently correlating the wrong video's lyrics against the wrong
video's scenes.

Known limits: correlation quality depends entirely on caption accuracy
(auto-generated captions can mis-transcribe lyrics); a scene with no
lyric segment overlapping its timestamp range is skipped, not guessed
at; this reads captions only, so it doesn't distinguish sung lyrics from
spoken interludes or ad-libs beyond what the caption track itself says.

## Truth Boundary (pipeline.py / article_pipeline.py / dispatch.py / cli.py / server.py)

This pipeline never downloads video or audio files, never logs in, and
never bypasses YouTube's or any other site's terms of service or
paywalls. For YouTube it reads only two public endpoints: the oEmbed
metadata endpoint and the official caption/transcript track YouTube
already serves for the video. For articles/webpages it reads only the
page's own public HTML, the same thing a browser would fetch. Auto-
generated captions can contain transcription errors, article extraction
can occasionally include junk on unusual page layouts, and the LLM's
categorization/phrasing is inferred, not verified fact -- named laws and
theories should be checked against a primary source before you rely on
or republish them.

## Run it

### Easiest: command line

No server, no browser, one command. Only needs `requests`,
`youtube-transcript-api`, `trafilatura`, and `openai` (skip
`fastapi`/`uvicorn` entirely):

```bash
pip install requests youtube-transcript-api trafilatura openai
export OPENAI_API_KEY=sk-...          # required for extraction/summary
cd "APEX/03_APPLICATION/consoles/youtube-principles/v0.1/backend"
python3 cli.py "https://www.youtube.com/watch?v=..." "https://example.com/some-article"
```

Mix YouTube and article URLs freely in one call -- each is routed
automatically. Other ways to feed it URLs:

```bash
python3 cli.py --file urls.txt             # one URL per line, any mix of source types
cat urls.txt | python3 cli.py              # via stdin
python3 cli.py URL --out-dir reports/      # also save one JSON report per URL
python3 cli.py URL --json                  # print raw JSON instead of formatted text
```

### Alternative: web page

If you'd rather paste URLs into a browser page than a terminal:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # required for extraction/summary
uvicorn backend.server:app --reload --app-dir "APEX/03_APPLICATION/consoles/youtube-principles/v0.1"
```

Then open http://127.0.0.1:8000/ and paste URLs, one per line, any mix of
YouTube and article/webpage links.

In either form, without `OPENAI_API_KEY` set, metadata/content fetching
still works, but each report will carry an `llm_extraction_error` /
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
  `disabled`/`unavailable` transcript status and no principles. Articles
  behind a paywall, gated behind login, or rendered entirely by
  JavaScript return an analogous `unavailable` content status rather
  than a guessed/partial extraction.
- Long videos/articles are processed as multiple sequential LLM calls,
  which can take a while and cost more tokens; there is no caching yet.
- No YouTube Data API key is used or required -- only the public oEmbed
  endpoint, so video metadata is limited to title/channel/thumbnail.
- Requests are processed sequentially, one URL at a time.
- Books and audio/podcasts are not yet supported source types (books
  need a user-supplied file; audio needs a transcription step like
  Whisper) -- planned next, using the same shared extraction/labeling
  helpers in `pipeline.py`.
