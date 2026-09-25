# Review history — That's a Great Question

Every question asked of this specification after it was first drafted, and every defect found
reviewing it, in the order the work happened. Each entry says what was wrong, what changed, and
why — so a decision can be revisited later without re-deriving the argument behind it.

The specification itself is [`../spec.md`](../spec.md). The quality checklist it is measured
against is [`requirements.md`](requirements.md).

## 1. Specify phase — one open question, resolved

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

## 2. Before the clarify phase — three gaps closed

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

## 3. Clarify phase — five questions

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

## 4. First full review — six issues

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

## 5. Second full review — five issues

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

## 6. Third full review — four issues

A third front-to-back read found one ambiguity worth fixing and three smaller inconsistencies.
The findings shrank sharply across the three passes, which is the expected pattern: the first
found a missing section and twenty-six unmapped requirements, the second a requirement that was
factually wrong for every expansion, the third a wording ambiguity that a careful implementer
would probably have read correctly anyway.

- **"The question currently being viewed" excluded the seed.** Seven requirements used that
  phrase, but at the top of an inquiry the thing being viewed is a seed, which this specification
  defines as a different entity from a question. Read strictly, FR-026 meant the first set of
  questions could not be regenerated — the most likely use of asking again, and what User Story 4
  describes. FR-018, FR-020 and FR-026 through FR-028 now say "seed or question".
- **An acceptance scenario overclaimed distinctness**, saying each question "is different from
  every other question shown" — which straddles the two standards the specification is careful to
  separate. Narrowed to word-for-word repetition, which is what FR-007 actually rejects.
- **Two places still described clearing an inquiry as unconditional**, written before FR-057
  required a confirmation.
- **Out of Scope ruled out undoing a regeneration** but said nothing about recovering an inquiry
  cleared by a new seed, the more destructive of the two.

Also added a Last Updated field, since the specification was created on the 21st and revised
substantially through the 22nd with no way for a reader to tell.

## 7. Plan phase — two findings decided

Planning found two things the specification and constitution could not deliver as written. Both
were decided by the maintainer on 2026-09-24.

- **FR-060 rested on a false premise.** It said a cancelled request should not count against the
  request limit because cancelling threatens neither cost nor availability. But cancelling in the
  browser does not stop the model call already running on the server — it finishes and is billed —
  and a limit enforced at the hosting platform's edge counts requests on arrival without ever
  learning that the browser gave up. FR-060 now requires the limit to be high enough that ordinary
  use, including occasional cancelling, never reaches it, and allows cancelled requests to count.
  SC-019, the matching edge case, and the format mapping table were updated to match.
- **The constitution said nothing is stored server-side**, but the only workable per-visitor limit
  keeps request counts at the platform edge. Amended to 1.1.1: no user content is stored
  server-side, and platform request counters are permitted because they hold no content.

Also recorded: the model moved from `claude-opus-5` to `claude-opus-5-5` at the maintainer's
request. That is a planning decision rather than a specification change — the specification names
no model — and is reasoned in `research.md` R1.

## 8. Cross-artifact analysis — seven issues fixed

`/speckit-analyze` checked the specification, plan and task list against each other and against the
constitution. Seven issues were fixed on 2026-09-25; four minor ones were left, as recorded in the
analysis.

- **Two constitution conflicts.** The constitution limited JavaScript to "sending requests and
  displaying results", but browser-only retention (FR-021) means JavaScript must keep the inquiry
  tree. The plan had called this "justified", which is not something a plan can do to a MUST. The
  constitution was amended to 1.2.0 to say what JavaScript may do — keep the session's tree, in its
  own unit-tested module — and what it may not: judge question content. Separately, the HTTP handler
  decided which status code each outcome got, with no test; that mapping now lives in a tested
  function, and the handler only passes values between tested functions.
- **The specification contradicted a decision already made.** An assumption said an approach slower
  than ten seconds was too slow "regardless of how good its output is", after the maintainer had put
  quality first. Rewritten, and SC-015 marked provisional until it is set from measurement.
- **Three smaller gaps in the task list.** Only one task mentioned the docstring every module must
  open with; the page's 2,000-character limit was a second, unnamed copy of a server value; and
  three success criteria (SC-001, SC-005, SC-013) had no task that verified them.

## What these passes have in common

Almost every defect was introduced by a later addition rather than present from the start. The
specification went from 28 requirements to 60 in a day, edited in pieces, and each addition left
some earlier sentence describing the behaviour it had replaced. The mechanical checks now run on
every change — sequential numbering, every requirement mapped to exactly one row of the format
table — catch structural drift, but they cannot catch a sentence that is merely out of date. That
is what the read-throughs were for.

---

*Developed with the assistance of Claude, reviewed and edited by me.*
