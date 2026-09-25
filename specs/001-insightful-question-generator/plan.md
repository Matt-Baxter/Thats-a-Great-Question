# Implementation Plan: That's a Great Question — Insightful Question Generation

**Feature directory**: `specs/001-insightful-question-generator` (committed to `main`; no feature branch) | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-insightful-question-generator/spec.md`

## Summary

A single web page takes a seed and shows three to five questions about it; any question can be
opened for three to five more, and the whole tree is kept in the browser for the session. One
stateless Python function does all the judgment: it validates what the browser sends, asks Claude
for 10–15 candidate questions *and* its choice of the strongest 3–5 in one structured response,
checks that choice against the specification's rules, and returns either questions or a
plain-language message. The browser holds the tree and draws it; it makes no decisions about
questions. Rate limiting happens at the hosting platform's edge, so the application itself stores
nothing between requests.

The decisions behind each of these, and the alternatives rejected, are in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+ (server); plain JavaScript, HTML and CSS (browser)

**Primary Dependencies**: `anthropic` (the official SDK — required to call the model). Development
only: `pytest`. Nothing else; the HTTP handler uses the standard library.

**Storage**: None on the server. The inquiry tree lives in browser memory for the session and is
discarded on reload.

**Testing**: `pytest` with a hand-written fake model client, never the live API. Browser tree logic:
Node's built-in `node --test`, no packages (see Complexity Tracking).

**Target Platform**: Vercel — static files plus one Python serverless function

**Project Type**: Web application — static frontend and one API endpoint

**Model**: `claude-opus-5-5`, effort `medium`, with `high` tried on the review set; thinking is always on for this model ([research.md](research.md) R1)

**Performance Goals**: question quality first. SC-015's ten-second target will be re-set from real measurements rather than met by lowering effort; the thirty-second hard stop (FR-038) holds

**Constraints**: every request resolves within 30 seconds (FR-038); no user or model text in any
server-side record (FR-048); keyboard-operable and phone-sized (FR-043, FR-044)

**Scale/Scope**: one user per browser session, low traffic; a class project with a public URL

## Constitution Check

*Gate: must pass before Phase 0 research. Re-checked after Phase 1 design, below.*

| Principle | Status | How the design meets it |
|---|---|---|
| I. Explainable code | ✅ Pass | No web framework — a standard-library handler. The model's reply is checked by one readable Python function rather than a schema library. Every value that shapes behaviour is a named, commented constant in one file. |
| II. Tests cover decisions | ✅ Pass | Every Python function that transforms or decides has unit tests against a fake client, covering the failure cases the constitution names — including the mapping from outcome to HTTP status. Browser tree logic in `public/tree.mjs` is tested with `node --test`, as constitution 1.2.0 requires. |
| III. Secrets | ✅ Pass | Key read from `QUESTION_APP_API_KEY` — its name a constant in `inquiry/config.py` — in server code only, and passed to the client explicitly along with a fixed `base_url`, so no other `ANTHROPIC_*` variable can supply a different key or redirect the call (research.md R11). `.gitignore` covering `.env*` and `.vercel/` is the first file committed, before any key exists. |
| IV. Untrusted model output | ✅ Pass | Structured output, then validation in Python, before anything reaches the browser. The browser inserts text with `textContent`, never as markup. Every failure maps to a written message. |
| V. Small and finished | ✅ Pass | One endpoint, one Python package, three frontend files, one runtime dependency. |
| Stack constraints | ✅ Pass | Python serverless on Vercel; plain HTML/CSS/JS, no framework, no build step; Claude API. |
| No user content stored server-side | ✅ Pass | The application stores nothing. The platform's rate limiter keeps per-address request counts, which constitution 1.1.1 permits because they hold no content. |
| JavaScript's role | ✅ Pass | Constitution 1.2.0 lets JavaScript keep the session's inquiry tree in a separate module, unit-tested, provided it makes no judgment about question content. `public/tree.mjs` is that module. |

**Gate result**: passes.

## Project Structure

### Documentation (this feature)

```text
specs/001-insightful-question-generator/
├── spec.md
├── plan.md              # this file
├── research.md          # decisions and rejected alternatives
├── data-model.md        # entities, fields, validation, state transitions
├── quickstart.md        # how to run it and prove it works
├── contracts/
│   └── questions-api.md # the one HTTP endpoint
├── checklists/
│   ├── requirements.md
│   └── reviews.md
└── tasks.md             # created by /speckit-tasks, not by this command
```

### Source code (repository root)

```text
api/
└── questions.py            # Vercel entry point: reads the request, calls inquiry/, writes JSON. No judgment.

inquiry/                    # every judgment the app makes
├── config.py               # named, commented constants: limits, counts, model, effort, timeout, key variable, API address
├── lines_of_inquiry.py     # the written list of angles a question may take, each commented
├── prompts.py              # builds the model prompt from a seed and its ancestor chain
├── request_checks.py       # validates what the browser sent (FR-002, FR-003, chain lengths)
├── response_checks.py      # validates what the model returned (FR-004 to FR-011)
├── generate.py             # builds the model client; one call to the model; maps every outcome to a result
├── http_response.py        # turns a result into a status code and JSON body; the only place outcomes become HTTP
└── messages.py             # every plain-language message a user can see, in one place

public/
├── index.html
├── styles.css              # colours, spacing and type defined once
├── tree.mjs                # the session's inquiry tree: structure, navigation, counts. No page access; unit-tested
└── app.js                  # draws the page and sends requests, using tree.mjs

tests/
├── fakes.py                # a fake model client returning canned responses
├── test_request_checks.py
├── test_response_checks.py
├── test_prompts.py
├── test_generate.py
├── test_http_response.py
└── tree.test.mjs           # browser tree logic, run with `node --test`

requirements.txt            # anthropic
requirements-dev.txt        # pytest
vercel.json                 # function duration; no rewrites needed
.gitignore                  # first commit: .env*, .vercel/, __pycache__/
.env.example                # the variable name (QUESTION_APP_API_KEY) only, never a value
```

**Structure decision**: a web application with one endpoint, split by responsibility rather than by
layer. `api/questions.py` is kept deliberately thin — it reads the request, passes values between
tested functions, and writes the response — so every decision, including which status code an
outcome gets, sits in `inquiry/`, where it can be tested without a server. The existing `mockups/`
folder is untouched; `public/` starts from it.

## Complexity Tracking

| Departure | Why it is needed | Simpler alternative rejected because |
|---|---|---|
| A second test runner (`node --test`) | The browser tree functions decide things — whether to regenerate, how much a confirmation will discard — and Principle II requires every decision to be tested. `node --test` is built into Node and adds no packages. | Leaving it untested breaks Principle II. Testing it only by hand through the quickstart is the fallback if the maintainer would rather not install Node; that is the maintainer's call. |
| A platform-level rate limit | FR-045 needs a per-visitor count, and a stateless function cannot keep one. | A database counter breaks the constitution as written; an in-memory counter resets on every cold start and would claim protection it does not give. See research.md R7. |

## Findings raised during planning

Planning turned up three things the specification or constitution could not deliver as written.
The first two were decided by the maintainer on 2026-09-24 and are resolved.

1. **FR-060 rests on a false premise.** It says a cancelled request should not count against the
   limit because cancelling "has threatened neither" cost nor availability. But cancelling in the
   browser does not stop the model call already running on the server — the call finishes and is
   billed. And a platform rate limiter counts a request when it arrives; it cannot learn later
   that the browser gave up on it. **Resolved:** FR-060 now requires the limit to be high enough
   that ordinary use, including occasional cancelling, never reaches it — and says plainly that a
   cancelled request may count, because it still costs.
2. **The constitution said "Nothing is stored server-side."** The platform rate limiter keeps
   per-address counts. **Resolved:** constitution amended to 1.1.1 — no user content is stored
   server-side, and platform request counters are permitted because they hold no content.
3. **"No limit on depth" has a practical ceiling.** The browser sends the ancestor chain with each
   request, and the request size is capped. At the maximum question length the cap is reached at
   several hundred levels deep. This is a technical ceiling rather than a product limit, and no
   change is recommended — but FR-015 promises no limit, so it is recorded here rather than left
   for someone to discover.

## Post-design Constitution Check

Re-checked against the Phase 1 artifacts. No new departures. The data model keeps judgment in
`inquiry/` and state in the browser; the contract returns only validated questions or a message
written in Python; the quickstart runs the full test suite without the live API. Both
conditional items from the first check were resolved by the maintainer.
