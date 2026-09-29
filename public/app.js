/*
  The page's behaviour: taking a seed, opening questions, and showing what comes back.

  It makes no judgment about questions or seeds. The inquiry tree — its structure, and
  which node is waiting for a reply — is kept by tree.mjs; which of a reply's fields to
  show is decided by reply.mjs; every message about a request is written in Python
  (inquiry/messages.py). All three are tested; this file only connects them to the
  page. Every string from the server is inserted with textContent, never as markup, so
  nothing it contains can run in the page (FR-034). Nothing is saved to browser
  storage, so a reload starts empty (FR-042).
*/

import { countCharacters, messageForNoReply, replyToDisplay } from "./reply.mjs";
import {
  ancestorTexts,
  attachResult,
  childrenOf,
  createTree,
  endRequest,
  getNode,
  isRequestInFlight,
  startRequest,
} from "./tree.mjs";

// The longest seed, in characters, for the counter under the text box. Must match
// MAX_SEED_CHARS in inquiry/config.py. The server is what enforces it (FR-003).
const MAX_SEED_CHARS = 2000;

// How long to wait for questions before giving up, in milliseconds (FR-038).
const REQUEST_TIMEOUT_MS = 30000;

const homeView = document.getElementById("view-home");
const inquiryTop = document.getElementById("view-inquiry-top");
const inquiryQuestions = document.getElementById("view-inquiry-questions");
const seedForm = document.getElementById("seed-form");
const seedInput = document.getElementById("seed");
const counter = document.getElementById("count");
const submitButton = document.getElementById("submit");
const focusKind = document.getElementById("focus-kind");
const focusText = document.getElementById("focus-text");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const messageBox = document.getElementById("message");
const listLabel = document.getElementById("list-label");
const questionList = document.getElementById("questions");
const announcer = document.getElementById("announcer");

// The session's inquiry, and the node on screen. `currentId` is null while the seed
// entry is showing. Both live only in memory.
let tree = null;
let currentId = null;

// --- Small helpers -----------------------------------------------------------------

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

function showMessage(text) {
  messageBox.textContent = text;
  messageBox.hidden = false;
  announce(text);
}

// How a node is named on the page: "Seed", or "question 2.3".
function nameOf(node) {
  if (node.kind === "seed") {
    return "Seed";
  }
  return "Question " + node.label;
}

// --- Drawing the page ----------------------------------------------------------------

function renderQuestion(node) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "q";
  button.disabled = isRequestInFlight(tree);

  const number = document.createElement("span");
  number.className = "q-num";
  number.textContent = node.label;

  const text = document.createElement("span");
  text.className = "q-text";
  text.textContent = node.text;

  const hint = document.createElement("span");
  hint.className = "q-open";
  hint.textContent = "open →";

  button.append(number, text, hint);
  button.addEventListener("click", function () { openQuestion(node.id); });

  const item = document.createElement("li");
  item.append(button);
  return item;
}

// Draw whatever `currentId` points at: the seed entry, or a seed or question with its
// questions beneath it (FR-020).
function render() {
  const onHome = currentId === null;
  homeView.hidden = !onHome;
  inquiryTop.hidden = onHome;
  inquiryQuestions.hidden = onHome;
  if (onHome) {
    return;
  }

  const node = getNode(tree, currentId);
  focusKind.textContent = nameOf(node);
  focusText.textContent = node.text;
  if (node.kind === "seed") {
    listLabel.textContent = "Questions worth asking";
  } else {
    listLabel.textContent = "Questions about question " + node.label;
  }
  questionList.replaceChildren();
  for (const child of childrenOf(tree, currentId)) {
    questionList.append(renderQuestion(child));
  }
}

// Show that the app is busy, and make every control that would start another request
// inert, so an ignored click is never silent (FR-054, FR-055).
function setBusy(busy, text) {
  loading.hidden = !busy;
  loadingText.textContent = text;
  submitButton.disabled = busy;
  for (const button of questionList.querySelectorAll("button.q")) {
    button.disabled = busy;
  }
  if (busy) {
    messageBox.hidden = true;
  }
}

// --- Talking to the server -----------------------------------------------------------

// Send one request. Resolves to the HTTP status and the parsed JSON body, or null for
// the body if it was not JSON.
async function fetchQuestions(seed, ancestors, signal) {
  const response = await fetch("/api/questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed: seed, ancestors: ancestors }),
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

// Ask for the children of node `id`. On success they are attached to that node — and
// only that node (FR-056) — and it is shown. Anything else leaves the tree and the
// view as they were, with a message, so the same node can be opened again (FR-036).
async function requestChildren(id, busyText) {
  if (!startRequest(tree, id)) {
    return;
  }
  setBusy(true, busyText);

  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(function () {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  let display;
  try {
    const seedText = getNode(tree, tree.seedId).text;
    const reply = await fetchQuestions(seedText, ancestorTexts(tree, id), controller.signal);
    display = replyToDisplay(reply.status, reply.body);
  } catch (noReply) {
    display = { kind: "message", text: messageForNoReply(timedOut) };
  }
  clearTimeout(timer);

  if (display.kind === "questions" && attachResult(tree, id, display.questions)) {
    setBusy(false, "");
    currentId = id;
    render();
    focusText.focus();
    announce(display.questions.length + " questions about " + nameOf(getNode(tree, id)).toLowerCase() + ", listed below.");
    return;
  }

  endRequest(tree);
  // A seed whose first request failed never became an inquiry.
  if (currentId === null) {
    tree = null;
  }
  setBusy(false, "");
  if (display.kind === "message") {
    showMessage(display.text);
  }
}

// --- What the user does ----------------------------------------------------------------

function submitSeed(event) {
  event.preventDefault();
  if (tree !== null && isRequestInFlight(tree)) {
    return;
  }
  tree = createTree(seedInput.value);
  requestChildren(tree.seedId, "Looking for the questions worth asking…");
}

function openQuestion(id) {
  const node = getNode(tree, id);
  requestChildren(id, "Looking for questions about question " + node.label + "…");
}

seedInput.addEventListener("input", updateCounter);
seedForm.addEventListener("submit", submitSeed);
updateCounter();
render();
