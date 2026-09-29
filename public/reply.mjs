/*
  Decides what the page shows for a reply from the server, and counts characters the
  way the server does. Pure functions with no page access, so they are tested with
  `node --test` (tests/reply.test.mjs), as the constitution requires of any code that
  makes a decision.

  No judgment about questions happens here. The server has already checked them and
  written every message about a request; this only picks which of the reply's fields
  to show, or one of three fixed messages when no usable reply from the app exists
  (contracts/questions-api.md).
*/

// Shown when the hosting platform refuses a request for exceeding the per-visitor
// limit. The platform's reply carries no message from this app (FR-046).
export const RATE_LIMITED_MESSAGE =
  "You've asked for a lot of questions in a short time. Wait a minute, then try again.";

// Shown when the page stops waiting for a reply. Same wording as the server's own
// timed-out message (FR-038).
export const TIMED_OUT_MESSAGE = "That took too long and was stopped. Try again.";

// Shown when no readable reply arrives: the network failed, or the server answered
// with something that is not this app's JSON. Same wording as the server's own
// failure message (FR-035, FR-039).
export const NO_REPLY_MESSAGE =
  "The questions could not be generated just now. Try again in a moment.";

// Count characters the way Python does, so the counter agrees with the server's limit:
// an emoji is one character here, not the two that `text.length` would count.
export function countCharacters(text) {
  return Array.from(text).length;
}

// True if the value is a list whose every entry is a string.
function isListOfStrings(value) {
  if (!Array.isArray(value)) {
    return false;
  }
  return value.every(function (entry) { return typeof entry === "string"; });
}

// What to show for a reply that arrived. `body` is the parsed JSON, or null if the
// reply was not JSON. Returns { kind: "questions", questions } or { kind: "message", text }.
export function replyToDisplay(status, body) {
  // The platform's rate limit comes first: its body, if any, is not this app's.
  if (status === 429) {
    return { kind: "message", text: RATE_LIMITED_MESSAGE };
  }
  if (body !== null && typeof body === "object") {
    if (body.status === "ok" && isListOfStrings(body.questions)) {
      return { kind: "questions", questions: body.questions };
    }
    if (typeof body.message === "string") {
      return { kind: "message", text: body.message };
    }
  }
  return { kind: "message", text: NO_REPLY_MESSAGE };
}

// What to say when a request ended with no reply at all. `timedOut` is true when the
// page's own timer stopped it.
export function messageForNoReply(timedOut) {
  if (timedOut) {
    return TIMED_OUT_MESSAGE;
  }
  return NO_REPLY_MESSAGE;
}
