"""Tests for inquiry/response_checks.py: whether the model's reply may be shown (T013).

One test or more for each check in data-model.md, "Checks applied, in order". A reply
that fails any check is rejected, never repaired (FR-005).
"""

import fakes
from inquiry.response_checks import check_reply, normalise

SEED = fakes.SEED
GOOD = fakes.GOOD_CANDIDATES


def reply(candidates, selected):
    """A parsed model reply, as generate.py hands it to check_reply."""
    return {"candidates": candidates, "selected": selected}


# --- A reply that passes ------------------------------------------------------------


def test_a_good_reply_passes_and_returns_the_selected_questions_in_order():
    result = check_reply(reply(GOOD, [3, 0, 6]), SEED)
    assert result == {"passed": True, "questions": [GOOD[3], GOOD[0], GOOD[6]]}


def test_three_and_five_questions_are_both_accepted():
    # FR-004: the edges of the range are allowed.
    assert check_reply(reply(GOOD, [0, 1, 2]), SEED)["passed"] is True
    assert check_reply(reply(GOOD, [0, 1, 2, 3, 4]), SEED)["passed"] is True


def test_surrounding_whitespace_is_trimmed_from_returned_questions():
    candidates = ["  What is assumed?  ", "What is the evidence?", "Who is affected?"]
    result = check_reply(reply(candidates, [0, 1, 2]), SEED)
    assert result["questions"][0] == "What is assumed?"


# --- Shape: the reply is the object the prompt asked for ----------------------------


def test_a_reply_that_is_not_an_object_fails_the_shape_check():
    assert check_reply(["What?", "Why?", "How?"], SEED) == {"passed": False, "failed_check": "shape"}


def test_a_reply_missing_selected_fails_the_shape_check():
    assert check_reply({"candidates": GOOD}, SEED) == {"passed": False, "failed_check": "shape"}


def test_a_candidate_that_is_not_a_string_fails_the_shape_check():
    assert check_reply(reply(GOOD + [7], [0, 1, 2]), SEED) == {"passed": False, "failed_check": "shape"}


def test_a_position_that_is_not_a_whole_number_fails_the_shape_check():
    assert check_reply(reply(GOOD, [0, 1, "2"]), SEED) == {"passed": False, "failed_check": "shape"}


def test_true_is_not_accepted_as_a_position():
    # In Python, True counts as the number 1. It is still not a position.
    assert check_reply(reply(GOOD, [0, True, 2]), SEED) == {"passed": False, "failed_check": "shape"}


# --- Check 1: `selected` has 3–5 entries, all distinct, all valid positions ---------


def test_two_questions_are_rejected():
    # FR-005: too few is never padded.
    assert check_reply(reply(GOOD, [0, 1]), SEED) == {"passed": False, "failed_check": "selection"}


def test_six_questions_are_rejected_never_truncated():
    # FR-005: too many is never cut down to five.
    result = check_reply(reply(GOOD, [0, 1, 2, 3, 4, 5]), SEED)
    assert result == {"passed": False, "failed_check": "selection"}


def test_the_same_position_chosen_twice_is_rejected():
    assert check_reply(reply(GOOD, [0, 1, 1]), SEED) == {"passed": False, "failed_check": "selection"}


def test_a_position_past_the_end_of_the_candidates_is_rejected():
    assert check_reply(reply(GOOD, [0, 1, 10]), SEED) == {"passed": False, "failed_check": "selection"}


def test_a_negative_position_is_rejected():
    # Python would read -1 as "the last one". It is not a valid position here.
    assert check_reply(reply(GOOD, [0, 1, -1]), SEED) == {"passed": False, "failed_check": "selection"}


# --- Check 2: each is non-empty and ends with a question mark (FR-006) --------------


def test_an_empty_question_is_rejected():
    candidates = GOOD + ["   "]
    result = check_reply(reply(candidates, [0, 1, 10]), SEED)
    assert result == {"passed": False, "failed_check": "question_mark"}


def test_a_statement_without_a_question_mark_is_rejected():
    candidates = GOOD + ["Remote teams lose the chance meetings that spark ideas."]
    result = check_reply(reply(candidates, [0, 1, 10]), SEED)
    assert result == {"passed": False, "failed_check": "question_mark"}


def test_a_question_mark_in_the_middle_does_not_count():
    candidates = GOOD + ["Why? Because of chance meetings."]
    result = check_reply(reply(candidates, [0, 1, 10]), SEED)
    assert result == {"passed": False, "failed_check": "question_mark"}


# --- Check 3: each is at most 300 characters (FR-010) -------------------------------


def test_a_question_of_exactly_300_characters_is_accepted():
    question = "W" + "h" * 298 + "?"
    assert len(question) == 300
    result = check_reply(reply(GOOD + [question], [0, 1, 10]), SEED)
    assert result["passed"] is True


def test_a_question_of_301_characters_is_rejected():
    question = "W" + "h" * 299 + "?"
    assert len(question) == 301
    result = check_reply(reply(GOOD + [question], [0, 1, 10]), SEED)
    assert result == {"passed": False, "failed_check": "length"}


# --- Check 4: no two are the same once normalised (FR-007) --------------------------


def test_two_questions_differing_only_in_case_and_punctuation_are_rejected():
    candidates = GOOD + ["what do you MEAN by innovative and how would you measure it, for a team?"]
    result = check_reply(reply(candidates, [0, 3, 10]), SEED)
    assert result == {"passed": False, "failed_check": "duplicate"}


def test_two_questions_differing_only_in_spacing_are_rejected():
    candidates = ["What is assumed?", "What   is\nassumed?", "Who is affected?"]
    result = check_reply(reply(candidates, [0, 1, 2]), SEED)
    assert result == {"passed": False, "failed_check": "duplicate"}


# --- Check 5: none restates the seed or question being opened (FR-009) --------------


def test_a_question_that_restates_the_seed_is_rejected():
    candidates = GOOD + ["Remote work makes teams less innovative?"]
    result = check_reply(reply(candidates, [0, 3, 10]), SEED)
    assert result == {"passed": False, "failed_check": "restates"}


def test_a_question_restating_a_seed_that_was_itself_a_question_is_rejected():
    seed = "Why do cities grow?"
    candidates = ["why do cities grow?", "What is a city?", "Who decides where cities grow?"]
    result = check_reply(reply(candidates, [0, 1, 2]), seed)
    assert result == {"passed": False, "failed_check": "restates"}


# --- Checks run in the documented order ----------------------------------------------


def test_the_first_failing_check_is_the_one_reported():
    # Six questions, one of them over-length: the count check comes first.
    long_question = "W" + "h" * 299 + "?"
    candidates = GOOD + [long_question]
    result = check_reply(reply(candidates, [0, 1, 2, 3, 4, 10]), SEED)
    assert result == {"passed": False, "failed_check": "selection"}


# --- Normalising --------------------------------------------------------------------


def test_normalise_lower_cases_removes_punctuation_and_collapses_whitespace():
    assert normalise("  What's   THE point,\n really?! ") == "whats the point really"


def test_normalise_removes_typographic_punctuation_too():
    assert normalise("“Ready” — for what?") == "ready for what"
