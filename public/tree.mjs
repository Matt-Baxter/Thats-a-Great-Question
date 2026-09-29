/*
  The session's inquiry tree: every seed and question, how they connect, and which
  one is waiting for a reply. Pure functions with no page access, so they are tested
  with `node --test` (tests/tree.test.mjs).

  The tree lives in browser memory only, for the session (FR-021); nothing here saves
  it anywhere, so a reload starts empty (FR-042). It makes no judgment about what a
  question says: it only holds questions the server has already checked.

  A tree looks like this:
    {
      nodes: { "n1": node, "n2": node, ... },
      seedId: "n1",
      nextNumber: 3,         // used to make the next node's id
      loadingId: null,       // the node whose children are being requested, if any
    }
  and each node like this (data-model.md, Node):
    { id, kind: "seed" or "question", label: "" or "2.3", text, parentId, childIds }
  childIds is null until the node is first opened.
*/

// Make a node, add it to the tree, and return it.
function addNode(tree, kind, label, text, parentId) {
  const id = "n" + tree.nextNumber;
  tree.nextNumber = tree.nextNumber + 1;
  const node = { id: id, kind: kind, label: label, text: text, parentId: parentId, childIds: null };
  tree.nodes[id] = node;
  return node;
}

// A new tree holding only the seed, which has not been opened yet.
export function createTree(seedText) {
  const tree = { nodes: {}, seedId: null, nextNumber: 1, loadingId: null };
  const seed = addNode(tree, "seed", "", seedText, null);
  tree.seedId = seed.id;
  return tree;
}

export function getNode(tree, id) {
  return tree.nodes[id];
}

// The node's children, in order. Empty if it has never been opened.
export function childrenOf(tree, id) {
  const childIds = getNode(tree, id).childIds;
  if (childIds === null) {
    return [];
  }
  return childIds.map(function (childId) { return getNode(tree, childId); });
}

// The label for a node's child at `position` (counting from 1). Children are numbered
// from their parent: the seed's children are 1 to 5, and the children of 2.3 are 2.3.1
// to 2.3.5.
function childLabel(parent, position) {
  if (parent.label === "") {
    return String(position);
  }
  return parent.label + "." + position;
}

export function isRequestInFlight(tree) {
  return tree.loadingId !== null;
}

// Mark a node as waiting for its children. Returns false, and changes nothing, if
// another request is already in flight: only one at a time (FR-054).
export function startRequest(tree, id) {
  if (isRequestInFlight(tree)) {
    return false;
  }
  tree.loadingId = id;
  return true;
}

// End the request without a result — it failed, was declined, or was cancelled. The
// node is left exactly as it was, so it can be opened again (FR-036).
export function endRequest(tree) {
  tree.loadingId = null;
}

// Give a node the questions that came back for it, and end the request. The result is
// attached only if this node is the one waiting; a result for any other node, or one
// that arrives after its request ended, is ignored and false is returned (FR-056).
export function attachResult(tree, id, questions) {
  if (tree.loadingId !== id) {
    return false;
  }
  const parent = getNode(tree, id);
  const childIds = [];
  questions.forEach(function (text, index) {
    const child = addNode(tree, "question", childLabel(parent, index + 1), text, id);
    childIds.push(child.id);
  });
  parent.childIds = childIds;
  tree.loadingId = null;
  return true;
}

// The texts the server needs to know what is being opened: every question from the
// seed's child down to this node, in order. Empty for the seed itself.
export function ancestorTexts(tree, id) {
  const texts = [];
  let node = getNode(tree, id);
  while (node.kind !== "seed") {
    texts.unshift(node.text);
    node = getNode(tree, node.parentId);
  }
  return texts;
}
