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


def build_client(environ, http_client=None):
    """Build the Anthropic client from the app's own key, or return None if the key is not set.

    The key, the address and the authentication headers are all set explicitly, so
    nothing another tool put in the environment can change them (research.md R11).
    Only tests pass `http_client`, to capture what would be sent without sending it.
    """
    api_key = environ.get(config.API_KEY_ENV_VAR, "").strip()
    if api_key == "":
        # Never build a client with no key: the SDK would then search the environment
        # and disk for one, and could find a key meant for something else.
        return None
    return anthropic.Anthropic(
        api_key=api_key,
        base_url=config.API_BASE_URL,
        # The SDK also adds every header listed in ANTHROPIC_CUSTOM_HEADERS, and one of
        # those could carry another tool's key or token. Headers given here win, so the
        # key header is always the app's own and no bearer token is ever sent.
        default_headers={"X-Api-Key": api_key, "Authorization": anthropic.omit},
        timeout=config.API_TIMEOUT_SECONDS,
        max_retries=config.API_MAX_RETRIES,
        http_client=http_client,
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
        messages=[
            {"role": "user", "content": build_user_message(request["seed"], request["ancestors"])}
        ],
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": REPLY_SCHEMA},
        },
        betas=[FALLBACK_BETA],
        fallbacks=FALLBACK_MODE,
    )


def result_from_response(response, request, depth):
    """Turn the model's response into a result, checking why it stopped before reading it."""
    # A decline for which the fallback could not be tried, because it was overloaded or
    # out of capacity. The seed may be fine, so this is a failure worth retrying, not a
    # decline (research.md R4).
    if response.stop_reason == "refusal" and fallback_was_skipped(response):
        log_outcome("failed", "fallback_unavailable", depth, refusal_category(response))
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    # A decline by the model and its fallback. The refusal's own wording is never shown
    # or logged (FR-053); only its category is logged.
    if response.stop_reason == "refusal":
        log_outcome("declined", "refusal", depth, refusal_category(response))
        return {"outcome": "declined", "message": messages.declined(what_is_opened(request))}

    # The reply was cut off at the output-token limit, so its JSON is incomplete (FR-035).
    if response.stop_reason == "max_tokens":
        log_outcome("failed", "max_tokens", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    reply = read_reply(response)
    if reply is None:
        log_outcome("failed", "unparseable", depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    # Expansions pass exactly the same checks as a first set, compared against the
    # question being opened rather than the seed (FR-009, FR-016).
    checked = check_reply(reply, text_being_opened(request))
    if not checked["passed"]:
        log_outcome("failed", checked["failed_check"], depth)
        return {"outcome": "failed", "message": messages.GENERATION_FAILED}

    log_outcome("ok", "passed", depth)
    return {"outcome": "ok", "questions": checked["questions"]}


def text_being_opened(request):
    """The seed, or the question being opened: the last ancestor, when there are any."""
    if len(request["ancestors"]) == 0:
        return request["seed"]
    return request["ancestors"][-1]


def what_is_opened(request):
    """Return "seed" or "question", whichever the request is about, for the declined message (FR-052)."""
    if len(request["ancestors"]) == 0:
        return "seed"
    return "question"


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


def fallback_was_skipped(response):
    """True if the API says it could not try the fallback model for this refusal.

    The API sets `recommended_model` only in that case, naming the model it would have tried.
    """
    if response.stop_details is None:
        return False
    return response.stop_details.recommended_model is not None


def refusal_category(response):
    """The refusal's category, such as "cyber", or None if the API gave none."""
    if response.stop_details is None:
        return None
    return response.stop_details.category


def log_outcome(outcome, reason, depth, category=None):
    """Record what happened to a request, without any of its content (FR-048, FR-049)."""
    logger.info("outcome=%s reason=%s category=%s depth=%d", outcome, reason, category, depth)
