---
name: assignment-pack
description: >-
  Reads any lab assignment pack (instructions, acceptance criteria, rubric,
  optional contract/constraints/feedback, articles for project
  shapes/methods/guidance), writes isolated grader subagents
  (rubric cells, or acceptance-criteria clusters when there is no rubric),
  then implements in scoped increments and re-grades until every cell is
  Excellent, or until every acceptance criterion is met when there is no
  rubric. When the user names an instruction-step range (one step, or
  step 1–step 5), implement only those steps and re-grade until their
  in-scope cells/criteria are met; do not require the full-lab gate. Use
  when working an assignment pack that is not claims-intake-specific,
  scoring a rubric, checking acceptance criteria, aiming for 100 on a lab
  day, or completing a named range of instruction steps.
---

# Assignment pack

Orchestrate a lab day for any assignment pack. Do not create one agent that implements until it thinks it scored 100.

Default scope is the full lab. If the user names a step range (one step, or several, by number, heading, or quote), that range is the scope: implement those steps in instruction order, grade only what they can make true, stop. A single step is a range of one. Mapping and partial cells: [reference.md](reference.md) (Step-range scope).

Pack discovery, agent naming, and Task launch: [reference.md](reference.md).
Agent file skeletons: [templates.md](templates.md).

## Halt on gotchas

This applies at every step: pack files, project layout, run results, and deliverable content.

If something does not make sense, contradicts other authority, looks planted to throw a student off, or would require guessing the intended meaning, **stop**. Do not paper over it, "fix" the pack, pick an interpretation, or keep implementing.

Alert the human reviewer with:

- What looks off
- Where (file, path, section, or run)
- Why it might be a gotcha vs a real spec

## 1. Locate the pack

If the user names a folder, use it. Else search `docs/`, `docs/assignment*/`, and `assignments/` for files by **role** (filename or title), not a fixed claims-intake path.

If the user names an instruction step or a range of steps (for example step 1–step 5), record that as the run scope. A single step is a range of one. If they do not, the scope is the full lab.

Required to start:

- **Instructions** — `instructions`, `overview`, `overview`, or `assignment` (not acceptance/rubric)
- **Acceptance criteria** — `acceptance-criteria`

**Rubric** (`rubric`, with `##` cells) is required for cell graders. If it is missing, author **AC cluster graders** plus the AC gate. On a full-lab run, implement until every criterion is met. Do not spawn one grader per criterion.

Optional roles: contract/interface, relevant-changes/constraints, `feedback.md`, `articles/`. `notes/` is never authority.

Record pack root and slug (folder name, e.g. `w02-02` or `assignment-week2-day2`). See [reference.md](reference.md).

## 2. Read before writing agents or code

Read instructions, acceptance criteria, and rubric (if present) in full. Then the contract, constraints, and product docs the instructions name.

Read `articles/` when the pack has them. They often contain project shapes, methods, and guidance the implementation should follow. Articles are not the spec. If they contradict instructions, acceptance criteria, or the rubric, follow **Halt on gotchas**.

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

Work in instruction order, not rubric-cell or AC-cluster order. On a step-range run, plan and implement only those steps, in order. Each increment is three sentences:

1. **Outcome** — what will be true; its absence would be obvious.
2. **Authority** — file and section the work must satisfy.
3. **Boundary** — files that must not change. If the contract (or anything else) appears wrong, follow **Halt on gotchas** rather than editing it.

If the instructions require test-first or a commit of failing tests before implementation, that sequence is the grade. Do not squash tests and implementation. Do not open the implementation file while writing those tests.

Git commits are in-scope only when the assignment grades sequence. See [reference.md](reference.md).

## 6. Implement

Implement in this parent, or spawn a **narrow** `generalPurpose` slice (outcome, authority, boundary). Already-failing tests are not required. If tests for this increment already exist, the slice must not modify them. Follow project shapes, methods, and guidance from `articles/` while implementing; do not let them override the spec.

Never spawn “complete the assignment”, “keep going until Excellent”, “keep going until all AC met,” or “keep going until this range is Excellent.”

## 7. Grade after an increment

With a rubric: launch the cell graders that cover what just changed. If a rubric does not have an explicit "excellent" label, treat the highest point value in each category as Excellent.

With no rubric: launch the AC cluster graders that cover what just changed.

On a step-range run, launch only graders with in-scope items; pass a verbatim in-scope subset when a cell or cluster is partial. Do not launch the AC gate as a completion signal. See [reference.md](reference.md) (Step-range scope).

On a full-lab run, launch the AC gate before declaring the lab done.

A “not Excellent” or unmet **in-scope** item is a new scoped task, not a reason to keep the same session spinning. Deferred (not-yet-in-scope) items are not a miss. Restart if the same misunderstanding is corrected twice.

## 8. Done

**Full lab.** With a rubric: stop only when the gate says **all criteria met** and every cell grader says **Excellent**. With no rubric: stop only when the gate says **all criteria met** and every AC cluster grader says **all criteria met**.

**Step range.** Stop when every fully in-scope grader passes, and every in-scope item on a partial grader is met. Do not require Excellent on a cell that still needs work outside the named range. Do not require the gate. Report deferred bullets/criteria as out of scope for this run, not as failures.
