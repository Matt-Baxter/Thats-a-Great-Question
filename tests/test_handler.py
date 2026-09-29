"""Tests for api/questions.py, run as a real local server (T022).

The handler only passes values between tested functions, but its one branch decides
whether the model is called at all, so it is tested too. Every request here stops
before the model: an invalid request never builds a client, and a valid one is sent
with no key configured. Nothing reaches the network beyond this machine.
"""

import http.client
import json
import logging
import pathlib
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import HTTPServer

import pytest

import api.questions
from api.questions import handler
from inquiry import config, messages

# The folder holding api/ and inquiry/, for the test that starts a fresh Python.
REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def server_url(monkeypatch):
    """Start the handler on a free local port, with no API key set, and stop it afterwards."""
    monkeypatch.delenv(config.API_KEY_ENV_VAR, raising=False)
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/api/questions"
    server.shutdown()
    server.server_close()


# Talks to the local server directly, ignoring any proxy set in the environment.
DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def send(url, method, body=None):
    """Send a request and return the status code and the decoded JSON body, if any."""
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    try:
        with DIRECT_OPENER.open(request) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    payload = json.loads(raw) if raw else None
    return status, payload


def test_an_empty_seed_gets_400_with_the_empty_seed_message(server_url):
    body = json.dumps({"seed": "   ", "ancestors": []}).encode("utf-8")
    status, payload = send(server_url, "POST", body)
    assert status == 400
    assert payload == {"status": "invalid_input", "message": messages.EMPTY_SEED}


def test_a_body_that_is_not_json_gets_400(server_url):
    status, payload = send(server_url, "POST", b"not json")
    assert status == 400
    assert payload == {"status": "invalid_input", "message": messages.INVALID_REQUEST}


def test_a_valid_seed_with_no_key_configured_gets_502_failed(server_url):
    # research.md R11: without the app's own key, no client is built and nothing is called.
    body = json.dumps({"seed": "Why do cities grow?", "ancestors": []}).encode("utf-8")
    status, payload = send(server_url, "POST", body)
    assert status == 502
    assert payload == {"status": "failed", "message": messages.GENERATION_FAILED}


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "DELETE"])
def test_every_method_other_than_post_gets_405(server_url, method):
    status, _ = send(server_url, method)
    assert status == 405


def send_with_content_length(url, declared_length, body):
    """Send a POST whose Content-Length header says `declared_length`, whatever the body is."""
    parts = urllib.parse.urlsplit(url)
    connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=5)
    connection.putrequest("POST", parts.path)
    connection.putheader("Content-Type", "application/json")
    connection.putheader("Content-Length", declared_length)
    connection.endheaders()
    connection.send(body)
    response = connection.getresponse()
    status, raw = response.status, response.read()
    connection.close()
    return status, json.loads(raw)


@pytest.mark.parametrize("declared_length", ["abc", "-1"])
def test_a_content_length_that_is_not_a_whole_number_gets_400_not_a_hang(server_url, declared_length):
    body = json.dumps({"seed": "Why?", "ancestors": []}).encode("utf-8")
    status, payload = send_with_content_length(server_url, declared_length, body)
    assert status == 400
    assert payload == {"status": "invalid_input", "message": messages.INVALID_REQUEST}


def test_an_unexpected_error_still_gets_this_apps_json(server_url, monkeypatch):
    # FR-039: nothing the handler calls can make it crash without a reply.
    def explode(body):
        raise RuntimeError("something nobody planned for")

    monkeypatch.setattr(api.questions, "check_request", explode)
    body = json.dumps({"seed": "Why?", "ancestors": []}).encode("utf-8")
    status, payload = send(server_url, "POST", body)
    assert status == 502
    assert payload == {"status": "failed", "message": messages.GENERATION_FAILED}


def test_anthropic_log_debug_cannot_turn_on_request_logging():
    # FR-048: with ANTHROPIC_LOG=debug the SDK logs whole requests, seed included. The
    # handler must turn that back down. Run in a fresh Python, because the SDK reads the
    # variable when it is first imported.
    script = (
        "import logging, api.questions; "
        "print(logging.getLogger('anthropic').getEffectiveLevel(), "
        "logging.getLogger('httpx2').getEffectiveLevel())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        env={"ANTHROPIC_LOG": "debug", "PYTHONPATH": str(REPOSITORY_ROOT)},
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    anthropic_level, httpx_level = completed.stdout.split()
    assert int(anthropic_level) >= logging.WARNING
    assert int(httpx_level) >= logging.WARNING
