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
from inquiry.http_response import to_http_response
from inquiry.request_checks import check_request

# Show the app's own outcome lines (see inquiry/generate.py), and only warnings from
# anything else, so no library prints request details into the log.
logging.basicConfig(level=logging.WARNING)
logging.getLogger("inquiry").setLevel(logging.INFO)


# Vercel's Python runtime looks for a class with exactly this lower-case name.
class handler(BaseHTTPRequestHandler):
    """Answers POST with questions or a message; answers every other method with 405."""

    def do_POST(self):
        body = self.read_body()
        result = check_request(body)
        if result["outcome"] == "checked":
            client = build_client(os.environ)
            result = generate_questions(client, result["request"])
        status_code, payload = to_http_response(result)
        self.write_json(status_code, payload)

    def do_GET(self):
        self.write_method_not_allowed()

    def do_PUT(self):
        self.write_method_not_allowed()

    def do_PATCH(self):
        self.write_method_not_allowed()

    def do_DELETE(self):
        self.write_method_not_allowed()

    def read_body(self):
        """Read the request body, using the length the browser declared."""
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length)

    def write_json(self, status_code, payload):
        """Send a status code and a JSON body."""
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def write_method_not_allowed(self):
        """Send a fixed 405 for any method other than POST. No body is promised."""
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        """Say nothing about each request. The standard library's own line is not needed,
        and inquiry/generate.py already records the outcome of every request."""
