# APEX Meta Studio Console v0.3

A single-file browser prototype for the APEX Meta Studio cockpit.

## Hosted console

Primary test URL:

```text
https://raw.githack.com/langeneggerotto-creator/agentic-twin/main/apex-meta-studio-console/index.html?v=0.3.2
```

Backup URL:

```text
https://cdn.jsdelivr.net/gh/langeneggerotto-creator/agentic-twin@main/apex-meta-studio-console/index.html?v=0.3.2
```

## Current capability set

- Dashboard command router
- Mini Python-style Code Lab
- File upload/intake lab
- Visual Wisdom Lab
- Media Factory
- Human State Studio
- StoryTruth Game Lab
- RightsChain manifest builder
- QA/Safety/Integrity Lab
- Roadmap / Next 3+1 planner
- Diagnostics panel

## Truth boundary

This is a visible working browser prototype. It is not yet:

- a full backend application
- a full Python IDE
- a secure production SaaS
- a legal-rights engine
- a blockchain/NFT deployment
- a medical or mental-health treatment tool

## Test flow

1. Open the primary test URL.
2. Confirm the dashboard loads.
3. Press **Run Full Demo**.
4. Open **Code Lab** and press **Run Current Cell**.
5. Open **QA Lab** and press **Run Console Self-Tests**.
6. Open **Diagnostics** and copy the report.

## Next engineering iteration

The next build should split the single-file prototype into modules:

```text
apex-meta-studio-console/
  index.html
  src/style.css
  src/app.js
  src/mini.js
  src/files.js
  src/rights.js
  src/qa.js
  src/media.js
  src/state.js
  tests/self-test.html
```

Stop rule: do not add more features until the hosted browser runtime and QA self-tests pass on desktop and iPhone.
