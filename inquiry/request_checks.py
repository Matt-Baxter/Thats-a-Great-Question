"""Checks what the browser sent before anything is asked of the model.

The browser is not trusted: anyone can send anything to the server. So every rule is
checked here, even the ones the page also shows, and a request that breaks one is
answered with a plain-language message instead of reaching the model (FR-002, FR-003).

read_body reads the body only if its declared length is sensible. check_request then
returns one of two shapes:
    {"outcome": "checked", "request": {"seed": ..., "ancestors": [...]}}
    {"outcome": "invalid_input", "message": ...}
"""

import json

from inquiry import config, messages


def read_body(content_length, stream):
    """Read the request body, or return None if its declared length is not a whole number from 0 to the cap.

    Checking first means a missing, negative or huge Content-Length can never make the
    server wait for bytes that will not come, or read more than the cap allows.
    """
    if content_length is None:
        return b""
    # isdigit alone would accept characters like "²", which int() cannot read.
    if not (content_length.isascii() and content_length.isdigit()):
        return None
    length = int(content_length)
    if length > config.MAX_REQUEST_BYTES:
        return None
    return stream.read(length)


def check_request(body):
    """Check a raw request body and return either the checked request or an invalid_input result.

    `body` is None when read_body refused to read it.
    """
    if body is None or len(body) > config.MAX_REQUEST_BYTES:
        return invalid(messages.INVALID_REQUEST)

    payload = parse_json_object(body)
    if payload is None:
        return invalid(messages.INVALID_REQUEST)

    seed = payload.get("seed")
    if not is_sendable_text(seed):
        return invalid(messages.INVALID_REQUEST)

    # The length is measured as typed, before trimming, so it matches the counter the
    # user sees on the page.
    if len(seed) > config.MAX_SEED_CHARS:
        return invalid(messages.seed_too_long(len(seed)))

    trimmed_seed = seed.strip()
    if trimmed_seed == "":
        return invalid(messages.EMPTY_SEED)

    ancestors = check_ancestors(payload.get("ancestors"))
    if ancestors is None:
        return invalid(messages.INVALID_REQUEST)

    checked_request = {"seed": trimmed_seed, "ancestors": ancestors}
    return {"outcome": "checked", "request": checked_request}


def check_ancestors(ancestors):
    """Return the ancestor questions trimmed, or None if they break a rule.

    The ancestors are the questions from the seed's first question down to the one being
    opened; an empty list means the request is about the seed. Each was returned by this
    app, so each must be a non-empty question within the question limit (data-model.md,
    "Generation request"). There is no limit on how many there are (FR-015).
    """
    if not isinstance(ancestors, list):
        return None
    trimmed_ancestors = []
    for ancestor in ancestors:
        if not is_sendable_text(ancestor):
            return None
        trimmed = ancestor.strip()
        if trimmed == "" or len(trimmed) > config.MAX_QUESTION_CHARS:
            return None
        trimmed_ancestors.append(trimmed)
    return trimmed_ancestors


def parse_json_object(body):
    """Decode a body as a UTF-8 JSON object, returning None if it is not one."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        # RecursionError: JSON nested thousands of levels deep, such as a body of "[[[[...".
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def is_sendable_text(value):
    """True if the value is a string that can be sent on to the model as UTF-8.

    JSON can carry half of a two-part character (a lone surrogate) that no UTF-8 text
    may contain; such a string would crash the request to the model, so it is refused here.
    """
    if not isinstance(value, str):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def invalid(message):
    """An invalid_input result carrying a message for the user."""
    return {"outcome": "invalid_input", "message": message}
