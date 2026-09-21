# Feature Specification: That's a Great Question — Insightful Question Generation

**Feature Branch**: `001-insightful-question-generator`

**Created**: 2026-09-21

**Status**: Draft

**Input**: User description: A web app that takes a seed — a topic, a claim, a half-formed idea, or a question — and returns a small set of insightful questions worth asking about it. Any returned question can be opened to generate further questions about that question, so a user follows one line of inquiry deeper instead of stopping at the first set. The app generates questions only. It never answers them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get questions about a seed (Priority: P1)

A person is reasoning through a complex claim or decision on their own. They type the claim, topic, or half-formed idea into a single text box and submit it. Within seconds they receive three to five questions about it — questions chosen to be insightful, consequential, or critical rather than merely related. They read them and notice at least one thing they had not thought to ask.

**Why this priority**: This is the entire premise of the product in its smallest useful form. A person who only ever used this one capability would still get the core value: their thinking interrogated by questions they did not generate themselves. Every other story builds on it.

**Independent Test**: Can be fully tested by entering a seed and confirming that a set of 3–5 well-formed, distinct questions is returned, and that no answers appear anywhere. Delivers value with no other functionality present.

**Acceptance Scenarios**:

1. **Given** the app is open with an empty text box, **When** the user enters a seed and submits it, **Then** between three and five questions about that seed are displayed.
2. **Given** a seed has been submitted, **When** the questions are displayed, **Then** each question is non-empty, is phrased as a question, is different from every other question shown, and is different from the seed itself.
3. **Given** a seed has been submitted, **When** the response is displayed, **Then** no answer, explanation, or commentary about any question appears.
4. **Given** the user has submitted a seed, **When** the request is in progress, **Then** a visible loading state is shown from the moment of submission until the result appears.

---

### User Story 2 - Expand a question into deeper questions (Priority: P2)

Having read the first set of questions, the user finds one that strikes them as the important one. They open it, and receive three to five further questions about *that question* specifically — not about the original seed. They can repeat this as many times as they want, following a single line of inquiry as far as it goes.

**Why this priority**: This is what separates the product from a one-shot prompt. It is where "follow a line of inquiry deeper instead of stopping at the first set" actually happens. It is P2 rather than P1 only because it cannot exist without P1 — there must be a first question before there is a second.

**Independent Test**: Can be fully tested by expanding a returned question and confirming that the new questions interrogate that question rather than restating questions about the seed, and that expansion can be repeated without an imposed limit.

**Acceptance Scenarios**:

1. **Given** a set of questions is displayed, **When** the user opens one of them, **Then** between three and five further questions about that specific question are displayed.
2. **Given** a question has been expanded, **When** the new questions are displayed, **Then** they address the expanded question rather than the original seed.
3. **Given** the user has expanded questions several times in succession, **When** they continue expanding, **Then** the app imposes no limit on how deep they may go.
4. **Given** a question is being expanded, **When** the request is in progress, **Then** a visible loading state is shown and the questions already on screen remain readable.

---

### User Story 3 - Stay oriented and move between lines of inquiry (Priority: P3)

The user has followed one line of questioning several levels down. Above the current set they see a compact trail of every question they came through, starting from the original seed, so they always know where they are in their own reasoning. Clicking any question in that trail takes them straight back to it — including all the way to the seed in a single click. Having gone back, they can open a different question at that level and follow a second line of inquiry instead, without losing the first: returning to the earlier branch shows the same questions it showed before.

**Why this priority**: Without it the app is still usable — a user can expand and read — but the deeper they go, the less the output means, because a question detached from its lineage loses the thread that made it worth asking. And a user who cannot come back up is forced into whichever branch they happened to open first. It is P3 because value degrades gradually with depth rather than failing outright.

**Independent Test**: Can be fully tested by expanding to at least five levels, confirming the full trail from seed to current question is visible and each entry navigates correctly, then returning to an earlier level, opening a different question there, and confirming the original branch is unchanged when revisited. Verifiable on both a desktop and a phone-sized screen.

**Acceptance Scenarios**:

1. **Given** the user has expanded questions five or more levels deep, **When** they look at the display, **Then** a trail showing every ancestor from the original seed to the current question is visible, and the current question is shown in full.
2. **Given** a trail of ancestors is displayed, **When** the user selects any entry in it, **Then** they are returned to that question and its existing child questions.
3. **Given** the user is deep in one line of inquiry, **When** they return to the original seed, **Then** it takes a single action regardless of how deep they were.
4. **Given** the user has returned to an earlier level, **When** they open a different question at that level, **Then** questions about that question are generated and displayed.
5. **Given** the user has explored two different branches, **When** they navigate back to the first branch, **Then** it shows the same questions it showed originally, with no new generation.
6. **Given** a deep chain of questions, **When** the app is viewed on a phone-sized screen, **Then** the trail and the current questions remain readable without horizontal scrolling.

---

### Edge Cases

- **Empty seed**: The user submits nothing, or only whitespace. The submission is rejected with a plain-language message before any generation is attempted.
- **Over-length seed**: The user pastes a document instead of a seed. The submission is rejected with a message that names the length limit.
- **Generation unavailable**: The question source cannot be reached. The user sees a plain-language message and the app remains usable.
- **Malformed output**: Generation returns something that is not a usable set of questions — empty, unparseable, or structurally wrong. The user sees a plain-language message rather than raw or partial output.
- **Too few questions**: Generation returns fewer than three questions. This is treated as a failed response, not displayed as a short list.
- **Over-length question**: A returned question exceeds the maximum question length. The response is treated as unusable rather than displayed truncated.
- **Slow response**: Generation does not complete promptly. The request resolves to either questions or a message within thirty seconds, never hanging indefinitely.
- **Deep chain**: The user expands many levels. No limit is imposed, and the display continues to function.
- **Revisiting an expanded question**: The user navigates back to a question they already expanded. Its existing questions are shown; nothing is regenerated and nothing is lost.
- **Failed expansion, then retry**: An expansion fails. The user sees a message, the tree is unchanged, and the same question can be expanded again.
- **Refresh mid-inquiry**: The user reloads the page. They return to an empty starting state, with no part of the inquiry restored.
- **Narrow screen**: The app is used on a phone. All content, including a deep trail, remains readable and every control remains reachable.

## Requirements *(mandatory)*

### Functional Requirements

**Accepting a seed**

- **FR-001**: System MUST accept a free-text seed, which may be a topic, a claim, a half-formed idea, or a question.
- **FR-002**: System MUST reject an empty or whitespace-only seed with a plain-language message, before any generation is attempted.
- **FR-003**: System MUST reject a seed longer than the maximum seed length with a message that names the limit.

**Generating questions**

- **FR-004**: System MUST return between three and five questions in every successful response.
- **FR-005**: System MUST ensure every returned question is non-empty and is phrased as a question.
- **FR-006**: System MUST ensure every returned question is distinct from every other question in the same response.
- **FR-007**: System MUST ensure every returned question is distinct from the seed or question it was generated from.
- **FR-008**: System MUST ensure every returned question falls within the maximum question length.
- **FR-009**: System MUST generate questions by drawing on an explicit, written, human-readable list of lines of inquiry, and MUST return questions without type labels attached.

**Expanding a question**

- **FR-010**: Users MUST be able to open any returned question to generate further questions about it.
- **FR-011**: System MUST generate expansion questions about the question being expanded, not about the original seed.
- **FR-012**: System MUST NOT impose any limit on how many times a user may expand.
- **FR-013**: System MUST apply FR-004 through FR-009 to expansion responses identically to first-level responses.

**Staying oriented**

- **FR-014**: System MUST display, above the current set of questions, a trail of every ancestor from the original seed through to the question currently being viewed.
- **FR-015**: System MUST display the question currently being viewed in full, and MAY abbreviate ancestors in the trail to keep it compact.
- **FR-016**: Users MUST be able to return to any ancestor in the trail, including the original seed, with a single action.
- **FR-017**: System MUST show only the current question and its direct child questions alongside the trail, rather than the whole accumulated tree.

**Moving between lines of inquiry**

- **FR-018**: System MUST retain, for the duration of the browser session, every question generated and the parent-child structure connecting them.
- **FR-019**: System MUST display the questions already generated for a question when the user returns to it, without generating new ones.
- **FR-020**: System MUST generate questions when the user opens a question that has not been expanded before.
- **FR-021**: Users MUST be able to open any sibling of a question they have already expanded, and MUST NOT be confined to a single line of inquiry.
- **FR-022**: System MUST leave a previously explored branch unchanged when the user explores a different one.

**Never answering**

- **FR-023**: System MUST NOT provide answers, explanations, or commentary on any question it generates.
- **FR-024**: System MUST present generated questions as suggestions, never as authoritative or complete.

**Treating generated content as untrusted**

- **FR-025**: System MUST validate every generated response — shape, count, and non-emptiness — before any part of it is displayed.
- **FR-026**: System MUST display generated text exactly as text, never interpreting it as markup, formatting, or instructions.

**Failing safely**

- **FR-027**: System MUST show a plain-language message when generation fails, is unavailable, or returns unusable output, and MUST remain usable afterward.
- **FR-028**: System MUST leave the existing tree of questions unchanged when an expansion fails, and MUST allow the same question to be opened again.
- **FR-029**: System MUST display a visible loading state from the moment a request begins until it resolves.
- **FR-030**: System MUST resolve every request to either questions or a message within thirty seconds.
- **FR-031**: System MUST NOT crash, hang, or present a blank screen under any failure condition.

**Privacy and persistence**

- **FR-032**: System MUST NOT store anything a user types anywhere other than the user's own browser session.
- **FR-033**: System MUST NOT require an account, login, or any user identification.
- **FR-034**: System MUST return the user to an empty starting state when the page is reloaded, retaining no part of the previous inquiry.

**Access**

- **FR-035**: System MUST make every interactive element reachable and operable using a keyboard alone.
- **FR-036**: System MUST remain usable on a phone-sized screen, with no horizontal scrolling required to read content.

### Key Entities

- **Seed**: The free text a user submits to begin an inquiry. Bounded in length. The root of the inquiry tree. Not retained beyond the user's browser session.
- **Question**: A single generated question. Non-empty, phrased as a question, bounded in length, unlabeled, and distinct from its siblings and from its parent. Never accompanied by an answer. May be unexpanded, or expanded and therefore holding children of its own.
- **Inquiry Tree**: The whole structure built during a session — the seed, every question generated from it, and the parent-child links between them. Retained in full for the session so the user can move freely between branches; discarded entirely on reload.
- **Trail**: The ordered path from the seed to the question currently being viewed. What the user is shown in order to stay oriented, and the means by which they navigate back up. A view onto the tree rather than a separate structure.
- **Lines of Inquiry**: The explicit written list of angles a question may take — assumption, evidence, consequence, alternative, stakeholder, definition, framing, precedent, incentive, failure mode, and others. Guides generation; is not exposed as labels on output.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of submitted requests resolve to either a set of questions or a plain-language message within thirty seconds.
- **SC-002**: 100% of successful responses contain between three and five questions, each non-empty, phrased as a question, distinct from its siblings, distinct from its parent, and within the maximum question length.
- **SC-003**: 100% of induced failure conditions — unreachable generation, malformed output, empty output, too few questions, empty seed, over-length seed — produce a plain-language message with no crash, hang, or blank screen.
- **SC-004**: A first-time user, given no instructions, can go from opening the app to reading generated questions in under sixty seconds.
- **SC-005**: A user at any depth can identify the original seed from the trail and return to it in a single action, on both a desktop and a phone-sized screen.
- **SC-006**: 100% of returns to a previously expanded question, within a session, display the same questions that were shown before, with no new generation.
- **SC-007**: Across a review set of at least twenty varied seeds spanning technical, social, and philosophical subjects, a human reviewer judges that at least 80% of responses contain at least one question the reviewer had not already considered.
- **SC-008**: Across the same review set, 100% of responses contain no answers, no commentary, and no question that merely restates the seed.
- **SC-009**: 100% of interactive elements can be reached and operated using a keyboard alone.

## Assumptions

- **Maximum seed length is 2,000 characters.** The input description required a cap and a message naming it, but did not fix a value. Two thousand characters comfortably holds a topic, a claim, or a paragraph-long idea while rejecting a pasted document. Adjustable without affecting any other requirement.
- **Maximum question length is 300 characters.** Chosen so a question stays readable at a glance on a phone, including within a trail. Also adjustable in isolation.
- **Generation happens once per question.** Opening a question that has never been expanded generates its children; returning to one that already has children displays them. Backtracking is only meaningful if a branch is stable, so results are not regenerated on revisit.
- **The inquiry tree lives only in the browser, only for the session.** It is retained so the user can move between branches, and discarded on reload. Nothing is written to a server.
- **Question quality cannot be scored automatically.** Whether a question is genuinely insightful is context-dependent and assessed by human review (SC-007, SC-008). The automated criteria in SC-002 check the *shape* of a response, not its worth. No metric in this specification claims otherwise, because one that did would be false precision.
- **Users have an internet connection and a current browser.**
- **Users want questions, not answers.** Someone seeking answers is explicitly not a target user and will find the product frustrating by design.
- **A single user, in a single browser session, with no collaboration.** Nothing is shared, synced, or visible to anyone else.
- **English-language seeds and questions for the first version.** Other languages are neither prevented nor guaranteed.

## Out of Scope

- Answering questions, or offering explanation or commentary on them
- Accounts, login, or syncing across devices
- Any database or server-side storage of user input
- Saving, resuming, or exporting an inquiry after a page refresh
- Shareable links to an inquiry
- Rating or giving feedback on question quality
- Editing a generated question
- Suggesting or scoring which question the user should expand next
- Displaying the whole inquiry tree at once, or any overview map of it
- Regenerating or refreshing the questions under an already-expanded question

## Specification Format Mapping

This specification is organized around the Spec Kit template. The four-part format used in class maps onto it as follows.

| Format element | Where it lives in this document |
|---|---|
| **Objective** — the failure mode, not the feature description | The Input statement above, and the premise running through User Story 1: people stop at their first answer, accept the framing a topic arrives in, and act on conclusions whose assumptions were never named. The failure is not missing information — it is never asking the question that would have changed the conclusion. |
| **Behavior** — observable outcomes only, no tech details | User Stories 1–3 with their acceptance scenarios, and Functional Requirements FR-001 through FR-022. |
| **Constraints** — non-negotiables regardless of implementation | FR-012 (no depth limit), FR-023 and FR-024 (never answers), FR-025 and FR-026 (generated content untrusted), FR-027 through FR-031 (fails safely), FR-032 through FR-034 (no storage beyond the session), FR-035 and FR-036 (keyboard and phone access), plus Assumptions and Out of Scope. |
| **Verification** — testable criteria, not subjective ones | The Acceptance Scenarios under each user story, the Edge Cases, and Success Criteria SC-001 through SC-009. SC-007 and SC-008 are assessed by human review and are labeled as such rather than presented as automated tests. |

---

*Developed with the assistance of Claude, reviewed and edited by me.*
