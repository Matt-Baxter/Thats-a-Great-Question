# That's a Great Question

A web app that takes a seed — a topic, a claim, a half-formed idea, or a question — and returns a
small set of insightful questions worth asking about it. Any returned question can be opened to
generate further questions about *that* question, so you follow one line of inquiry deeper instead
of stopping at the first set.

**It generates questions only. It never answers them.**

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

There is no limit on how deep you can go. Nothing you type is stored anywhere but your own
browser, for the length of the session — a page refresh starts you over.

## Project status

Specification stage. No application code yet.

| Artifact | Location |
|---|---|
| Constitution — the project's governing principles | [`.specify/memory/constitution.md`](.specify/memory/constitution.md) |
| Specification — user stories, requirements, success criteria | [`specs/001-insightful-question-generator/spec.md`](specs/001-insightful-question-generator/spec.md) |
| Specification quality checklist | [`specs/001-insightful-question-generator/checklists/requirements.md`](specs/001-insightful-question-generator/checklists/requirements.md) |
| Context for AI agents working in this repository | [`CLAUDE.md`](CLAUDE.md) |

The specification defines 3 prioritized user stories with Given/When/Then acceptance scenarios,
36 functional requirements (`FR-001`–`FR-036`), and 9 measurable success criteria
(`SC-001`–`SC-009`).

## How this is being built

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

Not yet applicable — there is no application code. When there is:

The app will need an Anthropic API key, supplied through an environment variable and read
server-side only. The key will never appear in frontend code, in any response sent to the browser,
in logs, or in the repository. Setup instructions will be added here alongside the first working
version.

## Stack

- **Backend**: Python 3.11+, deployed as serverless functions
- **Frontend**: plain HTML, CSS, and JavaScript — no framework, no build step
- **Hosting**: Vercel
- **Question generation**: the Anthropic Claude API
- **Storage**: none. No database, no accounts. Anything the app remembers lives in the browser.

---

*Developed with the assistance of Claude, reviewed and edited by me.*
