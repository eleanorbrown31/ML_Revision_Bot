"""Ability update, band progression and spaced repetition (spec §4).

Pure functions -- no DB or "now" access. The repo layer is responsible for
turning the returned interval_days into an actual next_due_at timestamp.
"""

from lib.constants import (
    ABILITY_MAX,
    ABILITY_MIN,
    BAND_WEIGHT,
    DEMOTE_CONSECUTIVE_WEAK,
    DIFFICULTY_BANDS,
    EWMA_ALPHA,
    PROMOTE_CONSECUTIVE_STRONG,
    PROMOTE_MIN_ATTEMPTS_AT_BAND,
    RAW_SCORE_CAP,
    SM2_EASE_MAX,
    SM2_EASE_MIN,
    SM2_EASE_STRONG_DELTA,
    SM2_EASE_WEAK_DELTA,
    SM2_INTERVAL_MAX_DAYS,
    SM2_INTERVAL_MIN_DAYS,
    SM2_MEDIUM_INTERVAL_MULTIPLIER,
    STRONG_SCORE_THRESHOLD,
    WEAK_SCORE_THRESHOLD,
)


def update_ability(ability_old: float, score: float, difficulty: str) -> float:
    """Difficulty-weighted EWMA. raw is capped so one strong ADV answer alone
    cannot max out a topic."""
    raw = min(score * BAND_WEIGHT[difficulty] * 100, RAW_SCORE_CAP)
    ability_new = (1 - EWMA_ALPHA) * ability_old + EWMA_ALPHA * raw
    return max(ABILITY_MIN, min(ABILITY_MAX, ability_new))


def band_progression(
    current_band: str,
    score: float,
    attempts_count: int,
    consecutive_strong: int,
    consecutive_weak: int,
) -> dict:
    """Promote/demote a difficulty band.

    attempts_count/consecutive_strong/consecutive_weak all reset to 0 on a
    band change, since "attempts_count >= 5" is only meaningful per-band.
    """
    is_strong = score >= STRONG_SCORE_THRESHOLD
    is_weak = score < WEAK_SCORE_THRESHOLD

    new_attempts = attempts_count + 1
    new_consecutive_strong = consecutive_strong + 1 if is_strong else 0
    new_consecutive_weak = consecutive_weak + 1 if is_weak else 0

    band_index = DIFFICULTY_BANDS.index(current_band)
    new_band = current_band

    can_promote = band_index < len(DIFFICULTY_BANDS) - 1
    can_demote = band_index > 0

    if (
        can_promote
        and new_consecutive_strong >= PROMOTE_CONSECUTIVE_STRONG
        and new_attempts >= PROMOTE_MIN_ATTEMPTS_AT_BAND
    ):
        new_band = DIFFICULTY_BANDS[band_index + 1]
        new_attempts = new_consecutive_strong = new_consecutive_weak = 0
    elif can_demote and new_consecutive_weak >= DEMOTE_CONSECUTIVE_WEAK:
        new_band = DIFFICULTY_BANDS[band_index - 1]
        new_attempts = new_consecutive_strong = new_consecutive_weak = 0

    return {
        "band": new_band,
        "attempts_count": new_attempts,
        "consecutive_strong": new_consecutive_strong,
        "consecutive_weak": new_consecutive_weak,
    }


def update_spaced_repetition(ease: float, interval_days: float, score: float) -> dict:
    """SM-2 variant (spec §4). Interval cap of 21 days is deliberate -- with
    a fixed exam date a six-month interval is not affordable on anything."""
    if score >= STRONG_SCORE_THRESHOLD:
        new_ease = ease + SM2_EASE_STRONG_DELTA
        new_interval = interval_days * new_ease
    elif score >= WEAK_SCORE_THRESHOLD:
        new_ease = ease
        new_interval = interval_days * SM2_MEDIUM_INTERVAL_MULTIPLIER
    else:
        new_ease = ease + SM2_EASE_WEAK_DELTA
        new_interval = SM2_INTERVAL_MIN_DAYS

    new_ease = max(SM2_EASE_MIN, min(SM2_EASE_MAX, new_ease))
    new_interval = max(SM2_INTERVAL_MIN_DAYS, min(SM2_INTERVAL_MAX_DAYS, new_interval))
    return {"ease": new_ease, "interval_days": new_interval}


def update_mastery_after_attempt(mastery: dict, score: float, difficulty: str) -> dict:
    """Single entry point: given a topic's current mastery row (as a dict with
    ability/current_band/attempts_count/consecutive_strong/consecutive_weak/
    ease/interval_days) and the score+difficulty of a new attempt, returns the
    updated fields. Does not touch last_seen_at/next_due_at -- that's the
    repo layer's job, since it needs "now"."""
    band_result = band_progression(
        mastery["current_band"],
        score,
        mastery["attempts_count"],
        mastery["consecutive_strong"],
        mastery["consecutive_weak"],
    )
    sr_result = update_spaced_repetition(mastery["ease"], mastery["interval_days"], score)

    return {
        "ability": update_ability(mastery["ability"], score, difficulty),
        "current_band": band_result["band"],
        "attempts_count": band_result["attempts_count"],
        "consecutive_strong": band_result["consecutive_strong"],
        "consecutive_weak": band_result["consecutive_weak"],
        "ease": sr_result["ease"],
        "interval_days": sr_result["interval_days"],
    }
