"""Tests for inquiry/http_response.py: each outcome's status code and JSON body (T016).

The status codes and bodies are the ones contracts/questions-api.md specifies. No body
may carry a field the contract does not list.
"""

import logging

import pytest

from inquiry import messages
from inquiry.http_response import to_http_response, unexpected_error_response

QUESTIONS = ["What is assumed?", "What is the evidence?", "Who is affected?"]


def test_ok_becomes_200_with_status_and_questions():
    status, body = to_http_response({"outcome": "ok", "questions": QUESTIONS})
    assert status == 200
    assert body == {"status": "ok", "questions": QUESTIONS}


def test_declined_becomes_200_with_status_and_message():
    # FR-052: a decline is not an error, so it is not an error status.
    message = messages.declined("seed")
    status, body = to_http_response({"outcome": "declined", "message": message})
    assert status == 200
    assert body == {"status": "declined", "message": message}


def test_invalid_input_becomes_400():
    status, body = to_http_response({"outcome": "invalid_input", "message": messages.EMPTY_SEED})
    assert status == 400
    assert body == {"status": "invalid_input", "message": messages.EMPTY_SEED}


def test_failed_becomes_502():
    status, body = to_http_response({"outcome": "failed", "message": messages.GENERATION_FAILED})
    assert status == 502
    assert body == {"status": "failed", "message": messages.GENERATION_FAILED}


def test_a_timeout_becomes_504_with_status_failed_and_the_timed_out_message():
    status, body = to_http_response({"outcome": "timed_out", "message": messages.TIMED_OUT})
    assert status == 504
    assert body == {"status": "failed", "message": messages.TIMED_OUT}


@pytest.mark.parametrize(
    "result",
    [
        {"outcome": "ok", "questions": QUESTIONS, "extra": "internal detail"},
        {"outcome": "declined", "message": "m", "category": "cyber"},
        {"outcome": "invalid_input", "message": "m", "questions": QUESTIONS},
        {"outcome": "failed", "message": "m", "reason": "selection"},
        {"outcome": "timed_out", "message": "m", "questions": QUESTIONS},
    ],
)
def test_no_body_carries_a_field_the_contract_does_not_list(result):
    _, body = to_http_response(result)
    if body["status"] == "ok":
        assert set(body) == {"status", "questions"}
    else:
        assert set(body) == {"status", "message"}


def test_an_unexpected_error_becomes_502_failed_with_the_failure_message():
    # FR-039: even an unforeseen error ends in this app's JSON.
    status, body = unexpected_error_response(ValueError("anything"))
    assert status == 502
    assert body == {"status": "failed", "message": messages.GENERATION_FAILED}


def test_an_unexpected_error_logs_its_type_but_never_its_message(caplog):
    # FR-048: an error's message could quote the seed.
    caplog.set_level(logging.DEBUG, logger="inquiry")
    unexpected_error_response(ValueError("Remote work makes teams less innovative."))
    assert "type=ValueError" in caplog.text
    assert "Remote work" not in caplog.text
