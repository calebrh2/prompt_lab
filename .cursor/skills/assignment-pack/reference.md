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
| Method | `articles/` | How to work; not the spec |
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

## Git commits

Commits are in-scope only when the assignment grades sequence (for example: failing tests committed before the matching implementation). Then follow that order in the history. Do not squash tests and implementation. Do not commit when the pack does not grade history.
