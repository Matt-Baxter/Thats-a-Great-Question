"""Every value that shapes what the app does, named and explained in one place.

The constitution requires that any limit, count or timeout a user could notice be
defined here with a comment, not written as a bare number inside a function. Each
comment says what the value controls and which requirement or research entry set it.
"""

# --- What a user may send -------------------------------------------------------

# The longest seed accepted, in characters. Longer seeds are refused with a message
# naming this limit and the seed's actual length (FR-003). public/app.js repeats this
# number for its character counter; the server is what enforces it.
MAX_SEED_CHARS = 2000

# The largest request body accepted, in bytes. A seed plus the chain of questions
# above the one being opened fits in far less; the cap stops an oversized body from
# being parsed at all. It also sets a practical ceiling on depth of several hundred
# levels, recorded as a finding in plan.md (research.md R6).
MAX_REQUEST_BYTES = 256_000


# --- What a successful answer contains -------------------------------------------

# The fewest and most questions a successful response may hold. A reply outside this
# range is rejected, never trimmed or padded (FR-004, FR-005).
MIN_QUESTIONS = 3
MAX_QUESTIONS = 5

# The longest question accepted, in characters (FR-010). Also the longest ancestor
# question the browser may send back, since ancestors are questions this app returned.
MAX_QUESTION_CHARS = 300

# How many candidate questions the model is asked to write before choosing the
# strongest few. A wider pool gives the choice something to choose between
# (research.md R2).
CANDIDATES_MIN = 10
CANDIDATES_MAX = 15

# How many of the most recent ancestor questions are included in the prompt, besides
# the seed, which is always included. Keeps the prompt bounded and on-topic however
# deep a user goes (research.md R6).
MAX_ANCESTORS_IN_PROMPT = 6


# --- Which model, and how it is called --------------------------------------------

# The model that writes the questions, chosen by the maintainer (research.md R1).
MODEL = "claude-opus-5-5"

# How hard the model thinks. Quality comes before speed; "medium" is this model's
# own default and the starting point, with "high" to be tried on the review set
# (research.md R1, T049).
EFFORT = "medium"

# The most tokens the model may produce. Thinking counts toward this limit even though
# its text is not returned, so it is sized for thinking plus the reply (research.md R1).
MAX_OUTPUT_TOKENS = 16000

# How long to wait for the model before giving up, in seconds. Kept under the thirty
# seconds within which every request must resolve (FR-038), leaving room for the rest
# of the request. vercel.json caps the whole function at 30 seconds (research.md R5).
API_TIMEOUT_SECONDS = 25

# How many times the SDK retries a failed call on its own. Zero, because the SDK
# retries timeouts too, and each retry could add another 25 seconds (research.md R5).
API_MAX_RETRIES = 0


# --- The key, and where it is sent -------------------------------------------------

# The environment variable holding the Anthropic API key. Deliberately not the SDK's
# usual ANTHROPIC_API_KEY, so a key set for some other tool on the same machine is
# never picked up. Its value is read in server code only, never logged, and never sent
# to the browser (constitution Principle III; research.md R11).
API_KEY_ENV_VAR = "QUESTION_APP_API_KEY"

# Where the model is called. Passed to the client explicitly so that an
# ANTHROPIC_BASE_URL set in the environment for another tool cannot redirect the
# app's calls, or its key, somewhere else (research.md R11).
API_BASE_URL = "https://api.anthropic.com"
