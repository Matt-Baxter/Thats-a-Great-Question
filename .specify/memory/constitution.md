# That's a Great Question Constitution

## Core Principles

### I. Explainable Code Over Clever Code (NON-NEGOTIABLE)

Every file in this project MUST be understandable by its author, reading it cold, without
assistance.

- Functions MUST do one thing, and their names MUST say what that thing is.
- Every module MUST begin with a short docstring in plain English: what it does and why it exists.
- Clever one-liners, metaprogramming, and dynamic attribute tricks are BANNED, even where they
  are shorter.
- If explaining what a function does takes more than two sentences, the function MUST be split.

Rationale: the sole maintainer is new to professional software development, and this project is
deliberately a corrective to an earlier one whose predictions its own author could not explain.
Code that cannot be explained cannot be debugged, defended, or trusted.

### II. Tests Cover Decisions, Not Percentages

- Every function that transforms data or makes a decision MUST have at least one unit test.
- Tests MUST NOT call the live model API. Model responses are faked or recorded, so the suite is
  fast, free, and gives the same answer every time.
- Tests MUST cover failure cases, not only the happy path: empty input, oversized input, the model
  returning malformed output, the model being unavailable.
- A failing test MUST NOT be deleted, skipped, or weakened to make the suite pass. Either the code
  is wrong or the test is wrong, and which one it is MUST be decided deliberately.
- Purely presentational code (page layout, styling) is exempt.

Rationale: a coverage percentage is easy to hit without testing anything that matters. Naming what
must be tested is harder to fake and more useful.

### III. Secrets Never Reach the Browser or the Repository (NON-NEGOTIABLE)

- The model API key MUST be read from an environment variable, in server-side Python only.
- The key MUST NOT appear in frontend code, in any response sent to the browser, in logs, or in
  error messages.
- Files holding real keys MUST be excluded by `.gitignore` before any key is placed in them.
- A key that is ever committed MUST be treated as compromised: revoked and replaced, not merely
  deleted from the file.

Rationale: anything the browser downloads is public to its user, and git history is permanent.
Deleting a committed secret in a later commit does not remove it.

### IV. Model Output Is Untrusted Input

- Every model response MUST be validated before display: correct shape, non-empty, and the
  expected number of questions.
- Model output MUST be rendered as plain text, never as markup, so returned content cannot execute
  in the page.
- When the model fails, is unavailable, or returns something unusable, the app MUST show a clear
  plain-language message. It MUST NOT crash, hang, or show a blank screen.
- Generated questions MUST be presented as suggestions, never as authoritative or complete.

Rationale: the model is a third party that can return malformed, empty, refused, or unexpected
content. Treating its output as guaranteed-good is the most likely way this app breaks in front of
a user.

### V. Small and Finished Beats Large and Broken

- Scope is fixed by the specification. No feature is built unless a numbered requirement calls
  for it.
- The simplest implementation that satisfies a requirement wins.
- No abstraction is introduced until at least two concrete cases need it.
- No dependency is added without a one-line justification for why the standard library will not do.

Rationale: one maintainer, four weeks, and a graded deliverable. A narrow app that works beats a
broad one that half-works.

## Technology and User Experience Constraints

**Stack**

- Backend: Python 3.11+, deployed as serverless functions.
- Frontend: plain HTML, CSS, and JavaScript. No frontend framework and no build step.
- JavaScript is limited to sending requests and displaying results. All logic involving judgment
  lives in Python.
- Hosting: Vercel.
- Question generation: the Anthropic Claude API.
- Nothing is stored server-side. There is no database and no user account. Anything the app
  remembers lives in the browser only.

**User experience**

- Colors, spacing, and type styles MUST be defined once and reused. No per-page variations.
- Every interactive element MUST be reachable and operable by keyboard.
- The interface MUST be usable on a phone-sized screen.

**Performance**

- A visible loading state MUST appear immediately when a request starts, so the app never looks
  frozen.
- A request MUST resolve to either questions or an error message within 30 seconds.

## Development Workflow

- Specification before code: specify, plan, tasks, then implement.
- Every requirement carries an ID (REQ-NNN). Tasks and tests reference the requirement they serve,
  so any piece of code can be traced back to a stated reason for existing.
- Tests MUST pass before a commit is pushed.
- Commit messages MUST explain why a change was made, not only what changed.
- AI assistance MUST be disclosed in work products, per course policy.

## Governance

- This constitution supersedes convenience. Where it conflicts with the fastest path, it wins.
- Amendments are made by editing this file in a commit that states what changed and why, and by
  bumping the version: MAJOR for removing or redefining a principle, MINOR for adding one, PATCH
  for wording and clarifications.
- A principle that blocks necessary work MUST be amended deliberately, never quietly ignored. An
  unenforced principle is worse than no principle, because every later Spec Kit command keeps
  citing it.
- Every specification, plan, and task set MUST be checked against this file before implementation
  begins.

**Version**: 1.0.0 | **Ratified**: 2026-09-21 | **Last Amended**: 2026-09-21
