"""Tunable constants for scoring, mastery and question selection.

Values are transcribed from revision-engine-build-spec.md sections 4 and 5.
Where the spec leaves a formula unspecified, the choice is noted inline
(see the plan's "open flags" section for the full rationale).
"""

DIFFICULTY_BANDS = ["F1", "F2", "F3", "INT", "ADV"]
QUESTION_FORMATS = ["mcq", "multi", "fill", "match", "order", "numeric"]

# --- Ability update (spec §4, "Ability update") -----------------------------

BAND_WEIGHT = {"F1": 0.6, "F2": 0.8, "F3": 1.0, "INT": 1.3, "ADV": 1.6}
EWMA_ALPHA = 0.3
ABILITY_MIN = 0
ABILITY_MAX = 100
RAW_SCORE_CAP = 100  # a single strong ADV answer cannot max out a topic

# --- Band progression (spec §4, "Band progression") -------------------------

STRONG_SCORE_THRESHOLD = 0.8   # score >= this counts as "strong"
WEAK_SCORE_THRESHOLD = 0.5     # score < this counts as "weak"
PROMOTE_CONSECUTIVE_STRONG = 3
PROMOTE_MIN_ATTEMPTS_AT_BAND = 5
DEMOTE_CONSECUTIVE_WEAK = 2

# --- Spaced repetition, SM-2 variant (spec §4, "Spaced repetition") ---------

SM2_EASE_MIN = 1.3
SM2_EASE_MAX = 2.8
SM2_EASE_STRONG_DELTA = 0.10
SM2_EASE_WEAK_DELTA = -0.20
SM2_INTERVAL_MIN_DAYS = 1
SM2_INTERVAL_MAX_DAYS = 21
SM2_MEDIUM_INTERVAL_MULTIPLIER = 1.2  # 0.5 <= score < 0.8

# --- Question selection priority (spec §4, "Question selection") -----------

PRIORITY_WEIGHT_OVERDUE = 0.40
PRIORITY_WEIGHT_ABILITY = 0.30
PRIORITY_WEIGHT_COVERAGE_GAP = 0.15
PRIORITY_WEIGHT_EXAM_WEIGHT = 0.10
PRIORITY_WEIGHT_RANDOM = 0.05

OVERDUE_NORM_DAYS_CAP = 7  # days past due / 7, capped at 1

# Spec states coverage_gap is "1 if never attempted, decaying with attempts"
# but gives no formula. Using max(0, 1 - attempts/N); flagged in the plan.
COVERAGE_GAP_DECAY_ATTEMPTS = 5

# Timetable pressure (spec §4, "Timetable pressure"): interpolate between an
# early/breadth-first vector and a late/shore-up-weak-spots vector as the
# exam approaches. days_to_exam=None (no exam date set) uses the early vector.
TIMETABLE_EARLY_WEIGHTS = {
    "overdue_norm": 0.25,
    "ability_gap": 0.20,
    "coverage_gap": 0.35,
    "exam_weight_norm": 0.15,
    "random": 0.05,
}
TIMETABLE_LATE_WEIGHTS = {
    "overdue_norm": 0.45,
    "ability_gap": 0.35,
    "coverage_gap": 0.05,
    "exam_weight_norm": 0.10,
    "random": 0.05,
}
TIMETABLE_INTERPOLATION_WINDOW_DAYS = 60  # fully "late" at or inside this many days out

# --- Interleaving constraints (spec §4, reinterpreted at topic-level mastery,
# see plan's "Module boundaries" section) ------------------------------------

MAX_CONSECUTIVE_SAME_AREA = 2
MIN_SESSION_LENGTH_FOR_AREA_SPREAD = 8
MIN_AREAS_IN_LARGE_SESSION = 3
NEGLECT_DAYS_THRESHOLD = 14  # at least one question from a topic unseen this long
DEFAULT_SESSION_LENGTH = 10
LEARN_SESSION_LENGTH = 5

# --- Marking (spec §5) -------------------------------------------------------

HINT_PENALTY_MULTIPLIER = 0.5
FUZZY_MATCH_MIN_TOKEN_LENGTH = 4
FUZZY_MATCH_MAX_LEVENSHTEIN_DISTANCE = 2
