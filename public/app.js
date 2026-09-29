/*
  The page's behaviour: taking a seed, opening questions, moving along the trail,
  asking again, cancelling, and starting over.

  It makes no judgment about questions or seeds. The inquiry tree — its structure, the
  path to any node, what would be discarded, and which node is waiting for a reply — is
  kept by tree.mjs; which of a reply's fields to show is decided by reply.mjs; every
  message about a request is written in Python (inquiry/messages.py). All three are
  tested; this file only connects them to the page. Every string from the server is
  inserted with textContent, never as markup, so nothing it contains can run in the
  page (FR-034). Nothing is saved to browser storage, so a reload starts empty (FR-042).
*/

import { countCharacters, messageForNoReply, replyToDisplay } from "./reply.mjs";
import {
  ancestorTexts,
  attachResult,
  childrenOf,
  countDescendants,
  createTree,
  endRequest,
  getNode,
  isRequestInFlight,
  needsRequest,
  pathTo,
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
const trail = document.getElementById("trail");
const focusKind = document.getElementById("focus-kind");
const focusText = document.getElementById("focus-text");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const cancelButton = document.getElementById("cancel");
const messageBox = document.getElementById("message");
const listLabel = document.getElementById("list-label");
const questionList = document.getElementById("questions");
const askAgainButton = document.getElementById("ask-again");
const newInquiryButton = document.getElementById("new-inquiry");
const confirmDialog = document.getElementById("confirm");
const confirmTitle = document.getElementById("confirm-title");
const confirmBody = document.getElementById("confirm-body");
const confirmDiscard = document.getElementById("confirm-discard");
const confirmKeep = document.getElementById("confirm-keep");
const announcer = document.getElementById("announcer");

// The session's inquiry, and the node on screen. `currentId` is null while the seed
// entry is showing. Both live only in memory.
let tree = null;
let currentId = null;

// The request in flight, so Cancel can stop it: its AbortController, and the control
// that started it, so keyboard focus can go back there if it does not succeed.
let activeController = null;
let returnFocusTo = null;

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

// How a node is named on the page: "Seed", or "Question 2.3".
function nameOf(node) {
  if (node.kind === "seed") {
    return "Seed";
  }
  return "Question " + node.label;
}

// "1 question" or "5 questions".
function questionCount(count) {
  if (count === 1) {
    return "1 question";
  }
  return count + " questions";
}

// Ask the user to confirm discarding something. Resolves to true only if they choose
// to discard; closing the dialog any other way, including Escape, keeps everything.
function askToConfirm(title, body, discardLabel, keepLabel) {
  confirmTitle.textContent = title;
  confirmBody.textContent = body;
  confirmDiscard.textContent = discardLabel;
  confirmKeep.textContent = keepLabel;
  confirmDialog.returnValue = "";
  confirmDialog.showModal();
  return new Promise(function (resolve) {
    confirmDialog.addEventListener("close", function () {
      resolve(confirmDialog.returnValue === "discard");
    }, { once: true });
  });
}

// --- Drawing the page ----------------------------------------------------------------

function renderQuestion(node) {
  const opened = !needsRequest(tree, node.id);
  const button = document.createElement("button");
  button.type = "button";
  button.className = opened ? "q seen" : "q";
  button.disabled = isRequestInFlight(tree);

  const number = document.createElement("span");
  number.className = "q-num";
  number.textContent = node.label;

  const text = document.createElement("span");
  text.className = "q-text";
  text.textContent = node.text;

  const hint = document.createElement("span");
  hint.className = "q-open";
  hint.textContent = opened ? "opened" : "open →";

  button.append(number, text, hint);
  button.addEventListener("click", function () { openQuestion(node.id); });

  const item = document.createElement("li");
  item.append(button);
  return item;
}

// One entry in the trail: a button that returns to that point in one action (FR-019).
// The label and the start of the text show; the rest is cut off by CSS (FR-018).
function renderCrumb(node) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "crumb";
  button.disabled = isRequestInFlight(tree);
  if (node.id === currentId) {
    button.setAttribute("aria-current", "location");
  }

  const label = document.createElement("span");
  label.className = "crumb-label";
  label.textContent = node.kind === "seed" ? "Seed" : node.label;
  button.append(label, " " + node.text);

  button.addEventListener("click", function () { goTo(node.id); });
  return button;
}

function renderTrail() {
  trail.replaceChildren();
  pathTo(tree, currentId).forEach(function (node, index) {
    if (index > 0) {
      const separator = document.createElement("span");
      separator.className = "trail-sep";
      separator.setAttribute("aria-hidden", "true");
      separator.textContent = "›";
      trail.append(separator);
    }
    trail.append(renderCrumb(node));
  });
}

// Draw whatever `currentId` points at: the seed entry, or the trail and a seed or
// question with only its own questions beneath it (FR-020).
function render() {
  const onHome = currentId === null;
  homeView.hidden = !onHome;
  inquiryTop.hidden = onHome;
  inquiryQuestions.hidden = onHome;
  if (onHome) {
    return;
  }

  const node = getNode(tree, currentId);
  renderTrail();
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
// or move away inert, so an ignored click is never silent (FR-054, FR-055). Cancel is
// the one control that stays live (FR-058).
function setBusy(busy, text) {
  loading.hidden = !busy;
  loadingText.textContent = text;
  submitButton.disabled = busy;
  for (const button of document.querySelectorAll("button.q, button.crumb, button.action")) {
    button.disabled = busy;
  }
  if (busy) {
    messageBox.hidden = true;
  }
}

// After a request that did not succeed, put keyboard focus back where it started.
function restoreFocus() {
  if (returnFocusTo !== null && document.body.contains(returnFocusTo)) {
    returnFocusTo.focus();
  }
  returnFocusTo = null;
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

// Ask for the children of node `id` — a first set, an expansion, or a fresh set. On
// success they are attached to that node, and only that node (FR-056), and it is
// shown. Anything else leaves the tree and the view as they were, with a message, so
// the same node can be opened again (FR-029, FR-036).
async function requestChildren(id, busyText) {
  if (!startRequest(tree, id)) {
    return;
  }
  returnFocusTo = document.activeElement;
  setBusy(true, busyText);
  cancelButton.focus();

  const controller = new AbortController();
  activeController = controller;
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

  // Cancelled by the user: cancelRequest has already put everything back, and another
  // request may have started since, so nothing more is done here (FR-059).
  if (controller.signal.aborted && !timedOut) {
    return;
  }
  activeController = null;

  if (display.kind === "questions" && attachResult(tree, id, display.questions)) {
    setBusy(false, "");
    currentId = id;
    render();
    focusText.focus();
    returnFocusTo = null;
    announce(questionCount(display.questions.length) + " about " + nameOf(getNode(tree, id)).toLowerCase() + ", listed below.");
    return;
  }

  endRequest(tree);
  // A seed whose first request failed never became an inquiry.
  if (currentId === null) {
    tree = null;
  }
  setBusy(false, "");
  restoreFocus();
  showMessage(display.text);
}

// Stop the request in flight. The inquiry is left exactly as it was, no partial result
// is shown, and the next request is accepted at once (FR-058, FR-059). The model call
// may still finish on the server, and is still billed (research.md R7).
function cancelRequest() {
  if (activeController === null) {
    return;
  }
  activeController.abort();
  activeController = null;
  endRequest(tree);
  if (currentId === null) {
    tree = null;
  }
  setBusy(false, "");
  restoreFocus();
  announce("Cancelled. Nothing was changed.");
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

// Show a node that already has questions, with no request (FR-022).
function goTo(id) {
  if (isRequestInFlight(tree)) {
    return;
  }
  currentId = id;
  messageBox.hidden = true;
  render();
  focusText.focus();
  announce(nameOf(getNode(tree, id)) + ", " + questionCount(childrenOf(tree, id).length) + " below.");
}

// Open a question: show its questions if it has any, or ask for them if it has never
// been opened (FR-022, FR-023). Any sibling can be opened this way (FR-024).
function openQuestion(id) {
  if (!needsRequest(tree, id)) {
    goTo(id);
    return;
  }
  const node = getNode(tree, id);
  requestChildren(id, "Looking for questions about question " + node.label + "…");
}

// Ask for a fresh set for the seed or question on screen, first set included (FR-026).
// It would discard what is there, so the user confirms first, told how many questions
// go (FR-028). Nothing is discarded unless the new set arrives (FR-027, FR-029).
async function askAgain() {
  if (isRequestInFlight(tree)) {
    return;
  }
  const shown = childrenOf(tree, currentId).length;
  const beneath = countDescendants(tree, currentId) - shown;
  let body = "A fresh set replaces these " + questionCount(shown) + ".";
  if (beneath > 0) {
    body = "A fresh set replaces these " + questionCount(shown) + ", and the " +
      questionCount(beneath) + " you opened beneath them will be gone.";
  }
  const confirmed = await askToConfirm("Replace these questions?", body + " This cannot be undone.", "Replace", "Keep them");
  if (!confirmed) {
    return;
  }
  const node = getNode(tree, currentId);
  requestChildren(currentId, "Looking for a fresh set for " + nameOf(node).toLowerCase() + "…");
}

// Start over with a different seed, without reloading (FR-030). The whole inquiry
// would be lost, so the user confirms first, told how many questions go (FR-057).
async function newInquiry() {
  if (isRequestInFlight(tree)) {
    return;
  }
  const total = countDescendants(tree, tree.seedId);
  const confirmed = await askToConfirm(
    "Lose this inquiry?",
    "A new seed clears everything here — " + questionCount(total) +
      " across this inquiry. Nothing is saved, so this cannot be recovered.",
    "Discard",
    "Keep it"
  );
  if (!confirmed) {
    return;
  }
  tree = null;
  currentId = null;
  seedInput.value = "";
  updateCounter();
  messageBox.hidden = true;
  render();
  seedInput.focus();
}

seedInput.addEventListener("input", updateCounter);
seedForm.addEventListener("submit", submitSeed);
cancelButton.addEventListener("click", cancelRequest);
askAgainButton.addEventListener("click", askAgain);
newInquiryButton.addEventListener("click", newInquiry);
updateCounter();
render();
