(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.DreamCore = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function clean(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function sentence(value, fallback) {
    const text = clean(value);
    if (!text) return fallback;
    return /[.!?]$/.test(text) ? text : text + ".";
  }

  function normalizeDream(raw) {
    let dream = clean(raw);
    if (!dream) return "";
    dream = dream.replace(/^(i\s+)?(really\s+)?(want|would like|hope|dream)\s+to\s+/i, "");
    dream = dream.charAt(0).toLowerCase() + dream.slice(1);
    return dream.replace(/[.!?]+$/, "");
  }

  function calculateScore(input) {
    const fields = [
      clean(input.original),
      clean(input.audience),
      clean(input.outcome),
      clean(input.constraint),
      clean(input.evidence)
    ];

    let score = 4.6;
    fields.forEach(function (field, index) {
      if (!field) return;
      score += index === 0 ? Math.min(1.2, field.length / 120) : 0.8;
    });

    if (clean(input.original).length > 120) score += 0.25;
    return Math.max(4.6, Math.min(9.4, Math.round(score * 10) / 10));
  }

  function buildDreamCard(input) {
    const original = sentence(input.original, "A dream has not been described yet.");
    const normalized = normalizeDream(input.original) || "make this dream real";
    const audience = clean(input.audience) || "the people who would benefit most";
    const outcome = clean(input.outcome) || "create a meaningful and measurable improvement";
    const constraint = clean(input.constraint) || "available time, resources, and evidence";
    const evidence = clean(input.evidence) || "real people confirm the problem and value the proposed result";

    const statement =
      "Build a practical pathway to " + normalized +
      " for " + audience +
      ", so they can " + outcome.replace(/[.!?]+$/, "") +
      ", while respecting " + constraint.replace(/[.!?]+$/, "") + ".";

    const nextStep =
      "Speak with 3 people who match “" + audience.replace(/[.!?]+$/, "") +
      "” and ask them to describe the problem in their own words. Record the exact evidence before choosing a solution.";

    return {
      original: original,
      statement: statement,
      audience: sentence(audience, "Needs clarification."),
      outcome: sentence(outcome, "Needs clarification."),
      constraint: sentence(constraint, "Needs clarification."),
      evidence: sentence(evidence, "Needs clarification."),
      nextStep: nextStep,
      score: calculateScore(input),
      createdAt: new Date().toISOString(),
      evidenceLabel: "LOCAL · USER-GROUNDED"
    };
  }

  function validateDream(raw) {
    const value = clean(raw);
    if (!value) return { ok: false, message: "Describe the dream before continuing." };
    if (value.length < 18) return { ok: false, message: "Add a little more detail so the clarity engine has enough to work with." };
    return { ok: true, value: value };
  }

  function exportText(card) {
    return [
      "APEX DREAM CARD",
      "================",
      "",
      "Clear Dream Statement",
      card.statement,
      "",
      "Who It Is For",
      card.audience,
      "",
      "Desired Result",
      card.outcome,
      "",
      "Biggest Constraint",
      card.constraint,
      "",
      "Success Evidence",
      card.evidence,
      "",
      "Next Best Step",
      card.nextStep,
      "",
      "Clarity Score: " + card.score + " / 10",
      "Evidence Label: " + card.evidenceLabel
    ].join("\n");
  }

  return {
    clean: clean,
    validateDream: validateDream,
    buildDreamCard: buildDreamCard,
    calculateScore: calculateScore,
    exportText: exportText
  };
});
