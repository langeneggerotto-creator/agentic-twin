const assert = require("assert");
const core = require("../core.js");

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

const exported = core.exportText(card);
assert.ok(exported.includes("APEX DREAM CARD"));
assert.ok(exported.includes("Next Best Step"));

console.log("PASS: Dream validation");
console.log("PASS: Dream Card generation");
console.log("PASS: Clarity scoring boundaries");
console.log("PASS: Export formatting");
console.log("RESULT: 4/4 smoke tests passed");
