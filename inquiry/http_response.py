"""Turns a result into the HTTP status code and JSON body the browser receives.

This is the only place an outcome becomes HTTP, so the mapping in
contracts/questions-api.md can be tested without running a server. Each body carries
only the fields the contract lists, whatever else a result may hold.
"""

# The status code for each outcome. A decline is not an error, so it gets 200 like
# questions do (FR-052). A timeout gets its own code but the same "failed" status in the
# body, because the browser treats it like any other failure.
STATUS_CODE_FOR_OUTCOME = {
    "ok": 200,
    "declined": 200,
    "invalid_input": 400,
    "failed": 502,
    "timed_out": 504,
}

# The `status` field the browser branches on, for each outcome.
BODY_STATUS_FOR_OUTCOME = {
    "ok": "ok",
    "declined": "declined",
    "invalid_input": "invalid_input",
    "failed": "failed",
    "timed_out": "failed",
}


def to_http_response(result):
    """Return the status code and JSON body for a result from request_checks or generate."""
    outcome = result["outcome"]
    status_code = STATUS_CODE_FOR_OUTCOME[outcome]
    body_status = BODY_STATUS_FOR_OUTCOME[outcome]

    if outcome == "ok":
        body = {"status": body_status, "questions": result["questions"]}
    else:
        body = {"status": body_status, "message": result["message"]}
    return status_code, body
