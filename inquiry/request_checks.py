"""Checks what the browser sent before anything is asked of the model.

The browser is not trusted: anyone can send anything to the server. So every rule is
checked here, even the ones the page also shows, and a request that breaks one is
answered with a plain-language message instead of reaching the model (FR-002, FR-003).

check_request returns one of two shapes:
    {"outcome": "checked", "request": {"seed": ..., "ancestors": [...]}}
    {"outcome": "invalid_input", "message": ...}
"""

import json

from inquiry import config, messages


def check_request(body):
    """Check a raw request body and return either the checked request or an invalid_input result."""
    if len(body) > config.MAX_REQUEST_BYTES:
        return invalid(messages.INVALID_REQUEST)

    payload = parse_json_object(body)
    if payload is None:
        return invalid(messages.INVALID_REQUEST)

    seed = payload.get("seed")
    if not isinstance(seed, str):
        return invalid(messages.INVALID_REQUEST)

    # The length is measured as typed, before trimming, so it matches the counter the
    # user sees on the page.
    if len(seed) > config.MAX_SEED_CHARS:
        return invalid(messages.seed_too_long(len(seed)))

    trimmed_seed = seed.strip()
    if trimmed_seed == "":
        return invalid(messages.EMPTY_SEED)

    # Until User Story 2 (T030), every request is about the seed: the ancestors the page
    # sends are not yet read, so the chain is always empty here.
    checked_request = {"seed": trimmed_seed, "ancestors": []}
    return {"outcome": "checked", "request": checked_request}


def parse_json_object(body):
    """Decode a body as a UTF-8 JSON object, returning None if it is not one."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def invalid(message):
    """An invalid_input result carrying a message for the user."""
    return {"outcome": "invalid_input", "message": message}
