# That's a Great Question

A web app that takes a seed — a topic, a claim, a half-formed idea, or a question — and returns a
small set of insightful questions worth asking about it. Any returned question can be opened to
generate further questions about *that* question, so you follow one line of inquiry deeper instead
of stopping at the first set.

**It generates questions only. It never answers them.**

## ▶ [Use the app: thats-a-great-question.vercel.app](https://thats-a-great-question.vercel.app/)

Type a topic, claim, idea or question and get back the questions worth asking about it. Nothing to
install and no account needed.

Coursework for SEIS 606: Vibe Coding, University of St. Thomas, Fall 2026 — Project 1.

## Why

People stop at their first answer. They accept the framing a topic arrives in, interrogate it
shallowly, and act on conclusions whose assumptions were never named. Existing tools make this
worse: ask a chatbot about a claim and it hands you an answer, which ends inquiry rather than
opening it.

The failure this app addresses is not a lack of information. It is never asking the question that
would have changed the conclusion.

## How it works

1. You enter a seed — anything from a single topic to a paragraph-long idea.
2. The app returns 3–5 questions about it, chosen to be insightful, consequential, or critical
   rather than merely related. They come back unlabeled, so the output does not become formulaic.
3. You open whichever question strikes you as the important one, and get 3–5 further questions
   about that question specifically.
4. A trail above the current questions shows every question you came through, starting from your
   original seed. Any entry takes you straight back — including to the seed, in one click.
5. From an earlier point you can follow a different line instead. The branch you left is unchanged
   when you return to it.
6. Any set can be asked for again, a slow request cancelled, or a new inquiry started. The app asks
   before discarding anything.

There is no limit on how deep you can go. Nothing you type is stored anywhere but your own
browser, for the length of the session — a page refresh starts you over.

## Project status

All four user stories are built. A seed returns three to five checked questions; any question
opens into questions about it, to any depth; a trail leads back to any earlier point, and branches
stay as they were; and any set can be asked for again, a slow request cancelled, or a new inquiry
started, with a confirmation before anything is discarded. Deployed to Vercel on 2026-09-26; every
push to `main` redeploys it.

The question-quality review set has been scored, and the app now runs at `high` effort, the only
level that passed every quality check (T049). A per-visitor rate limit is on, and the checks against
the live site all passed (T047). Every task in the task list is done.

### The original mockup (not the app)

[Open the mockup →](https://matt-baxter.github.io/Thats-a-Great-Question/mockups/inquiry-flow.html)

A clickable prototype made before the app was built, to settle how it should look and behave. **To
use the real app, use the link at the top of this page.** The mockup starts with an example seed
loaded, returns five numbered questions about it, and any of those can be opened to get its own
five, numbered from it. The trail across the top walks back to any earlier question, or to the
seed, in one click.

It calls no model. Every question shown is written by hand as an example of the shape and calibre
of question the app is meant to return, and the pause before a set appears is a fixed timer
standing in for a real request.

> GitHub never renders HTML files: clicking `mockups/inquiry-flow.html` in the file list shows its
> source code, not the page. Use the link above to run the mockup.

### Where everything lives

| What | Link | Opens as |
|---|---|---|
| **The app — use it** | [thats-a-great-question.vercel.app](https://thats-a-great-question.vercel.app/) | the live website |
| UI mockup — the prototype made before the app | [mockup page](https://matt-baxter.github.io/Thats-a-Great-Question/mockups/inquiry-flow.html) | a clickable web page, no model connected |
| UI mockup — read the source | [`mockups/inquiry-flow.html`](mockups/inquiry-flow.html) | HTML source on GitHub |
| Constitution — the project's governing principles | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | rendered document |
| Specification — user stories, requirements, success criteria | [`specs/001-insightful-question-generator/spec.md`](specs/001-insightful-question-generator/spec.md) | rendered document |
| Task list — the 50 build steps, all done |  [`specs/001-insightful-question-generator/tasks.md`](specs/001-insightful-question-generator/tasks.md) | rendered document |
| Implementation plan — how it is built, and why | [`specs/001-insightful-question-generator/plan.md`](specs/001-insightful-question-generator/plan.md) | rendered document |
| Specification quality checklist | [`specs/001-insightful-question-generator/checklists/requirements.md`](specs/001-insightful-question-generator/checklists/requirements.md) | rendered document |
| Review set — 10 seeds and their questions at two effort levels, scored by hand to choose the effort level | [`specs/001-insightful-question-generator/review-set.md`](specs/001-insightful-question-generator/review-set.md) | rendered document |
| Review history — every question asked of the spec, and every defect found | [`specs/001-insightful-question-generator/checklists/reviews.md`](specs/001-insightful-question-generator/checklists/reviews.md) | rendered document |
| Context for AI agents working in this repository | [`CLAUDE.md`](CLAUDE.md) | rendered document |
| Every judgment the app makes — checks, prompt, lines of inquiry, messages | [`inquiry/`](inquiry/) | Python source |
| The one HTTP endpoint, which only passes values to `inquiry/` | [`api/questions.py`](api/questions.py) | Python source |
| The page, the inquiry tree, and how replies are shown | [`public/`](public/) | HTML, CSS, JavaScript |
| Tests — none calls the live model | [`tests/`](tests/) | Python and JavaScript |

The specification defines 4 prioritized user stories with Given/When/Then acceptance scenarios,
61 functional requirements (`FR-001`–`FR-061`), and 20 measurable success criteria
(`SC-001`–`SC-020`), with five clarifications recorded from the clarify phase.

## How this was built

Spec-driven development using [Spec Kit](https://github.com/github/spec-kit), following the
workflow: constitution → specify → plan → tasks → implement. The constitution is read at the start
of every session and shapes every decision downstream; requirements carry IDs so any piece of code
traces back to a stated reason for existing.

One thing worth naming, because it is the interesting problem in this project rather than a gap:
**what makes a question good cannot be scored automatically.** The specification splits the two
honestly. Whether a response has the right *shape* — 3–5 questions, non-empty, phrased as
questions, distinct from each other and from the seed, within a length bound — is checked by
automated tests. Whether the questions are actually *insightful* is assessed by human review over a
defined set of varied seeds, and the specification says so rather than inventing a metric that
would be false precision.

## Running it locally

You need Python 3.11 or newer, Node.js (for the Vercel CLI and the browser-logic tests), the
[Vercel CLI](https://vercel.com/docs/cli) for `vercel dev`, and an Anthropic API key.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # then put your key after QUESTION_APP_API_KEY=
git check-ignore .env              # must print ".env"; if it prints nothing, stop
pytest                             # needs no key, and never calls the live model
node --test "tests/*.test.mjs"     # the inquiry tree and how replies are shown; no packages
vercel dev                         # serves the page and the API together
```

**The key.** The app reads its Anthropic API key from `QUESTION_APP_API_KEY` — deliberately not
the SDK's usual `ANTHROPIC_API_KEY`, so a key set for another tool on the same machine is never
used — and always sends it to `https://api.anthropic.com`, whatever `ANTHROPIC_BASE_URL` says. The
key is read in server-side Python only. It never appears in frontend code, in any response sent to
the browser, in logs, or in the repository; `.env` is git-ignored. When deploying, set the same
variable in the Vercel project's environment settings.

The full validation guide is [quickstart.md](specs/001-insightful-question-generator/quickstart.md).

## Stack

- **Backend**: Python 3.11+, deployed as serverless functions
- **Frontend**: plain HTML, CSS, and JavaScript — no framework, no build step
- **Hosting**: Vercel
- **Question generation**: the Anthropic Claude API
- **Storage**: none. No database, no accounts. Anything the app remembers lives in the browser.

---

*Developed with the assistance of Claude, reviewed and edited by me.*
