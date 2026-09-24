# Quickstart: That's a Great Question

How to run the app and prove it meets the specification. This is a validation guide, not an
implementation guide; the build steps come from `tasks.md`.

## Prerequisites

- Python 3.11 or newer
- Node.js — for the Vercel CLI (local running and deploying) and `node --test` (browser tree tests)
- A Vercel account with this repository connected
- An Anthropic API key, with a **monthly spend limit set on the account before the site is public**
  (research.md R7, R11)

## Set up

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # then put your key in .env — never commit it
```

Confirm `.env` is ignored before going further:

```bash
git check-ignore .env              # must print ".env"; if it prints nothing, stop
```

## Automated tests — no API key needed

```bash
pytest                             # every Python check, against a fake model client
node --test tests/                 # browser tree logic
```

Both must pass before any commit is pushed (constitution, Development Workflow). Neither calls the
live model. If either needs a key, that is a defect in the tests.

| What the tests prove | Requirements |
|---|---|
| Empty and over-length seeds rejected before any model call | FR-002, FR-003, SC-004 |
| Wrong question count rejected, never truncated or padded | FR-005, SC-003 |
| Duplicates, non-questions, over-length and seed-restating questions rejected | FR-006, FR-007, FR-009, FR-010, SC-002 |
| A refusal becomes a `declined` result with no refusal text | FR-051 to FR-053, SC-016 |
| Cut-off, unparseable and timed-out replies become `failed` | FR-035, SC-004 |
| Long chains keep the seed and the most recent six ancestors | research.md R6 |
| No seed or question text reaches log output | FR-048, SC-014 |
| Revisiting an opened question reuses its children | FR-022, SC-007 |
| A failed or cancelled regeneration changes nothing | FR-029, FR-059, SC-019 |
| Confirmations count what will be discarded | FR-028, FR-057, SC-008, SC-018 |

## Run it locally

```bash
vercel dev                         # serves public/ and the api/ function together
```

Open the address it prints.

## Validate by hand

Each scenario maps to the specification. Run them on a desktop browser and again at phone width.

1. **Seed to questions** — submit a seed. A loading state appears at once; 3–5 questions follow.
   None is answered. (User Story 1; FR-031, FR-037)
2. **Open a question** — the new set is about that question, not the seed, numbered from it.
   (User Story 2)
3. **Go deep, come back** — open five levels down. The trail shows every ancestor; one click returns
   to the seed. (User Story 3; SC-006)
4. **Switch branches** — from an earlier level, open a sibling; then return to the first branch. It
   appears instantly with the same questions and no loading state. (FR-022, FR-025; SC-007)
5. **Ask again** — on a question with descendants, the confirmation says how many will be discarded.
   Decline it: nothing changes. Accept it: new questions, descendants gone. (User Story 4; SC-008)
6. **New seed** — with an inquiry open, start a new one. Confirm first; then the old one is gone
   without a reload. (FR-057; SC-018)
7. **Cancel** — cancel a request mid-load. Nothing changes; the next request is accepted. (SC-019)
8. **Click while busy** — open a second question during a load. It is ignored, and the page shows
   it is busy. (FR-054, FR-055; SC-017)
9. **Empty and over-length seeds** — both rejected with a message naming the problem; the second
   names the limit. (FR-002, FR-003)
10. **Failure** — set an invalid key in `.env` and restart. Submitting shows a plain-language failure
    and the page stays usable. Restore the key. (FR-035, FR-039)
11. **Keyboard only** — repeat scenarios 1–5 without a mouse. (FR-043; SC-012)
12. **Reload** — mid-inquiry, reload the page. It returns empty. (FR-042)

## Measure against the numbers

- **Speed (SC-015)** — time twenty consecutive requests across varied seeds. At least eighteen must
  finish within ten seconds. If fewer do, lower effort first; then bring the numbers to the
  maintainer (research.md R1).
- **Quality (SC-009, SC-010, SC-011)** — run the review set of at least twenty seeds spanning
  technical, social and philosophical subjects. Include deliberately factual seeds (spec,
  Assumptions) and adversarial seeds that try to make the app answer (research.md R9). Score by
  hand against the three criteria.

## Deploy

1. Set `ANTHROPIC_API_KEY` in the Vercel project's environment settings.
2. Configure the firewall rate-limit rule on `/api/questions` (research.md R7 — verify it is
   available first).
3. Confirm the Anthropic spend limit is set.
4. Push to `main`; Vercel deploys it.
5. Repeat scenarios 1, 3 and 10 against the live address.
