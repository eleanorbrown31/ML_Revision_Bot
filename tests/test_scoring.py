from lib import scoring


# --- mcq ---------------------------------------------------------------

def test_mcq_correct():
    assert scoring.score_mcq({"correct": 2}, 2) == 1.0


def test_mcq_incorrect():
    assert scoring.score_mcq({"correct": 2}, 0) == 0.0


def test_mcq_no_response():
    assert scoring.score_mcq({"correct": 2}, None) == 0.0


# --- multi (Jaccard) -----------------------------------------------------

def test_multi_exact_match():
    assert scoring.score_multi({"correct": [0, 3]}, [0, 3]) == 1.0


def test_multi_partial_overlap():
    # correct={0,3}, selected={0,1} -> intersection=1, union=3
    assert scoring.score_multi({"correct": [0, 3]}, [0, 1]) == 1 / 3


def test_multi_no_response():
    assert scoring.score_multi({"correct": [0, 3]}, []) == 0.0


# --- fill (synonyms + fuzzy matching) -------------------------------------

def test_fill_all_correct():
    answer_key = {"blanks": [["gini", "gini impurity"], ["impurity"]]}
    assert scoring.score_fill(answer_key, ["Gini", "impurity"]) == 1.0


def test_fill_partial():
    answer_key = {"blanks": [["gini", "gini impurity"], ["impurity"]]}
    assert scoring.score_fill(answer_key, ["entropy", "impurity"]) == 0.5


def test_fill_fuzzy_typo_within_distance_2_on_long_token():
    # "impurty" vs "impurity" is one deletion -> distance 1, token >4 chars
    answer_key = {"blanks": [["impurity"]]}
    assert scoring.score_fill(answer_key, ["impurty"]) == 1.0


def test_fill_short_token_requires_exact_match():
    # "K" vs "Q" -- both length 1, well under the fuzzy threshold, must be exact
    answer_key = {"blanks": [["k"]]}
    assert scoring.score_fill(answer_key, ["q"]) == 0.0


def test_fill_missing_response_entries():
    answer_key = {"blanks": [["gini"], ["impurity"]]}
    assert scoring.score_fill(answer_key, ["gini"]) == 0.5


# --- match (keyed on text, not index) -------------------------------------

def test_match_all_correct():
    answer_key = {"pairs": {"Gini impurity": "Measures node purity", "Entropy": "Measures disorder"}}
    response = {"Gini impurity": "Measures node purity", "Entropy": "Measures disorder"}
    assert scoring.score_match(answer_key, response) == 1.0


def test_match_partial():
    answer_key = {"pairs": {"Gini impurity": "Measures node purity", "Entropy": "Measures disorder"}}
    response = {"Gini impurity": "Measures node purity", "Entropy": "Wrong definition"}
    assert scoring.score_match(answer_key, response) == 0.5


def test_match_is_keyed_on_text_not_position():
    # Regression guard: a response dict with entries in a different order to
    # the answer_key's pairs must still score correctly, since matching is
    # by text key, not by insertion/list position.
    answer_key = {"pairs": {"A": "1", "B": "2"}}
    response = {"B": "2", "A": "1"}
    assert scoring.score_match(answer_key, response) == 1.0


# --- order (Kendall-tau-style partial credit) -----------------------------

def test_order_exact_sequence():
    answer_key = {"sequence": [2, 0, 1, 3]}
    assert scoring.score_order(answer_key, [2, 0, 1, 3]) == 1.0


def test_order_fully_reversed_scores_zero():
    answer_key = {"sequence": [0, 1, 2, 3]}
    assert scoring.score_order(answer_key, [3, 2, 1, 0]) == 0.0


def test_order_single_adjacent_swap_scores_partial():
    # 4 items -> 6 pairs total; swapping one adjacent pair breaks exactly 1 pair
    answer_key = {"sequence": [0, 1, 2, 3]}
    assert scoring.score_order(answer_key, [1, 0, 2, 3]) == 5 / 6


def test_order_incomplete_response():
    answer_key = {"sequence": [0, 1, 2, 3]}
    assert scoring.score_order(answer_key, []) == 0.0


# --- numeric ---------------------------------------------------------------

def test_numeric_within_tolerance():
    assert scoring.score_numeric({"value": 0.48, "tolerance": 0.01}, 0.485) == 1.0


def test_numeric_outside_tolerance():
    assert scoring.score_numeric({"value": 0.48, "tolerance": 0.01}, 0.50) == 0.0


def test_numeric_no_response():
    assert scoring.score_numeric({"value": 0.48, "tolerance": 0.01}, None) == 0.0


# --- hint penalty ------------------------------------------------------------

def test_hint_penalty_applied():
    assert scoring.apply_hint_penalty(1.0, hint_used=True) == 0.5


def test_hint_penalty_not_applied():
    assert scoring.apply_hint_penalty(1.0, hint_used=False) == 1.0


# --- dispatcher --------------------------------------------------------------

def test_score_question_dispatches_by_format():
    question = {"format": "mcq", "answer_key": {"correct": 1}}
    assert scoring.score_question(question, 1) == 1.0


def test_score_question_applies_hint_penalty():
    question = {"format": "numeric", "answer_key": {"value": 5, "tolerance": 0}}
    assert scoring.score_question(question, 5, hint_used=True) == 0.5
