/*
  The page's behaviour for the seed flow: counting characters, sending the seed to
  the server, and showing the questions or the message that comes back.

  It makes no judgment about questions or seeds. Which of the reply's fields to show
  is decided in reply.mjs, which is tested; every message about a request is written
  in Python (inquiry/messages.py). Every string from the server is inserted with
  textContent, never as markup, so nothing it contains can run in the page (FR-034).
*/

import { countCharacters, messageForNoReply, replyToDisplay } from "./reply.mjs";

// The longest seed, in characters, for the counter under the text box. Must match
// MAX_SEED_CHARS in inquiry/config.py. The server is what enforces it (FR-003).
const MAX_SEED_CHARS = 2000;

// How long to wait for questions before giving up, in milliseconds (FR-038).
const REQUEST_TIMEOUT_MS = 30000;

const seedForm = document.getElementById("seed-form");
const seedInput = document.getElementById("seed");
const counter = document.getElementById("count");
const submitButton = document.getElementById("submit");
const loading = document.getElementById("loading");
const messageBox = document.getElementById("message");
const results = document.getElementById("results");
const questionList = document.getElementById("questions");
const announcer = document.getElementById("announcer");

// True while a request is on its way, so a second submit is ignored.
let requestInFlight = false;

function updateCounter() {
  const length = countCharacters(seedInput.value);
  counter.textContent = length.toLocaleString("en-US") + " / " + MAX_SEED_CHARS.toLocaleString("en-US");
  counter.classList.toggle("over", length > MAX_SEED_CHARS);
}

// Tell screen-reader users what just changed. Cleared first, so the same words twice
// in a row are still read out.
function announce(text) {
  announcer.textContent = "";
  setTimeout(function () { announcer.textContent = text; }, 50);
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
  announce(text);
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
  announce(questions.length + " questions worth asking, listed below.");
}

// Send the seed and wait up to REQUEST_TIMEOUT_MS. Resolves to the HTTP status and the
// parsed JSON body, or null for the body if it was not JSON.
async function requestQuestions(seed, signal) {
  const response = await fetch("/api/questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed: seed, ancestors: [] }),
    signal: signal,
  });
  let body = null;
  try {
    body = await response.json();
  } catch (notJson) {
    body = null;
  }
  return { status: response.status, body: body };
}

// Questions replace the ones on screen; anything else shows a message and leaves the
// questions already on screen as they were (FR-047).
function show(display) {
  if (display.kind === "questions") {
    showQuestions(display.questions);
  } else {
    showMessage(display.text);
  }
}

async function submitSeed(event) {
  event.preventDefault();
  if (requestInFlight) {
    return;
  }
  showLoading();
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(function () {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  try {
    const reply = await requestQuestions(seedInput.value, controller.signal);
    show(replyToDisplay(reply.status, reply.body));
  } catch (noReply) {
    showMessage(messageForNoReply(timedOut));
  } finally {
    clearTimeout(timer);
    hideLoading();
  }
}

seedInput.addEventListener("input", updateCounter);
seedForm.addEventListener("submit", submitSeed);
updateCounter();
