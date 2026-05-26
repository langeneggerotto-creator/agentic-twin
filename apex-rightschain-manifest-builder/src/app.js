const q = (id) => document.getElementById(id);
const VERSION = "0.1.0";
const STORAGE_KEY = "apex_rights_ledger_builder_v01";

function setPill(id, text, cls) {
  const el = q(id);
  el.textContent = text;
  el.className = "pill " + cls;
}

function storageWorks() {
  try {
    const key = "apex_storage_probe";
    localStorage.setItem(key, "ok");
    const ok = localStorage.getItem(key) === "ok";
    localStorage.removeItem(key);
    return ok;
  } catch (_) {
    return false;
  }
}

function rows(text, fields) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split("|").map((p) => p.trim());
      const item = {};
      fields.forEach((field, i) => item[field] = parts[i] || "");
      return item;
    });
}

function percentTotal(list) {
  return list.reduce((sum, item) => sum + Number(item.percent || 0), 0);
}

function artifactId() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return "APEX-ART-" + yyyy + mm + dd + "-" + Math.random().toString(36).slice(2, 8).toUpperCase();
}

function buildManifest() {
  const contributors = rows(q("contributors").value, ["name", "role", "percent"]);
  const sources = rows(q("sources").value, ["type", "description", "permission_status"]);
  const flags = {
    private_or_sensitive: q("flagPrivate").checked,
    unclear_source_permission: q("flagSource").checked,
    claims_need_expert_review: q("flagClaims").checked,
    real_person_likeness: q("flagLikeness").checked,
    intended_public_release: q("flagPublic").checked,
    public_record_requested: q("flagToken").checked
  };
  const recommendation = decide(flags, q("recordPreference").value);
  return {
    manifest_type: "APEX_RIGHTS_LEDGER_MANIFEST",
    manifest_version: VERSION,
    created_utc: new Date().toISOString(),
    artifact: {
      artifact_id: artifactId(),
      title: q("title").value.trim(),
      artifact_type: q("artifactType").value,
      description: q("description").value.trim(),
      status: q("status").value
    },
    owner: {
      vision_owner: q("owner").value.trim(),
      ownership_note: "Human authorship, permissions, and contractual rights must be verified before public release."
    },
    credit_ledger: {
      contributors,
      total_percent: percentTotal(contributors),
      total_percent_ok: percentTotal(contributors) === 100
    },
    source_ledger: {
      sources,
      principle: "Extract principles and permissions; do not copy protected expression without permission."
    },
    license_intent: {
      default_use: q("defaultUse").value,
      derivatives: q("derivatives").value,
      attribution_required: true,
      legal_review_required_for_public_or_commercial_use: true
    },
    review_flags: flags,
    decision: recommendation,
    proof: {
      manifest_hash_sha256: "pending_hash_button",
      proof_status: "manifest_created_not_yet_hashed"
    },
    truth_boundary: "This record supports provenance and review. It is not legal advice, copyright registration, or enforcement."
  };
}

function decide(flags, preference) {
  const blockers = [];
  if (flags.unclear_source_permission) blockers.push("unclear_source_permission");
  if (flags.claims_need_expert_review) blockers.push("claims_need_expert_review");
  if (flags.real_person_likeness) blockers.push("likeness_or_publicity_review_required");
  if ((flags.private_or_sensitive || flags.real_person_likeness) && flags.public_record_requested) blockers.push("do_not_place_sensitive_or_likeness_data_in_public_record");

  let release_status = "private_ok";
  if (blockers.length) release_status = "hold_for_review";
  else if (flags.intended_public_release) release_status = "release_candidate_after_human_review";

  let record_path = "private_ledger";
  if (preference !== "auto_recommend") record_path = preference;
  else if (flags.private_or_sensitive) record_path = "private_ledger";
  else if (flags.intended_public_release && !blockers.length) record_path = "hash_timestamp_only";

  return {
    release_status,
    record_path,
    blockers,
    next_action: blockers.length ? "resolve blockers before public release" : "hash the manifest and export the record"
  };
}

function renderManifest(manifest) {
  q("manifestOut").textContent = JSON.stringify(manifest, null, 2);
  q("decisionOut").textContent = JSON.stringify(manifest.decision, null, 2);
  setPill("releasePill", "Status: " + manifest.decision.release_status, manifest.decision.blockers.length ? "bad" : "good");
  saveDraft();
}

async function sha256(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function hashCurrent() {
  const raw = q("manifestOut").textContent;
  if (!raw || raw.startsWith("Press")) {
    renderManifest(buildManifest());
  }
  const manifest = JSON.parse(q("manifestOut").textContent);
  manifest.proof.manifest_hash_sha256 = await sha256(JSON.stringify(manifest, null, 2));
  manifest.proof.proof_status = "manifest_hashed_in_browser";
  q("manifestOut").textContent = JSON.stringify(manifest, null, 2);
  setPill("hashPill", "Hash: ready", "good");
  q("decisionOut").textContent = JSON.stringify({ hash: manifest.proof.manifest_hash_sha256, decision: manifest.decision }, null, 2);
}

function copyManifest() {
  const text = q("manifestOut").textContent;
  navigator.clipboard.writeText(text).then(() => q("decisionOut").textContent += "\n\nCopied manifest to clipboard.").catch(() => q("decisionOut").textContent += "\n\nCopy failed. Select the manifest manually.");
}

function downloadManifest() {
  const text = q("manifestOut").textContent;
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "apex-rights-ledger-manifest.json";
  a.click();
  URL.revokeObjectURL(url);
}

function saveDraft() {
  if (!storageWorks()) return;
  const state = {
    title: q("title").value,
    type: q("artifactType").value,
    description: q("description").value,
    owner: q("owner").value,
    status: q("status").value,
    contributors: q("contributors").value,
    sources: q("sources").value
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadDraft() {
  if (!storageWorks()) return;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const state = JSON.parse(raw);
    q("title").value = state.title || q("title").value;
    q("artifactType").value = state.type || q("artifactType").value;
    q("description").value = state.description || q("description").value;
    q("owner").value = state.owner || q("owner").value;
    q("status").value = state.status || q("status").value;
    q("contributors").value = state.contributors || q("contributors").value;
    q("sources").value = state.sources || q("sources").value;
  } catch (_) {}
}

function resetExample() {
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
}

async function selfTest() {
  const m = buildManifest();
  const ok = m.credit_ledger.total_percent_ok && !!m.artifact.title && m.source_ledger.sources.length > 0;
  const hash = await sha256(JSON.stringify(m));
  q("decisionOut").textContent = JSON.stringify({ self_test: ok ? "PASS" : "FAIL", hash_available: !!hash, storage: storageWorks(), generated_manifest: true }, null, 2);
  setPill("releasePill", ok ? "Self-test: PASS" : "Self-test: FAIL", ok ? "good" : "bad");
}

function boot() {
  setPill("jsPill", "JavaScript: PASS", "good");
  setPill("storagePill", storageWorks() ? "Storage: PASS" : "Storage: blocked", storageWorks() ? "good" : "bad");
  loadDraft();
  renderManifest(buildManifest());
}

q("generateBtn").addEventListener("click", () => renderManifest(buildManifest()));
q("hashBtn").addEventListener("click", hashCurrent);
q("selfTestBtn").addEventListener("click", selfTest);
q("copyBtn").addEventListener("click", copyManifest);
q("downloadBtn").addEventListener("click", downloadManifest);
q("resetBtn").addEventListener("click", resetExample);
q("manifestForm").addEventListener("input", () => renderManifest(buildManifest()));
boot();
