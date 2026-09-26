# Tasks: That's a Great Question — Insightful Question Generation

**Input**: design documents in `specs/001-insightful-question-generator/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/questions-api.md](contracts/questions-api.md),
[quickstart.md](quickstart.md)

**Tests**: included. The constitution (Principle II) requires a test for every function that
transforms data or makes a decision, including failure cases, and forbids tests that call the live
model. Within each story, write the tests first and confirm they fail before implementing.

**Organization**: by user story, so each story can be built and checked on its own.

**Every file**: each new Python module begins with a plain-English docstring, and each new
JavaScript file with a comment, saying what it does and why it exists (constitution Principle I,
non-negotiable). This applies to every task below that creates a file, whether or not the task
repeats it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — a different file, with no dependency on an unfinished task
- **[US1]–[US4]**: the user story in spec.md the task serves
- **(maintainer)**: needs a person at a dashboard; cannot be done from code

---

## Phase 1: Setup

- [X] T001 Create `.gitignore` at the repository root ignoring `.env`, `.env.*` except `.env.example`, `.vercel/`, `.venv/`, `__pycache__/` and `.pytest_cache/`. Commit it on its own, before any key exists anywhere, and confirm `git check-ignore .env` prints `.env` (constitution Principle III; research.md R11)
- [X] T002 [P] Create `.env.example` containing only the line `QUESTION_APP_API_KEY=` and a comment that the real value goes in `.env` locally and in Vercel's environment settings — never in the repository — and that the app deliberately does not read `ANTHROPIC_API_KEY` (research.md R11)
- [X] T003 [P] Create `requirements.txt` containing `anthropic>=1.0,<2.0`, `requirements-dev.txt` containing `pytest`, and `pytest.ini` containing `[pytest]` and `pythonpath = .` so tests can import `inquiry`. Give each dependency a one-line comment saying why the standard library will not do (constitution Principle V; research.md R10)
- [ ] T004 (maintainer) Settle the four items in research.md "Must verify before implementation" — the maximum function duration on Vercel Hobby, firewall rate limiting on Hobby, whether Vercel's Python runtime accepts a `BaseHTTPRequestHandler` subclass and bundles a root-level package, and where the Anthropic spend limit is set — and record each answer in research.md. If a root-level package is not bundled, every later task uses `api/_inquiry/` in place of `inquiry/`. **Open, one item left:** the first deploy on 2026-09-26 settled three of the four (see research.md); firewall rate limiting on Hobby remains, and is checked as part of T047
- [X] T005 Create `vercel.json` setting the maximum duration of `api/questions.py` to 30 seconds, or to the Hobby maximum found in T004 if that is lower (research.md R5)
- [X] T006 [P] Create `inquiry/__init__.py` with a plain-English docstring saying the package holds every judgment the app makes, plus empty `api/`, `public/` and `tests/` folders (constitution Principle I)

---

## Phase 2: Foundational

Shared by every story. No story work starts until this phase is done.

- [X] T007 Create `inquiry/config.py` with one named, commented constant per value, each comment saying what it controls and which requirement sets it: `MAX_SEED_CHARS = 2000` (FR-003), `MAX_QUESTION_CHARS = 300` (FR-010), `MIN_QUESTIONS = 3` and `MAX_QUESTIONS = 5` (FR-004), `CANDIDATES_MIN = 10` and `CANDIDATES_MAX = 15` (research.md R2), `MAX_ANCESTORS_IN_PROMPT = 6` (R6), `MODEL = "claude-opus-5-5"` and `EFFORT = "medium"` (R1), `MAX_OUTPUT_TOKENS = 16000` (sized for thinking plus the reply, R1), `API_TIMEOUT_SECONDS = 25` and `API_MAX_RETRIES = 0` (R5), `MAX_REQUEST_BYTES = 256_000` (R6), `API_KEY_ENV_VAR = "QUESTION_APP_API_KEY"` and `API_BASE_URL = "https://api.anthropic.com"` (R11) (constitution, Documentation Standards)
- [X] T008 [P] Create `inquiry/lines_of_inquiry.py`: a list of entries, each with a `name` and a one-sentence `description` telling the model what that angle looks for, covering at least assumption, evidence, consequence, alternative, stakeholder, definition, framing, precedent, incentive and failure mode. Comment every entry. The list guides generation and is never shown to the user (FR-012; data-model.md, Line of inquiry)
- [X] T009 [P] Create `inquiry/messages.py` holding every user-facing message the server can send: an empty seed; `seed_too_long(length)` returning "A seed can be up to 2,000 characters. This one is {length}." with the length comma-formatted; generation failed; timed out; and `declined(about)` where `about` is `"seed"` or `"question"`, saying no questions could be generated for that seed or question and that rephrasing may help, without calling it an error and without suggesting the user did anything wrong (FR-002, FR-003, FR-035, FR-052)
- [X] T010 [P] Create `tests/fakes.py`: a hand-written fake model client whose `beta.messages.create(**kwargs)` records the arguments it was given and returns a queued canned response — a valid set; too few; too many; a duplicate pair; a statement without a question mark; a 301-character question; a question restating the seed; a thinking block before the text block; `stop_reason="refusal"`; `stop_reason="max_tokens"`; unparseable text — or raises `anthropic.APITimeoutError`, `anthropic.APIConnectionError` or `anthropic.APIStatusError`. No mocking library (research.md R10)
- [X] T011 [P] Create `public/styles.css` from the tokens in `mockups/inquiry-flow.html`: colours, spacing and type defined once as custom properties, a dark theme, and `[hidden] { display: none !important; }` placed before any rule that sets `display` (constitution, User experience)

**Checkpoint**: configuration, messages, lines of inquiry, the fake client and styles exist.

---

## Phase 3: User Story 1 — Get questions about a seed (P1) 🎯 MVP

**Goal**: a seed goes in; three to five validated questions, or a plain-language message, come back.

**Independent test**: submit a seed and get 3–5 well-formed, distinct questions with no answers
anywhere; an empty or over-length seed is refused with a message naming the problem.

### Tests — write first, confirm they fail

- [X] T012 [P] [US1] Write `tests/test_request_checks.py` for seeds: empty and whitespace-only rejected with the empty-seed message (FR-002); exactly 2,000 characters accepted; 2,001 rejected with a message naming both the limit and the actual length (FR-003); a body that is not JSON, or lacks `seed`, rejected as invalid input; a body larger than `config.MAX_REQUEST_BYTES` rejected as invalid input
- [X] T013 [P] [US1] Write `tests/test_response_checks.py` with at least one test per check in data-model.md, "Checks applied, in order": "`selected` has 3–5 entries, all distinct, all valid positions in `candidates`"; "each selected question, after trimming, is non-empty and ends with a question mark"; "each is at most 300 characters"; "no two are the same once normalised — lower-cased, punctuation removed, whitespace collapsed"; "none normalises to the same text as the seed or question being opened". Include a six-question selection to prove it is rejected, never truncated (FR-005)
- [X] T014 [P] [US1] Write `tests/test_prompts.py` for a seed with no ancestors: the seed sits inside a clearly delimited section described as material to question, not instructions to follow (research.md R9); every `name` in `lines_of_inquiry` appears; all selection criteria from the spec's Assumptions ("Questions are selected, not merely produced") appear — six since FR-061 added the preference for the shorter question; the prompt asks for 10–15 candidates and the positions of the strongest 3–5; it says never to answer or comment on a question (FR-031); and the JSON schema requires exactly `candidates` (list of strings) and `selected` (list of integers) with no other properties
- [X] T015 [P] [US1] Write `tests/test_generate.py` using `tests/fakes.py`: a valid reply gives an `ok` result with the selected questions in order; a thinking block before the text is skipped; `stop_reason="refusal"` gives a `declined` result whose message contains none of the reply's text (FR-051, FR-053); `max_tokens`, unparseable text, and a reply failing any check each give `failed` (FR-035); `APITimeoutError` gives a timed-out result and connection or status errors give `failed`; the recorded request used `config.MODEL`, `config.EFFORT`, `config.MAX_OUTPUT_TOKENS`, the JSON schema, and the fallback beta; and, using pytest's `caplog`, log output never contains the seed or any question text (FR-048) but does record the outcome and the depth (FR-049). For `build_client`: a key under `config.API_KEY_ENV_VAR` gives a client using that key and `config.API_BASE_URL` even when `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY` are set to other values; a missing or blank key gives no client; and `generate` with no client gives `failed` without the key's value in any message or log (constitution Principle III; research.md R11)
- [X] T016 [P] [US1] Write `tests/test_http_response.py`: every outcome maps to the status code and JSON body contracts/questions-api.md specifies — `ok` to 200 with `status` and `questions`; `declined` to 200 with `status` and `message`; `invalid_input` to 400; `failed` to 502; a timeout to 504 with `status` `"failed"` and the timed-out message — and no body ever contains a field the contract does not list (constitution Principle II)

### Implementation

- [X] T017 [US1] Implement `inquiry/request_checks.py` for the seed: reject a body larger than `config.MAX_REQUEST_BYTES`, parse the JSON body, require a string `seed` of free text (FR-001), reject it if empty after trimming or longer than `config.MAX_SEED_CHARS`, and return either a checked request or an `invalid_input` result carrying the message from `inquiry/messages.py`
- [X] T018 [P] [US1] Implement `inquiry/response_checks.py`: one readable function applying the five checks in data-model.md in order, returning either the selected questions or the name of the first check that failed (FR-006, FR-007, FR-009, FR-010). Never repair a reply (FR-005). Normalise by lower-casing, removing punctuation and collapsing whitespace
- [X] T019 [P] [US1] Implement `inquiry/prompts.py`: the system prompt — the app's purpose, that it never answers, the lines of inquiry, the five selection criteria including that the set covers genuinely different angles and contains no leading or rhetorical questions (FR-008, FR-011), and the instruction to return 10–15 candidates and the positions of the strongest 3–5 — plus the user content with the seed in a delimited section, and the JSON schema as a named constant
- [X] T020 [US1] Implement `inquiry/generate.py`: a function taking the model client and a checked request. Call `client.beta.messages.create` with `model=config.MODEL`, `max_tokens=config.MAX_OUTPUT_TOKENS`, `output_config={"effort": config.EFFORT, "format": {"type": "json_schema", "schema": <schema>}}`, `betas=["server-side-fallback-2026-07-01"]` and `fallbacks="default"` (if the installed SDK rejects `fallbacks` as a keyword, pass it through `extra_body` and say so in a comment). Check `stop_reason` before anything else: `"refusal"` is `declined`, `"max_tokens"` is `failed`. Otherwise find the text block by type, parse its JSON, run `response_checks` before anything is returned (FR-033), and return a result. Catch `anthropic.APITimeoutError` before `anthropic.APIConnectionError`. Log only the outcome, a refusal's category if any, and the depth (FR-048, FR-049; research.md R3, R4). Also in this module, `build_client(environ)`: read the key from `environ[config.API_KEY_ENV_VAR]`; if it is missing or blank return `None`, never `anthropic.Anthropic(api_key=None)`, which would let the SDK find some other key; otherwise return `anthropic.Anthropic(api_key=<key>, base_url=config.API_BASE_URL, timeout=config.API_TIMEOUT_SECONDS, max_retries=config.API_MAX_RETRIES)`. `generate` given `None` returns `failed` and logs that no key is configured, without any key value (research.md R11)
- [X] T021 [P] [US1] Implement `inquiry/http_response.py`: one function taking a result from `generate` or `request_checks` and returning the status code and JSON body for it, exactly as contracts/questions-api.md specifies. This is the only place outcomes become HTTP
- [X] T022 [US1] Implement `api/questions.py` as a pass-through with no decisions of its own: a `BaseHTTPRequestHandler` subclass whose POST handler reads the body, calls `request_checks`, then `generate.build_client(os.environ)`, then `generate`, then `http_response`, and writes what `http_response` returns; every other method gets a fixed 405. Nothing from the request body is logged or stored (FR-040), and there is no account or login of any kind (FR-041)
- [X] T023 [P] [US1] Create `public/index.html`: a labelled seed textarea with a character counter driven by `MAX_SEED_CHARS` in `app.js`, a submit button, a results region with `aria-live="polite"` so screen readers hear new questions, a message region, and a line saying the questions are suggestions the app will not answer (FR-032). No third-party scripts (FR-050)
- [X] T024 [US1] Create `public/app.js` for the seed flow only. At the top, name and comment the two values the page needs: `MAX_SEED_CHARS = 2000` for the character counter, with a comment that it must match `inquiry/config.py` and that the server enforces it (FR-003), and `REQUEST_TIMEOUT_MS = 30000` (FR-038). Then: on submit, show a loading state immediately (FR-037); POST `{"seed", "ancestors": []}`; abandon the request after 30 seconds with a fixed timed-out message (FR-038); on HTTP 429 show a fixed wait-and-try-again message (FR-046); otherwise show `questions`, or the server's `message`, inserting every string with `textContent`, never as markup (FR-034). Every outcome — including a network error with no response — ends in questions or a message, never a blank or frozen page (FR-039). A 429 leaves whatever is on screen untouched (FR-047)
- [X] T025 [US1] Run `pytest` until everything passes. Then, with `QUESTION_APP_API_KEY` set, run `vercel dev` and work through quickstart.md scenarios 1, 9 and 10. **Done 2026-09-25 against a local stand-in, not `vercel dev`** (no Vercel CLI or account in that session): a standard-library server serving `public/` and routing to the real `api/questions.py` handler, driven in Chromium at desktop and phone width. All three scenarios passed; live requests took 10–12 seconds. Whether Vercel's own runtime accepts the handler and bundles `inquiry/` is still T004

**Checkpoint**: MVP. A seed returns validated questions, and every failure is readable.

---

## Phase 4: User Story 2 — Expand a question (P2)

**Goal**: any question opens into 3–5 questions about that question, as deep as the user likes.

**Independent test**: open a returned question; the new set addresses it rather than the seed, is
numbered from it, and can be expanded again with no limit.

### Tests — write first, confirm they fail

- [ ] T026 [P] [US2] Add to `tests/test_request_checks.py`: an empty `ancestors` list accepted; a list entry that is empty, or longer than 300 characters, rejected; `ancestors` missing or not a list rejected
- [ ] T027 [P] [US2] Add to `tests/test_prompts.py`: a chain of six or fewer ancestors appears whole; a chain of nine keeps the seed and the last six, and says that earlier links were left out; the last ancestor is named as the question being opened, so the new questions are about it rather than the seed (FR-014); no depth is ever refused (FR-015) (research.md R6)
- [ ] T028 [P] [US2] Add to `tests/test_response_checks.py` and `tests/test_generate.py`: a question restating the question being opened is rejected (FR-009); a decline on an expansion produces the message about a *question*, not a seed (FR-052)
- [ ] T029 [P] [US2] Write `tests/tree.test.mjs` for `public/tree.mjs`, run with `node --test tests/tree.test.mjs`: the seed's children are labelled `1`–`5` and the children of `2.3` are labelled `2.3.1`–`2.3.5`; a result is attached only to the node it was requested for (FR-056); a failed request leaves the node unopened so it can be opened again (FR-036); while a request is in flight, starting another is refused (FR-054)

### Implementation

- [ ] T030 [US2] Extend `inquiry/request_checks.py` to check `ancestors` as data-model.md, "Generation request", specifies: "each at most 300 characters, not empty"
- [ ] T031 [US2] Extend `inquiry/prompts.py` to include the seed plus the last `config.MAX_ANCESTORS_IN_PROMPT` ancestors, mark any links left out, and name the last ancestor as the question being opened
- [ ] T032 [US2] Extend `inquiry/response_checks.py` and `inquiry/generate.py` so expansions pass exactly the same checks as the first set (FR-016), comparing against the question being opened rather than always the seed, and to pass `"question"` to `messages.declined` when `ancestors` is not empty
- [ ] T033 [P] [US2] Create `public/tree.mjs` as an ES module of pure functions with no page access: create a tree from a seed and hold it for the session (FR-021), add children to a node with hierarchical labels, look up a node, and track whether a request is in flight (data-model.md, Node)
- [ ] T034 [US2] Extend `public/app.js`, loaded as `type="module"` and importing `./tree.mjs`: render each question as a button that opens it (FR-013); send the seed and ancestor chain; show that the app is busy and ignore other opens while a request is in flight (FR-054, FR-055); attach the result to the requested node only (FR-056); after a failure, leave the question closed and openable again (FR-036). Nothing about the tree is saved to browser storage, so a reload starts empty (FR-042)
- [ ] T035 [US2] Run `pytest` and `node --test tests/tree.test.mjs`, then quickstart.md scenarios 2 and 8

**Checkpoint**: questions open into questions, to any depth.

---

## Phase 5: User Story 3 — Stay oriented and move between lines of inquiry (P3)

**Goal**: a trail from the seed to the current question, one click back to any ancestor, and
branches that stay as they were.

**Independent test**: go five levels deep, return to the seed in one click, open a sibling, then go
back to the first branch — it appears immediately, unchanged, with no loading state.

- [ ] T036 [P] [US3] Add to `tests/tree.test.mjs`: the path from the seed to any node, in order; reopening an expanded node needs no request and returns the same children (FR-022); any sibling can be opened (FR-024), and opening it leaves the first branch unchanged (FR-025)
- [ ] T037 [US3] Add to `public/tree.mjs`: the path from the seed to a node, and whether opening a node needs a request (only when it has never been expanded, FR-023)
- [ ] T038 [US3] Extend `public/app.js`, `public/index.html` and `public/styles.css`: a trail above the current questions showing every ancestor from the seed (FR-017), the current seed or question in full with ancestors shortened (FR-018), every trail entry a button returning to that point in one action (FR-019), only the current seed or question and its children on screen (FR-020), no request when revisiting (FR-022), and no horizontal scrolling at phone width (FR-044)
- [ ] T039 [US3] Run `node --test tests/tree.test.mjs`, then quickstart.md scenarios 3, 4 and 11

---

## Phase 6: User Story 4 — Ask again, or ask something else (P3)

**Goal**: a fresh set for any seed or question, a way out of a slow request, and a new inquiry
without reloading — never losing work without a warning.

**Independent test**: regenerate a question with descendants (warned first, then replaced); cancel a
request (nothing changes); start a new seed (warned first, then cleared without a reload).

- [ ] T040 [P] [US4] Add to `tests/tree.test.mjs`: counting all of a node's descendants; discarding everything below a node; replacing a node's children only when the new set succeeds, leaving the tree unchanged on failure or cancel (FR-029, FR-059); clearing the whole tree
- [ ] T041 [US4] Add those functions to `public/tree.mjs`
- [ ] T042 [US4] Extend `public/app.js` and `public/index.html`: an "Ask again" control for the current seed or question, including the first set (FR-026); a confirmation naming how many questions will be discarded before regenerating anything with descendants (FR-028); replacement on success (FR-027) and no change on failure (FR-029); a Cancel control during loading, using `AbortController`, that leaves the tree unchanged and accepts the next request immediately (FR-058, FR-059); and a "New inquiry" control that warns how many questions will be lost (FR-057) and clears without a reload (FR-030). Confirmations use `<dialog>` and work from the keyboard (FR-043)
- [ ] T043 [US4] Run `node --test tests/tree.test.mjs`, then quickstart.md scenarios 5, 6, 7 and 12

---

## Phase 7: Polish, deploy, and measure

- [ ] T044 [P] Audit: confirm nothing in `public/` uses `innerHTML` or `insertAdjacentHTML` (FR-034), and search the repository for `sk-ant-` to confirm no key has been committed (constitution Principle III). Confirm every Python module and JavaScript file opens with its explanatory docstring or comment (Principle I), and that `MAX_SEED_CHARS` in `public/app.js` matches `inquiry/config.py`
- [ ] T045 [P] Update `README.md` "Running it locally" with the real setup steps, the project status, and the new source folders; add `public/tree.mjs` to plan.md's source layout and the new folders to `CLAUDE.md`, "Where things live" (constitution, Documentation Standards)
- [X] T046 (maintainer) Confirm the monthly spend limit on the Anthropic account is set before the site is public (research.md R7, R11)
- [ ] T047 (maintainer) Deploy: add `QUESTION_APP_API_KEY` in the Vercel project's environment settings; add a firewall rate-limit rule on `/api/questions`, per visitor address, high enough that ordinary use never reaches it (FR-045, FR-060) — 60 requests per 10 minutes is a reasonable start; push to `main`; then repeat quickstart.md scenarios 1, 3 and 10 against the live address. Then lower the rule temporarily, exceed it, and confirm the wait-and-try-again message appears with the inquiry on screen untouched, before restoring it (SC-013). Finally, ask someone who has not seen the app to use it with no instructions, and time how long they take to reach a set of questions — under sixty seconds passes (SC-005)
- [ ] T048 Time twenty consecutive requests across varied seeds at `medium` effort. Set SC-015 in spec.md to the time within which eighteen finished, and treat any request over 30 seconds as a defect (FR-038, SC-001). Remove the "Provisional" note from SC-015 once it is set. Record the numbers in checklists/reviews.md (research.md R1)
- [ ] T049 Run the review set — at least twenty seeds spanning technical, social and philosophical subjects, including deliberately factual seeds and seeds that try to make the app answer — at `medium`, then at `high`. Score SC-009, SC-010, SC-011 and SC-020 by hand. Adopt `high` in `inquiry/config.py` only if its questions are clearly better and every request ends within 30 seconds, and record the result in research.md R1
- [X] T050 Ask for short, single-idea questions (FR-061): add `TARGET_QUESTION_WORDS` to `inquiry/config.py`; in `inquiry/prompts.py`, ask for one idea per question at that length, add a sixth selection criterion preferring the shorter of two equal questions, and stop quoting `MAX_QUESTION_CHARS` to the model; update `tests/test_prompts.py`. Added 2026-09-26 after the first live questions ran long

---

## Dependencies and execution order

- **Setup (Phase 1)** first. T001 comes before anything else, so no key can ever be committed. T004's answers may move `inquiry/` to `api/_inquiry/`.
- **Foundational (Phase 2)** depends on Setup and blocks every story.
- **US1 (Phase 3)** depends on Foundational. It is the MVP and the base the other stories extend.
- **US2 (Phase 4)** extends US1's request checks, prompts and page.
- **US3 (Phase 5)** and **US4 (Phase 6)** both extend US2's tree. They touch the same files, so do them one after the other: US3, then US4.
- **Polish (Phase 7)** after the stories. T048 and T049 need a real key; T046 and T047 need the maintainer.

Within each story: tests, then the Python they test, then the handler — which only passes values between tested functions — then the page.

## Parallel opportunities

- Phase 1: T002, T003 and T006 together, after T001.
- Phase 2: T008, T009, T010 and T011 together, after T007.
- US1: the five test files (T012–T016) together; then T018, T019 and T021 together; T023 alongside any of them.
- US2: T026–T029 together; T033 alongside T030–T032.
- Polish: T044 and T045 together.

### Example: US1

```text
Together:   T012 test_request_checks · T013 test_response_checks · T014 test_prompts · T015 test_generate · T016 test_http_response
Then:       T017 request_checks
Together:   T018 response_checks · T019 prompts · T021 http_response · T023 index.html
Then:       T020 generate → T022 api/questions.py → T024 app.js → T025 run and check
```

## Implementation strategy

1. **MVP**: Setup, Foundational, then US1. Stop and check it against a real key — a seed in,
   validated questions out, every failure readable. This alone is a working app.
2. **Add US2**: questions open into questions. Check it on its own.
3. **Add US3, then US4**: orientation, then recovery. Check each.
4. **Polish, deploy, measure**: including the two measurements that set SC-015 and choose the effort
   level from evidence rather than assumption.

Commit after each task or logical group, with tests passing before every push (constitution,
Development Workflow).
