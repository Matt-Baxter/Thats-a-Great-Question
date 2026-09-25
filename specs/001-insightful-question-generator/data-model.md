# Data Model: That's a Great Question

Nothing here is stored on a server. The browser holds the inquiry tree for the session; the server
sees one request at a time and forgets it. Limits below are the named constants in
`inquiry/config.py`.

## In the browser

### Node

One seed or one question in the inquiry tree.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique within the session |
| `kind` | `"seed"` or `"question"` | Exactly one node per tree is the seed |
| `label` | string | Hierarchical number: `""` for the seed, `"2"`, `"2.3"`, `"2.3.1"` |
| `text` | string | The seed as typed, or the question as returned |
| `parentId` | string or null | Null only for the seed |
| `childIds` | list of strings, or null | **Null means never opened.** An empty list never occurs |
| `state` | see below | Whether a request for this node's children is in progress |

**Rules**
- A node's children are numbered from it: the children of `2.3` are `2.3.1` through `2.3.5`.
- `childIds` goes from null to a list exactly once per generation. Opening a node that already has
  children shows them without a request (FR-022).

### State transitions of a node

```text
            open                      success
unopened ─────────► loading ─────────────────────► expanded
   ▲                   │ failure, decline,                │
   └───────────────────┘ limit, or cancel                 │ ask again
                                                          ▼
                           success: children replaced,   loading
                           everything below discarded ◄──┘
                           failure or cancel: unchanged ──► expanded
```

- **unopened → loading**: user opens a node with no children (FR-023).
- **loading → expanded**: a valid set arrives; it is attached to *this* node and no other (FR-056).
- **loading → unopened**: anything else — failure, decline, rate limit, or cancel. Nothing is added
  (FR-036, FR-047, FR-059).
- **expanded → loading**: user asks again. If the node has descendants, a confirmation naming how
  many will be lost comes first (FR-028).
- **loading → expanded, regenerated**: the new set replaces the old one and everything beneath it is
  discarded (FR-027).
- **loading → expanded, unchanged**: a failed or cancelled regeneration leaves everything as it was
  (FR-029).

While any node is loading, no other request can start (FR-054).

### Inquiry tree

All nodes of the session. One seed; every other node has exactly one parent.

- Discarded on page reload (FR-042), or on a new seed after the user confirms (FR-057).
- Never sent to the server as a whole — only one chain at a time (see below).

### Trail

Not stored. Computed from the tree: the path of nodes from the seed to the node being viewed. Shown
above the current questions; every entry navigates in one action (FR-017, FR-019).

## Between the browser and the server

### Generation request

What the browser sends for one set of questions. Full shapes in
[contracts/questions-api.md](contracts/questions-api.md).

| Field | Type | Server-side check |
|---|---|---|
| `seed` | string | Not empty after trimming (FR-002); at most 2,000 characters (FR-003) |
| `ancestors` | list of strings, possibly empty | Each at most 300 characters, not empty; the list is the path from the seed's first question down to the question being opened |

The question being opened is the last entry of `ancestors`, or the seed when the list is empty. The
server keeps the seed plus the most recent six ancestors when building the prompt.

### Generation result

What the server returns. Exactly one of these outcomes.

| Outcome | Carries | When |
|---|---|---|
| `ok` | 3–5 questions | The model's selection passed every check |
| `declined` | a message | The model, and its fallback, declined (FR-051 to FR-053) |
| `invalid_input` | a message | The request failed a server-side check (FR-002, FR-003) |
| `failed` | a message | Timeout, unreachable model, or a reply that failed validation (FR-035) |

Every message is written in `inquiry/messages.py`. The browser displays it as text and never
composes one — except when no reply from this application exists to carry one: the platform's
rate-limit response, the browser giving up at 30 seconds, and a network failure or unreadable
reply ([contracts/questions-api.md](contracts/questions-api.md)).

## Inside the server

### Model reply

The structured reply requested from the model, before any checking.

| Field | Type | Meaning |
|---|---|---|
| `candidates` | list of strings | The wider set, target 10–15 |
| `selected` | list of integers | Positions in `candidates` of the chosen 3–5 |

**Checks applied, in order** — a reply failing any of them becomes a `failed` result, never a
repaired one (FR-005):

1. `selected` has 3–5 entries, all distinct, all valid positions in `candidates`.
2. Each selected question, after trimming, is non-empty and ends with a question mark (FR-006).
3. Each is at most 300 characters (FR-010).
4. No two are the same once normalised — lower-cased, punctuation removed, whitespace collapsed (FR-007).
5. None normalises to the same text as the seed or question being opened (FR-009).

Checks for different angles (FR-008) and for leading or rhetorical questions (FR-011) are
judgements, handled by the model's selection criteria and verified by human review (SC-010, SC-011).
No automated check claims them.

### Line of inquiry

One entry in `inquiry/lines_of_inquiry.py`.

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Short name: "assumption", "evidence", "incentive" |
| `description` | string | One sentence the model reads, saying what this angle looks for |

Guides generation. Never shown to the user and never attached to a question (FR-012).
