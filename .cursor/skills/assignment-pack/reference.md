# Assignment-pack reference

## Pack vs product

Identify files by **role**, then by filename or heading. Do not assume a claims-intake tree.

Search, in order: the folder the user named, then `docs/`, `docs/assignment*/`, `assignments/`.

| Kind | How to recognize | Role |
| --- | --- | --- |
| Instructions | `instructions`, `overview`, or `assignment` in the name or title; not acceptance/rubric | What this day asks and the step order |
| Acceptance | `acceptance-criteria` | Binary pass/fail list |
| Rubric | `rubric`, with `##` cells | Graded cells; one grader per `##` |
| Contract | `contract` in the name or title | Interface / field authority |
| Constraints | `relevant-changes`, `constraints` | Error types, retry, deliverables, what not to change |
| Feedback | `feedback.md` | Optional extra checks |
| Articles | `articles/` | Project shapes, methods, and guidance; not the spec |
| Scratch | `notes/` | Never authority |

Required: instructions + acceptance criteria. Rubric required for cell graders. If absent: AC cluster graders plus the AC gate; implement until every criterion is met.

**Slug:** pack folder name, shortened if it already contains a day id (e.g. `assignment-week2-day2` or `w02-02`). If the pack is a single file under `assignments/`, slug from the stem (`W02_Day1_Assignment_LOCAL` → `w02-day1`).

Examples in this lab: `docs/instructions.md` + `docs/acceptance-criteria.md` + `docs/callRecordContract.md`; `docs/assignment-week2-day2/w02-02-*.md`.

## Agent naming

Gate: `<slug>-acceptance-criteria` at `.cursor/agents/<slug>-acceptance-criteria.md`.

Cell graders: `<slug>-<cell-slug>` at `.cursor/agents/<slug>-<cell-slug>.md`.

AC cluster graders (no rubric): `<slug>-ac-<cluster-slug>` at `.cursor/agents/<slug>-ac-<cluster-slug>.md`.

Reuse files when they already exist **for this pack** and the pack is unchanged. Do not overwrite agents whose names belong to a different pack.

## AC clusters (no rubric)

Cluster graders stand in for rubric cells. The gate still checks the full list, out-of-scope, and feedback. Cluster graders score only their assigned criteria.

**Do not spawn one grader per criterion.** Related items share files; one-per-item duplicates work and misses interactions.

How to group:

1. If the AC file has `##` headings (or numbered sections), one cluster per heading.
2. Else group a flat list by **shared concern and shared files**, keeping consecutive items that would pass or fail together.
3. Typical cluster size: 2–6 criteria. A singleton is allowed when a criterion is independent (tooling, secrets, a single deliverable path). Never more than 8 in one cluster.
4. Do not mix unrelated concerns to reduce launch count. Do not split a tight group to manufacture more agents.
5. Target 3–8 cluster graders. If the list is tiny (≤4, one concern), one cluster plus the gate is enough.

Name clusters from the concern, not from numbers (`schema-contract`, not `ac-1-5`). Record original criterion numbers in the agent body.

Example (flat list): schema/types together; renderer behavior together; run protocol together; scoring together; committed artifacts / lint as their own clusters if they do not share files with the others.

## Task launch

This chat: `Task` `subagent_type: generalPurpose`, prompt = the agent file body (system prompt plus “score now”). Newly written custom types often are missing from the enum until a new conversation.

Next chat: `subagent_type` equal to the agent `name` if listed.

Launch several graders in parallel. They must not edit the repo.

## Step-range scope

When the user names an instruction-step range — one step, or several (for example step 1–step 5) — that range is the run. A single named step is a range of one. Author the full grader set as usual. Do not write range-specific agent files. Do not split a cell or cluster to manufacture a range grader.

Work the named steps in instruction order. Do not start a step outside the range.

**Map before implementing.** From the **union** of the named steps' required outcomes, classify every rubric Excellent bullet, or every acceptance criterion:

| Class | Meaning | How to grade |
| --- | --- | --- |
| Fully in-scope | The named range can make the whole cell, cluster, or criterion true | Launch the grader unchanged once the steps in the range that own it are done. The range is not done if that grader fails |
| Partial | Some bullets or criteria belong to the range; the rest need steps or files outside it | Do not require Excellent / all met for the whole cell or cluster. Launch the same grader with an explicit in-scope list copied verbatim. Remaining items are **not yet in scope**, not unmet |
| Out of scope | Nothing in the named range can satisfy it | Do not launch. Do not treat as a fail |

Do not require a fully-in-scope cell in the middle of the range if a later named step still owns part of it. After each increment, grade what that increment (and the completed prefix of the range) can make true.

Filter at launch time only: grader body plus “score only these in-scope items; do not fail this run for the rest.” Never persist a filtered grader. Never spawn one grader per leftover criterion.

**Gate.** Do not launch the AC gate as a completion signal. Criteria owned by steps outside the range are supposed to still fail.

**Ambiguous mapping.** If a bullet could belong to the range or to a step outside it, follow **Halt on gotchas**. Do not guess.

**Done.** All fully in-scope graders pass, and every in-scope subset item on partial graders is met. Name the deferred items in the wrap-up.

Example: steps 1–3 that add scorer metrics and a version rule can fully own “metrics are deterministic” and `select_current_version`. A “comparison evidence” cell that also requires `comparison.md` (a later step) is partial: grade the scoring-file bullets, defer the report bullets. Criteria about `run.py` are out of scope until that step is in the range. A run of step 1 alone uses the same rules with a smaller union.

## Git commits

Commits are in-scope only when the assignment grades sequence (for example: failing tests committed before the matching implementation). Then follow that order in the history. Do not squash tests and implementation. Do not commit when the pack does not grade history.
