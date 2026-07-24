(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.DreamAnalysis = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function clean(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  const UNCERTAIN_PATTERN = /\b(not sure|no idea|don'?t know|unsure|unknown|none|nothing|n\/a|maybe)\b/i;

  // Deterministic 0-10 score for a free-text answer: rewards a concrete,
  // specific answer; penalizes emptiness or explicit uncertainty language.
  // This is the transparent basis shown to the user for every dimension.
  function scoreText(value, weight) {
    const text = clean(value);
    if (!text) {
      return { score: 0, basis: "No answer was provided." };
    }
    if (UNCERTAIN_PATTERN.test(text)) {
      return { score: 2, basis: "Answer indicates this is not yet known: “" + text + "”." };
    }
    const lengthPoints = Math.min(weight, (text.length / 60) * weight);
    const score = Math.max(3, Math.round(lengthPoints * 10) / 10);
    return { score: Math.min(10, score), basis: "Scored from the specificity of the answer: “" + text + "”." };
  }

  function scoreChoice(value, map, missingBasis) {
    const key = clean(value).toLowerCase();
    if (!key || !(key in map)) {
      return { score: 0, basis: missingBasis };
    }
    return map[key];
  }

  const READINESS_MAP = {
    yes: { score: 9, basis: "You reported the needed skills and tools are already in place." },
    partial: { score: 5, basis: "You reported partial readiness: some skills or tools are missing." },
    no: { score: 2, basis: "You reported the needed skills and tools are not yet in place." }
  };

  function buildDimensions(input) {
    const time = scoreText(input.timeAvailable, 8);
    const resources = scoreText(input.resources, 8);
    const readiness = scoreChoice(input.skillsReadiness, READINESS_MAP, "Skill and tool readiness was not answered.");
    const ownership = scoreText(input.ownershipPlan, 7);
    const risk = scoreText(input.biggestRisk, 6);

    // Feasibility is derived, not separately asked: the average of the
    // concrete inputs that determine whether the dream can actually be
    // attempted (time, resources, readiness).
    const feasibilityScore = Math.round(((time.score + resources.score + readiness.score) / 3) * 10) / 10;

    return {
      feasibility: {
        score: feasibilityScore,
        basis: "Average of Time (" + time.score + "), Resources (" + resources.score + "), and Readiness (" + readiness.score + ")."
      },
      readiness: readiness,
      resources: resources,
      time: time,
      ownership: ownership,
      risk: risk
    };
  }

  function buildBarrierMap(dimensions) {
    const barriers = [];
    Object.keys(dimensions).forEach(function (key) {
      const dimension = dimensions[key];
      if (dimension.score <= 3) {
        barriers.push({
          dimension: key,
          severity: dimension.score === 0 ? "BLOCKING" : "HIGH",
          description: dimension.basis
        });
      } else if (dimension.score <= 6) {
        barriers.push({
          dimension: key,
          severity: "MODERATE",
          description: dimension.basis
        });
      }
    });
    return barriers;
  }

  const EVIDENCE_BY_DIMENSION = {
    feasibility: "Confirm feasibility by running one small real attempt at the dream's first step and recording what actually happened.",
    readiness: "Confirm readiness by attempting the smallest real use of the required skill or tool and recording the result.",
    resources: "Confirm resources by getting one real quote, price, or commitment instead of an estimate.",
    time: "Confirm time by tracking actual hours spent on this dream for one real week.",
    ownership: "Confirm ownership by naming the specific person or team who will maintain this after launch.",
    risk: "Confirm the risk by identifying the earliest observable sign that it is occurring."
  };

  function buildEvidenceRequired(dimensions) {
    return Object.keys(dimensions)
      .filter(function (key) { return dimensions[key].score < 8; })
      .map(function (key) { return EVIDENCE_BY_DIMENSION[key]; });
  }

  function buildUnknowns(input) {
    const unknowns = [];
    if (!clean(input.timeAvailable)) unknowns.push("Weekly time available");
    if (!clean(input.resources)) unknowns.push("Resources available");
    if (!clean(input.skillsReadiness)) unknowns.push("Skill and tool readiness");
    if (!clean(input.ownershipPlan)) unknowns.push("Ownership and maintenance plan");
    if (!clean(input.biggestRisk)) unknowns.push("Biggest risk");
    return unknowns;
  }

  function calculateDreamScore(dimensions) {
    const values = Object.keys(dimensions).map(function (key) { return dimensions[key].score; });
    const average = values.reduce(function (sum, value) { return sum + value; }, 0) / values.length;
    return Math.round(average * 10) / 10;
  }

  function recommendNextStep(barriers) {
    if (!barriers.length) {
      return "No blocking or high-severity barriers were found from the answers given. Choose the single next real-world action that produces evidence, and take it this week.";
    }
    const worst = barriers.slice().sort(function (a, b) {
      const order = { BLOCKING: 0, HIGH: 1, MODERATE: 2 };
      return order[a.severity] - order[b.severity];
    })[0];
    return "Address the " + worst.dimension + " barrier first: " + (EVIDENCE_BY_DIMENSION[worst.dimension] || "Gather direct evidence before proceeding.");
  }

  // Analysis Data Contract (v0.2.1)
  //
  // Input:
  //   card              — the Dream Card object produced by core.buildDreamCard (v0.1), required
  //   timeAvailable     — free text, hours/week the person can realistically give
  //   resources         — free text, money/tools/materials already available
  //   skillsReadiness   — one of "yes" | "partial" | "no"
  //   ownershipPlan     — free text, who owns and maintains the result
  //   biggestRisk       — free text, the single largest risk in the person's own words
  //
  // Output: see returned object shape below. Every score carries a `basis`
  // string explaining exactly how it was computed from the given answers.
  // No field is derived from external research or an AI model call.
  function buildAnalysis(input) {
    const card = input.card || {};
    const dimensions = buildDimensions(input);
    const barrierMap = buildBarrierMap(dimensions);
    const evidenceRequired = buildEvidenceRequired(dimensions);
    const unknowns = buildUnknowns(input);
    const dreamScore = calculateDreamScore(dimensions);

    return {
      purpose: card.statement || "",
      beneficiary: card.audience || "",
      impact: card.outcome || "",
      dimensions: dimensions,
      barrierMap: barrierMap,
      evidenceRequired: evidenceRequired,
      unknowns: unknowns,
      dreamScore: dreamScore,
      scoreBasis: "Average of Feasibility, Readiness, Resources, Time, Ownership, and Risk dimension scores, each scored 0-10 from your own answers.",
      recommendedNextStep: recommendNextStep(barrierMap),
      truthLabels: {
        method: "LOCAL · DETERMINISTIC · USER-GROUNDED",
        aiApiUsed: false,
        externalResearchUsed: false,
        validated: "NOT_YET_PROVEN"
      },
      createdAt: new Date().toISOString(),
      version: "0.2.1"
    };
  }

  function exportText(analysis) {
    const lines = [
      "APEX DREAM ANALYSIS",
      "====================",
      "",
      "Purpose",
      analysis.purpose,
      "",
      "Dream Score: " + analysis.dreamScore + " / 10",
      "Score Basis: " + analysis.scoreBasis,
      "",
      "Dimension Scores"
    ];
    Object.keys(analysis.dimensions).forEach(function (key) {
      const dimension = analysis.dimensions[key];
      lines.push("- " + key + ": " + dimension.score + "/10 — " + dimension.basis);
    });

    lines.push("", "Barrier Map");
    if (analysis.barrierMap.length) {
      analysis.barrierMap.forEach(function (barrier) {
        lines.push("- [" + barrier.severity + "] " + barrier.dimension + ": " + barrier.description);
      });
    } else {
      lines.push("- No barriers identified from the answers given.");
    }

    lines.push("", "Evidence Required");
    if (analysis.evidenceRequired.length) {
      analysis.evidenceRequired.forEach(function (item) { lines.push("- " + item); });
    } else {
      lines.push("- No further evidence required from current answers.");
    }

    lines.push("", "Unknowns");
    lines.push(analysis.unknowns.length ? analysis.unknowns.join(", ") : "None reported.");

    lines.push("", "Recommended Next Step", analysis.recommendedNextStep);
    lines.push("", "Truth Label: " + analysis.truthLabels.method);

    return lines.join("\n");
  }

  return {
    buildAnalysis: buildAnalysis,
    exportText: exportText
  };
});
