"""Tests for inquiry/request_checks.py: what the server accepts from the browser (T012).

The browser is not trusted, so every rule is checked again on the server. Each test
sends a raw request body, exactly as the handler receives it.
"""

import io
import json

import pytest

from inquiry import config, messages
from inquiry.request_checks import check_request, read_body


def body_for(payload):
    """Encode a request payload the way the browser sends it."""
    return json.dumps(payload).encode("utf-8")


def test_a_normal_seed_is_accepted():
    result = check_request(body_for({"seed": "Remote work makes teams less innovative.", "ancestors": []}))
    assert result["outcome"] == "checked"
    assert result["request"]["seed"] == "Remote work makes teams less innovative."


def test_surrounding_whitespace_is_trimmed_from_the_seed():
    result = check_request(body_for({"seed": "  A question about tides?\n", "ancestors": []}))
    assert result["request"]["seed"] == "A question about tides?"


def test_an_empty_seed_is_rejected_with_the_empty_seed_message():
    # FR-002
    result = check_request(body_for({"seed": "", "ancestors": []}))
    assert result == {"outcome": "invalid_input", "message": messages.EMPTY_SEED}


def test_a_whitespace_only_seed_is_rejected_with_the_empty_seed_message():
    # FR-002
    result = check_request(body_for({"seed": "  \n\t  ", "ancestors": []}))
    assert result == {"outcome": "invalid_input", "message": messages.EMPTY_SEED}


def test_a_seed_of_exactly_the_maximum_length_is_accepted():
    # FR-003: the limit itself is allowed.
    seed = "a" * config.MAX_SEED_CHARS
    result = check_request(body_for({"seed": seed, "ancestors": []}))
    assert result["outcome"] == "checked"


def test_a_seed_one_character_over_the_maximum_is_rejected_naming_the_limit_and_length():
    # FR-003
    seed = "a" * (config.MAX_SEED_CHARS + 1)
    result = check_request(body_for({"seed": seed, "ancestors": []}))
    assert result["outcome"] == "invalid_input"
    assert result["message"] == "A seed can be up to 2,000 characters. This one is 2,001."


def test_a_body_that_is_not_json_is_rejected_as_invalid_input():
    result = check_request(b"this is not json")
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_body_that_is_not_utf8_is_rejected_as_invalid_input():
    result = check_request(b"\xff\xfe\xfd")
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_json_body_that_is_not_an_object_is_rejected_as_invalid_input():
    result = check_request(body_for(["a list", "not an object"]))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_body_without_a_seed_is_rejected_as_invalid_input():
    result = check_request(body_for({"ancestors": []}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_seed_that_is_not_a_string_is_rejected_as_invalid_input():
    # FR-001: the seed is free text.
    result = check_request(body_for({"seed": 42, "ancestors": []}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_body_larger_than_the_request_cap_is_rejected_before_it_is_parsed():
    oversized = b"x" * (config.MAX_REQUEST_BYTES + 1)
    result = check_request(oversized)
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_body_exactly_at_the_request_cap_is_not_rejected_for_size():
    # Padding inside a valid seed field would break the seed limit, so pad with spaces
    # after the JSON object, which JSON allows.
    payload = body_for({"seed": "A seed.", "ancestors": []})
    padded = payload + b" " * (config.MAX_REQUEST_BYTES - len(payload))
    assert len(padded) == config.MAX_REQUEST_BYTES
    result = check_request(padded)
    assert result["outcome"] == "checked"


def test_a_seed_containing_half_of_a_two_part_character_is_rejected_as_invalid_input():
    # JSON can carry a lone surrogate, which cannot be sent on as UTF-8.
    body = b'{"seed": "\\ud800 why?", "ancestors": []}'
    result = check_request(body)
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_json_nested_too_deeply_to_parse_is_rejected_as_invalid_input():
    result = check_request(b"[" * 100_000)
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_body_that_read_body_refused_is_rejected_as_invalid_input():
    assert check_request(None) == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


# --- Reading the body -----------------------------------------------------------------


def test_read_body_reads_exactly_the_declared_length():
    stream = io.BytesIO(b'{"seed": "x"}and more')
    assert read_body("13", stream) == b'{"seed": "x"}'


def test_read_body_with_no_declared_length_reads_nothing():
    assert read_body(None, io.BytesIO(b"ignored")) == b""


@pytest.mark.parametrize("declared", ["abc", "-1", "", "1.5", "²", " 12"])
def test_read_body_refuses_a_length_that_is_not_a_whole_number(declared):
    # Reading -1 would wait for the connection to close; "abc" would crash int().
    assert read_body(declared, io.BytesIO(b"body")) is None


def test_read_body_refuses_a_length_over_the_cap_without_reading():
    stream = io.BytesIO(b"x" * 10)
    assert read_body(str(config.MAX_REQUEST_BYTES + 1), stream) is None
    assert stream.tell() == 0


# --- Ancestors: the chain of questions above the one being opened (T026) --------------


def test_an_empty_ancestor_list_is_accepted():
    result = check_request(body_for({"seed": "A seed.", "ancestors": []}))
    assert result["outcome"] == "checked"
    assert result["request"]["ancestors"] == []


def test_ancestors_are_passed_on_in_order_and_trimmed():
    ancestors = ["What is assumed? ", " Who decides?"]
    result = check_request(body_for({"seed": "A seed.", "ancestors": ancestors}))
    assert result["request"]["ancestors"] == ["What is assumed?", "Who decides?"]


def test_an_empty_ancestor_is_rejected():
    result = check_request(body_for({"seed": "A seed.", "ancestors": ["What is assumed?", "   "]}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_an_ancestor_of_exactly_the_question_limit_is_accepted():
    ancestor = "W" + "h" * (config.MAX_QUESTION_CHARS - 2) + "?"
    result = check_request(body_for({"seed": "A seed.", "ancestors": [ancestor]}))
    assert result["outcome"] == "checked"


def test_an_ancestor_over_the_question_limit_is_rejected():
    ancestor = "W" + "h" * (config.MAX_QUESTION_CHARS - 1) + "?"
    result = check_request(body_for({"seed": "A seed.", "ancestors": [ancestor]}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_missing_ancestor_list_is_rejected():
    result = check_request(body_for({"seed": "A seed."}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


@pytest.mark.parametrize("ancestors", ["What is assumed?", None, {"a": "b"}, ["fine?", 7]])
def test_ancestors_that_are_not_a_list_of_strings_are_rejected(ancestors):
    result = check_request(body_for({"seed": "A seed.", "ancestors": ancestors}))
    assert result == {"outcome": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_long_chain_of_ancestors_is_accepted():
    # FR-015: no depth is refused, as long as the request fits under the size cap.
    ancestors = [f"What about step {number}?" for number in range(200)]
    result = check_request(body_for({"seed": "A seed.", "ancestors": ancestors}))
    assert result["outcome"] == "checked"
