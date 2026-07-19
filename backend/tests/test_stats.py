from datetime import date, datetime, timedelta

from app.models import Stats
from app.schemas import Grade
from app.stats import (
    SESSION_COMPLETE_BONUS,
    award_session_complete,
    record_card_mastered,
    record_comeback,
    record_training_activity,
    reset_all_stats,
    sync_day,
)

TEST_USER_ID = "test-user"


def make_stats(**overrides) -> Stats:
    stats = Stats(user_id=TEST_USER_ID)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return stats


def test_first_ever_grade_starts_streak_at_one():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.wrong, today=today)

    assert stats.current_streak == 1
    assert stats.longest_streak == 1
    assert stats.last_active_date == today


def test_same_day_grade_does_not_change_streak():
    today = date(2026, 1, 10)
    stats = make_stats(current_streak=3, longest_streak=3, last_active_date=today)

    record_training_activity(stats, Grade.correct, today=today)

    assert stats.current_streak == 3


def test_next_day_grade_increments_streak():
    yesterday = date(2026, 1, 10)
    stats = make_stats(current_streak=3, longest_streak=3, last_active_date=yesterday)

    record_training_activity(stats, Grade.wrong, today=yesterday + timedelta(days=1))

    assert stats.current_streak == 4
    assert stats.longest_streak == 4


def test_gap_resets_streak():
    last_active = date(2026, 1, 1)
    stats = make_stats(current_streak=10, longest_streak=10, last_active_date=last_active)

    record_training_activity(stats, Grade.wrong, today=last_active + timedelta(days=5))

    assert stats.current_streak == 1
    assert stats.longest_streak == 10  # high-water mark preserved


def test_correct_awards_coins_wrong_does_not():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.wrong, today=today)

    assert stats.coins == 1
    assert stats.lifetime_coins_earned == 1


def test_correct_awards_xp_wrong_does_not():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.wrong, today=today)

    assert stats.xp == 1


def test_session_complete_bonus_awards_xp():
    stats = make_stats()

    award_session_complete(stats)

    assert stats.xp == SESSION_COMPLETE_BONUS


def test_correct_and_wrong_update_total_counters():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.wrong, today=today)

    assert stats.total_correct == 2
    assert stats.total_wrong == 1


def test_correct_grades_build_a_correct_streak():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.correct, today=today)

    assert stats.current_correct_streak == 3
    assert stats.longest_correct_streak == 3


def test_wrong_grade_resets_correct_streak_but_keeps_high_water_mark():
    stats = make_stats()
    today = date(2026, 1, 10)

    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.correct, today=today)
    record_training_activity(stats, Grade.wrong, today=today)

    assert stats.current_correct_streak == 0
    assert stats.longest_correct_streak == 2  # preserved

    record_training_activity(stats, Grade.correct, today=today)
    assert stats.current_correct_streak == 1
    assert stats.longest_correct_streak == 2  # not beaten yet


def test_reset_all_stats_clears_lifetime_coins_earned_too():
    stats = make_stats()

    record_training_activity(stats, Grade.correct, today=date(2026, 1, 10))
    reset_all_stats(stats)

    assert stats.coins == 0
    assert stats.lifetime_coins_earned == 0


def test_reset_all_stats_does_not_clear_total_cards():
    # total_cards deliberately survives "reset all progress" — mirrors the
    # deck-size achievements' documented exception (this action doesn't
    # delete cards, only resets scheduling state).
    stats = make_stats(total_cards=12, total_correct=5, total_wrong=2)

    reset_all_stats(stats)

    assert stats.total_cards == 12
    assert stats.total_correct == 0
    assert stats.total_wrong == 0


def test_session_complete_awards_flat_bonus():
    stats = make_stats(coins=50, current_streak=1)

    award_session_complete(stats)

    assert stats.coins == 60  # 50 + flat 10, no streak scaling
    assert stats.lifetime_coins_earned == 10
    assert stats.sessions_completed == 1


def test_session_complete_bonus_does_not_scale_with_streak():
    stats = make_stats(coins=0, current_streak=3)

    award_session_complete(stats)

    assert stats.coins == 10  # still flat 10, streak length irrelevant


def test_wrong_grade_marks_session_had_wrong():
    stats = make_stats()

    record_training_activity(stats, Grade.wrong, today=date(2026, 1, 10))

    assert stats.session_had_wrong is True


def test_session_complete_awards_flawless_only_without_a_wrong():
    stats = make_stats(session_had_wrong=False)

    award_session_complete(stats)

    assert stats.flawless_sessions_completed == 1


def test_session_complete_skips_flawless_after_a_wrong():
    stats = make_stats(session_had_wrong=True)

    award_session_complete(stats)

    assert stats.flawless_sessions_completed == 0
    assert stats.session_had_wrong is False  # reset for the next round


def test_session_complete_tracks_largest_session():
    stats = make_stats(session_initial_due=30, largest_session_completed=10)

    award_session_complete(stats)

    assert stats.largest_session_completed == 30


def test_sync_day_resets_had_wrong_on_new_day(store):
    yesterday = date(2026, 1, 10)
    stats = make_stats(session_date=yesterday, session_had_wrong=True)

    sync_day(store, TEST_USER_ID, stats, today=yesterday + timedelta(days=1))

    assert stats.session_had_wrong is False


def test_early_bird_and_night_owl_flags():
    stats = make_stats()

    record_training_activity(stats, Grade.correct, today=date(2026, 1, 10), now=datetime(2026, 1, 10, 6, 30))
    assert stats.trained_before_7am is True
    assert stats.trained_after_11pm is False

    record_training_activity(stats, Grade.correct, today=date(2026, 1, 10), now=datetime(2026, 1, 10, 23, 30))
    assert stats.trained_after_11pm is True


def test_night_owl_flag_spans_midnight():
    # Regression test: Night Owl originally only checked `hour >= 23`, so
    # training right after midnight (e.g. 00:19) didn't count as "late" at
    # all — worse, it satisfied Early Bird's old `hour < 7` instead,
    # mislabeling a night owl as an early riser. User-reported bug.
    stats = make_stats()

    record_training_activity(stats, Grade.correct, today=date(2026, 1, 10), now=datetime(2026, 1, 10, 0, 19))
    assert stats.trained_after_11pm is True
    assert stats.trained_before_7am is False


def test_early_bird_flag_does_not_fire_before_4am():
    stats = make_stats()

    record_training_activity(stats, Grade.correct, today=date(2026, 1, 10), now=datetime(2026, 1, 10, 2, 0))
    assert stats.trained_before_7am is False
    assert stats.trained_after_11pm is True


def test_record_comeback_and_card_mastered():
    stats = make_stats()

    record_comeback(stats)
    record_comeback(stats)
    record_card_mastered(stats)

    assert stats.comebacks == 2
    assert stats.cards_mastered == 1


def test_sync_day_freezes_due_count_on_first_check_in(store):
    stats = make_stats()
    today = date(2026, 1, 10)

    sync_day(store, TEST_USER_ID, stats, today=today)

    assert stats.session_initial_due == 0  # no cards due for this fresh user
    assert stats.session_date == today


def test_sync_day_does_not_shrink_within_the_same_day(store):
    stats = make_stats()
    today = date(2026, 1, 10)

    stats.session_initial_due = 10
    stats.session_date = today
    # Simulate cards being graded correct later the same day — a repeat
    # sync_day call on the same day must not re-freeze from a live count.
    sync_day(store, TEST_USER_ID, stats, today=today)

    assert stats.session_initial_due == 10


def test_sync_day_resets_on_a_new_day(store):
    yesterday = date(2026, 1, 10)
    stats = make_stats(session_date=yesterday, session_initial_due=10)

    sync_day(store, TEST_USER_ID, stats, today=yesterday + timedelta(days=1))

    assert stats.session_initial_due == 0  # no cards due for this fresh user
    assert stats.session_date == yesterday + timedelta(days=1)


def test_reset_all_stats_clears_everything():
    stats = make_stats(
        coins=99,
        current_streak=5,
        longest_streak=8,
        last_active_date=date(2026, 1, 1),
        session_date=date(2026, 1, 1),
        session_initial_due=10,
    )

    reset_all_stats(stats)

    assert stats.coins == 0
    assert stats.current_streak == 0
    assert stats.longest_streak == 0
    assert stats.last_active_date is None
    assert stats.session_date is None
    assert stats.session_initial_due == 0


def test_reset_all_stats_clears_lifetime_achievement_fields_too():
    # Reversed from the original design: leaving these alone meant
    # achievements re-unlocked immediately after a reset with no new
    # activity, since the numbers they check never actually went back down.
    stats = make_stats(
        lifetime_coins_earned=500,
        sessions_completed=20,
        longest_correct_streak=15,
        cards_mastered=3,
        comebacks=2,
        flawless_sessions_completed=4,
        largest_session_completed=40,
        trained_before_7am=True,
        trained_after_11pm=True,
        xp=1200,
        level=5,
    )

    reset_all_stats(stats)

    assert stats.lifetime_coins_earned == 0
    assert stats.sessions_completed == 0
    assert stats.longest_correct_streak == 0
    assert stats.cards_mastered == 0
    assert stats.comebacks == 0
    assert stats.flawless_sessions_completed == 0
    assert stats.largest_session_completed == 0
    assert stats.xp == 0
    assert stats.level == 1
    assert stats.trained_before_7am is False
    assert stats.trained_after_11pm is False
