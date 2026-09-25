/*
  The page's behaviour for the seed flow: counting characters, sending the seed to
  the server, and showing the questions or the message that comes back.

  It makes no judgment about questions or seeds. Every message about a request is
  written in Python (inquiry/messages.py) and shown here exactly as sent. The only
  messages written here are three fixed ones for when no usable reply arrives from
  the application at all. Every string from the server is inserted with textContent,
  never as markup, so nothing it contains can run in the page (FR-034).
*/

"use strict";

// The longest seed, in characters, for the counter under the text box. Must match
// MAX_SEED_CHARS in inquiry/config.py. The server is what enforces it (FR-003).
const MAX_SEED_CHARS = 2000;

// How long to wait for questions before giving up, in milliseconds (FR-038).
const REQUEST_TIMEOUT_MS = 30000;

// Shown when the hosting platform refuses a request for exceeding the per-visitor
// limit. The platform's reply carries no message from this app (FR-046).
const RATE_LIMITED_MESSAGE =
  "You've asked for a lot of questions in a short time. Wait a minute, then try again.";

// Shown when the page stops waiting after REQUEST_TIMEOUT_MS. Same wording as the
// server's own timed-out message (FR-038).
const TIMED_OUT_MESSAGE = "That took too long and was stopped. Try again.";

// Shown when no readable reply arrives: the network failed, or the server answered
// with something that is not this app's JSON. Same wording as the server's own
// failure message (FR-035, FR-039).
const NO_REPLY_MESSAGE = "The questions could not be generated just now. Try again in a moment.";

const seedForm = document.getElementById("seed-form");
const seedInput = document.getElementById("seed");
const counter = document.getElementById("count");
const submitButton = document.getElementById("submit");
const loading = document.getElementById("loading");
const messageBox = document.getElementById("message");
const results = document.getElementById("results");
const questionList = document.getElementById("questions");

// True while a request is on its way, so a second submit is ignored.
let requestInFlight = false;

// Count characters the way Python does: an emoji is one character, not two.
function countCharacters(text) {
  return Array.from(text).length;
}

function updateCounter() {
  const length = countCharacters(seedInput.value);
  counter.textContent = length.toLocaleString("en-US") + " / " + MAX_SEED_CHARS.toLocaleString("en-US");
  counter.classList.toggle("over", length > MAX_SEED_CHARS);
}

function showLoading() {
  requestInFlight = true;
  submitButton.disabled = true;
  loading.hidden = false;
  messageBox.hidden = true;
}

function hideLoading() {
  requestInFlight = false;
  submitButton.disabled = false;
  loading.hidden = true;
}

function showMessage(text) {
  messageBox.textContent = text;
  messageBox.hidden = false;
}

function showQuestions(questions) {
  questionList.replaceChildren();
  questions.forEach(function (question, index) {
    const item = document.createElement("li");
    item.className = "q";

    const number = document.createElement("span");
    number.className = "q-num";
    number.textContent = String(index + 1);

    const text = document.createElement("span");
    text.className = "q-text";
    text.textContent = question;

    item.append(number, text);
    questionList.append(item);
  });
  messageBox.hidden = true;
  results.hidden = false;
}

// Send the seed and wait up to REQUEST_TIMEOUT_MS. Resolves to the HTTP status and the
// parsed JSON body, or null for the body if it was not JSON.
async function requestQuestions(seed) {
  const controller = new AbortController();
  const timer = setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: seed, ancestors: [] }),
      signal: controller.signal,
    });
    let body = null;
    try {
      body = await response.json();
    } catch (notJson) {
      body = null;
    }
    return { status: response.status, body: body };
  } finally {
    clearTimeout(timer);
  }
}

// Show whatever came back. Questions replace the ones on screen; anything else shows
// a message and leaves the questions already on screen as they were (FR-047).
function showReply(reply) {
  if (reply.status === 429) {
    showMessage(RATE_LIMITED_MESSAGE);
    return;
  }
  const body = reply.body;
  if (body !== null && body.status === "ok" && Array.isArray(body.questions)) {
    showQuestions(body.questions);
    return;
  }
  if (body !== null && typeof body.message === "string") {
    showMessage(body.message);
    return;
  }
  showMessage(NO_REPLY_MESSAGE);
}

async function submitSeed(event) {
  event.preventDefault();
  if (requestInFlight) {
    return;
  }
  showLoading();
  try {
    const reply = await requestQuestions(seedInput.value);
    showReply(reply);
  } catch (error) {
    // An abort means the timer fired; anything else means no reply arrived at all.
    if (error.name === "AbortError") {
      showMessage(TIMED_OUT_MESSAGE);
    } else {
      showMessage(NO_REPLY_MESSAGE);
    }
  } finally {
    hideLoading();
  }
}

seedInput.addEventListener("input", updateCounter);
seedForm.addEventListener("submit", submitSeed);
updateCounter();
