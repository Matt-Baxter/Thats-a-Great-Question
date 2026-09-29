// Tests for public/reply.mjs: what the page shows for each kind of reply. Run with
// `node --test "tests/*.test.mjs"`. Uses only Node's built-in test runner; no packages.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  NO_REPLY_MESSAGE,
  RATE_LIMITED_MESSAGE,
  TIMED_OUT_MESSAGE,
  countCharacters,
  messageForNoReply,
  replyToDisplay,
} from "../public/reply.mjs";

const QUESTIONS = ["What is assumed?", "What is the evidence?", "Who is affected?"];

test("an ok reply shows its questions", () => {
  const shown = replyToDisplay(200, { status: "ok", questions: QUESTIONS });
  assert.deepEqual(shown, { kind: "questions", questions: QUESTIONS });
});

test("a declined, invalid or failed reply shows the server's message exactly", () => {
  for (const [status, bodyStatus] of [[200, "declined"], [400, "invalid_input"], [502, "failed"], [504, "failed"]]) {
    const shown = replyToDisplay(status, { status: bodyStatus, message: "Words from the server." });
    assert.deepEqual(shown, { kind: "message", text: "Words from the server." });
  }
});

test("a 429 shows the fixed rate-limit message, whatever its body says (FR-046)", () => {
  const shown = replyToDisplay(429, { status: "ok", questions: QUESTIONS });
  assert.deepEqual(shown, { kind: "message", text: RATE_LIMITED_MESSAGE });
});

test("a reply that is not JSON shows the no-reply message (FR-039)", () => {
  assert.deepEqual(replyToDisplay(500, null), { kind: "message", text: NO_REPLY_MESSAGE });
});

test("an ok reply whose questions are not a list of strings shows the no-reply message", () => {
  assert.deepEqual(replyToDisplay(200, { status: "ok", questions: "not a list" }), { kind: "message", text: NO_REPLY_MESSAGE });
  assert.deepEqual(replyToDisplay(200, { status: "ok", questions: ["fine?", 7] }), { kind: "message", text: NO_REPLY_MESSAGE });
});

test("JSON that is not an object shows the no-reply message", () => {
  assert.deepEqual(replyToDisplay(200, "a string"), { kind: "message", text: NO_REPLY_MESSAGE });
  assert.deepEqual(replyToDisplay(200, 42), { kind: "message", text: NO_REPLY_MESSAGE });
});

test("no reply at all says timed out when the page's timer stopped it, and failed otherwise", () => {
  assert.equal(messageForNoReply(true), TIMED_OUT_MESSAGE);
  assert.equal(messageForNoReply(false), NO_REPLY_MESSAGE);
});

test("characters are counted as Python counts them", () => {
  assert.equal(countCharacters(""), 0);
  assert.equal(countCharacters("abc"), 3);
  assert.equal(countCharacters("why 🤔"), 5);
});
