(() => {
  "use strict";

  const STORAGE_KEY = "dreamDrawValueCompassRecords.v0.1";
  const form = document.getElementById("dreamForm");
  const emptyState = document.getElementById("emptyState");
  const resultContent = document.getElementById("resultContent");
  let activeRecord = null;

  const principles = {
    Direction: {
      guide: ["Nola", "Begin", "🧭"],
      card: "Direction is not more motion. It is one true step taken on purpose.",
      bridge: "Reduce the noise until the next useful move becomes visible.",
      metaphor: "A fog-covered bridge reveals one illuminated plank directly ahead; the horizon remains present, but only the next crossing is required.",
      next: "Write one outcome that would prove you moved in the right direction, then complete the smallest action that makes it visible.",
      why: "You are describing uncertainty or drift; clarity has more value than expanding the task.",
      watch: "Do not confuse generating more options with making progress."
    },
    Correction: {
      guide: ["Rowan", "Break / Correct", "↺"],
      card: "A wrong turn is not your future. Refusing to correct it is.",
      bridge: "Use what failed as a map, not a verdict.",
      metaphor: "A compass needle rotates away from a storm-lit dead end and locks onto a safer, brighter route.",
      next: "Identify the single mismatch or error causing the most friction and repair that before adding new work.",
      why: "Correction creates leverage when the current route is producing repeated friction.",
      watch: "Do not build faster on top of an unresolved flaw."
    },
    Compounding: {
      guide: ["Sienna", "Build", "△"],
      card: "Small true work becomes visible when you protect the repetition.",
      bridge: "Progress may be quiet before it becomes undeniable.",
      metaphor: "Individual gold markers accumulate across a dark trail until they form a luminous pathway toward a distant summit.",
      next: "Choose one repeatable proof-producing action and log one completed repetition today.",
      why: "You appear to need momentum and visible evidence more than a new destination.",
      watch: "Do not abandon a sound path merely because its payoff is delayed."
    },
    Transition: {
      guide: ["Zara", "Explore", "✦"],
      card: "The future often begins where an old route stops answering your question.",
      bridge: "Explore without losing the truth that brought you here.",
      metaphor: "Two pathways meet at a bright threshold: one fading behind, one emerging across an open landscape.",
      next: "Create one bounded experiment that tests the new direction without requiring irreversible commitment.",
      why: "Transition is best navigated through a meaningful but reversible proof step.",
      watch: "Do not turn possibility into certainty before the experiment speaks."
    },
    Leverage: {
      guide: ["Mira", "Integrate", "∞"],
      card: "The strongest next move is often the one that makes future moves easier.",
      bridge: "Build the system that protects the meaning of the effort.",
      metaphor: "A central compass connects several small streams into one clear river of progress, each branch visibly governed.",
      next: "Build or document one reusable component that removes repeated effort from your path.",
      why: "Your goal points toward systems, scale, or automation; reusable structure may compound value.",
      watch: "Do not automate a process whose truth or safety boundaries are unclear."
    },
    Becoming: {
      guide: ["Mira", "Integrate", "◎"],
      card: "You become the direction you keep choosing when no one is watching.",
      bridge: "Let the next action express the person you intend to become.",
      metaphor: "A person stands before a calm illuminated horizon while a compass reflection aligns with their next footprint.",
      next: "Name one standard your future self would keep, then perform one observable act that honors it.",
      why: "Your dream concerns identity or purpose, so an aligned action matters more than a large task list.",
      watch: "Do not replace lived evidence with an idealized self-image."
    }
  };

  const horizonText = {
    today: ["now", "one completed move today"],
    days: ["short sprint", "one repeatable proof this cycle"],
    quarter: ["build arc", "one foundation that compounds"],
    years: ["life path", "one identity-aligned commitment"]
  };

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, c => ({
      "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    }[c]));
  }

  function records() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
    catch (_) { return []; }
  }

  function saveRecords(list) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    updateDashboard();
  }

  function keywordIncludes(text, words) {
    return words.some(w => text.includes(w));
  }

  function chooseMode(intake) {
    const t = `${intake.dream} ${intake.why} ${intake.state} ${intake.constraint}`.toLowerCase();
    if (keywordIncludes(t, ["mistake","failed","failure","wrong","repair","broken","fix","error"])) return "Correction";
    if (keywordIncludes(t, ["automate","system","scale","reuse","platform","app","workflow","github","tool"])) return "Leverage";
    if (keywordIncludes(t, ["stuck","confused","overwhelmed","unclear","lost","fog","direction"])) return "Direction";
    if (keywordIncludes(t, ["new","begin","restart","change","transition","explore","different"])) return "Transition";
    if (keywordIncludes(t, ["slow","plateau","repeat","habit","consistent","progress","practice"])) return "Compounding";
    return "Becoming";
  }

  function scoreDirection(intake, mode) {
    let score = 62;
    if (intake.dream.length > 35) score += 7;
    if (intake.why.length > 20) score += 5;
    if (intake.state.length > 15) score += 5;
    if (intake.capability.length > 4) score += 4;
    if (intake.constraint.length > 4) score += 5;
    if (intake.energy === "strong") score += 3;
    if (intake.challenge === "balanced") score += 2;
    if (mode === "Leverage" && intake.capability.length < 5) score -= 4;
    return Math.max(40, Math.min(91, score));
  }

  function buildHorizonPath(intake, mode) {
    const cfg = principles[mode];
    const dreamShort = intake.dream.length > 54 ? `${intake.dream.slice(0, 54)}…` : intake.dream;
    return [
      ["H0", "Current", intake.state || "A direction is named; baseline needs capture."],
      ["H1", "Next", cfg.next],
      ["H2", "Stretch", "Complete the same move with less guidance or a stronger success condition."],
      ["H3", "Transfer", "Apply the skill or insight in a different situation and record what holds."],
      ["H4", "Contribution", "Turn the improvement into value for a person, project, or community."],
      ["H5", "Vision", dreamShort]
    ];
  }

  function buildMotion(mode) {
    const scenes = {
      Direction: ["Fog and scattered light slowly reveal a single compass point.", "Camera follows one lit bridge plank as surrounding noise fades.", "Horizon opens; the chosen step glows without forcing movement."],
      Correction: ["Storm and wrong-turn marker enter frame; compass trembles.", "Needle rotates; abandoned path dims while safe line appears.", "One corrected footprint lands; the route stabilizes."],
      Compounding: ["One small gold marker appears on a dark path.", "Repeated markers connect into a visible climbing trail.", "Wide reveal shows the accumulated pathway reaching higher ground."],
      Transition: ["Old route softens behind a figure at a threshold.", "Two possible paths form; one reversible experiment illuminates.", "The new direction opens while the origin remains respected."],
      Leverage: ["Many disconnected tasks pulse across a dark grid.", "A central compass links them into a reusable system.", "The system clears space for purposeful forward movement."],
      Becoming: ["A still figure faces a distant dawn and quiet compass reflection.", "One footprint aligns with the compass and grows brighter.", "The horizon reflects the chosen standard, not an imposed destiny."]
    };
    return scenes[mode];
  }

  function buildPrompt(intake, mode) {
    const cfg = principles[mode];
    return `Premium vertical 9:16 Dream Draw / Value Compass guidance card. Midnight navy and warm-gold cinematic palette, elegant minimal compass interface, ${cfg.metaphor} Human-centred, calm, truthful and agency-preserving. Large readable headline: “${cfg.card}” Supporting line: “${cfg.bridge}” No clutter, no manipulative imagery, no false certainty, no mystical claims; sophisticated app-style footer and subtle proof-status mark: PROPOSED STEP.`;
  }

  function createRecord(intake) {
    const mode = chooseMode(intake);
    const cfg = principles[mode];
    const score = scoreDirection(intake, mode);
    const created = new Date().toISOString();
    const horizon = horizonText[intake.horizon];
    return {
      record_id: `DD-${Date.now()}`,
      created_utc: created,
      app_version: "v0.1.0-DRAFT",
      engine: "🅾️♾️ Value Compass",
      truth_status: "PROTOTYPE_RECOMMENDATION_NOT_OUTCOME_PROOF",
      intake,
      result: {
        mode,
        guide: { name: cfg.guide[0], role: cfg.guide[1], icon: cfg.guide[2] },
        compass_value_design_score: score,
        reflection_title: `A ${horizon[0]} direction for your dream`,
        best_move: cfg.next,
        why_now: cfg.why,
        watch_out: cfg.watch,
        horizon_path: buildHorizonPath(intake, mode),
        card: {
          headline: cfg.card,
          supporting_bridge: cfg.bridge,
          metaphor: cfg.metaphor,
          image_prompt: buildPrompt(intake, mode),
          motion_segments: buildMotion(mode)
        }
      },
      feedback: null
    };
  }

  function render(record) {
    activeRecord = record;
    emptyState.classList.add("hidden");
    resultContent.classList.remove("hidden");
    const r = record.result;
    document.getElementById("reflectionTitle").textContent = r.reflection_title;
    document.getElementById("score").textContent = `${r.compass_value_design_score}/100`;
    document.getElementById("bestMove").textContent = r.best_move;
    document.getElementById("whyNow").textContent = r.why_now;
    document.getElementById("watchOut").textContent = r.watch_out;
    document.getElementById("guideIcon").textContent = r.guide.icon;
    document.getElementById("guide").textContent = r.guide.name;
    document.getElementById("guideRole").textContent = r.guide.role;
    document.getElementById("mode").textContent = r.mode.toUpperCase();
    document.getElementById("headline").textContent = r.card.headline;
    document.getElementById("bridgeLine").textContent = r.card.supporting_bridge;
    document.getElementById("metaphor").textContent = r.card.metaphor;
    document.getElementById("imagePrompt").textContent = r.card.image_prompt;
    const horizons = document.getElementById("horizons");
    horizons.innerHTML = r.horizon_path.map((h, idx) => `<div class="horizon ${idx === 1 ? "active" : ""}"><span class="tag">${escapeHtml(h[0])} · ${escapeHtml(h[1])}</span><p>${escapeHtml(h[2])}</p></div>`).join("");
    const motion = document.getElementById("motionSegments");
    motion.innerHTML = r.card.motion_segments.map((s, i) => `<li><strong>${i * 10}:00–${(i + 1) * 10}:00</strong> ${escapeHtml(s)}</li>`).join("");
    document.getElementById("feedbackStatus").textContent = record.feedback ? `Evidence recorded: ${record.feedback.signal.replace("_", " ")} at ${new Date(record.feedback.captured_utc).toLocaleString()}.` : "No outcome claim recorded. Your response becomes the first evidence signal.";
    resultContent.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function updateDashboard() {
    const list = records();
    const feedback = list.filter(r => r.feedback);
    document.getElementById("countDreams").textContent = list.length;
    document.getElementById("countFeedback").textContent = feedback.length;
    document.getElementById("countHelpful").textContent = feedback.filter(r => r.feedback.signal === "helped").length;
    document.getElementById("countRedirect").textContent = feedback.filter(r => r.feedback.signal === "reframe").length;
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    const intake = {
      dream: document.getElementById("dream").value.trim(),
      why: document.getElementById("why").value.trim(),
      horizon: document.getElementById("horizon").value,
      energy: document.getElementById("energy").value,
      state: document.getElementById("state").value.trim(),
      capability: document.getElementById("capability").value.trim(),
      constraint: document.getElementById("constraint").value.trim(),
      challenge: document.getElementById("challenge").value
    };
    const record = createRecord(intake);
    const list = records();
    list.push(record);
    saveRecords(list);
    render(record);
  });

  document.getElementById("demoBtn").addEventListener("click", () => {
    document.getElementById("dream").value = "Build Dream Draw into a usable application that turns my vision into a real guided next step.";
    document.getElementById("why").value = "I want the vision to become a real tool without losing truth, direction, or human control.";
    document.getElementById("horizon").value = "quarter";
    document.getElementById("energy").value = "strong";
    document.getElementById("state").value = "The product vision is strong, but the first runnable application needs to be proven.";
    document.getElementById("capability").value = "Define product goals and review generated prototypes";
    document.getElementById("constraint").value = "Need a simple testable first version";
    document.getElementById("challenge").value = "balanced";
  });

  document.querySelectorAll("[data-feedback]").forEach(button => {
    button.addEventListener("click", () => {
      if (!activeRecord) return;
      const list = records();
      const current = list.find(r => r.record_id === activeRecord.record_id);
      if (!current) return;
      current.feedback = { signal: button.dataset.feedback, captured_utc: new Date().toISOString(), interpretation: "USER_REPORTED_SIGNAL_NOT_VALIDATED_OUTCOME" };
      activeRecord = current;
      saveRecords(list);
      render(current);
    });
  });

  document.getElementById("exportBtn").addEventListener("click", () => {
    const payload = { export_type: "DREAM_DRAW_LOCAL_EVIDENCE_EXPORT", exported_utc: new Date().toISOString(), truth_boundary: "User-entered prototype records and feedback signals; not validated outcomes.", records: records() };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type:"application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `dream_draw_evidence_${new Date().toISOString().slice(0,10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  });

  document.getElementById("resetBtn").addEventListener("click", () => {
    if (!window.confirm("Clear all local Dream Draw records stored in this browser?")) return;
    localStorage.removeItem(STORAGE_KEY);
    activeRecord = null;
    resultContent.classList.add("hidden");
    emptyState.classList.remove("hidden");
    updateDashboard();
  });

  updateDashboard();
})();
