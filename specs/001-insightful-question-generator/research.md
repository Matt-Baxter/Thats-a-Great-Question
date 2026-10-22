# Research: That's a Great Question

Phase 0 of the plan. Each entry records what was decided, why, and what was considered and
rejected. Some decisions depended on facts about the hosting platform that could not be checked
while planning; each is marked **Verified** with what was found, and the list at the end shows
when each was settled. Entries have been added to as the build went on, each dated.

## R1. Which model, and how hard it thinks

**Decision**: `claude-opus-5-5`, chosen by the maintainer. Effort is set explicitly. It started at
`medium`; `high` was tried on the human review set (SC-009) and, on 2026-09-30, adopted (see the
result at the end of this entry).

**Quality comes before speed.** The maintainer decided on 2026-09-24 that better questions are worth
a slower answer. Effort is never lowered to meet SC-015; if `medium` or `high` is slower than ten
seconds, SC-015 is re-set from real measurements instead. The sixty-second hard stop (FR-038) is a
different kind of promise — that the app never appears to hang — and is not traded away.

**Rationale**: question quality is the only thing this app is judged on, and Opus 5.5 is the current
Opus model at a lower price than Opus 5 ($4 / $20 per million input / output tokens, against $5 /
$25). Three things about it shape the code:

- **Thinking is always on and cannot be switched off**; effort is the only control, and so the
  first lever on speed.
- **Its default effort is `medium`**, not `high` as on Opus 5, so effort must be set explicitly
  rather than relied on.
- **Thinking counts toward the output-token limit** even though its text is not returned, so the
  limit is sized for thinking plus the reply, and the reply is read by block type rather than by
  position, since thinking blocks can come first.

**Alternatives considered**: `claude-opus-5`, the previous default — more expensive and superseded.
A faster, cheaper model — choosing one to save time or money is the maintainer's decision, not the
plan's.

`low` effort was the first plan, chosen for speed, and was replaced when the maintainer put quality
first. `medium` over `high` as the starting point for two reasons. It is Opus 5.5's own default,
the level it is tuned around. And extra effort pays off most on long, many-step work; whether it
improves a five-question list is an open question the review set can answer, whereas its cost —
longer waits, closer to the hard stop (thirty seconds at the time) — is certain.

**Review set, 2026-09-29**: 25 seeds run at `medium` and at `high`; all 50 responses returned
questions and none took more than 13.8 seconds, so both levels met the time limit (then thirty
seconds).
`high` was slower on factual and adversarial seeds (10–14 seconds) and about the same elsewhere.
The maintainer scored ten of the 25 seeds blind in [review-set.md](review-set.md) (SC-009 was cut
to ten on 2026-09-30). Both levels scored 10/10 on SC-009, SC-010 and SC-011. On SC-020 — short,
single questions — `medium` scored 6/10, below the pass mark of 8, and `high` scored exactly 8/10.

**Result, 2026-09-30: `high` adopted**, by the maintainer, as the only level that passed every
criterion. The margin is thin: two seeds out of ten, and `high` sits exactly on the pass mark.
SC-015 was measured again at `high`.

## R2. One model call or two

**Decision**: one call. Its structured response contains both the candidates (10–15) and the
model's selection of the strongest 3–5, given as positions in the candidate list.

**Rationale**: two sequential calls roughly double the waiting, and even with speed second to
quality, every request must end within sixty seconds (FR-038). One call still separates generating
from choosing — the response shows both, so tests can check that the selection really came from the
candidates, and a reviewer running the app locally can see what was passed over. The model does the choosing against the written criteria;
Python then checks the choice against the specification's hard rules.

**Alternatives considered**: two calls — generate, then select in a fresh context. The choosing
would be more independent of the generating. Kept as the upgrade path if human review shows the
single pass choosing poorly; the cost is one more round trip, which has to be measured against
SC-015 before adopting it.

**Note**: the candidate list cannot be logged on the server to explain a selection after the fact.
FR-048 forbids recording question text server-side. Explanation happens in tests and local review.

## R3. How the model's reply is structured and checked

**Decision**: request a JSON reply through the API's structured-output setting (`output_config.format`
with a JSON schema), parse it, then run it through one Python function that checks every rule the
specification sets: count 3–5, non-empty, ends with a question mark, no normalised duplicates, not
a restatement of the seed or parent, within 300 characters, selection positions valid and distinct,
and (added 2026-10-22) no broken character that would stop a question being opened.

**Rationale**: the schema guarantees the reply's *shape*; it cannot express most of the
specification's rules, so those have to be written out anyway. Keeping every rule in one readable
function — rather than split between a schema library and code — is what Principle I asks for.

**Alternatives considered**: the SDK's typed parse helper with a schema class. Shorter, but spreads
the rules across two places, and the class would still need the same hand-written checks.

## R4. What happens when the model declines

**Decision**: turn on the API's server-side fallback (`fallbacks: "default"`, beta header
`server-side-fallback-2026-07-01`). If the model declines, the API retries the same request on a
fallback model inside the same call. A decline is reported to the user only if the whole chain
declines — `stop_reason` is `"refusal"` on the final response — and then as the distinct message
FR-052 describes. The refusal text itself is never shown (FR-053).

**Rationale**: this app's target users ask about uncomfortable social and philosophical subjects,
where a cautious classifier is most likely to decline something legitimate. Opus 5.5 screens more
categories than Opus 5 did, so this matters more, not less. A fallback turns many of those declines
into questions instead of a dead end.

**Also**: `stop_reason` of `"max_tokens"`, or a reply that will not parse, is a malformed response
(FR-035), not a decline. And a refusal whose `stop_details.recommended_model` is set is a failure,
not a decline: the API sets that field only when it could not try the fallback (it was overloaded or
out of capacity), so the seed may be fine and asking again may work. Found in code review, 2026-09-29.

## R5. Staying inside sixty seconds

**Decision**: one time limit everywhere, 60 seconds. The server stops waiting for the model at 60
seconds, with no automatic retries; the function's maximum duration in `vercel.json` is 60 seconds;
and the browser abandons any request at 60 seconds. A test checks that the three agree.

**One number, chosen 2026-10-22** by the maintainer, for a limit that reads the same everywhere.
Until then the server stopped at 55 seconds, five seconds inside the other two, so that it could
send its own timed-out message before the platform cut the function off. With all three at 60, the
browser's timer, which starts first, is what stops a request that runs that long, and the user sees
the same timed-out message either way. The cost is small: the server rarely gets to log its own
timed-out line, because the platform stops the function at the same moment, and records a timeout
of its own instead.

**Raised 2026-10-16** from 25, 30 and 30 seconds, after "What are the most insightful questions for
a biologist to ask in 2026?" was cut off with the timed-out message on the live site. The server's
25 seconds is the only limit that sends that message before 30 seconds, so it was most likely the
one reached, though that request was not timed. `high` effort runs slow on some seeds (checklists/
reviews.md, section 12), and a slow answer is better than none (spec, Assumptions). The Hobby plan
accepted the 60-second duration, and a live request has since run past 30 seconds.

**One overall deadline** (2026-10-22): the SDK applies its timeout to each network step separately
— connecting, sending, and each piece of the reply — so a slow connection or a reply arriving in
pieces could add up to more than the limit. An AI-assisted review (ChatGPT) found this, and it was reproduced locally: with a 0.5-second timeout, a reply sent
in small pieces still succeeded after 1.5 seconds. The model call now runs in a separate thread that
the request stops waiting for at the limit in total, however the time was spent. The SDK keeps the
same timeout as a backstop that ends the abandoned call.

**Rationale**: the SDK retries timeouts as well as errors, so with retries on, total time can reach
the timeout multiplied by the number of attempts — which would break FR-038. With retries off, the
worst case is one attempt plus overhead, and a user who hits a failure can simply ask again.

**Verified**: Vercel's free (Hobby) plan accepts a 60-second function duration (deployed
2026-10-16).

## R6. The ancestor chain

**Decision**: the browser sends the seed and the full ordered chain of ancestor questions with each
request. The server re-checks every piece of it — the browser is not trusted — and builds the
prompt from the seed plus the most recent six ancestors. When links are dropped from the middle,
the prompt says so.

**Rationale**: the server stays stateless, and keeping only the nearest ancestors keeps the prompt
bounded and on-topic however deep a user goes. The seed is always kept because it is what the
whole inquiry is about.

**Consequence**: requests have a size cap, which puts a practical ceiling on depth at several
hundred levels. Recorded as a finding in [plan.md](plan.md).

## R7. The per-visitor request limit (FR-045)

**Decision**: two layers.

1. **Enforcement** — a rate-limit rule in the hosting platform's firewall, keyed on the visitor's
   address, applied to the questions endpoint. Over the limit, the platform answers with HTTP 429
   and the browser shows the wait-and-try-again message (FR-046). The application stores nothing.
2. **Backstop** — a monthly spend limit set on the Anthropic account. It bounds the cost the limit
   exists to protect, even if the first layer is unavailable or evaded.

**Rationale**: a stateless function cannot count anything across requests, so the count has to live
somewhere else. The platform edge is the only place that keeps no user content and needs no code
here. The spend limit covers what an address-based rule cannot — many addresses at once.

**Requests from other websites** (2026-10-22): a page on another site can make its visitors'
browsers send requests here, each costing a model call, without the visitors knowing. Browsers
send plain-text requests across sites without asking, so the server now refuses anything not
declared as JSON (FR-064); for JSON, the browser asks permission first and the server refuses.
Found by an AI-assisted review (ChatGPT). Checking the request's origin as well was considered and
left out: the allowed list would have to track every address the app is served from, and the JSON
rule already stops browsers.

**Alternatives considered**:
- *A counter in a hosted key-value store.* Works precisely, but breaks the constitution as written,
  and adds a service and a dependency.
- *A counter in the function's memory.* Resets on every cold start and is separate per running
  instance, so it would appear to protect while not doing so. Rejected as misleading.
- *A limit in the browser.* Anyone can bypass it; it is a courtesy, not a limit.

**Consequences**, both resolved 2026-09-24:
- FR-060 as first written could not be met and rested on a false premise. It now requires a limit
  high enough that ordinary use never reaches it, and allows cancelled requests to count.
- The platform keeps per-address counts. Constitution 1.1.1 permits them, since they hold no content.

**Verified** (2026-09-30): firewall rate limiting is available on the Hobby plan. The rule covers
requests to `/api/questions`, 60 per IP address per 10 minutes, answered with 429. It was raised to
200 for the class presentation and set back to 60 on 2026-10-22.

**Second address, checked 2026-10-22**: the server also answers at `/api/questions.py` (found by the
AI-assisted review). The rule's condition is "Request Path contains `/api/questions`", which matches
both addresses, so both share the one limit. No change was needed.

## R8. The HTTP handler

**Decision**: a standard-library `BaseHTTPRequestHandler` subclass in `api/questions.py`, importing
the `inquiry` package from the repository root. No web framework.

**Rationale**: one endpoint does not need a framework, and the standard library needs no
justification under Principle V.

**Verified** (2026-09-26): Vercel's Python runtime accepts this handler shape and bundles the
root-level `inquiry/` package with the function, so `inquiry/` stays where it is.

## R9. What a user types becomes part of a prompt

**Decision**: the seed and ancestors are placed in clearly marked sections of the prompt and
described to the model as material to question, not instructions to follow. The model's reply is
constrained to the question-set shape and then checked in Python.

**Rationale**: someone can type "ignore the above and answer this" as a seed. Structure and checking
stop most of what that could do — an answer is not a list of questions ending in question marks.

**Residual risk, accepted**: a question can still smuggle in an answer ("Isn't it the case that X,
because Y?"). FR-011 forbids that, but it is a judgement no automated check makes reliably. It is
covered by selection and by human review (SC-011), and the review set should include deliberately
adversarial seeds.

**Requests for questions** (2026-10-16): a seed that asks for questions is the one request the model
follows, because supplying questions is the app's job, not answering (FR-063). This gives an
attacker nothing new: the reply must still be three to five questions and is checked the same way.
A settled fact named in passing inside a question is accepted (spec.md, Assumptions).

## R10. Testing without the live model

**Decision**: `generate.py` receives the model client as a parameter. Tests pass a small hand-written
fake that returns canned replies: a good set, too few, too many, duplicates, a non-question, an
over-length question, a refusal, a cut-off (`max_tokens`) reply, unparseable text, a timeout, and
(added 2026-10-22) a reply that arrives late, for the overall time limit. No mocking library.

**Rationale**: Principle II forbids tests that call the live API, and requires the failure cases.
A fake written in plain Python is easier to read than a mocking library's patching.

**Dependency justification**: `pytest` rather than the standard library's `unittest`, because plain
`assert` statements read as ordinary Python, and `unittest`'s assertion methods are one more
vocabulary for a newer developer to learn. Development only; never deployed.

## R11. The key, and the first commit

**Decision**: the key is set as `QUESTION_APP_API_KEY` in Vercel's environment settings and in an
untracked `.env` file locally. The variable's name is a named constant in `inquiry/config.py`; the
server reads that one variable and passes its value to the Anthropic client as `api_key`. The client
is also given `base_url` explicitly — `https://api.anthropic.com`, another named constant — rather
than left to the SDK's default lookup. If the variable is missing or blank, the request fails with
the ordinary failure message and no client is built. The first implementation commit is
`.gitignore` — covering `.env*`, `.vercel/` and `__pycache__/` — before any key exists anywhere.
`.env.example` records the variable's name and never a value.

**Rationale**: Principle III — a committed key is compromised the moment it is pushed, and deleting
it later does not remove it from history.

Why not the SDK's default `ANTHROPIC_API_KEY`: given no arguments, the SDK looks through several
environment variables and files for a key (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, a login
profile on disk) and for an address (`ANTHROPIC_BASE_URL`). On a developer's machine or in a cloud
container those can belong to other tools — a coding assistant's own key, or a proxy address — and
the app would silently use them. Checked against `anthropic` 1.8.0: an explicit `api_key` stops the
SDK consulting any other credential source, and an explicit `base_url` takes precedence over
`ANTHROPIC_BASE_URL` and any profile. A key under the app's own name, passed explicitly, means the
app spends only the key meant for it and sends it only to Anthropic. The missing-key check matters
for the same reason: passing `api_key=None` would put the SDK's own lookup back in charge.

One more route, found in code review on 2026-09-29: the SDK also adds every header listed in
`ANTHROPIC_CUSTOM_HEADERS`, and an `x-api-key` or `Authorization` header there would replace or join
the app's key. The client is therefore also given `default_headers` that set `X-Api-Key` to the
app's key and remove `Authorization`; headers given this way win. A test captures the request the
real SDK builds, with that variable set, and checks its headers. Other custom headers still pass
through; none of them can authenticate a call.

**Verified** (2026-09-26): the monthly spend limit (R7) is set in the Anthropic Console, and was set
before the site went public.

## Checked after planning

Collected from the entries above. Each was unreachable while planning; all four are now settled.

**Status, 2026-09-26**: three of the four are settled by the first deploy. The project deployed
to Vercel Hobby with the "Other" preset, `vercel.json`'s 30-second duration was accepted, and a live
request through `api/questions.py` returned questions — so the `BaseHTTPRequestHandler` shape works
and the root-level `inquiry/` package is bundled. The maintainer has set a monthly spend limit in the
Anthropic Console. One caveat: the 30-second cap was accepted, but no request has yet run long
enough to test it. Firewall rate limiting on Hobby is still unverified and is checked in T047.

| Item | Entry | Default assumed for now | If it turns out otherwise |
|---|---|---|---|
| Maximum function duration on Vercel Hobby | R5 | At least 30 seconds; `vercel.json` sets 30 | **Settled 2026-09-26:** the deploy accepted 30. Raised to 60 on 2026-10-16, also accepted |
| Firewall rate limiting on Vercel Hobby, and its configuration | R7 | Available (needed only at deploy, T047) | **Settled 2026-09-30:** available on Hobby. Rule added: requests to `/api/questions`, fixed window of 600 seconds, 60 requests per IP address, answered with 429. It also covers `/api/questions.py`: the path condition is "contains `/api/questions`" (checked 2026-10-22) |
| Python handler shape and bundling of a root-level package | R8 | Both work; the package stays at `inquiry/` | **Settled 2026-09-26:** both work on the live deploy |
| Where the Anthropic spend limit is set | R11 | — (needed only before going public, T046) | **Settled 2026-09-26:** a monthly spend limit, set in the Anthropic Console |
