# That's a Great Question

Give it a topic, a claim, or a half-formed idea, and it gives back the questions worth asking
about it. **It never answers them.**

### ▶ Try it: [thats-a-great-question.vercel.app](https://thats-a-great-question.vercel.app/)

SEIS 606 (Vibe Coding), University of St. Thomas, Fall 2026 — Project 1.

## How it works

1. Enter a seed: a topic, claim, idea or question.
2. Get 3–5 questions about it.
3. Open any question to get questions about *that* question, as deep as you like.
4. A trail leads back to any earlier point. You can also ask again, cancel, or start over.

Nothing you type is stored. Refreshing the page starts you over.

## What's in this repository

| Folder | What's in it |
|---|---|
| [`inquiry/`](inquiry/) | The app's logic in Python: input checks, the prompt sent to Claude, answer checks, messages |
| [`api/`](api/) | The web endpoint the page calls |
| [`public/`](public/) | The web page |
| [`tests/`](tests/) | Automated tests; none calls the real Claude API |
| [`specs/`](specs/001-insightful-question-generator/) | The specification, plan, task list, and review results |
| [`mockups/`](mockups/) | The clickable prototype made before the app ([open it](https://matt-baxter.github.io/Thats-a-Great-Question/mockups/inquiry-flow.html)) |

The folders starting with a dot hold tooling. The project's ground rules are in
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## How it was built

Spec-driven development with [Spec Kit](https://github.com/github/spec-kit): constitution →
specification → plan → tasks → code. Every requirement has an ID (`FR-001` to `FR-062`) that the
code and tests point back to. Question quality can't be measured automatically, so it was scored
by hand on a [review set](specs/001-insightful-question-generator/review-set.md).

Python on Vercel, plain HTML/CSS/JavaScript with no framework, and the Anthropic Claude API.

## Running it locally

You need Python 3.11+, Node.js, the [Vercel CLI](https://vercel.com/docs/cli), and an Anthropic API
key.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env               # put your key after QUESTION_APP_API_KEY=
pytest                             # Python tests
node --test "tests/*.test.mjs"     # browser tests
vercel dev                         # run the app
```

The key is read only by the server, from `QUESTION_APP_API_KEY`. It never reaches the browser or
the repository. Full setup and manual checks:
[quickstart.md](specs/001-insightful-question-generator/quickstart.md).

---

*Developed with the assistance of Claude, reviewed and edited by me.*
