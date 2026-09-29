// Tests for public/tree.mjs: the session's inquiry tree. Run with
// `node --test "tests/*.test.mjs"`. Uses only Node's built-in test runner; no packages.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  ancestorTexts,
  attachResult,
  childrenOf,
  createTree,
  endRequest,
  getNode,
  isRequestInFlight,
  startRequest,
} from "../public/tree.mjs";

const FIVE = ["One?", "Two?", "Three?", "Four?", "Five?"];

// A tree whose seed has been opened, with the given questions as its children.
function openedTree(questions) {
  const tree = createTree("A seed.");
  startRequest(tree, tree.seedId);
  attachResult(tree, tree.seedId, questions);
  return tree;
}

// The child of `parentId` whose label is `label`.
function childLabelled(tree, parentId, label) {
  return childrenOf(tree, parentId).find(function (node) { return node.label === label; });
}

// --- Creating a tree (FR-021) ----------------------------------------------------------

test("a new tree holds only the seed, never opened", () => {
  const tree = createTree("A seed.");
  const seed = getNode(tree, tree.seedId);
  assert.equal(seed.kind, "seed");
  assert.equal(seed.text, "A seed.");
  assert.equal(seed.label, "");
  assert.equal(seed.parentId, null);
  assert.equal(seed.childIds, null);
  assert.equal(isRequestInFlight(tree), false);
});

// --- Labels -------------------------------------------------------------------------------

test("the seed's children are labelled 1 to 5", () => {
  const tree = openedTree(FIVE);
  const labels = childrenOf(tree, tree.seedId).map(function (node) { return node.label; });
  assert.deepEqual(labels, ["1", "2", "3", "4", "5"]);
});

test("the children of 2.3 are labelled 2.3.1 to 2.3.5", () => {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  startRequest(tree, two.id);
  attachResult(tree, two.id, FIVE);
  const twoThree = childLabelled(tree, two.id, "2.3");
  startRequest(tree, twoThree.id);
  attachResult(tree, twoThree.id, FIVE);
  const labels = childrenOf(tree, twoThree.id).map(function (node) { return node.label; });
  assert.deepEqual(labels, ["2.3.1", "2.3.2", "2.3.3", "2.3.4", "2.3.5"]);
});

test("children keep the text and order they were returned in", () => {
  const tree = openedTree(["A?", "B?", "C?"]);
  const texts = childrenOf(tree, tree.seedId).map(function (node) { return node.text; });
  assert.deepEqual(texts, ["A?", "B?", "C?"]);
});

test("a node that has never been opened has no children to show", () => {
  const tree = createTree("A seed.");
  assert.deepEqual(childrenOf(tree, tree.seedId), []);
});

// --- Attaching a result to the node it was requested for (FR-056) ------------------------

test("a result is attached to the node it was requested for and no other", () => {
  const tree = openedTree(FIVE);
  const three = childLabelled(tree, tree.seedId, "3");
  startRequest(tree, three.id);
  attachResult(tree, three.id, ["Deeper?", "Wider?", "Other?"]);
  assert.equal(childrenOf(tree, three.id).length, 3);
  for (const sibling of childrenOf(tree, tree.seedId)) {
    if (sibling.id !== three.id) {
      assert.equal(sibling.childIds, null);
    }
  }
});

test("a result for a node that is not the one loading is ignored", () => {
  const tree = openedTree(FIVE);
  const one = childLabelled(tree, tree.seedId, "1");
  const two = childLabelled(tree, tree.seedId, "2");
  startRequest(tree, one.id);
  const attached = attachResult(tree, two.id, ["Stray?", "Late?", "Wrong?"]);
  assert.equal(attached, false);
  assert.equal(getNode(tree, two.id).childIds, null);
  assert.equal(isRequestInFlight(tree), true);
});

test("a result that arrives after its request ended is ignored", () => {
  const tree = openedTree(FIVE);
  const one = childLabelled(tree, tree.seedId, "1");
  startRequest(tree, one.id);
  endRequest(tree);
  assert.equal(attachResult(tree, one.id, ["Late?", "Very late?", "Too late?"]), false);
  assert.equal(getNode(tree, one.id).childIds, null);
});

// --- A failed request (FR-036) --------------------------------------------------------------

test("a failed request leaves the node unopened, so it can be opened again", () => {
  const tree = openedTree(FIVE);
  const four = childLabelled(tree, tree.seedId, "4");
  startRequest(tree, four.id);
  endRequest(tree);
  assert.equal(getNode(tree, four.id).childIds, null);
  assert.equal(isRequestInFlight(tree), false);
  assert.equal(startRequest(tree, four.id), true);
});

// --- One request at a time (FR-054) -----------------------------------------------------------

test("while a request is in flight, starting another is refused", () => {
  const tree = openedTree(FIVE);
  const one = childLabelled(tree, tree.seedId, "1");
  const two = childLabelled(tree, tree.seedId, "2");
  assert.equal(startRequest(tree, one.id), true);
  assert.equal(isRequestInFlight(tree), true);
  assert.equal(startRequest(tree, two.id), false);
  assert.equal(startRequest(tree, one.id), false);
});

test("attaching a result ends the request, so the next one can start", () => {
  const tree = openedTree(FIVE);
  assert.equal(isRequestInFlight(tree), false);
  const one = childLabelled(tree, tree.seedId, "1");
  assert.equal(startRequest(tree, one.id), true);
});

// --- The chain the server needs (FR-014) -----------------------------------------------------

test("the seed has no ancestors to send", () => {
  const tree = createTree("A seed.");
  assert.deepEqual(ancestorTexts(tree, tree.seedId), []);
});

test("a question's ancestors run from the seed's child down to the question itself", () => {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  startRequest(tree, two.id);
  attachResult(tree, two.id, ["Two-one?", "Two-two?", "Two-three?"]);
  const twoThree = childLabelled(tree, two.id, "2.3");
  assert.deepEqual(ancestorTexts(tree, twoThree.id), ["Two?", "Two-three?"]);
});
