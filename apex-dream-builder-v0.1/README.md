# APEX Dream Builder v0.1

## First independently testable release

This release implements only **Step 1: Dream Capture & Clarity Engine** from the supplied APEX Dream Builder vision.

### Operational now

- Mobile-first interface designed for iPhone
- Text capture
- Voice capture when the browser supports Web Speech; iPhone Dictation remains the fallback
- Photo or screenshot selection with user-supplied meaning
- Brain-dump capture
- One-question-at-a-time clarification
- Dream Card generation
- Clarity score with a transparent deterministic method
- Local-device persistence using `localStorage`
- Native share sheet or clipboard fallback
- Installable PWA behavior when served over localhost or HTTPS
- Offline caching after the first successful load

### Intentionally not claimed

- No external research
- No hidden AI API
- No autonomous deployment
- No real-world outreach
- No background server orchestration
- No proof that later Dream Builder modules are implemented

The UI labels the generated result **LOCAL · USER-GROUNDED** to preserve the truth boundary.

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

Your computer firewall may need to allow Node.js on private networks.

## Files

- `index.html` — app structure
- `styles.css` — mobile visual system
- `core.js` — deterministic clarity engine
- `app.js` — user flow, persistence, voice, image preview, share
- `manifest.json` — PWA metadata
- `service-worker.js` — offline cache
- `server.js` — dependency-free local server
- `tests/smoke.test.js` — repeatable smoke tests

## Next bite-size release

**v0.2 — Dream Analysis & Intelligence Core**

It should consume the saved Dream Card and add:
- purpose and impact
- feasibility
- resources
- time horizon
- risk and dependency discovery
- evidence-aware Dream Score

It should not be built until v0.1 is tested on the actual iPhone workflow.
