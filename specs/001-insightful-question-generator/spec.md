# Feature Specification: That's a Great Question — Insightful Question Generation

**Feature Directory**: `specs/001-insightful-question-generator` (this project commits to `main`; no feature branch is used)

**Created**: 2026-09-21

**Last Updated**: 2026-09-22

**Status**: Draft

**Input**: User description: A web app that takes a seed — a topic, a claim, a half-formed idea, or a question — and returns a small set of insightful questions worth asking about it. Any returned question can be opened to generate further questions about that question, so a user follows one line of inquiry deeper instead of stopping at the first set. The app generates questions only. It never answers them.

## Objective

> **Where the four parts of the class format live.** This specification follows the Spec Kit
> template, and each of its sections is labelled below with which part of the
> Objective / Behavior / Constraints / Verification format it carries.
>
> | Format element | Section |
> |---|---|
> | **Objective** | this section |
> | **Behavior** | User Scenarios & Testing · Requirements (the groups marked *Behavior*) |
> | **Constraints** | Requirements (the groups marked *Constraints*) · Assumptions · Out of Scope |
> | **Verification** | Acceptance Scenarios · Edge Cases · Success Criteria |

**The failure mode this exists to prevent.** People stop at their first answer. They accept the
framing a topic arrives in, interrogate it shallowly, and act on conclusions whose assumptions were
never named. Existing tools make this worse: ask a chatbot about a claim and it hands back an
answer, which ends inquiry rather than opening it. The failure is not a lack of information — it is
never asking the right question, the one that would have changed the conclusion.

### Who experiences this failure

- **Primary**: someone reasoning through a complex claim or decision alone, who wants their own
  thinking stress-tested before committing to it — a student writing on a hard topic, an analyst
  evaluating a proposal, anyone auditing their own reasoning for what they have missed.
- **Secondary**: someone preparing for a conversation where the questions matter more than the
  answers — an interview, a design review, a difficult meeting. Also someone in science,
  engineering, or philosophy reasoning technically, critically, and deeply about a problem.
- **Not for**: someone who wants answers. This tool withholds them deliberately and will frustrate
  anyone looking for a traditional chatbot. This boundary is load-bearing — without it the product
  drifts into being a general-purpose assistant.

## Clarifications

### Session 2026-09-22

- Q: Should the app limit how many question requests one visitor can make, and what should a visitor see when they hit that limit? → A: Cap requests per visitor over a rolling window; when exceeded, show a plain-language message saying to wait and try again.
- Q: Is the app allowed to record what a user types into a server-side log? → A: Log request metadata and failure reasons only — never seed or question text.
- Q: How quickly should a normal request finish, as distinct from the thirty seconds at which it gives up? → A: Under 10 seconds typical, 30 seconds hard stop.
- Q: What should a user see when the model declines to generate questions about their seed? → A: A distinct message saying no questions could be generated for this seed and suggesting a rephrase, claiming no fault either way.
- Q: What should happen if a user clicks to expand a second question while the first expansion is still loading? → A: Ignore new expansion requests while one is in flight; the loading state shows the app is busy.

## User Scenarios & Testing *(mandatory)*

***Behavior*** — each user story describes observable outcomes, with no technology in it.
***Verification*** — the Acceptance Scenarios under each story, and the Edge Cases that follow
them, are the testable criteria, written as Given / When / Then.

### User Story 1 - Get questions about a seed (Priority: P1)

A person is reasoning through a complex claim or decision on their own. They type the claim, topic, or half-formed idea into a single text box and submit it. Within seconds they receive three to five questions about it — questions chosen to be insightful, consequential, or critical rather than merely related. They read them and notice at least one thing they had not thought to ask.

**Why this priority**: This is the entire premise of the product in its smallest useful form. A person who only ever used this one capability would still get the core value: their thinking interrogated by questions they did not generate themselves. Every other story builds on it.

**Independent Test**: Can be fully tested by entering a seed and confirming that a set of 3–5 well-formed, distinct questions is returned, and that no answers appear anywhere. Delivers value with no other functionality present.

**Acceptance Scenarios**:

1. **Given** the app is open with an empty text box, **When** the user enters a seed and submits it, **Then** between three and five questions about that seed are displayed.
2. **Given** a seed has been submitted, **When** the questions are displayed, **Then** each question is non-empty, is phrased as a question, is not a word-for-word repeat of another question shown, and is different from the seed itself.
3. **Given** a seed has been submitted, **When** the questions are displayed, **Then** they address different angles on the seed rather than restating one another in different words.
4. **Given** a seed has been submitted, **When** the response is displayed, **Then** no answer, explanation, or commentary about any question appears.
5. **Given** the user has submitted a seed, **When** the request is in progress, **Then** a visible loading state is shown from the moment of submission until the result appears.

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

### User Story 4 - Ask again, or ask something else (Priority: P3)

The user reads a set of questions and finds them unconvincing — or simply wants to see what a second pass turns up. Without retyping anything, they ask for a fresh set for the same question. If a request is taking longer than they are willing to wait, they can cancel it and carry on. And when they are finished with one inquiry, they can start a new one with a different seed without reloading the page — after confirming, since that discards everything they have built.

**Why this priority**: None of it is essential to the core value, and a user can get most of it today by reloading and retyping. But a set of questions is a judgment call made by a system that will sometimes judge poorly, and being stuck with one pass makes that failure permanent. Cancelling matters for the same reason in the other direction: a user who has changed their mind should not have to wait out a request. It shares P3 with staying oriented: recovery and control rather than core capability.

**Independent Test**: Can be fully tested by requesting a fresh set for a question and confirming new questions replace the old ones, by cancelling a request in flight and confirming the inquiry is untouched and the next request is accepted, and by starting a new inquiry with a different seed and confirming that it warns first and then clears the previous inquiry without a page reload.

**Acceptance Scenarios**:

1. **Given** a set of questions is displayed, **When** the user asks for a fresh set for the same question, **Then** a newly generated set replaces the previous one without the seed being retyped.
2. **Given** a question has further questions beneath it, **When** the user asks for a fresh set for that question, **Then** they are warned that the questions below will be discarded, and it proceeds only if they confirm.
3. **Given** the user has confirmed a fresh set for a question with descendants, **When** the new questions are displayed, **Then** everything previously beneath that question is gone.
4. **Given** an inquiry is in progress, **When** the user starts a new inquiry with a different seed, **Then** they are warned that the current inquiry will be lost and it proceeds only if they confirm.
5. **Given** the user has confirmed a new seed, **When** the new questions are displayed, **Then** the previous inquiry is gone and no page reload has occurred.
6. **Given** a request is in flight, **When** the user cancels it, **Then** no partial result is displayed, the inquiry is exactly as it was before the request, and the next request the user makes is accepted.

---

### Edge Cases — ***Verification*** (boundary conditions)

- **Empty seed**: The user submits nothing, or only whitespace. The submission is rejected with a plain-language message before any generation is attempted.
- **Over-length seed**: The user pastes a document instead of a seed. The submission is rejected with a message that names the length limit.
- **Generation unavailable**: The question source cannot be reached. The user sees a plain-language message and the app remains usable.
- **Malformed output**: Generation returns something that is not a usable set of questions — empty, unparseable, or structurally wrong. The user sees a plain-language message rather than raw or partial output.
- **Too few questions**: Generation returns fewer than three questions. This is treated as a failed response, not displayed as a short list.
- **Too many questions**: Generation returns more than five questions. This is treated as a failed response, not silently truncated to five — a response of the wrong shape is a signal that something went wrong, not something to quietly repair.
- **Over-length question**: A returned question exceeds the maximum question length. The response is treated as unusable rather than displayed truncated.
- **Duplicate questions**: Two returned questions are identical once normalised. The response is rejected rather than displayed with a redundant question in it (FR-007). Two questions that pursue the same underlying goal in *different* wording are not mechanically detectable; that is handled when questions are selected (FR-008) and judged by human review (SC-010), not by rejecting the response.
- **Clicking while busy**: The user opens a second question while the first is still loading. The second request is ignored rather than queued or raced, and the display makes clear the app is already working. The user is not stuck: they may cancel the request in flight and then make the request they wanted.
- **Generation declines**: The model returns a refusal instead of questions. The user sees a distinct message saying no questions could be generated for that seed and that rephrasing may help — not a technical error, and not the refusal text itself. The inquiry already on screen is untouched.
- **Request limit reached**: A visitor exceeds the per-visitor request limit. They see a plain-language message asking them to wait and try again, and the inquiry already on screen is untouched.
- **Slow response**: Generation does not complete promptly. The request resolves to either questions or a message within thirty seconds, never hanging indefinitely.
- **Deep chain**: The user expands many levels. No limit is imposed, and the display continues to function.
- **Revisiting an expanded question**: The user navigates back to a question they already expanded. Its existing questions are shown; nothing is regenerated and nothing is lost.
- **Asking again below a subtree**: The user asks for a fresh set for a question that has further questions beneath it. They are warned what will be lost and must confirm before anything is discarded.
- **Failed regeneration**: A request for a fresh set fails. The existing questions are left in place, nothing is discarded, and the user can try again.
- **Failed expansion, then retry**: An expansion fails. The user sees a message, the tree is unchanged, and the same question can be expanded again.
- **New seed mid-inquiry**: The user starts a new inquiry while deep in an existing one. They are warned that the current inquiry will be lost and must confirm; on confirmation it is cleared without a page reload.
- **Cancelled request**: The user cancels a request before it resolves. The inquiry is unchanged, no partial result is displayed, the next request is accepted immediately, and the cancelled request does not count against their request limit.
- **Refresh mid-inquiry**: The user reloads the page. They return to an empty starting state, with no part of the inquiry restored.
- **Narrow screen**: The app is used on a phone. All content, including a deep trail, remains readable and every control remains reachable.

## Requirements *(mandatory)*

### Functional Requirements

***Behavior*** and ***Constraints***, as numbered requirements. Each group below is labelled with
which one it carries: *Behavior* for what a user does and sees, *Constraints* for rules that hold
regardless of how the app is built. Requirement ids are assigned once and never reused or
reordered, so requirements added by later clarification appear at the end rather than beside
related ones.

**Accepting a seed** — *Behavior*

- **FR-001**: System MUST accept a free-text seed, which may be a topic, a claim, a half-formed idea, or a question.
- **FR-002**: System MUST reject an empty or whitespace-only seed with a plain-language message, before any generation is attempted.
- **FR-003**: System MUST reject a seed longer than the maximum seed length with a message that names the limit.

**Generating questions** — *Behavior, with Constraints at FR-005 and FR-011*

- **FR-004**: System MUST return between three and five questions in every successful response.
- **FR-005**: System MUST treat any response containing fewer than three or more than five questions as unusable, and MUST NOT truncate, pad, or otherwise repair it.
- **FR-006**: System MUST ensure every returned question is non-empty and is phrased as a question.
- **FR-007**: System MUST reject a response in which any two questions are duplicates of one another when compared as normalised text.
- **FR-008**: System MUST ensure the questions in a response address different angles rather than restating one another in different words.
- **FR-009**: System MUST ensure every returned question is distinct from the seed or question it was generated from.
- **FR-010**: System MUST ensure every returned question falls within the maximum question length.
- **FR-011**: System MUST NOT return a question that presupposes its own answer, a rhetorical question, or a statement written with a question mark.
- **FR-012**: System MUST generate questions by drawing on an explicit, written, human-readable list of lines of inquiry, and MUST return questions without type labels attached.

**Expanding a question** — *Behavior, with a Constraint at FR-015*

- **FR-013**: Users MUST be able to open any returned question to generate further questions about it.
- **FR-014**: System MUST generate expansion questions about the question being expanded, not about the original seed.
- **FR-015**: System MUST NOT impose any limit on how many times a user may expand.
- **FR-016**: System MUST apply FR-004 through FR-012 to expansion responses identically to first-level responses.

**Staying oriented** — *Behavior*

- **FR-017**: System MUST display, above the current set of questions, a trail of every ancestor from the original seed through to the question currently being viewed.
- **FR-018**: System MUST display the seed or question currently being viewed in full, and MAY abbreviate ancestors in the trail to keep it compact.
- **FR-019**: Users MUST be able to return to any ancestor in the trail, including the original seed, with a single action.
- **FR-020**: System MUST show only the current seed or question and its direct child questions alongside the trail, rather than the whole accumulated tree.

**Moving between lines of inquiry** — *Behavior*

- **FR-021**: System MUST retain, for the duration of the browser session, every question generated and the parent-child structure connecting them.
- **FR-022**: System MUST display the questions already generated for a question when the user returns to it, without generating new ones.
- **FR-023**: System MUST generate questions when the user opens a question that has not been expanded before.
- **FR-024**: Users MUST be able to open any sibling of a question they have already expanded, and MUST NOT be confined to a single line of inquiry.
- **FR-025**: System MUST leave a previously explored branch unchanged when the user explores a different one.

**Asking again** — *Behavior, with a Constraint at FR-028*

- **FR-026**: Users MUST be able to request a freshly generated set of questions for the seed or question currently being viewed, without retyping the seed. This includes the first set of questions, generated from the seed itself.
- **FR-027**: System MUST replace that seed's or question's existing questions with the new set, and MUST discard everything previously beneath them.
- **FR-028**: System MUST warn the user what will be discarded and require confirmation before regenerating a seed or question that has further questions beneath it.
- **FR-029**: System MUST leave the existing questions and everything beneath them untouched when a regeneration request fails.
- **FR-030**: Users MUST be able to begin a new inquiry with a different seed without reloading the page, clearing the previous inquiry.

**Never answering** — *Constraints*

- **FR-031**: System MUST NOT provide answers, explanations, or commentary on any question it generates.
- **FR-032**: System MUST present generated questions as suggestions, never as authoritative or complete.

**Treating generated content as untrusted** — *Constraints*

- **FR-033**: System MUST validate every generated response — shape, count, and non-emptiness — before any part of it is displayed.
- **FR-034**: System MUST display generated text exactly as text, never interpreting it as markup, formatting, or instructions.

**Failing safely** — *Behavior and Constraints*

- **FR-035**: System MUST show a plain-language message when generation fails, is unavailable, or returns unusable output, and MUST remain usable afterward.
- **FR-036**: System MUST leave the existing tree of questions unchanged when an expansion fails, and MUST allow the same question to be opened again.
- **FR-037**: System MUST display a visible loading state from the moment a request begins until it resolves.
- **FR-038**: System MUST resolve every request to either questions or a message within thirty seconds.
- **FR-039**: System MUST NOT crash, hang, or present a blank screen under any failure condition.

**Privacy and persistence** — *Constraints*

- **FR-040**: System MUST NOT store anything a user types anywhere other than the user's own browser session.
- **FR-041**: System MUST NOT require an account, login, or any user identification.
- **FR-042**: System MUST return the user to an empty starting state when the page is reloaded, retaining no part of the previous inquiry.

**Access** — *Constraints*

- **FR-043**: System MUST make every interactive element reachable and operable using a keyboard alone.
- **FR-044**: System MUST remain usable on a phone-sized screen, with no horizontal scrolling required to read content.

**Protecting against abuse** — *Behavior and Constraints*

- **FR-045**: System MUST limit the number of question requests a single visitor may make within a rolling time window.
- **FR-046**: System MUST show a plain-language message asking the visitor to wait and try again when that limit is exceeded.
- **FR-047**: System MUST leave the inquiry already on screen intact when a request is refused for exceeding the limit. Hitting a limit MUST NOT cost the user their work.

**What may be recorded** — *Constraints*

- **FR-048**: System MUST NOT write any seed text or generated question text to a server-side log, an error trace, or any other server-side record.
- **FR-049**: System MUST record enough about each request to diagnose failures — that a request occurred, which failure occurred, and at what depth — without recording any content the user typed or the model produced.
- **FR-050**: System MUST NOT include seed text or generated question text in any message it sends to an external service other than the request that generates questions.

**When generation declines** — *Behavior and Constraints*

- **FR-051**: System MUST distinguish a declined request — one where generation returns a refusal rather than questions — from a technical failure.
- **FR-052**: System MUST show, for a declined request, a plain-language message stating that no questions could be generated for the seed or question the request was made about, and that rephrasing may help. The message MUST refer to whichever of the two the request concerned, since a request may be declined at any depth. It MUST NOT describe the outcome as an error or fault, and MUST NOT suggest the user did something wrong.
- **FR-053**: System MUST NOT display the text of a refusal. A refusal is commentary, and FR-031 forbids commentary reaching the user.

**One request at a time** — *Constraints*

- **FR-054**: System MUST ignore any request to generate or regenerate questions while another such request is in flight.
- **FR-055**: System MUST make it evident while a request is in flight that further requests will not be accepted, so an ignored click is never silent.
- **FR-056**: System MUST attach every response to the question it was requested for. A response MUST NEVER be displayed beneath a different question.

**Protecting work in progress** — *Behavior and Constraints*

- **FR-057**: System MUST warn the user that the current inquiry will be lost and require confirmation before a new seed replaces an inquiry already in progress. Discarding a whole inquiry MUST NOT be easier than discarding one question's children (FR-028).
- **FR-058**: Users MUST be able to cancel a request that is in flight.
- **FR-059**: System MUST leave the inquiry unchanged when a request is cancelled, and MUST accept new requests immediately afterward.
- **FR-060**: System MUST NOT count a cancelled request against the per-visitor request limit of FR-045. The limit exists to bound cost and protect availability, and a user who changes their mind has not threatened either.

### Key Entities

- **Seed**: The free text a user submits to begin an inquiry. Bounded in length. The root of the inquiry tree. Not retained beyond the user's browser session.
- **Question**: A single generated question. Non-empty, phrased as a question, bounded in length, unlabeled, and distinct from its siblings and from its parent. Never accompanied by an answer. May be unexpanded, or expanded and therefore holding children of its own.
- **Inquiry Tree**: The whole structure built during a session — the seed, every question generated from it, and the parent-child links between them. Retained in full for the session so the user can move freely between branches; discarded entirely on reload, or on a new seed once the user has confirmed the loss.
- **Trail**: The ordered path from the seed to the question currently being viewed. What the user is shown in order to stay oriented, and the means by which they navigate back up. A view onto the tree rather than a separate structure.
- **Lines of Inquiry**: The explicit written list of angles a question may take — assumption, evidence, consequence, alternative, stakeholder, definition, framing, precedent, incentive, failure mode, and others. Guides generation; is not exposed as labels on output.

## Success Criteria *(mandatory)*

***Verification*** — testable criteria, not subjective ones. Every criterion below is objectively
checkable except SC-009, SC-010 and SC-011, which are assessed by human review over a defined
review set and are labelled as such, because question quality cannot be scored automatically and a
metric claiming otherwise would be false precision.

### Measurable Outcomes

- **SC-001**: 100% of submitted requests resolve to either a set of questions or a plain-language message within thirty seconds.
- **SC-002**: 100% of displayed responses contain between three and five questions, each non-empty, phrased as a question, not a normalised-text duplicate of another question in the same response, distinct from its parent, and within the maximum question length.
- **SC-003**: 100% of responses containing fewer than three or more than five questions are rejected rather than displayed, truncated, or padded.
- **SC-004**: 100% of induced failure conditions produce a plain-language message with no crash, hang, or blank screen. The conditions include, and are not limited to: unreachable generation, malformed output, empty output, wrong question count, duplicate questions, an over-length question, an empty seed, an over-length seed, a declined request (SC-016), and a request refused for exceeding the limit (SC-013).
- **SC-005**: A first-time user, given no instructions, can go from opening the app to reading generated questions in under sixty seconds.
- **SC-006**: A user at any depth can identify the original seed from the trail and return to it in a single action, on both a desktop and a phone-sized screen.
- **SC-007**: 100% of returns to a previously expanded question, within a session, display the same questions that were shown before, with no new generation.
- **SC-008**: 100% of regeneration requests on a question with descendants warn the user and require confirmation before anything is discarded.
- **SC-009**: Across a review set of at least twenty varied seeds spanning technical, social, and philosophical subjects, a human reviewer judges that at least 80% of responses contain at least one question the reviewer had not already considered.
- **SC-010**: Across the same review set, a human reviewer judges that at least 80% of responses contain no two questions pursuing the same underlying goal in different words.
- **SC-011**: Across the same review set, 100% of responses contain no answers, no commentary, and no question that merely restates the seed.
- **SC-012**: 100% of interactive elements can be reached and operated using a keyboard alone.
- **SC-013**: 100% of requests beyond the per-visitor limit produce a plain-language wait-and-retry message, with the inquiry already on screen left intact.
- **SC-014**: Across every induced failure condition, 100% of server-side log output contains no seed text and no generated question text.
- **SC-015**: At least 90% of successful requests complete within ten seconds. The thirty seconds in SC-001 is the point at which a request is abandoned, not a target.
- **SC-016**: 100% of declined requests produce the distinct could-not-generate message rather than a technical error message, and 0% display any refusal text. The message names the seed when the request concerned a seed and the question when it concerned a question, at every depth.
- **SC-017**: 0% of responses are displayed beneath a question other than the one they were requested for, including when a user repeatedly attempts to start requests while one is in flight.
- **SC-018**: 100% of attempts to start a new inquiry over an inquiry already in progress warn the user and require confirmation before anything is discarded.
- **SC-019**: 100% of cancelled requests leave the inquiry unchanged, display no partial result, are followed by a request that is accepted without delay, and are not counted against the per-visitor request limit.

## Assumptions

***Constraints*** — what is taken as given, and the decisions behind each.

- **Maximum seed length is 2,000 characters.** The input description required a cap and a message naming it, but did not fix a value. Two thousand characters comfortably holds a topic, a claim, or a paragraph-long idea while rejecting a pasted document. Adjustable without affecting any other requirement.
- **Maximum question length is 300 characters.** Chosen so a question stays readable at a glance on a phone, including within a trail. Also adjustable in isolation.
- **Distinctness is enforced at two levels, and only one of them is automatable.** Duplicate or near-identical wording is rejected mechanically (FR-007, SC-002). Whether two differently-worded questions pursue the same underlying goal — "What drives you?" and "What are you passionate about?" point at one goal; "What are you best at?" points at another — is a judgment call, delivered by how questions are selected (FR-008) and verified by human review (SC-010). Claiming the second is machine-checkable would be false precision.
- **Ten seconds is the budget any selection design must fit.** Choosing among candidates costs time, and SC-015 is the number that design is measured against rather than the thirty-second abandonment point. If an approach cannot typically deliver questions within ten seconds, it is too slow regardless of how good its output is.
- **Questions are selected, not merely produced.** A response is the strongest few questions chosen from a wider set of candidates against written criteria, rather than the first few generated. The criteria cover whether answering a question would change the user's conclusion, whether the user would plausibly have asked it themselves, whether it can actually be pursued, whether the chosen set covers genuinely different angles, and whether it is faithful to the seed as given. How selection is performed is a planning decision, not a requirement of this specification.
- **Generation happens once per question, unless the user asks again.** Opening a question that has never been expanded generates its children; returning to one that already has children displays them. Backtracking is only meaningful if a branch is stable. The user may explicitly request a fresh set, which replaces what was there.
- **The inquiry tree lives only in the browser, only for the session.** It is retained so the user can move between branches, and discarded on reload, or on starting a new inquiry once the user has confirmed the loss. Nothing is written to a server.
- **Question quality cannot be scored automatically.** Whether a question is genuinely insightful is context-dependent and assessed by human review (SC-009, SC-010, SC-011). The automated criteria check the *shape* of a response, not its worth. No metric in this specification claims otherwise, because one that did would be false precision.
- **A seed whose answer is settled still gets questions.** A factual lookup — "Who was the first
  president of the United States?" — is treated no differently from a contested claim: the app
  returns three to five questions about it and never the answer. Answering such seeds was
  considered and rejected. It would require a classifier deciding which seeds are "merely factual",
  and that judgment fails worst on the seeds that matter most — "Is nuclear power safe?" and "What
  causes inflation?" look factual and are not — so the app would hand over an answer in precisely
  the cases that deserved interrogation. It would also put an answer in the response, which ends
  the questions-only boundary that the rest of this specification rests on. Whether the questions
  returned for a settled seed are actually worth reading is a matter of how well generation
  interrogates framing and definition rather than subject matter, and is to be confirmed in testing
  against deliberately factual seeds.
- **Repeated requests for the same question will not return identical questions.** Generation is not deterministic. This is why asking again is useful, and why reproducibility is not promised.
- **A specific bad response cannot be reconstructed after the fact.** Because no seed or question text is recorded server-side (FR-048), a complaint that "the questions were poor" cannot be traced to the exact exchange that produced them. Quality problems are diagnosed by human review against a deliberate review set, not by inspecting telemetry. This is an accepted cost of not holding what users type.
- **Users have an internet connection and a current browser.**
- **Users want questions, not answers.** Someone seeking answers is explicitly not a target user and will find the product frustrating by design.
- **A single user, in a single browser session, with no collaboration.** Nothing is shared, synced, or visible to anyone else.
- **English-language seeds and questions for the first version.** Other languages are neither prevented nor guaranteed.

## Out of Scope

***Constraints*** — the boundaries of this version.

- Answering questions, or offering explanation or commentary on them
- Accounts, login, or syncing across devices
- Any database or server-side storage of user input
- Saving, resuming, or exporting an inquiry after a page refresh
- Shareable links to an inquiry
- Rating or giving feedback on question quality
- Editing a generated question
- Suggesting or scoring which question the user should expand next
- Displaying the whole inquiry tree at once, or any overview map of it
- Keeping both the old and new question sets after a regeneration
- Undoing a regeneration, or recovering an inquiry cleared by a new seed, once either has been confirmed

## Specification Format Mapping

Every section of this document is labelled inline with the part of the class format it carries;
this table is the same mapping gathered in one place, down to the individual requirement.

| Format element | Where it lives |
|---|---|
| **Objective** — the failure mode, not the feature description | The **Objective** section at the top, stated as the failure it exists to prevent rather than a description of the product, with who suffers that failure and who the product is explicitly not for. |
| **Behavior** — observable outcomes only, no tech details | User Stories 1–4, and the requirement groups labelled *Behavior*: accepting a seed (FR-001–FR-003), generating questions (FR-004, FR-006–FR-010, FR-012), expanding (FR-013, FR-014, FR-016), staying oriented (FR-017–FR-020), moving between lines of inquiry (FR-021–FR-025), asking again (FR-026, FR-027, FR-029, FR-030), loading and failure messages (FR-035–FR-037), the wait-and-retry message (FR-046), the declined-request message (FR-052), the busy indication (FR-055), and cancelling (FR-058, FR-059). |
| **Constraints** — non-negotiables regardless of implementation | The requirement groups labelled *Constraints*, plus Assumptions and Out of Scope: wrong-shape responses are never repaired (FR-005); no leading or rhetorical questions (FR-011); no depth limit (FR-015); confirmation before destroying work (FR-028, FR-057); never answers or comments (FR-031, FR-032); generated content is untrusted (FR-033, FR-034); never crashes, hangs or blanks, and resolves within thirty seconds (FR-038, FR-039); nothing stored beyond the browser session (FR-040–FR-042); keyboard and phone access (FR-043, FR-044); a per-visitor request limit that never costs a user their work and never charges them for a request they cancelled (FR-045, FR-047, FR-060); no user or model text recorded or sent elsewhere (FR-048–FR-050); a refusal is not an error and its text is never shown (FR-051, FR-053); one request at a time, never misattributed (FR-054, FR-056). |
| **Verification** — testable criteria, not subjective ones | The Acceptance Scenarios under each user story, written as Given / When / Then; the Edge Cases, which are the boundary conditions; and Success Criteria SC-001 through SC-019. SC-009, SC-010 and SC-011 are assessed by human review and are labelled as such rather than presented as automated tests. |


---

*Developed with the assistance of Claude, reviewed and edited by me.*
