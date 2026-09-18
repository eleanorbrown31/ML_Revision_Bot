"""Deterministic marking for all six objective question formats (spec §5).

Pure functions -- no DB or Streamlit imports. No model is ever asked "how
did she do?"; every score here is computed, not judged.

Response shapes expected (produced by app/components/question_render.py):
  mcq     -> int | None            selected option index
  multi   -> list[int]             selected option indices
  fill    -> list[str]             one entry per blank, in template order
  match   -> dict[str, str]        left text -> chosen right text
  order   -> list[int]             original item indices, in chosen order
  numeric -> float | None
"""

import re

from rapidfuzz.distance import Levenshtein

from lib.constants import (
    FUZZY_MATCH_MAX_LEVENSHTEIN_DISTANCE,
    FUZZY_MATCH_MIN_TOKEN_LENGTH,
    HINT_PENALTY_MULTIPLIER,
)

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = _PUNCTUATION_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _matches_synonym(response_text: str, synonym: str) -> bool:
    a, b = normalize_text(response_text), normalize_text(synonym)
    if not a:
        return False
    if a == b:
        return True
    if len(a) > FUZZY_MATCH_MIN_TOKEN_LENGTH and len(b) > FUZZY_MATCH_MIN_TOKEN_LENGTH:
        return Levenshtein.distance(a, b) <= FUZZY_MATCH_MAX_LEVENSHTEIN_DISTANCE
    return False


def score_mcq(answer_key: dict, response: int | None) -> float:
    if response is None:
        return 0.0
    return 1.0 if response == answer_key.get("correct") else 0.0


def score_multi(answer_key: dict, response: list[int] | None) -> float:
    """Jaccard: hits / (correct ∪ selected)."""
    correct = set(answer_key.get("correct", []))
    selected = set(response or [])
    union = correct | selected
    if not union:
        return 1.0
    return len(correct & selected) / len(union)


def score_fill(answer_key: dict, response: list[str] | None) -> float:
    """Fraction of blanks correct; accepts any listed synonym, fuzzy-matched."""
    blanks = answer_key.get("blanks", [])
    if not blanks:
        return 0.0
    response = response or []
    hits = 0
    for i, synonyms in enumerate(blanks):
        user_text = response[i] if i < len(response) else ""
        if any(_matches_synonym(user_text, syn) for syn in synonyms):
            hits += 1
    return hits / len(blanks)


def score_match(answer_key: dict, response: dict[str, str] | None) -> float:
    """Fraction of pairs correct, keyed on text -- not index."""
    pairs = answer_key.get("pairs", {})
    if not pairs:
        return 0.0
    response = response or {}
    hits = sum(1 for left, right in pairs.items() if response.get(left) == right)
    return hits / len(pairs)


def score_order(answer_key: dict, response: list[int] | None) -> float:
    """Kendall-tau-style pairwise concordance, normalised to 0-1 so near
    misses score partial credit. Items missing from `response` are simply
    excluded from the pairwise comparison rather than penalised twice."""
    sequence = answer_key.get("sequence", [])
    if len(sequence) < 2:
        return 0.0
    correct_rank = {item: pos for pos, item in enumerate(sequence)}
    response_rank = {
        item: pos for pos, item in enumerate(response or []) if item in correct_rank
    }

    items = list(response_rank.keys())
    total_pairs = 0
    concordant_pairs = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            total_pairs += 1
            if (correct_rank[a] < correct_rank[b]) == (response_rank[a] < response_rank[b]):
                concordant_pairs += 1

    if total_pairs == 0:
        return 0.0
    return concordant_pairs / total_pairs


def score_numeric(answer_key: dict, response: float | None) -> float:
    if response is None:
        return 0.0
    value = answer_key.get("value")
    tolerance = answer_key.get("tolerance", 0)
    return 1.0 if abs(response - value) <= tolerance else 0.0


def apply_hint_penalty(score: float, hint_used: bool) -> float:
    return score * HINT_PENALTY_MULTIPLIER if hint_used else score


_SCORERS = {
    "mcq": score_mcq,
    "multi": score_multi,
    "fill": score_fill,
    "match": score_match,
    "order": score_order,
    "numeric": score_numeric,
}


def score_question(question: dict, response, hint_used: bool = False) -> float:
    scorer = _SCORERS.get(question["format"])
    if scorer is None:
        raise ValueError(f"unknown question format: {question['format']}")
    raw_score = scorer(question["answer_key"], response)
    return apply_hint_penalty(raw_score, hint_used)
