---
name: assignment-pack
description: >-
  Reads any lab assignment pack (instructions, acceptance criteria, rubric,
  optional contract/constraints/feedback), writes isolated grader subagents
  (rubric cells, or acceptance-criteria clusters when there is no rubric),
  then implements in scoped increments and re-grades until every cell is
  Excellent, or until every acceptance criterion is met when there is no
  rubric. Use when working an assignment pack that is not claims-intake-specific,
  scoring a rubric, checking acceptance criteria, or aiming for 100 on a lab day.
---

# Assignment pack

Orchestrate a lab day for any assignment pack. Do not create one agent that implements until it thinks it scored 100.

Pack discovery, agent naming, and Task launch: [reference.md](reference.md).
Agent file skeletons: [templates.md](templates.md).

## 1. Locate the pack

If the user names a folder, use it. Else search `docs/`, `docs/assignment*/`, and `assignments/` for files by **role** (filename or title), not a fixed claims-intake path.

Required to start:

- **Instructions** — `instructions`, `overview`, `overview`, or `assignment` (not acceptance/rubric)
- **Acceptance criteria** — `acceptance-criteria`

**Rubric** (`rubric`, with `##` cells) is required for cell graders. If it is missing, author **AC cluster graders** plus the AC gate, and implement until every criterion is met. Do not spawn one grader per criterion.

Optional roles: contract/interface, relevant-changes/constraints, `feedback.md`, `articles/`. `notes/` is never authority.

Record pack root and slug (folder name, e.g. `w02-02` or `assignment-week2-day2`). See [reference.md](reference.md).

## 2. Read before writing agents or code

Read instructions, acceptance criteria, and rubric (if present) in full. Then only the contract, constraints, and product docs the instructions name.

Read `articles/` only for method (scoping, test-first, review). Articles are not the spec.

## 3. Author graders, then persist them

Write files under `.cursor/agents/`. Reuse existing files for **this pack** if the pack has not changed. Do not overwrite graders that belong to a different pack.

New agents: `<slug>-<cell-slug>` (rubric) or `<slug>-ac-<cluster-slug>` (no rubric). Gate: `<slug>-acceptance-criteria`.

**Binary gate.** Always author. Every acceptance criterion, every out-of-scope / deliverable check, optional feedback items. Verdict: all met or unmet. No points.

**Cell grader.** One per `##` heading in the rubric. Score only that cell. Copy the Excellent row into the prompt; do not paraphrase it. Skip cell graders if there is no rubric.

**AC cluster grader.** Only when there is no rubric. These replace cell graders. Group related criteria that share files or a concern; copy assigned criteria verbatim. Verdict: all met or unmet for that cluster. Clustering rules: [reference.md](reference.md).

Each body lists files to read (pack + named product docs + deliverable source/tests), the Excellent checklist or numbered AC list, **do not edit the codebase**, and the output format. Fill from [templates.md](templates.md).

## 4. Same-session launch

Newly written types may not appear in `Task.subagent_type` until a new chat.

This session: `Task` with `subagent_type: generalPurpose` and the generated prompt as the body.
Next session: use the custom type if it is listed.

## 5. Plan increments from instruction steps

Work in instruction order, not rubric-cell or AC-cluster order. Each increment is three sentences:

1. **Outcome** — what will be true; its absence would be obvious.
2. **Authority** — file and section the work must satisfy.
3. **Boundary** — files that must not change. If the contract appears wrong, stop and tell the user rather than editing it.

If the instructions require test-first or a commit of failing tests before implementation, that sequence is the grade. Do not squash tests and implementation. Do not open the implementation file while writing those tests.

Git commits are in-scope only when the assignment grades sequence. See [reference.md](reference.md).

## 6. Implement

Implement in this parent, or spawn a **narrow** `generalPurpose` slice against already-failing tests (outcome, authority, boundary; tests must not be modified).

Never spawn “complete the assignment”, “keep going until Excellent”, or “keep going until all AC met.”

## 7. Grade after an increment

With a rubric: launch the cell graders that cover what just changed. If a rubric does not have an explicit "excellent" label, treat the highest point value in each category as Excellent.

With no rubric: launch the AC cluster graders that cover what just changed.

Launch the AC gate before declaring the lab done.

A “not Excellent” or unmet criterion is a new scoped task, not a reason to keep the same session spinning. Restart if the same misunderstanding is corrected twice.

## 8. Done

With a rubric: stop only when the gate says **all criteria met** and every cell grader says **Excellent**.

With no rubric: stop only when the gate says **all criteria met** and every AC cluster grader says **all criteria met**.
