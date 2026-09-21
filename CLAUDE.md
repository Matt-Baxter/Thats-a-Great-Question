# CLAUDE.md

Read this before doing anything in this repository.

## Read the constitution first

`.specify/memory/constitution.md` governs this project. Read it at the start of every session,
before writing code, specs, plans, or tests — not only when running a `/speckit-*` command.

Where it conflicts with the fastest path, it wins. If a principle genuinely blocks necessary
work, amend it deliberately in a commit that says what changed and why, and bump the version.
Do not quietly ignore it.

The five principles, in short. The file itself is the authority.

1. **Explainable code over clever code** (non-negotiable) — the author must be able to read any
   file cold and understand it. No metaprogramming, no clever one-liners.
2. **Tests cover decisions, not percentages** — every function that transforms data or makes a
   decision gets a test, including failure cases. Tests never call the live model API.
3. **Secrets never reach the browser or the repository** (non-negotiable) — the model API key is
   read from an environment variable, server-side only.
4. **Model output is untrusted input** — validate every response before display, render as plain
   text, fail with a clear message.
5. **Small and finished beats large and broken** — no feature without a numbered requirement, no
   abstraction until two concrete cases need it.

## What this project is

**That's a Great Question** — a web app that takes a seed (a topic, claim, half-formed idea, or
question) and returns 3–5 insightful questions worth asking about it. Any returned question can be
opened to generate further questions about that question, so a user follows one line of inquiry
deeper instead of stopping at the first set.

**It generates questions only. It never answers them.** This is the load-bearing boundary — without
it the app drifts into being a general chatbot.

Coursework for SEIS 606 (Vibe Coding), University of St. Thomas. Project 1.

## Where things live

| Path | What it holds |
|---|---|
| `.specify/memory/constitution.md` | The governing principles. Read first. |
| `specs/001-insightful-question-generator/spec.md` | The specification: user stories, FR-NNN requirements, SC-NNN success criteria. |
| `specs/001-insightful-question-generator/checklists/` | Quality checklists for the spec. |
| `.claude/skills/speckit-*/` | The `/speckit-*` commands. |
| `.specify/templates/` | Templates those commands fill. |

Working notes, scope decisions, and course artifacts live in a separate repository:
`Matt-Baxter/seis-606-vibe-coding`. Keep this repository to the project itself.

## Conventions

- **Spec before code**: specify → plan → tasks → implement. Requirements carry IDs (`FR-NNN`,
  `SC-NNN`); tasks and tests cite the requirement they serve.
- **Commits** are authored as `Matt-Baxter <Matthew.Baxter03@gmail.com>` with Claude as
  co-author, and explain *why* a change was made, not only what changed.
- **Specs, plans, and tasks belong on the default branch** before anything is handed in. Work on a
  side branch is invisible to anyone reading the repository.
- **Disclose AI assistance** in work products, per course policy.

## Stack

Python serverless backend on Vercel, plain HTML/CSS/JS frontend with no framework and no build
step, question generation via the Anthropic Claude API. Nothing is stored server-side; anything the
app remembers lives in the browser only, for the session.

Note the division of labour: **all logic involving judgment lives in Python.** JavaScript is
limited to sending requests and displaying results. The maintainer reads Python comfortably and is
newer to JavaScript, so keep judgment out of the frontend.

## One thing to get right

The project exists as a corrective. An earlier project by the same author produced predictions its
own author could not explain. This one is meant to be traceable end to end. Surface the
uncomfortable finding rather than the flattering one, and do not round results up.
