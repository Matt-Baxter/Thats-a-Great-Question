// Tests for public/tree.mjs: the session's inquiry tree. Run with
// `node --test "tests/*.test.mjs"`. Uses only Node's built-in test runner; no packages.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  ancestorTexts,
  attachResult,
  childrenOf,
  countDescendants,
  createTree,
  discardBelow,
  endRequest,
  getNode,
  isRequestInFlight,
  needsRequest,
  pathTo,
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

// --- Staying oriented (T036) ------------------------------------------------------------

// Open `id` with the given questions, as a successful request would.
function open(tree, id, questions) {
  startRequest(tree, id);
  attachResult(tree, id, questions);
}

test("the path runs from the seed to the node, in order (FR-017)", () => {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  open(tree, two.id, FIVE);
  const twoThree = childLabelled(tree, two.id, "2.3");
  const labels = pathTo(tree, twoThree.id).map(function (node) { return node.label; });
  assert.deepEqual(labels, ["", "2", "2.3"]);
});

test("the path to the seed is the seed alone", () => {
  const tree = createTree("A seed.");
  assert.deepEqual(pathTo(tree, tree.seedId).map(function (node) { return node.id; }), [tree.seedId]);
});

test("a node needs a request only if it has never been opened (FR-023)", () => {
  const tree = openedTree(FIVE);
  assert.equal(needsRequest(tree, tree.seedId), false);
  const one = childLabelled(tree, tree.seedId, "1");
  assert.equal(needsRequest(tree, one.id), true);
});

test("reopening an expanded node needs no request and returns the same children (FR-022)", () => {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  open(tree, two.id, ["A?", "B?", "C?"]);
  const before = childrenOf(tree, two.id);
  assert.equal(needsRequest(tree, two.id), false);
  assert.deepEqual(childrenOf(tree, two.id), before);
});

test("any sibling can be opened, and opening it leaves the first branch unchanged (FR-024, FR-025)", () => {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  open(tree, two.id, ["A?", "B?", "C?"]);
  const twoA = childLabelled(tree, two.id, "2.1");
  open(tree, twoA.id, ["Deep?", "Deeper?", "Deepest?"]);
  const firstBranch = JSON.stringify(pathTo(tree, twoA.id)) + JSON.stringify(childrenOf(tree, twoA.id));

  const four = childLabelled(tree, tree.seedId, "4");
  assert.equal(startRequest(tree, four.id), true);
  attachResult(tree, four.id, ["X?", "Y?", "Z?"]);

  assert.equal(JSON.stringify(pathTo(tree, twoA.id)) + JSON.stringify(childrenOf(tree, twoA.id)), firstBranch);
  assert.equal(childrenOf(tree, four.id).length, 3);
});

// --- Asking again, and starting over (T040) ------------------------------------------------

// A tree with the seed opened (5), question 2 opened (3), and 2.1 opened (3): 11 questions.
function deepTree() {
  const tree = openedTree(FIVE);
  const two = childLabelled(tree, tree.seedId, "2");
  open(tree, two.id, ["A?", "B?", "C?"]);
  const twoOne = childLabelled(tree, two.id, "2.1");
  open(tree, twoOne.id, ["Deep?", "Deeper?", "Deepest?"]);
  return { tree: tree, two: two, twoOne: twoOne };
}

test("counting a node's descendants counts every question beneath it, at every depth", () => {
  const { tree, two, twoOne } = deepTree();
  assert.equal(countDescendants(tree, tree.seedId), 11);
  assert.equal(countDescendants(tree, two.id), 6);
  assert.equal(countDescendants(tree, twoOne.id), 3);
  assert.equal(countDescendants(tree, childLabelled(tree, twoOne.id, "2.1.1").id), 0);
});

test("discarding below a node removes every descendant and leaves it unopened", () => {
  const { tree, two, twoOne } = deepTree();
  const deepId = childLabelled(tree, twoOne.id, "2.1.1").id;
  discardBelow(tree, two.id);
  assert.equal(getNode(tree, two.id).childIds, null);
  assert.equal(getNode(tree, twoOne.id), undefined);
  assert.equal(getNode(tree, deepId), undefined);
  assert.equal(countDescendants(tree, tree.seedId), 5);
});

test("asking again replaces a node's children and discards everything beneath the old ones (FR-027)", () => {
  const { tree, two, twoOne } = deepTree();
  assert.equal(startRequest(tree, two.id), true);
  attachResult(tree, two.id, ["New one?", "New two?", "New three?", "New four?"]);
  const texts = childrenOf(tree, two.id).map(function (node) { return node.text; });
  assert.deepEqual(texts, ["New one?", "New two?", "New three?", "New four?"]);
  assert.equal(getNode(tree, twoOne.id), undefined);
  assert.equal(countDescendants(tree, two.id), 4);
  const labels = childrenOf(tree, two.id).map(function (node) { return node.label; });
  assert.deepEqual(labels, ["2.1", "2.2", "2.3", "2.4"]);
});

test("a failed or cancelled request to ask again leaves the tree unchanged (FR-029, FR-059)", () => {
  const { tree, two } = deepTree();
  const before = JSON.stringify(tree.nodes);
  assert.equal(startRequest(tree, two.id), true);
  endRequest(tree);
  assert.equal(JSON.stringify(tree.nodes), before);
  assert.equal(isRequestInFlight(tree), false);
});

test("asking again for the seed replaces the first set", () => {
  const { tree } = deepTree();
  startRequest(tree, tree.seedId);
  attachResult(tree, tree.seedId, ["Fresh?", "Start?", "Over?"]);
  assert.equal(countDescendants(tree, tree.seedId), 3);
});

test("a new inquiry starts from a tree that shares nothing with the old one (FR-030)", () => {
  // Clearing the whole tree is done by replacing it: the page drops the old tree and
  // creates a new one, so no old node can survive.
  const { tree: oldTree } = deepTree();
  const newTree = createTree("A different seed.");
  assert.equal(Object.keys(newTree.nodes).length, 1);
  assert.equal(getNode(newTree, newTree.seedId).text, "A different seed.");
  assert.equal(countDescendants(newTree, newTree.seedId), 0);
  assert.equal(countDescendants(oldTree, oldTree.seedId), 11);
});
