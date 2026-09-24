# Research: That's a Great Question

Phase 0 of the plan. Each entry records what was decided, why, and what was considered and
rejected. Entries marked **Verify** depend on facts about the hosting platform that could not be
checked while planning; each names what to confirm and what changes if it turns out otherwise.

## R1. Which model, and how hard it thinks

**Decision**: `claude-opus-5`. Effort starts at `low`, raised to `medium` only if the human review
set (SC-009) shows a real improvement. Adaptive thinking stays on — it is on by default for this
model — and is never switched off.

**Rationale**: `claude-opus-5` is the project default for question quality, which is the only thing
this app is judged on. Effort is the lever that trades depth for speed within one model, and it is
the first thing to tune against the ten-second target. Switching thinking off has two known failure
modes on this model; lowering effort gets the speed without them.

**Alternatives considered**: a faster, cheaper model. Not chosen here — choosing a smaller model to
save time or money is the maintainer's decision, not the plan's. If `low` effort still misses
SC-015 on real measurements, that decision comes back to the maintainer with the numbers.

## R2. One model call or two

**Decision**: one call. Its structured response contains both the candidates (10–15) and the
model's selection of the strongest 3–5, given as positions in the candidate list.

**Rationale**: two sequential calls roughly double the waiting, and ten seconds is the budget
(SC-015). One call still separates generating from choosing — the response shows both, so tests
can check that the selection really came from the candidates, and a reviewer running the app
locally can see what was passed over. The model does the choosing against the written criteria;
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
a restatement of the seed or parent, within 300 characters, selection positions valid and distinct.

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
where a cautious classifier is most likely to decline something legitimate. A fallback turns many
of those into questions instead of a dead end.

**Also**: `stop_reason` of `"max_tokens"`, or a reply that will not parse, is a malformed response
(FR-035), not a decline.

## R5. Staying inside thirty seconds

**Decision**: the model client times out at 25 seconds with no automatic retries. The function's
maximum duration is set to at least 30 seconds. The browser abandons any request at 30 seconds.

**Rationale**: the SDK retries timeouts as well as errors, so with retries on, total time can reach
the timeout multiplied by the number of attempts — which would break FR-038. With retries off, the
worst case is one attempt plus overhead, and a user who hits a failure can simply ask again.

**Verify**: the maximum function duration on Vercel's free (Hobby) plan. If it is below 30 seconds,
the client timeout must drop below that limit, and the thirty seconds in FR-038 becomes a ceiling
the platform enforces rather than one the app does.

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

**Alternatives considered**:
- *A counter in a hosted key-value store.* Works precisely, but breaks the constitution as written,
  and adds a service and a dependency.
- *A counter in the function's memory.* Resets on every cold start and is separate per running
  instance, so it would appear to protect while not doing so. Rejected as misleading.
- *A limit in the browser.* Anyone can bypass it; it is a courtesy, not a limit.

**Consequences**:
- FR-060 cannot be met as written, and its premise is wrong. See [plan.md](plan.md), Findings.
- The platform keeps per-address counts. See [plan.md](plan.md), Findings.

**Verify**: that Vercel's firewall rate limiting is available on the Hobby plan, and how it is
configured. If it is not available, the spend limit alone bounds cost, and FR-045 is not met until
the maintainer chooses between the key-value store (with a constitution amendment) or a paid plan.

## R8. The HTTP handler

**Decision**: a standard-library `BaseHTTPRequestHandler` subclass in `api/questions.py`, importing
the `inquiry` package from the repository root. No web framework.

**Rationale**: one endpoint does not need a framework, and the standard library needs no
justification under Principle V.

**Verify**: that Vercel's current Python runtime accepts this handler shape, and that it bundles a
package from the repository root with the function. If it does not, `inquiry/` moves under `api/`
into a folder whose name starts with an underscore, which keeps Vercel from treating it as a
separate endpoint.

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

## R10. Testing without the live model

**Decision**: `generate.py` receives the model client as a parameter. Tests pass a small hand-written
fake that returns canned replies: a good set, too few, too many, duplicates, a non-question, an
over-length question, a refusal, a cut-off (`max_tokens`) reply, unparseable text, and a timeout.
No mocking library.

**Rationale**: Principle II forbids tests that call the live API, and requires the failure cases.
A fake written in plain Python is easier to read than a mocking library's patching.

**Dependency justification**: `pytest` rather than the standard library's `unittest`, because plain
`assert` statements read as ordinary Python, and `unittest`'s assertion methods are one more
vocabulary for a newer developer to learn. Development only; never deployed.

## R11. The key, and the first commit

**Decision**: the key is set as `ANTHROPIC_API_KEY` in Vercel's environment settings and in an
untracked `.env` file locally. The first implementation commit is `.gitignore` — covering `.env*`,
`.vercel/` and `__pycache__/` — before any key exists anywhere. `.env.example` records the
variable's name and never a value.

**Rationale**: Principle III — a committed key is compromised the moment it is pushed, and deleting
it later does not remove it from history.

**Also verify**: where the monthly spend limit (R7) is set in the Anthropic Console, and set it
before the site is public.

## Must verify before implementation

Collected from the entries above. Each was unreachable while planning.

| Item | Entry | If it turns out otherwise |
|---|---|---|
| Maximum function duration on Vercel Hobby | R5 | Lower the client timeout below the platform limit |
| Firewall rate limiting on Vercel Hobby, and its configuration | R7 | FR-045 unmet until the maintainer chooses a store or a paid plan |
| Python handler shape and bundling of a root-level package | R8 | Move `inquiry/` under `api/_inquiry/` |
| Where the Anthropic spend limit is set | R11 | — set it before the site is public |
