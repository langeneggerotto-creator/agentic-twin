(() => {
  "use strict";
  const RECORD_KEY = "dreamDrawValueCompassRecords.v0.1";
  const CAPSULE_KEY = "dreamDrawContextCapsules.v0.2";
  let currentCapsule = null;
  const KERNEL = {
    purpose: "Help the user move from a chosen dream toward one meaningful next action without losing truth or agency.",
    rules: [
      "Guide without coercing.",
      "Separate proposed recommendation from validated outcome.",
      "Preserve privacy, safety, human override and evidence boundaries.",
      "Return Best move, Why now, Watch out and one evidence action."
    ]
  };
  function loadList(key) {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); }
    catch (_) { return []; }
  }
  function proxyTokens(text) { return Math.ceil(String(text || "").length / 4); }
  function trimValue(value, max) {
    const text = String(value || "").trim().replace(/\s+/g, " ");
    return text.length > max ? `${text.slice(0, max)}…` : text;
  }
  function latestRecord() {
    const records = loadList(RECORD_KEY);
    return records.length ? records[records.length - 1] : null;
  }
  function makeCapsule(record, extraContext) {
    if (!record) throw new Error("Create a Dream Draw result first.");
    const intake = record.intake || {};
    const result = record.result || {};
    const fullPayload = JSON.stringify({ kernel: KERNEL, record, extra_context: extraContext }, null, 2);
    const delta = {
      task: "Improve or evaluate the next Value Compass recommendation for this dream.",
      dream: trimValue(intake.dream, 180),
      why: trimValue(intake.why, 120),
      state: trimValue(intake.state, 140),
      capability: trimValue(intake.capability, 80),
      constraint: trimValue(intake.constraint, 80),
      horizon: intake.horizon || "unknown",
      challenge: intake.challenge || "unknown",
      prior_mode: result.mode || "unknown",
      prior_step: trimValue(result.best_move, 170),
      relevant_added_context: trimValue(extraContext, 280)
    };
    const capsule = {
      capsule_id: `CAP-${Date.now()}`,
      created_utc: new Date().toISOString(),
      module: "Dream Draw / 🅾️♾️ Value Compass",
      version: "v0.2.0-PROTOTYPE",
      truth_status: "CONTEXT_COMPRESSION_PROTOTYPE_NOT_TOKEN_OR_QUALITY_VALIDATED",
      kernel: KERNEL,
      delta,
      retrieval: [{ pointer: record.record_id, why_needed: "Current record may change the next decision." }],
      held_or_excluded: [
        "Unrelated history not supplied to the active decision.",
        "Decorative narrative not required for the next action.",
        "No validated outcome claim retained because none exists."
      ],
      metric: {
        measurement_type: "CHARACTER_BASED_TOKEN_PROXY_NOT_EXACT_MODEL_TOKEN_COUNT",
        full_prompt_proxy_tokens: proxyTokens(fullPayload),
        capsule_prompt_proxy_tokens: 0,
        estimated_reduction_percent: 0
      },
      optimized_prompt: "",
      reconstruction_note: "Original local record remains in browser storage; this capsule preserves its pointer."
    };
    capsule.optimized_prompt = [
      "[DREAM DRAW CONTEXT CAPSULE]",
      `Truth status: ${capsule.truth_status}`,
      `Purpose: ${KERNEL.purpose}`,
      `Rules: ${KERNEL.rules.join(" | ")}`,
      `Task: ${delta.task}`,
      `Dream: ${delta.dream}`,
      `Why: ${delta.why || "not supplied"}`,
      `Current state: ${delta.state || "not supplied"}`,
      `Capability: ${delta.capability || "not supplied"}`,
      `Constraint: ${delta.constraint || "not supplied"}`,
      `Horizon / challenge: ${delta.horizon} / ${delta.challenge}`,
      `Prior mode / step: ${delta.prior_mode} / ${delta.prior_step}`,
      delta.relevant_added_context ? `Relevant added context: ${delta.relevant_added_context}` : "",
      "Return only: Best move; Why now; Watch out; Next evidence action; Uncertainty or gate."
    ].filter(Boolean).join("\n");
    capsule.metric.capsule_prompt_proxy_tokens = proxyTokens(capsule.optimized_prompt);
    capsule.metric.estimated_reduction_percent = Math.max(0, Math.round((1 - capsule.metric.capsule_prompt_proxy_tokens / capsule.metric.full_prompt_proxy_tokens) * 100));
    return capsule;
  }
  function renderCapsule(capsule) {
    document.getElementById("capsuleOutput").classList.remove("hidden");
    document.getElementById("fullTokenProxy").textContent = `≈ ${capsule.metric.full_prompt_proxy_tokens}`;
    document.getElementById("capsuleTokenProxy").textContent = `≈ ${capsule.metric.capsule_prompt_proxy_tokens}`;
    document.getElementById("capsuleReduction").textContent = `${capsule.metric.estimated_reduction_percent}%`;
    document.getElementById("kernelRetained").textContent = capsule.kernel.rules.join(" ");
    document.getElementById("deltaRetained").textContent = `${capsule.delta.dream} ${capsule.delta.constraint ? "Constraint: " + capsule.delta.constraint : ""}`;
    document.getElementById("excludedContext").textContent = capsule.held_or_excluded.join(" ");
    document.getElementById("optimizedPrompt").textContent = capsule.optimized_prompt;
  }
  document.getElementById("buildCapsuleBtn").addEventListener("click", () => {
    try {
      currentCapsule = makeCapsule(latestRecord(), document.getElementById("capsuleExtra").value);
      const capsules = loadList(CAPSULE_KEY);
      capsules.push(currentCapsule);
      localStorage.setItem(CAPSULE_KEY, JSON.stringify(capsules));
      renderCapsule(currentCapsule);
    } catch (error) { window.alert(error.message); }
  });
  document.getElementById("copyCapsuleBtn").addEventListener("click", async () => {
    if (!currentCapsule) return window.alert("Generate a Context Capsule first.");
    try { await navigator.clipboard.writeText(currentCapsule.optimized_prompt); }
    catch (_) { window.prompt("Copy this optimized prompt:", currentCapsule.optimized_prompt); }
  });
  document.getElementById("exportCapsuleBtn").addEventListener("click", () => {
    if (!currentCapsule) return window.alert("Generate a Context Capsule first.");
    const blob = new Blob([JSON.stringify(currentCapsule, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `dream_draw_context_capsule_${new Date().toISOString().slice(0,10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  });
})();
