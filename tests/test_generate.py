"""Tests for inquiry/generate.py: one call to the model, and what each outcome becomes (T015).

Every test uses the fake client in tests/fakes.py. None calls the live model.
"""

import logging

import pytest

import fakes
from inquiry import config, messages
from inquiry.generate import build_client, generate_questions
from inquiry.prompts import REPLY_SCHEMA

SEED = fakes.SEED
REQUEST = {"seed": SEED, "ancestors": []}


# --- A good reply -------------------------------------------------------------------


def test_a_valid_reply_gives_ok_with_the_selected_questions_in_order():
    client = fakes.FakeClient(fakes.valid_reply())
    result = generate_questions(client, REQUEST)
    good = fakes.GOOD_CANDIDATES
    assert result == {"outcome": "ok", "questions": [good[0], good[3], good[6], good[7]]}


def test_a_thinking_block_before_the_text_is_skipped():
    # research.md R1: this model can send thinking blocks first.
    client = fakes.FakeClient(fakes.thinking_then_text())
    result = generate_questions(client, REQUEST)
    good = fakes.GOOD_CANDIDATES
    assert result == {"outcome": "ok", "questions": [good[1], good[2], good[4]]}


# --- What is sent to the model ------------------------------------------------------


def test_the_request_uses_the_configured_model_effort_limit_schema_and_fallback():
    client = fakes.FakeClient(fakes.valid_reply())
    generate_questions(client, REQUEST)
    sent = client.calls()[0]
    assert sent["model"] == config.MODEL
    assert sent["max_tokens"] == config.MAX_OUTPUT_TOKENS
    assert sent["output_config"] == {
        "effort": config.EFFORT,
        "format": {"type": "json_schema", "schema": REPLY_SCHEMA},
    }
    assert sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert sent["fallbacks"] == "default"


def test_the_seed_is_sent_in_the_user_message_not_the_system_prompt():
    client = fakes.FakeClient(fakes.valid_reply())
    generate_questions(client, REQUEST)
    sent = client.calls()[0]
    assert SEED not in sent["system"]
    assert SEED in sent["messages"][0]["content"]
    assert sent["messages"][0]["role"] == "user"


# --- A decline ------------------------------------------------------------------------


def test_a_refusal_gives_declined_about_the_seed():
    # FR-051, FR-052
    client = fakes.FakeClient(fakes.refusal())
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "declined", "message": messages.declined("seed")}


def test_a_refusal_message_contains_none_of_the_refusal_text():
    # FR-053
    client = fakes.FakeClient(fakes.refusal())
    result = generate_questions(client, REQUEST)
    assert "can't help" not in result["message"]


# --- Failures -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_reply",
    [
        fakes.cut_off,
        fakes.unparseable,
        fakes.too_few,
        fakes.too_many,
        fakes.duplicate_pair,
        fakes.statement_not_question,
        fakes.over_length_question,
        fakes.restates_seed,
    ],
)
def test_an_unusable_reply_gives_failed(make_reply):
    # FR-035: cut off, unparseable, or failing any check.
    client = fakes.FakeClient(make_reply())
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "failed", "message": messages.GENERATION_FAILED}


def test_a_reply_with_no_text_block_gives_failed():
    client = fakes.FakeClient(fakes.FakeResponse([fakes.FakeBlock("thinking", "")]))
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "failed", "message": messages.GENERATION_FAILED}


def test_a_timeout_gives_timed_out():
    # FR-038
    client = fakes.FakeClient(fakes.timeout_error())
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "timed_out", "message": messages.TIMED_OUT}


def test_an_unreachable_model_gives_failed():
    client = fakes.FakeClient(fakes.connection_error())
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "failed", "message": messages.GENERATION_FAILED}


@pytest.mark.parametrize("status_code", [401, 429, 500, 529])
def test_an_error_status_from_the_api_gives_failed(status_code):
    client = fakes.FakeClient(fakes.status_error(status_code))
    result = generate_questions(client, REQUEST)
    assert result == {"outcome": "failed", "message": messages.GENERATION_FAILED}


def test_no_client_gives_failed_without_calling_anything():
    # research.md R11: a missing key fails the request.
    result = generate_questions(None, REQUEST)
    assert result == {"outcome": "failed", "message": messages.GENERATION_FAILED}


# --- What is logged -------------------------------------------------------------------

ALL_REPLIES = [
    fakes.valid_reply,
    fakes.thinking_then_text,
    fakes.refusal,
    fakes.cut_off,
    fakes.unparseable,
    fakes.too_few,
    fakes.too_many,
    fakes.duplicate_pair,
    fakes.statement_not_question,
    fakes.over_length_question,
    fakes.restates_seed,
    fakes.timeout_error,
    fakes.connection_error,
    fakes.status_error,
]


@pytest.mark.parametrize("make_reply", ALL_REPLIES)
def test_logs_never_contain_the_seed_or_any_question_text(make_reply, caplog):
    # FR-048, SC-014: across every outcome, including failures.
    caplog.set_level(logging.DEBUG)
    generate_questions(fakes.FakeClient(make_reply()), REQUEST)
    logged = caplog.text
    assert "Remote work" not in logged
    for question in fakes.GOOD_CANDIDATES:
        assert question not in logged
    assert "can't help" not in logged
    assert "chance meetings" not in logged


def test_the_log_records_the_outcome_and_the_depth(caplog):
    # FR-049
    caplog.set_level(logging.INFO)
    generate_questions(fakes.FakeClient(fakes.valid_reply()), REQUEST)
    assert "outcome=ok" in caplog.text
    assert "depth=0" in caplog.text


def test_the_log_records_which_check_a_reply_failed(caplog):
    # FR-049: enough to diagnose, without content.
    caplog.set_level(logging.INFO)
    generate_questions(fakes.FakeClient(fakes.too_many()), REQUEST)
    assert "outcome=failed" in caplog.text
    assert "reason=selection" in caplog.text


def test_the_log_records_a_refusals_category(caplog):
    caplog.set_level(logging.INFO)
    generate_questions(fakes.FakeClient(fakes.refusal("cyber")), REQUEST)
    assert "outcome=declined" in caplog.text
    assert "category=cyber" in caplog.text


def test_the_log_says_when_no_key_is_configured(caplog):
    caplog.set_level(logging.INFO)
    generate_questions(None, REQUEST)
    assert "outcome=failed" in caplog.text
    assert "reason=no_api_key" in caplog.text


# --- Building the client --------------------------------------------------------------


def test_the_client_uses_the_apps_key_and_address_not_other_anthropic_variables(monkeypatch):
    # research.md R11: variables set for other tools must not reach the app's client.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-for-another-tool")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "token-for-another-tool")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://proxy.example.invalid")
    client = build_client({config.API_KEY_ENV_VAR: "the-apps-own-key"})
    assert client.api_key == "the-apps-own-key"
    assert client.auth_token is None
    assert str(client.base_url).rstrip("/") == config.API_BASE_URL


def test_the_client_has_the_configured_timeout_and_no_retries():
    # research.md R5
    client = build_client({config.API_KEY_ENV_VAR: "the-apps-own-key"})
    assert client.timeout == config.API_TIMEOUT_SECONDS
    assert client.max_retries == config.API_MAX_RETRIES


def test_a_missing_key_gives_no_client_even_when_another_key_is_set(monkeypatch):
    # research.md R11: never fall back to the SDK's own search for a key.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-for-another-tool")
    assert build_client({}) is None


def test_a_blank_key_gives_no_client():
    assert build_client({config.API_KEY_ENV_VAR: "   "}) is None


def test_building_the_client_never_logs_the_key(caplog):
    # Constitution Principle III
    caplog.set_level(logging.DEBUG)
    build_client({config.API_KEY_ENV_VAR: "test-secret-value-not-a-real-key"})
    assert "test-secret-value-not-a-real-key" not in caplog.text
