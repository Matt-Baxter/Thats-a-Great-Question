# Specification Quality Checklist: That's a Great Question — Insightful Question Generation

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-21
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`

**All 16 items pass.** `/speckit-clarify` has been run; the specification is ready for
`/speckit-plan`.

### Clarify session 2026-09-22

Five questions asked and answered, all integrated. Each closed a category the ambiguity scan
marked Missing, and none of them re-asked something already settled:

- **Abuse / rate limiting** — a public page with no login calling a paid API had no protection
  at all (FR-045 to FR-047, SC-013).
- **Server-side logging** — FR-040 promised nothing a user types is stored outside their browser,
  while ordinary error logging would have quietly broken that promise (FR-048 to FR-050, SC-014).
- **Performance target** — the thirty-second timeout was being read as a speed requirement; ten
  seconds is now the target and thirty is labelled as abandonment (SC-015).
- **Declined generation** — a model refusal was being reported as a technical error
  (FR-051 to FR-053, SC-016).
- **Concurrent requests** — nothing prevented a second response landing under the wrong question
  (FR-054 to FR-056, SC-017).

### Holistic review 2026-09-22

A full read-through of the spec against itself, the constitution, and the assignment found six
issues, all now fixed:

- **The Objective was never stated in the document body.** Slide 31 asks for the failure mode
  rather than a feature description, and the failure-mode framing existed only inside the format
  mapping table at the foot of the page. It is now the first section, above Clarifications.
- **Target users were missing entirely.** Agreed during drafting, present in the prompt, absent
  from the spec — including the anti-user line that keeps the product from drifting into a
  chatbot. Restored under Objective.
- **The format mapping table had gone stale**, claiming Behavior covered FR-001–FR-030 and
  Verification SC-001–SC-012, leaving 26 requirements unmapped. Rebuilt so every functional
  requirement appears in exactly one row; this is now checked mechanically.
- **An edge case contradicted its requirements.** "Near-duplicate questions" promised the app
  rejects responses whose questions differ only in wording. FR-007 rejects only normalised-text
  duplicates; semantic near-duplication is handled by selection and human review. Narrowed to
  match what the requirements actually deliver.
- **The most destructive action had the least protection.** Regenerating one question required
  confirmation while starting a new seed silently destroyed an entire inquiry (FR-057).
- **No way out of a slow request.** FR-054 blocks new requests and FR-038 allows thirty seconds,
  with nothing letting a user abort. Cancelling added (FR-058, FR-059).

Counts after that review: 59 functional requirements, 19 success criteria, 21 edge cases.

### Second review pass 2026-09-22

A second front-to-back read found five more issues, all fixed. Most were consequences of the
first pass rather than anything older: adding requirements updated some parts of the document
and left others describing the previous behaviour.

- **User Story 4 contradicted FR-057.** Its acceptance scenario still had a new seed clearing the
  inquiry with no confirmation, while FR-057 required one. The edge case and SC-018 had been
  updated; the scenario, the narrative and the independent test had not — and the scenario is the
  artifact a test gets written from.
- **FR-052 used seed-specific wording for a case that is not seed-specific.** A refusal can occur
  at any depth, where the request concerns a question rather than a seed, so the required message
  would have been wrong. FR-052 and SC-016 now name whichever the request concerned.
- **Cancelling had no acceptance scenario.** It existed only as an edge case and a success
  criterion, so the checklist's claim that every requirement has acceptance criteria was false for
  two of them. Now covered by a Given/When/Then in User Story 4.
- **The "clicking while busy" edge case was stale**, written before cancelling existed and
  implying a user must wait it out.
- **Nothing said whether a cancelled request counts against the rate limit.** It does not
  (FR-060): the limit bounds cost and protects availability, and a user who changes their mind
  has threatened neither.

Also corrected the header, which named a feature branch that does not exist — this project
commits directly to `main`.

Counts after the second pass: 60 functional requirements, 19 success criteria, 21 edge cases,
6 acceptance scenarios in User Story 4. Every functional requirement appears in exactly one row
of the format mapping table, verified mechanically.

### Resolved since the first validation pass

Three gaps found by reviewing the spec after the clarification above were closed before
running `/speckit-clarify`, so its question quota is not spent re-asking settled questions:

- **Wrong question count.** The spec covered "fewer than three" but was silent on "more than
  five". A response of the wrong shape is now rejected outright rather than truncated or padded
  (FR-005, SC-003) — the wrong count signals something went wrong, and quietly repairing it hides
  the signal.
- **What "distinct" means.** Split into two levels, only one automatable. Duplicate wording is
  rejected mechanically (FR-007); whether two differently-worded questions pursue the same
  underlying goal is a judgment delivered by selection (FR-008) and verified by human review
  (SC-010).
- **Starting over without a reload.** Added as User Story 4: a user can request a fresh set for
  the current question without retyping the seed (FR-026), and can begin a new inquiry with a
  different seed without reloading (FR-030). Regeneration replaces what was there and discards
  anything beneath it, with a confirmation first (FR-027, FR-028, SC-008).

Counts after these changes: 44 functional requirements, 12 success criteria, 4 user stories.

### The clarification resolved during the specify phase

The single `[NEEDS CLARIFICATION]` marker at the former FR-015 asked whether expanding a
question keeps sibling lines open or replaces the current set. Resolved deliberately, and
the answer separates structure from display:

- The **inquiry tree is retained in full** for the session (FR-021), so a user is never
  confined to whichever branch they opened first (FR-024, FR-025).
- The **display shows one level at a time** — the current question and its direct children
  (FR-020) — so the interface stays readable at depth and on a phone.
- A **trail of every ancestor from the seed onward** sits above the current questions
  (FR-017), each entry navigable in a single action (FR-019).

Requirement numbers in this section are the current ones; the spec has been renumbered twice
as requirements were added, so any FR number quoted in an earlier commit message refers to
that commit's numbering rather than today's.

### Validation notes

- **No implementation details**: the specification names no language, framework, service,
  or storage technology. "Browser session" appears as a boundary on persistence and
  "phone-sized screen" as a constraint on user experience, not as implementation choices.
- **Success criteria**: every criterion is objectively checkable except SC-009, SC-010 and
  SC-011, which are assessed by human review over a defined set of at least twenty seeds.
  The specification labels those three as human-reviewed rather than presenting them as
  automated tests. This is deliberate — question quality is context-dependent and cannot
  be scored automatically, and a metric claiming to would be false precision.
- **Seed and question length limits** (2,000 and 300 characters) were not supplied in the
  input description. Reasonable defaults were chosen and recorded in Assumptions, where
  they can be changed without affecting any other requirement.
