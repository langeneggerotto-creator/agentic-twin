const assert = require("assert");
const core = require("../core.js");
const analysis = require("../analysis.js");

// --- v0.1 Dream Card compatibility ---

const validation = core.validateDream(
  "I want to build an app that helps people make better decisions with AI guidance."
);
assert.strictEqual(validation.ok, true);

const card = core.buildDreamCard({
  original: validation.value,
  audience: "independent professionals facing complex decisions",
  outcome: "make confident decisions faster and understand why",
  constraint: "no more than four hours of founder effort per week",
  evidence: "users complete a decision and report greater confidence"
});

assert.ok(card.statement.includes("independent professionals"));
assert.ok(card.nextStep.includes("3 people"));
assert.ok(card.score >= 4.6 && card.score <= 9.4);
assert.strictEqual(card.evidenceLabel, "LOCAL · USER-GROUNDED");

const exportedCard = core.exportText(card);
assert.ok(exportedCard.includes("APEX DREAM CARD"));
assert.ok(exportedCard.includes("Next Best Step"));

console.log("PASS: Dream validation");
console.log("PASS: Dream Card generation");
console.log("PASS: Clarity scoring boundaries");
console.log("PASS: Export formatting");

// --- v0.2.1 Deterministic Local Analysis ---

const strongAnalysis = analysis.buildAnalysis({
  card: card,
  timeAvailable: "about six hours per week on evenings and weekends",
  resources: "a laptop, a small existing audience, and a modest personal budget",
  skillsReadiness: "yes",
  ownershipPlan: "I will own and maintain this myself for the first year",
  biggestRisk: "the audience may not convert into paying users quickly enough"
});

assert.ok(strongAnalysis.dreamScore > 0 && strongAnalysis.dreamScore <= 10, "dream score is within 0-10");
assert.strictEqual(strongAnalysis.truthLabels.aiApiUsed, false);
assert.strictEqual(strongAnalysis.truthLabels.externalResearchUsed, false);
assert.strictEqual(strongAnalysis.dimensions.readiness.score, 9);
assert.strictEqual(strongAnalysis.unknowns.length, 0);

console.log("PASS: Deterministic analysis on complete answers");

const emptyAnalysis = analysis.buildAnalysis({
  card: card,
  timeAvailable: "",
  resources: "",
  skillsReadiness: "",
  ownershipPlan: "",
  biggestRisk: ""
});

assert.strictEqual(emptyAnalysis.unknowns.length, 5, "every skipped field is reported as unknown");
assert.ok(emptyAnalysis.barrierMap.length >= 5, "every unanswered dimension becomes a barrier");
assert.ok(emptyAnalysis.evidenceRequired.length > 0);
assert.ok(emptyAnalysis.dreamScore < strongAnalysis.dreamScore, "fewer answers score lower than complete answers");

console.log("PASS: Deterministic analysis on empty answers surfaces unknowns and barriers");

const uncertainAnalysis = analysis.buildAnalysis({
  card: card,
  timeAvailable: "not sure yet",
  resources: "none right now",
  skillsReadiness: "no",
  ownershipPlan: "unknown",
  biggestRisk: "not sure"
});

assert.ok(uncertainAnalysis.barrierMap.some((barrier) => barrier.severity === "HIGH" || barrier.severity === "BLOCKING"));
assert.ok(uncertainAnalysis.recommendedNextStep.length > 0);

console.log("PASS: Deterministic analysis flags explicit uncertainty as a barrier");

const exportedAnalysis = analysis.exportText(strongAnalysis);
assert.ok(exportedAnalysis.includes("APEX DREAM ANALYSIS"));
assert.ok(exportedAnalysis.includes("Dream Score"));
assert.ok(exportedAnalysis.includes("Barrier Map"));
assert.ok(exportedAnalysis.includes("Evidence Required"));

console.log("PASS: Analysis export formatting");

console.log("RESULT: 9/9 smoke tests passed");
