"""A hand-written stand-in for the Anthropic client, so no test calls the live model.

The constitution forbids tests that call the real API (Principle II). Instead, a test
builds a FakeClient with the replies it wants, in order, and passes it to the code
under test. The fake records the arguments of every call, so a test can check what
would have been sent to the model.

Each canned reply below is a function rather than a shared object, so no test can
change a reply another test relies on. No mocking library is used (research.md R10).
"""

import json

import anthropic
import httpx2

# The seed every canned reply is written about.
SEED = "Remote work makes teams less innovative."

# Ten distinct candidate questions about SEED, each ending with a question mark.
GOOD_CANDIDATES = [
    "What do you mean by innovative, and how would you measure it for a team?",
    "Which teams did you have in mind when you formed this view?",
    "What evidence would show remote teams innovating as much as co-located ones?",
    "Is it remote work itself, or how remote work was introduced, that makes the difference?",
    "Who benefits if people believe remote teams innovate less?",
    "What happened to innovation at companies that went remote before the pandemic?",
    "Which kinds of innovation depend on chance meetings, and which do not?",
    "What would a remote team have to do differently to close the gap, if there is one?",
    "How long after going remote would a drop in innovation become visible?",
    "What are co-located teams giving up that remote teams gain?",
]


class FakeBlock:
    """One content block of a reply: a "text" block or a "thinking" block."""

    def __init__(self, block_type, text=""):
        self.type = block_type
        self.text = text


class FakeStopDetails:
    """Why the model refused, as the real API reports it."""

    def __init__(self, category):
        self.category = category


class FakeResponse:
    """A reply from the model: its content blocks, why it stopped, and refusal details."""

    def __init__(self, content, stop_reason="end_turn", stop_details=None):
        self.content = content
        self.stop_reason = stop_reason
        self.stop_details = stop_details


class FakeMessages:
    """Stands in for client.beta.messages. Records each call and returns the next queued reply."""

    def __init__(self, queued):
        self.queued = queued
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        next_reply = self.queued.pop(0)
        if isinstance(next_reply, Exception):
            raise next_reply
        return next_reply


class FakeBeta:
    """Stands in for client.beta, which holds the messages resource."""

    def __init__(self, queued):
        self.messages = FakeMessages(queued)


class FakeClient:
    """Stands in for anthropic.Anthropic. Give it replies or exceptions in the order to return them."""

    def __init__(self, *replies):
        self.beta = FakeBeta(list(replies))

    def calls(self):
        """Every set of arguments the code under test passed to create(), in order."""
        return self.beta.messages.calls


# --- Building replies -------------------------------------------------------------


def reply_with(candidates, selected):
    """A reply whose single text block is the JSON the prompt asks for."""
    text = json.dumps({"candidates": candidates, "selected": selected})
    return FakeResponse([FakeBlock("text", text)])


def valid_reply():
    """Four good questions chosen from ten candidates."""
    return reply_with(GOOD_CANDIDATES, [0, 3, 6, 7])


def too_few():
    """Only two questions chosen; the minimum is three."""
    return reply_with(GOOD_CANDIDATES, [0, 3])


def too_many():
    """Six questions chosen; the maximum is five."""
    return reply_with(GOOD_CANDIDATES, [0, 1, 2, 3, 4, 5])


def duplicate_pair():
    """Two chosen questions differ only in case and punctuation."""
    candidates = GOOD_CANDIDATES + ["what do you MEAN by innovative and how would you measure it, for a team?"]
    return reply_with(candidates, [0, 3, 10])


def statement_not_question():
    """One chosen question is a statement with no question mark."""
    candidates = GOOD_CANDIDATES + ["Remote teams lose the chance meetings that spark ideas."]
    return reply_with(candidates, [0, 3, 10])


def over_length_question():
    """One chosen question is 301 characters long; the maximum is 300."""
    long_question = "W" + "h" * 299 + "?"
    candidates = GOOD_CANDIDATES + [long_question]
    return reply_with(candidates, [0, 3, 10])


def restates_seed():
    """One chosen question is the seed itself, reworded only by punctuation."""
    candidates = GOOD_CANDIDATES + ["Remote work makes teams less innovative?"]
    return reply_with(candidates, [0, 3, 10])


def thinking_then_text():
    """A valid reply with a thinking block first, as this model can send (research.md R1)."""
    text = json.dumps({"candidates": GOOD_CANDIDATES, "selected": [1, 2, 4]})
    return FakeResponse([FakeBlock("thinking", ""), FakeBlock("text", text)])


def refusal(category="reasoning_extraction"):
    """The model, and its fallback, declined. The text block holds refusal wording that must never be shown."""
    return FakeResponse(
        [FakeBlock("text", "I can't help with that request.")],
        stop_reason="refusal",
        stop_details=FakeStopDetails(category),
    )


def cut_off():
    """The reply hit the output-token limit part way through its JSON."""
    return FakeResponse([FakeBlock("text", '{"candidates": ["What')], stop_reason="max_tokens")


def unparseable():
    """The reply is prose, not JSON."""
    return FakeResponse([FakeBlock("text", "Here are some questions you might ask.")])


# --- Building errors the SDK can raise --------------------------------------------

# A request object the SDK's exceptions require. Nothing is ever sent.
_FAKE_REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def timeout_error():
    """The model did not reply within the client's timeout."""
    return anthropic.APITimeoutError(request=_FAKE_REQUEST)


def connection_error():
    """The model could not be reached at all."""
    return anthropic.APIConnectionError(request=_FAKE_REQUEST)


def status_error(status_code=500):
    """The API answered with an error status, such as 401 for a bad key or 500 for a fault."""
    response = httpx2.Response(status_code, request=_FAKE_REQUEST)
    return anthropic.APIStatusError("API error", response=response, body=None)
