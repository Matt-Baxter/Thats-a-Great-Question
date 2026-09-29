"""The app's one HTTP endpoint, POST /api/questions, as Vercel runs it.

This file makes no judgments of its own. It reads the request body, hands it to the
tested functions in inquiry/, and writes back the status code and JSON they produce.
Its one branch only passes values along: if the request failed its checks, that result
is sent back and the model is never called. Every judgment, including which status code
an outcome gets, lives in inquiry/. tests/test_handler.py runs it as a real server.

Nothing from the request body is logged or stored (FR-040), and there is no account or
login of any kind (FR-041).
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler

from inquiry.generate import build_client, generate_questions
from inquiry.http_response import to_http_response, unexpected_error_response
from inquiry.request_checks import check_request, read_body

# Show the app's own outcome lines (see inquiry/generate.py) and only warnings from
# anything else. The SDK and its HTTP library are set to warnings by name, because
# setting ANTHROPIC_LOG=debug would otherwise make the SDK log every request in full,
# seed included (FR-048).
logging.basicConfig(level=logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("httpx2").setLevel(logging.WARNING)
logging.getLogger("inquiry").setLevel(logging.INFO)


# Vercel's Python runtime looks for a class with exactly this lower-case name.
class handler(BaseHTTPRequestHandler):
    """Answers POST with questions or a message; answers the other standard methods with 405."""

    def do_POST(self):
        # Anything unforeseen still ends in this app's JSON, never a crash (FR-039).
        try:
            status_code, payload = self.answer()
        except Exception as error:
            status_code, payload = unexpected_error_response(error)
        self.write_json(status_code, payload)

    def answer(self):
        """Read and check the request, ask the model if it passed, and return the status code and body."""
        body = read_body(self.headers.get("Content-Length"), self.rfile)
        result = check_request(body)
        if result["outcome"] == "checked":
            client = build_client(os.environ)
            result = generate_questions(client, result["request"])
        return to_http_response(result)

    def do_GET(self):
        self.write_method_not_allowed()

    def do_HEAD(self):
        self.write_method_not_allowed()

    def do_OPTIONS(self):
        self.write_method_not_allowed()

    def do_PUT(self):
        self.write_method_not_allowed()

    def do_PATCH(self):
        self.write_method_not_allowed()

    def do_DELETE(self):
        self.write_method_not_allowed()

    def write_json(self, status_code, payload):
        """Send a status code and a JSON body."""
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def write_method_not_allowed(self):
        """Send a fixed 405 for any standard method other than POST. No body is promised."""
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        """Say nothing about each request. The standard library's own line is not needed,
        and inquiry/generate.py already records the outcome of every request."""
