from lib import mastery


# --- update_ability (EWMA, difficulty-weighted, raw capped, clamped) -------

def test_ability_ewma_basic():
    # raw = min(1.0 * 1.3 * 100, 100) = 100; new = 0.7*50 + 0.3*100 = 65
    assert mastery.update_ability(50, 1.0, "INT") == 65.0


def test_ability_raw_capped_at_100_for_advanced_band():
    # weight 1.6 would push raw to 160 uncapped; capped to 100
    assert mastery.update_ability(0, 1.0, "ADV") == 30.0


def test_ability_clamped_to_max_100():
    assert mastery.update_ability(100, 1.0, "ADV") == 100


def test_ability_clamped_to_min_0():
    assert mastery.update_ability(0, 0.0, "F1") == 0


# --- band_progression ------------------------------------------------------

def test_promotion_after_three_strong_and_five_attempts_at_band():
    state = {"band": "F1", "attempts_count": 0, "consecutive_strong": 0, "consecutive_weak": 0}
    for _ in range(4):
        result = mastery.band_progression(
            state["band"], 0.8, state["attempts_count"], state["consecutive_strong"], state["consecutive_weak"]
        )
        state = {
            "band": result["band"],
            "attempts_count": result["attempts_count"],
            "consecutive_strong": result["consecutive_strong"],
            "consecutive_weak": result["consecutive_weak"],
        }
    assert state["band"] == "F1"  # not yet promoted: attempts_count only 4

    result = mastery.band_progression(
        state["band"], 0.8, state["attempts_count"], state["consecutive_strong"], state["consecutive_weak"]
    )
    assert result["band"] == "F2"
    assert result["attempts_count"] == 0
    assert result["consecutive_strong"] == 0


def test_score_exactly_0_8_counts_as_strong():
    # attempts_count=1 so this call's new_attempts(2) stays below the
    # promotion threshold of 5 -- isolates the is-strong boundary check
    # from the promotion reset.
    result = mastery.band_progression("F1", 0.8, 1, 2, 0)
    assert result["consecutive_strong"] == 3


def test_score_just_below_0_8_is_not_strong():
    result = mastery.band_progression("F1", 0.79, 10, 2, 0)
    assert result["consecutive_strong"] == 0


def test_score_exactly_0_5_is_not_weak():
    result = mastery.band_progression("F1", 0.5, 10, 0, 1)
    assert result["consecutive_weak"] == 0


def test_score_just_below_0_5_is_weak():
    result = mastery.band_progression("F1", 0.49, 10, 0, 1)
    assert result["consecutive_weak"] == 2


def test_demotion_after_two_consecutive_weak_regardless_of_attempts_count():
    result = mastery.band_progression("INT", 0.3, 20, 0, 1)
    assert result["band"] == "F3"
    assert result["attempts_count"] == 0
    assert result["consecutive_weak"] == 0


def test_never_promote_past_adv():
    result = mastery.band_progression("ADV", 0.8, 20, 2, 0)
    assert result["band"] == "ADV"


def test_never_demote_below_f1():
    result = mastery.band_progression("F1", 0.2, 20, 0, 1)
    assert result["band"] == "F1"


def test_medium_score_resets_both_streaks():
    result = mastery.band_progression("F2", 0.65, 5, 2, 0)
    assert result["consecutive_strong"] == 0
    assert result["consecutive_weak"] == 0


# --- update_spaced_repetition (SM-2 variant) --------------------------------

def test_sr_strong_increases_ease_and_interval():
    result = mastery.update_spaced_repetition(ease=2.5, interval_days=4, score=0.9)
    assert result["ease"] == 2.6
    assert result["interval_days"] == 4 * 2.6


def test_sr_medium_keeps_ease_multiplies_interval_by_1_2():
    result = mastery.update_spaced_repetition(ease=2.5, interval_days=4, score=0.6)
    assert result["ease"] == 2.5
    assert result["interval_days"] == 4 * 1.2


def test_sr_weak_decreases_ease_and_resets_interval_to_min():
    result = mastery.update_spaced_repetition(ease=2.5, interval_days=10, score=0.3)
    assert result["ease"] == 2.3
    assert result["interval_days"] == 1


def test_sr_ease_clamped_to_max():
    result = mastery.update_spaced_repetition(ease=2.75, interval_days=1, score=1.0)
    assert result["ease"] == 2.8


def test_sr_ease_clamped_to_min():
    result = mastery.update_spaced_repetition(ease=1.35, interval_days=1, score=0.2)
    assert result["ease"] == 1.3


def test_sr_interval_clamped_to_max_21():
    result = mastery.update_spaced_repetition(ease=2.8, interval_days=20, score=1.0)
    assert result["interval_days"] == 21


def test_sr_interval_clamped_to_min_1():
    result = mastery.update_spaced_repetition(ease=1.3, interval_days=1, score=0.0)
    assert result["interval_days"] == 1


# --- update_mastery_after_attempt (orchestration) ---------------------------

def test_update_mastery_after_attempt_combines_all_three():
    row = {
        "ability": 50,
        "current_band": "F1",
        "attempts_count": 0,
        "consecutive_strong": 0,
        "consecutive_weak": 0,
        "ease": 2.5,
        "interval_days": 1,
    }
    result = mastery.update_mastery_after_attempt(row, score=1.0, difficulty="F1")
    assert result["ability"] > 50
    assert result["current_band"] == "F1"
    assert result["attempts_count"] == 1
    assert result["consecutive_strong"] == 1
    assert result["ease"] == 2.6
    assert result["interval_days"] == 2.6
