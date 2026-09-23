# UI Mockup

### ▶ [Open the mockup in your browser →](https://matt-baxter.github.io/Thats-a-Great-Question/mockups/inquiry-flow.html)

That link runs it. Clicking `inquiry-flow.html` in the file list above shows the source code
instead — GitHub never renders HTML files, so the two links lead to the same file but do
completely different things.

If the link does not load, download `inquiry-flow.html` and open it in any browser. It is
self-contained and needs nothing installed.

## What it shows

A clickable walkthrough of the whole inquiry flow:

1. It opens with an example seed already loaded — replace it with anything you like.
2. Submitting returns five numbered questions about it.
3. Opening any question returns five more, numbered from it: question 2 gives 2.1 through 2.5.
4. The trail across the top walks back to any earlier question, or to the seed, in one click.
5. From there you can follow a different line. The branch you left is unchanged when you return —
   no loading pause, because the inquiry is kept for the session.

It also mocks the states that are easy to leave out: the empty and over-length seed messages, a
loading state with a working Cancel, and confirmations that name what will be lost before
discarding anything.

## What it is not

**No model is connected.** Every question shown is written by hand as an example of the shape and
calibre of question the app is meant to return, and the pause before a set appears is a fixed
timer standing in for a real request.

## How it relates to the specification

Built as plain HTML, CSS and JavaScript with no framework and no build step, matching the stack
named in [the constitution](../.specify/memory/constitution.md). The requirements it demonstrates
are listed in a comment at the top of the file, and defined in
[the specification](../specs/001-insightful-question-generator/spec.md).

---

*Developed with the assistance of Claude, reviewed and edited by me.*
