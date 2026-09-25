"""Checks the model's reply against the specification's rules before anything is shown.

The model is a third party, and what it returns is untrusted (constitution Principle
IV). The reply's JSON shape is requested from the API, but most of the specification's
rules cannot be expressed that way, so they are checked here, in the order data-model.md
lists them. A reply that fails any check is rejected whole; it is never trimmed, padded
or otherwise repaired (FR-005).

check_reply returns one of two shapes:
    {"passed": True, "questions": [...]}
    {"passed": False, "failed_check": <name of the first check that failed>}
The name is logged to help diagnose failures; it never contains any question text.
"""

import unicodedata

from inquiry import config


def check_reply(reply, opened_text):
    """Apply every check to a parsed reply, returning the selected questions or the first failed check.

    `opened_text` is the seed, or the question being opened, that the questions are about.
    """
    # Shape: the object the prompt asked for, with the types it asked for.
    if not has_expected_shape(reply):
        return failed("shape")

    # Check 1: 3–5 positions, all distinct, all pointing at a real candidate.
    candidates = reply["candidates"]
    selected = reply["selected"]
    if not config.MIN_QUESTIONS <= len(selected) <= config.MAX_QUESTIONS:
        return failed("selection")
    if len(set(selected)) != len(selected):
        return failed("selection")
    for position in selected:
        if position < 0 or position >= len(candidates):
            return failed("selection")

    questions = [candidates[position].strip() for position in selected]

    # Check 2: each is non-empty and ends with a question mark (FR-006).
    for question in questions:
        if question == "" or not question.endswith("?"):
            return failed("question_mark")

    # Check 3: each is within the maximum length (FR-010).
    for question in questions:
        if len(question) > config.MAX_QUESTION_CHARS:
            return failed("length")

    # Check 4: no two are the same once normalised (FR-007).
    normalised_questions = [normalise(question) for question in questions]
    if len(set(normalised_questions)) != len(normalised_questions):
        return failed("duplicate")

    # Check 5: none is a restatement of what the questions are about (FR-009).
    if normalise(opened_text) in normalised_questions:
        return failed("restates")

    return {"passed": True, "questions": questions}


def has_expected_shape(reply):
    """True if the reply is an object with a list of strings and a list of whole numbers."""
    if not isinstance(reply, dict):
        return False
    candidates = reply.get("candidates")
    selected = reply.get("selected")
    if not isinstance(candidates, list) or not isinstance(selected, list):
        return False
    for candidate in candidates:
        if not isinstance(candidate, str):
            return False
    for position in selected:
        # True and False count as whole numbers in Python, so they are ruled out by name.
        if isinstance(position, bool) or not isinstance(position, int):
            return False
    return True


def normalise(text):
    """Lower-case the text, remove punctuation, and collapse runs of whitespace to single spaces."""
    kept_characters = []
    for character in text.lower():
        # Unicode punctuation categories all start with "P", which covers curly quotes
        # and dashes as well as ordinary commas and question marks.
        if not unicodedata.category(character).startswith("P"):
            kept_characters.append(character)
    without_punctuation = "".join(kept_characters)
    return " ".join(without_punctuation.split())


def failed(check_name):
    """A failed check result naming which check failed."""
    return {"passed": False, "failed_check": check_name}
