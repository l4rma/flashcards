from datetime import date, datetime, timedelta, timezone

from app.models import Card
from app.scheduling import MASTERY_THRESHOLD_DAYS, apply_grade, reset_card_progress
from app.schemas import Grade


def make_card(interval_days: int = 0, due_date: date | None = None, **overrides) -> Card:
    defaults = dict(
        id="test-id",
        french="chat",
        english="cat",
        interval_days=interval_days,
        due_date=due_date or date.today(),
        times_correct=0,
        times_wrong=0,
        last_grade=None,
        mastered=False,
    )
    defaults.update(overrides)
    return Card(**defaults)


def test_new_card_correct_sets_interval_to_two_days():
    card = make_card(interval_days=0)
    today = date(2026, 1, 1)

    apply_grade(card, Grade.correct, today=today)

    assert card.interval_days == 2
    assert card.due_date == today + timedelta(days=2)
    assert card.last_reviewed_at is not None
    assert card.times_correct == 1
    assert card.times_wrong == 0


def test_repeated_correct_doubles_interval():
    card = make_card(interval_days=2)
    today = date(2026, 1, 1)

    apply_grade(card, Grade.correct, today=today)
    assert card.interval_days == 4
    assert card.due_date == today + timedelta(days=4)

    apply_grade(card, Grade.correct, today=today)
    assert card.interval_days == 8
    assert card.due_date == today + timedelta(days=8)


def test_wrong_resets_interval_to_zero_and_leaves_due_date():
    card = make_card(interval_days=8, due_date=date(2026, 1, 1))

    apply_grade(card, Grade.wrong, today=date(2026, 1, 10))

    assert card.interval_days == 0
    assert card.due_date == date(2026, 1, 1)
    assert card.times_wrong == 1
    assert card.times_correct == 0


def test_repeated_grading_accumulates_lifetime_counters():
    card = make_card(interval_days=0)
    today = date(2026, 1, 1)

    apply_grade(card, Grade.wrong, today=today)
    apply_grade(card, Grade.wrong, today=today)
    apply_grade(card, Grade.correct, today=today)

    assert card.times_wrong == 2
    assert card.times_correct == 1


def test_wrong_after_correct_resets_progress():
    card = make_card(interval_days=0)
    today = date(2026, 1, 1)

    apply_grade(card, Grade.correct, today=today)
    assert card.interval_days == 2

    apply_grade(card, Grade.wrong, today=today)
    assert card.interval_days == 0

    apply_grade(card, Grade.correct, today=today)
    assert card.interval_days == 2


def test_reset_card_progress_clears_scheduling_state():
    card = make_card(interval_days=8, due_date=date(2026, 1, 1))
    card.last_reviewed_at = datetime.now(timezone.utc)

    reset_card_progress(card, today=date(2026, 1, 10))

    assert card.interval_days == 0
    assert card.due_date == date(2026, 1, 10)
    assert card.last_reviewed_at is None


def test_reset_card_progress_clears_lifetime_counters_too():
    # Reversed from the original design: leaving these alone meant
    # deck/correct-count/mastery achievements re-unlocked immediately after
    # a reset, since the numbers they check never actually went back down.
    card = make_card(interval_days=8, due_date=date(2026, 1, 1))
    card.times_correct = 7
    card.times_wrong = 3
    card.mastered = True
    card.last_grade = "correct"

    reset_card_progress(card, today=date(2026, 1, 10))

    assert card.times_correct == 0
    assert card.times_wrong == 0
    assert card.mastered is False
    assert card.last_grade is None


def test_apply_grade_records_last_grade():
    card = make_card()
    today = date(2026, 1, 1)

    apply_grade(card, Grade.wrong, today=today)
    assert card.last_grade == "wrong"

    apply_grade(card, Grade.correct, today=today)
    assert card.last_grade == "correct"


def test_apply_grade_flags_newly_mastered_card():
    # interval_days=32 -> next correct doubles to 64, crossing the threshold.
    card = make_card(interval_days=32)
    assert MASTERY_THRESHOLD_DAYS == 64

    newly_mastered = apply_grade(card, Grade.correct, today=date(2026, 1, 1))

    assert newly_mastered is True
    assert card.mastered is True
    assert card.interval_days == 64


def test_apply_grade_does_not_re_flag_already_mastered_card():
    card = make_card(interval_days=64, mastered=True)

    newly_mastered = apply_grade(card, Grade.correct, today=date(2026, 1, 1))

    assert newly_mastered is False
    assert card.mastered is True


def test_apply_grade_not_mastered_below_threshold():
    card = make_card(interval_days=16)

    newly_mastered = apply_grade(card, Grade.correct, today=date(2026, 1, 1))

    assert newly_mastered is False
    assert card.mastered is False
    assert card.interval_days == 32
