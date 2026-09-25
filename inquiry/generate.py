"""Asks the model for questions once, and turns whatever happens into a result.

This is the only module that talks to the model. It builds the client from the app's
own key (build_client), makes one call, and maps every possible outcome — questions,
a decline, a cut-off or unusable reply, a timeout, an unreachable API, a missing key —
to exactly one result. Nothing the model returns is passed on until response_checks.py
has approved it (FR-033).

generate_questions returns one of these shapes:
    {"outcome": "ok", "questions": [...]}
    {"outcome": "declined", "message": ...}
    {"outcome": "failed", "message": ...}
    {"outcome": "timed_out", "message": ...}

What it logs is the outcome, the reason or refusal category, and the depth of the
request. It never logs the seed, any question, the model's text, or the key (FR-048,
FR-049; constitution Principle III).
"""

import json
import logging

import anthropic

from inquiry import config, messages
from inquiry.prompts import REPLY_SCHEMA, build_system_prompt, build_user_message
from inquiry.response_checks import check_reply

logger = logging.getLogger(__name__)

# Turns on the API's server-side fallback: if the model declines, the API retries the
# same request on a fallback model within the same call, chosen by the kind of decline
# (research.md R4). Only a decline by the whole chain reaches the user.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODE = "default"


def build_client(environ):
    """Build the Anthropic client from the app's own key, or return None if the key is not set.

    Both the key and the address are passed explicitly so the SDK never looks for them
    elsewhere, such as in ANTHROPIC_API_KEY or ANTHROPIC_BASE_URL (research.md R11).
    """
    api_key = environ.get(config.API_KEY_ENV_VAR, "").strip()
    if api_key == "":
        # Never build a client with no key: the SDK would then search the environment
        # and disk for one, and could find a key meant for something else.
        return None
    return anthropic.Anthropic(
        api_key=api_key,
        base_url=config.API_BASE_URL,
        timeout=config.API_TIMEOUT_SECONDS,
        max_retries=config.API_MAX_RETRIES,
    )


def generate_questions(client, request):
    """Ask the model for questions about a checked request and return the result.

    `client` is None when no key is configured, and the request then fails.
    """
    depth = len(request["ancestors"])

    if client is None:
        log_outcome("failed", "no_api_key", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    # The timeout error is a kind of connection error in the SDK, so it must be caught first.
    try:
        response = call_model(client, request)
    except anthropic.APITimeoutError:
        log_outcome("timed_out", "timeout", depth)
        return {"outcome": "timed_out", "message": messages.TIMED_OUT}
    except anthropic.APIConnectionError:
        log_outcome("failed", "unreachable", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}
    except anthropic.APIStatusError as error:
        log_outcome("failed", f"status_{error.status_code}", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    return result_from_response(response, request, depth)


def call_model(client, request):
    """Send one request to the model, with the settings research.md R1–R4 chose."""
    return client.beta.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_OUTPUT_TOKENS,
        system=build_system_prompt(),
        messages=[{"role": "user", "content": build_user_message(request["seed"])}],
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": REPLY_SCHEMA},
        },
        betas=[FALLBACK_BETA],
        fallbacks=FALLBACK_MODE,
    )


def result_from_response(response, request, depth):
    """Turn the model's response into a result, checking why it stopped before reading it."""
    # A decline by the model and its fallback. The refusal's own wording is never shown
    # or logged (FR-053); only its category is logged.
    if response.stop_reason == "refusal":
        log_outcome("declined", "refusal", depth, refusal_category(response))
        return {"outcome": "declined", "message": messages.declined("seed")}

    # The reply was cut off at the output-token limit, so its JSON is incomplete (FR-035).
    if response.stop_reason == "max_tokens":
        log_outcome("failed", "max_tokens", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    reply = read_reply(response)
    if reply is None:
        log_outcome("failed", "unparseable", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    checked = check_reply(reply, request["seed"])
    if not checked["passed"]:
        log_outcome("failed", checked["failed_check"], depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    log_outcome("ok", "passed", depth)
    return {"outcome": "ok", "questions": checked["questions"]}


def read_reply(response):
    """Parse the JSON in the response's text block, or return None if there is none or it will not parse.

    The text block is found by its type, because thinking blocks can come first (research.md R1).
    """
    for block in response.content:
        if block.type == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return None
    return None


def refusal_category(response):
    """The refusal's category, such as "cyber", or None if the API gave none."""
    if response.stop_details is None:
        return None
    return response.stop_details.category


def log_outcome(outcome, reason, depth, category=None):
    """Record what happened to a request, without any of its content (FR-048, FR-049)."""
    logger.info("outcome=%s reason=%s category=%s depth=%d", outcome, reason, category, depth)
