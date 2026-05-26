# 03 APEX Application Registry

This registry consolidates all current APEX-related application code into the APEX repository layer.

## Canonical Rule

All APEX-related code must be discoverable from this folder, even when the live prototype source temporarily remains in its original root-level folder to avoid breaking hosted URLs.

## Active Application Inventory

| ID | Application | Current Source Path | Canonical APEX Category | Status | Purpose |
|---|---|---|---|---|---|
| APP-001 | APEX Meta Studio Console | `apex-meta-studio-console/` | `03_APPLICATION/consoles/meta-studio` | Prototype-live | Full visible cockpit for APEX modules |
| APP-002 | APEX Meta Studio Self-Test | `apex-meta-studio-console/tests/` | `07_TESTING/browser-self-tests` | Prototype-live | Runtime verification for browser basics |
| APP-003 | APEX Python Intent Console v0.1 | `apex-python-intent-console/` | `03_APPLICATION/consoles/python-intent` | Superseded by v0.2 | Converts text/chat into APEX Python scaffolds |
| APP-004 | APEX Python Intent Console v0.2 | `apex-python-intent-console-v02/` | `03_APPLICATION/consoles/python-intent` | Active prototype | Adds video/YouTube/media routing and QA score cap |
| APP-005 | APEX RightsChain Manifest Builder | `apex-rightschain-manifest-builder/` | `05_GOVERNANCE/rightschain` | Prototype-live | Provenance, attribution, source, license, and release records |
| APP-006 | APEX Mobile Python Console v1.6.1 | `apex-mobile-python-console-v161/` | `03_APPLICATION/consoles/mobile-python` | Prototype-live | Mobile browser notebook / Python-style console |
| APP-007 | Content Scan Preflight | `tools/content-scan-preflight.mjs` | `04_ENGINEERING/tools` | Prototype QA tool | Static content/structure scan for browser apps |

## Migration Decision

Do not immediately delete or relocate root-level prototype folders because hosted RawGithack/jsDelivr URLs currently depend on those paths. Instead:

1. Document all source paths here.
2. Create APEX canonical documentation and registry entries.
3. Add source pointers and module summaries under APEX.
4. In the next engineering pass, create canonical APEX-hosted copies or redirects.
5. Only delete root-level originals after hosted URLs and tests prove the new paths work.

## Next Target Structure

```text
APEX/03_APPLICATION/consoles/
  meta-studio/
  python-intent/
  mobile-python/
APEX/05_GOVERNANCE/rightschain/
APEX/04_ENGINEERING/tools/
APEX/07_TESTING/browser-self-tests/
```

## Truth Status

| Claim | Status |
|---|---|
| APEX application inventory created | VERIFIED |
| All known current APEX prototype folders identified | VERIFIED from current project history and repo paths |
| Root-level code physically moved under APEX | NOT YET |
| Hosted URLs updated to APEX paths | NOT YET |
| Root-level originals safe to delete | UNKNOWN until tests pass |
