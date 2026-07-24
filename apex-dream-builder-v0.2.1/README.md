# APEX Dream Builder v0.2.1

## Second independently testable release

Continuation of v0.1, not a restart. This release adds only the first sub-increment of **v0.2 — Dream Analysis & Intelligence Core**:

```text
v0.2.1 — Analysis Data Contract + Deterministic Local Analysis
```

See [`ANALYSIS_DATA_CONTRACT.md`](./ANALYSIS_DATA_CONTRACT.md) for the full input/output schema.

### Operational now (inherited from v0.1, unmodified)

- Mobile-first interface designed for iPhone
- Text, voice, image, and brain-dump dream capture
- One-question-at-a-time clarification
- Dream Card generation with a transparent deterministic clarity score
- Local-device persistence, native share/clipboard, offline PWA caching

### New in v0.2.1

- "Analyze This Dream" flow on the Dream Card screen
- Five short grounding questions (time available, resources, skill/tool readiness, ownership plan, biggest risk) — each skippable
- Deterministic dimension scores (Feasibility, Readiness, Resources, Time, Ownership, Risk Awareness), each with a visible, plain-language score basis
- A barrier map that flags any dimension scoring 6 or below
- An evidence-required list: one concrete, real-world verification step per weak dimension
- An explicit unknowns list for any question left blank
- A recommended next step that targets the single worst barrier
- Local save (extends the same `localStorage` record used by v0.1) and native share/clipboard export

### Intentionally not claimed

- No AI API call and no external research feed the analysis — every score is computed from the words you typed
- No proof that later Dream Builder modules (Blueprint, Coach, Execution, etc.) are implemented
- No iPhone installation or public deployment evidence beyond what v0.1 already established

The UI labels the generated analysis **LOCAL · DETERMINISTIC · USER-GROUNDED** to preserve the same truth boundary v0.1 established for the Dream Card.

## Run on Windows, macOS, or Linux

```bash
npm test
npm start
```

Open:

```text
http://localhost:8080
```

## Test from iPhone on the same Wi-Fi

1. Start the app with `npm start`.
2. Find the computer's local IP address.
3. On iPhone Safari, open `http://<computer-ip>:8080`.
4. Use Safari Share → **Add to Home Screen**.

## Files

- `index.html` — app structure (v0.1 screens + new analysis screens)
- `styles.css` — mobile visual system
- `core.js` — deterministic clarity engine (unchanged from v0.1)
- `analysis.js` — new deterministic Dream Analysis engine
- `app.js` — user flow, persistence, voice, image preview, share, analysis flow
- `manifest.json` — PWA metadata
- `service-worker.js` — offline cache (now includes `analysis.js`)
- `server.js` — dependency-free local server
- `tests/smoke.test.js` — repeatable smoke tests for both the clarity engine and the analysis engine
- `ANALYSIS_DATA_CONTRACT.md` — input/output schema for the analysis engine

## Next bite-size release

The next sub-increment may add model-assisted analysis only after a privacy boundary, prompt contract, source evidence handling, cost controls, fallback behavior, and tests are defined — per the Genesis Seed. Until then, the next default increment continues **v0.2 — Dream Analysis & Intelligence Core** (readiness map depth, risk/dependency ledger, remaining analysis surface).
