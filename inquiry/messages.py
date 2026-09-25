"""Every plain-language message the server can send to a user, in one place.

Keeping them together means anyone can read, in a single file, everything the app
might say when it cannot return questions. The browser shows these exactly as text
and never writes its own, except for three fixed messages it must supply itself
because no reply from this server exists to carry one: the wait-and-try-again message
for the platform's rate limit, the timed-out message when it gives up waiting, and a
failure message when the network fails or the reply is unreadable
(contracts/questions-api.md).
"""

from inquiry import config

# The seed was empty, or only spaces (FR-002).
EMPTY_SEED = "Type a topic, claim, idea or question to get started."

# The request was not in the shape the page sends. A user should never see this
# unless something other than the page is calling the server.
INVALID_REQUEST = "That request could not be read. Reload the page and try again."

# The model was unreachable, or replied with something that could not be used (FR-035).
GENERATION_FAILED = "The questions could not be generated just now. Try again in a moment."

# The model did not reply within the timeout (FR-038).
TIMED_OUT = "That took too long and was stopped. Try again."


def seed_too_long(length):
    """Say that a seed is over the limit, naming both the limit and its actual length (FR-003)."""
    return (
        f"A seed can be up to {config.MAX_SEED_CHARS:,} characters. "
        f"This one is {length:,}."
    )


def declined(about):
    """Say that no questions could be generated, without calling it an error (FR-052).

    `about` is "seed" or "question", whichever the request concerned.
    """
    return f"No questions could be generated for this {about}. Rephrasing it may help."
