# APEX AI Agent-to-Application Learning Curriculum — 0D → 11D
## Proof-Based Capability Ladder v0.1.0-DRAFT

**Status:** DRAFT curriculum architecture  
**Pacing Rule:** There is no week-based or time-based pacing. Advance only when the required capability is demonstrated and its evidence is preserved.  
**Purpose:** Learn how ChatGPT prompts, agents, tools, code, GitHub, dashboards, automation, digital twins, tests, deployment and governed improvement fit together in a real build.

---

## 1. The Learning Law

The original straightforward beginner curriculum is the **0D foundation**. It introduces the system and prepares the learner to begin working with it.

This expanded ladder measures progress by demonstrated mastery:

> A learner is not advanced because they have received information. Advancement is earned when they can understand, perform, verify, preserve and safely reuse the capability.

Each dimension has five evaluation lanes:

| Lane | Test Question |
|---|---|
| Understanding | Can the learner explain what is happening and why? |
| Execution | Can the learner perform or build the required work? |
| Evidence | Can the learner demonstrate proof rather than claim success? |
| GitHub Continuity | Is the artifact versioned, recoverable and transferable? |
| Governance | Are risks, approvals, boundaries and rollback understood? |

---

## 2. Capability Ladder at a Glance

| Dimension | Curriculum Capability | Observable Outcome |
|---:|---|---|
| **0D** | Orientation / First Map | Understands prompts, agents, tools, code, GitHub, dashboard and application as distinct concepts. |
| **1D** | Prompt Signal | Writes bounded prompts that state current reality, desired outcome, constraint and proof. |
| **2D** | Agent and Tool Relationships | Routes a task among orchestrator, builder, tester, governance reviewer and available tools. |
| **3D** | Safe Execution | Runs local code or a software-only cycle and records what happened. |
| **4D** | Diagnosis and Repair | Identifies a failure cause, applies or specifies a repair and retests. |
| **5D** | Evidence-Based Evaluation | Compares options or workflows with criteria, evidence, uncertainty and risk. |
| **6D** | Minimum Viable Creation | Builds a useful runnable module with code, data, tests and documentation. |
| **7D** | Transfer and Adaptation | Reuses the capability in a new module or context and records adaptation. |
| **8D** | Invention from a Real Gap | Detects a validated gap and prototypes a novel, testable response. |
| **9D** | Repeatable Innovation System | Operates an agent/test/evidence loop for repeated bounded improvement. |
| **10D** | Governed Application Architecture | Integrates modules into a deployed, monitored and rollback-ready application. |
| **11D** | Regenerative Mastery | Improves the improvement system itself through evidence, review and human control. |
| **O∞** | Governed Evolution Direction | Continues learning and improvement without claiming a final unproven perfection. |

---

# 0D — Orientation / First System Map

## Capability Purpose
Understand the pieces before attempting to build or automate them.

## Learn

- What ChatGPT is and is not.
- What a prompt is.
- What an AI agent is.
- What a tool is.
- Why code is necessary for repeatable activity.
- Why GitHub matters for preservation and handoff.
- What a dashboard reveals.
- What turns a set of files into an application.
- The difference between `PROPOSED`, `CREATED`, `TESTED`, `MEASURED` and `VERIFIED`.

## Build Exercise

Inspect the APEX ARX Control Center and identify one tracked module, for example GPU Acceleration or Learning Compass. Capture:

- What is its current state?
- What is its intended vision state?
- What is currently missing?
- What is its next valid action?
- What evidence would prove progress?

## Proof Gate

Explain this chain accurately:

`Prompt → Agent or Tool → Artifact or Code → Test or Evidence → GitHub Version → Dashboard Status → Next Action`

## GitHub Evidence Package

- `records/0D/ORIENTATION_NOTES.md`
- `records/0D/FIRST_MODULE_SELECTION.md`
- Progress ledger entry.

## Advance to 1D When
You can distinguish a vision, an artifact, working code, test evidence and verified outcome without confusing them.

---

# 1D — Prompt Signal / Instructing the AI

## Capability Purpose
Turn an idea into a bounded, understandable and testable instruction.

## Learn

Use the prompt formula:

`Role + Current State + Desired Outcome + Constraints + Required Output + Proof Check`

## Build Exercise

Write three bounded prompts, such as:

1. GPU telemetry intake prompt.
2. Learning Compass measurement prompt.
3. Image2X8K Movie pipeline assessment prompt.

Every prompt must state:

- What exists now.
- What must be produced.
- What may not be claimed.
- What evidence would count as success.

## Proof Gate

A second person or AI can act on the prompt without inventing the important goal, boundary or acceptance test.

## GitHub Evidence Package

- `prompts/L01_<module>_PROMPT.md`
- `reviews/L01_PROMPT_REVIEW.md`
- Progress ledger entry.

## Advance to 2D When
You reliably convert an idea into bounded, testable work instructions.

---

# 2D — Relationships / Agent and Resource Routing

## Capability Purpose
Understand how roles and resources work together to complete a task.

## Learn

- An agent is a role with instructions, tools and boundaries.
- A tool performs an action or retrieves data.
- The orchestrator selects and sequences work.
- Builders create; testers test; governance reviewers stop unsupported or unsafe promotion.
- Human approval remains required for consequential actions.

## Build Exercise

Map one module task through:

- Orchestrator Agent.
- Build Agent.
- Test Agent.
- Governance/SENTINEL Agent.
- GitHub/Artifact Custodian.

Assign the tool, file, data or human approval needed by each role.

## Proof Gate

You can explain who should do each part, what gets handed off, what should be recorded, and where the work must stop for approval.

## GitHub Evidence Package

- `architecture/L02_AGENT_ROUTING_MAP.md`
- `architecture/L02_RESOURCE_REGISTRY.md`
- `reviews/L02_HANDOFF_CHECK.md`

## Advance to 3D When
You can route a task to the correct role and resource without treating all AI work as one undefined activity.

---

# 3D — Execution / Run Safe Software Work

## Capability Purpose
Move from instruction to actual controlled execution.

## Learn

- File and folder navigation.
- PowerShell command basics and quoting paths with spaces.
- Launching local software.
- Running a software-only cycle.
- Reading logs and basic errors.
- Saving execution evidence.

## Build Exercise

- Launch the ARX dashboard or another small local application.
- Run one approved software-only cycle.
- Save a log, screenshot or generated output.
- Record any error and its fix.

## Proof Gate

You have a repeatable command and an observable output, or you have accurately documented a blocked execution with a next repair action.

## GitHub Evidence Package

- `execution/L03_RUN_COMMANDS.md`
- `execution/L03_RUN_LOG.md`
- `failures/L03_FAILURE_AND_REPAIR.md`, when applicable.

## Advance to 4D When
You can run controlled local code, interpret what happened and preserve the record.

---

# 4D — Analysis / Debugging and Repair

## Capability Purpose
Diagnose failure causes and turn errors into reusable lessons.

## Learn

- Input failure, process failure, output failure and dependency failure.
- Symptom versus root cause.
- Repair, retest and rollback.
- Failure ledger discipline.

## Build Exercise

Use one real problem such as:

- A PowerShell path error.
- Missing script or package.
- GPU telemetry detection failure.
- Dashboard data not updating.

Capture:

- What failed.
- Evidence of the failure.
- Likely root cause.
- Repair attempted.
- Retest result.
- Prevention improvement.

## Proof Gate

The problem is corrected or accurately blocked, and another person can follow the record without repeating the same mistake.

## GitHub Evidence Package

- `issues/L04_<issue>_ANALYSIS.md`
- `failures/L04_REPAIR_LEDGER.md`
- Corrected source or instruction file, when applicable.

## Advance to 5D When
You can convert a failure into an auditable correction or defensible block.

---

# 5D — Evaluation / Decide from Evidence

## Capability Purpose
Judge alternatives based on evidence, risk, value and limits.

## Learn

- Baseline versus improved output.
- Prompt-only versus coded implementation.
- Human-only versus AI-only versus combined workflow.
- APEX versus standard benchmark logic.
- KPI design and confidence calibration.

## Build Exercise

Define and conduct one bounded comparison test, or produce a complete real-input test packet when the required input is unavailable.

Example comparison:

`Human only vs AI only vs Human + AI` on one clearly specified task.

## Proof Gate

You can recommend a path using criteria, evidence, unknowns, limitations and risk—without overstating the result.

## GitHub Evidence Package

- `evaluations/L05_TEST_PLAN.md`
- `evaluations/L05_RESULTS.md` or `evaluations/L05_READY_FOR_REAL_INPUT.md`
- `metrics/L05_KPI_DICTIONARY.md`

## Advance to 6D When
You can make a defensible evidence-bound decision about what to build next.

---

# 6D — Creation / Minimum Viable Application Module

## Capability Purpose
Build a useful runnable module rather than only describe one.

## Learn

- Application folder structure.
- Code, configuration, data, tests and user interface.
- Local-first deployment.
- Versioning and release notes.
- What MVP status means and does not mean.

## Build Exercise

Build or materially extend one module, for example:

- ARX Control Center module panel.
- GPU telemetry dashboard panel.
- Learning Compass test-record collector.
- Image2X8K output-scoring panel.

## Proof Gate

A runnable module exists, basic tests pass, documentation allows another person to run it, and limits are explicitly stated.

## GitHub Evidence Package

- Module source code.
- `tests/` for module validation.
- `docs/` and `README.md`.
- `CHANGELOG.md`.
- Versioned package or release record.

## Advance to 7D When
The MVP works in its initial intended context and can be reconstructed from its repository artifacts.

---

# 7D — Transfer / Reuse in a New Context

## Capability Purpose
Demonstrate that a capability generalizes beyond the first use case.

## Learn

- Template design.
- Shared schema and KPI reuse.
- Controlled adaptation.
- Transfer failure detection.

## Build Exercise

Apply a 6D-built pattern to a second module, such as:

- ARX tracking pattern → GPU telemetry module.
- GPU telemetry pattern → MotiViz render/quality module.
- Learning test pattern → second learning domain.

## Proof Gate

The reused pattern functions in the second context, with differences, adaptations and failures documented.

## GitHub Evidence Package

- `modules/<transferred_module>/`
- `transfer/L07_TRANSFER_REPORT.md`
- `transfer/L07_REUSE_AND_CHANGE_LOG.md`

## Advance to 8D When
The method works beyond the initial example and its transfer limits are understood.

---

# 8D — Invention / Create from a Validated Gap

## Capability Purpose
Create something genuinely new because reality reveals an important missing piece.

## Learn

- Gap detection from actual observations and tests.
- Opportunity scoring.
- New feature, twin, agent or metric proposals.
- Invention versus unneeded complexity.

## Build Exercise

Use a recorded failure, evidence gap or user need to propose and prototype one new solution.

## Proof Gate

The new solution traces to a documented problem, has a safe test plan, and is not promoted simply because it is novel.

## GitHub Evidence Package

- `inventions/L08_GAP_STATEMENT.md`
- `inventions/L08_SOLUTION_PROTOTYPE.md`
- `tests/L08_VALIDATION_PLAN.md`
- Risk/approval record.

## Advance to 9D When
You can repeatedly turn real gaps into testable, governable innovation candidates.

---

# 9D — Innovation System / Repeatable Agent Workflow

## Capability Purpose
Operate a repeated improvement workflow with evidence and governance.

## Learn

- Orchestration.
- Safe concurrency.
- Test automation.
- Evidence ledgers.
- Pull-request/review logic.
- CI workflows where appropriate.

## Build Exercise

Operate a bounded workflow that:

1. Selects a valid next target.
2. Assigns the right agent/tool.
3. Executes safe work.
4. Tests the output.
5. Records evidence and artifacts.
6. Updates module status.
7. Stops at approval gates.

## Proof Gate

Multiple execution cycles produce traceable improvements without uncontrolled scope growth, evidence loss or false promotion.

## GitHub Evidence Package

- `automation/`
- `.github/workflows/`, where justified.
- `ledgers/`
- `reports/L09_RUN_HISTORY.md`
- Regression test evidence.

## Advance to 10D When
Innovation becomes repeatable, measurable and governed rather than ad hoc.

---

# 10D — Architecture / Full Governed Application

## Capability Purpose
Integrate multiple modules into a usable, monitored application ecosystem.

## Learn

- Application architecture.
- Databases and APIs.
- Access control and security boundaries.
- Deployment and operations.
- Monitoring, alerts and backups.
- Integration and rollback.

## Build Exercise

Under appropriate approvals, architect and deploy a control center that connects multiple modules, displays real KPIs, preserves evidence and runs bounded automation.

## Proof Gate

The application operates across modules with tested deployment, access control, monitoring, backup/rollback and traceable evidence.

## GitHub Evidence Package

- Deployment architecture.
- Security/access-control documentation.
- Operations runbook.
- Monitoring specification.
- Release package.
- Rollback plan.
- Verified commit/release identifiers.

## Advance to 11D When
The application is an operational, governed system of systems—not disconnected prototypes.

---

# 11D — Regenerative Mastery / Improve the Improvement System

## Capability Purpose
Build a system that learns how to improve itself without removing human control.

## Learn

- Evaluation harnesses and benchmark trends.
- Failure-memory systems.
- Controlled repair proposals.
- Rollback discipline.
- Governance of agent/system changes.
- Human understanding and control supremacy.

## Build Exercise

Operate a governed loop that:

1. Detects weaknesses in its own performance or process.
2. Proposes the smallest valid improvement.
3. Tests that improvement against a baseline.
4. Rejects unsupported or harmful changes.
5. Rolls back failed changes.
6. Records verified lessons.
7. Updates the application or curriculum only through reviewable evidence.

## Proof Gate

Repeated improvements are evidence-backed, auditable and reversible, while human understanding and control increase rather than decrease.

## GitHub Evidence Package

- `governance/`
- `evals/`
- `lessons/`
- `rollback/`
- `releases/`
- `L11_REGENERATIVE_MASTERY_EVIDENCE.md`
- Human approval records for consequential promotions.

## O∞ Direction

After 11D, advancement is a direction rather than a final claim:

- Continuously learn.
- Continuously test.
- Continuously correct.
- Continuously preserve evidence.
- Continuously maintain truth, safety, dignity and human authority.

---

## 3. Promotion Decision Template

Every learner and every implemented module should use this record:

| Field | Required Entry |
|---|---|
| Learner / Module ID | |
| Current Level | |
| Target Level | |
| Capability Demonstrated | |
| Artifact Created | |
| Evidence or Test Result | |
| GitHub Path | |
| Commit SHA / Verification State | |
| Risks / Limitations | |
| Approval Required | |
| Promotion Decision | `NOT_STARTED`, `HOLD`, `PASSED`, `REWORK_REQUIRED` |
| Next Smallest Improvement | |

---

## 4. Recommended First Learning Run

Begin with **0D → 3D using the APEX ARX Control Center and GPU Telemetry module**.

This is the shortest honest path to real capability because it requires you to:

1. Understand the map.
2. Write one bounded prompt.
3. Assign the right role/tool.
4. Run safe software code.
5. Capture a real result or failure.
6. Preserve evidence in GitHub.
7. View progress in the dashboard.

Do not expand to larger autonomous claims until this real chain works and is documented.