# Contract: Questions API

The only interface the app exposes. The browser calls it once per set of questions — for the seed,
for any question being opened, and for any regeneration.

## `POST /api/questions`

### Request

`Content-Type: application/json`

```json
{
  "seed": "Superintelligence will arrive before governance is ready for it.",
  "ancestors": [
    "Is the binding constraint the pace of capability or the pace of institutions?"
  ]
}
```

| Field | Required | Rules | Requirement |
|---|---|---|---|
| `seed` | yes | string; not empty after trimming; at most 2,000 characters | FR-001, FR-002, FR-003 |
| `ancestors` | yes | list of strings, possibly empty; each not empty and at most 300 characters | FR-014, FR-016 |

- An empty `ancestors` asks for questions about the seed.
- Otherwise the **last** entry is the question being opened, and the entries before it are its
  ancestors in order from the seed downward.
- The server trusts none of it and re-checks everything, even though the browser checks the seed
  first.
- The request body is capped in size. This is a practical ceiling on depth of several hundred
  levels, recorded in [plan.md](../plan.md).

### Responses

Every response the application writes is JSON with a `status` field. The browser branches on
`status`, and displays `message` exactly as text.

**200 — questions**

```json
{
  "status": "ok",
  "questions": [
    "What would \"ready\" actually look like — which institutions would have to exist?",
    "What observable signal in the next two years would most change your confidence in this timing?",
    "Who benefits from governance staying unprepared?"
  ]
}
```

`questions` holds 3–5 strings, each already checked against FR-004 to FR-010. Never labelled, never
accompanied by an answer or commentary (FR-012, FR-031).

**200 — declined**

```json
{
  "status": "declined",
  "message": "No questions could be generated for this question. Rephrasing it may help."
}
```

A decline is not an error, so it is not an error status (FR-052). The message names the seed or the
question, whichever the request concerned. The refusal's own text is never included (FR-053).

**400 — invalid input**

```json
{
  "status": "invalid_input",
  "message": "A seed can be up to 2,000 characters. This one is 3,412."
}
```

For an empty seed, an over-length seed, or a malformed request (FR-002, FR-003).

**502 — failed**

```json
{
  "status": "failed",
  "message": "The questions could not be generated just now. Try again in a moment."
}
```

For an unreachable model, or a reply that failed validation — wrong count, duplicates, a
non-question, over-length, cut off, or unparseable (FR-005, FR-035).

**504 — timed out**

```json
{
  "status": "failed",
  "message": "That took too long and was stopped. Try again."
}
```

When the model call exceeds its timeout (FR-038).

**405 — method not allowed**

Any method other than POST. No body is promised.

**429 — too many requests** *(written by the platform, not this application)*

Returned by the hosting platform's rate limit (FR-045). The body is the platform's, not this
contract's, so the browser shows its own fixed wait-and-try-again message for any 429 (FR-046).

That is one of exactly two user-facing messages not written in `inquiry/messages.py`. The other is
the browser's own message when it abandons a request at 30 seconds, since by then no response has
arrived to carry one. Both are fixed strings, not judgments.

### Guarantees

- **Nothing is recorded.** No seed, ancestor, or question text is written to a log, an error trace,
  or any other record on the server. What is recorded is the outcome, its category, and the depth
  of the request (FR-048, FR-049).
- **Nothing is sent elsewhere.** The request's content goes to the model provider and nowhere else
  (FR-050).
- **Every request ends within 30 seconds** with one of the responses above (FR-038).
- **The server remembers nothing** between requests. Two identical requests are handled
  independently, and may return different questions.

## The browser's side

Not an HTTP contract, but the obligations that make the one above work:

- Send no second request while one is in flight (FR-054), and show that it is busy (FR-055).
- Abandon any request after 30 seconds and show the timed-out message.
- On cancel, abandon the request and leave the tree exactly as it was (FR-058, FR-059). The model
  call on the server may still complete and be billed — see research.md R7.
- Attach an `ok` result to the node it was requested for and no other (FR-056).
- Insert every string from the server with `textContent`, never as markup (FR-034).
