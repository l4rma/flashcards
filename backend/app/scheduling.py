from datetime import date, datetime, timedelta, timezone

from app.models import Card
from app.schemas import Grade

# A card that's survived this many days between reviews without a Wrong
# grade is considered "mastered" for achievement purposes (2 -> 4 -> 8 ->
# 16 -> 32 -> 64, i.e. six consecutive Correct grades from new).
MASTERY_THRESHOLD_DAYS = 64


def apply_grade(card: Card, grade: Grade, today: date | None = None) -> bool:
    """Mutates the card's scheduling state and returns True if this grade
    caused it to newly cross the mastery threshold (for the "Word Master"
    achievement — see app/achievements.py)."""
    today = today or date.today()
    newly_mastered = False

    if grade == Grade.correct:
        card.times_correct += 1
        card.interval_days = 2 if card.interval_days == 0 else card.interval_days * 2
        card.due_date = today + timedelta(days=card.interval_days)
        card.last_reviewed_at = datetime.now(timezone.utc)
        if not card.mastered and card.interval_days >= MASTERY_THRESHOLD_DAYS:
            card.mastered = True
            newly_mastered = True
    else:
        card.times_wrong += 1
        card.interval_days = 0
        # due_date intentionally left as-is: the card stays due until graded
        # correct, so it keeps reappearing in the current session's queue.

    card.last_grade = grade.value
    return newly_mastered


def reset_card_progress(card: Card, today: date | None = None) -> Card:
    """Reset a card back to its just-added state — used by Admin's "Reset
    all progress" action. Also clears the lifetime counters
    (times_correct/times_wrong/mastered/last_grade), not just scheduling —
    originally left those alone, but that meant deck/correct-count/mastery
    achievements would re-unlock immediately after a reset since the
    numbers they check never actually went back down. "Reset all progress"
    now means exactly that."""
    today = today or date.today()
    card.interval_days = 0
    card.due_date = today
    card.last_reviewed_at = None
    card.times_correct = 0
    card.times_wrong = 0
    card.mastered = False
    card.last_grade = None
    return card
