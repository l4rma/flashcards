import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Card:
    """Plain in-memory representation of a card — no ORM/DB binding. Used
    both as scheduling.py's mutation target (attribute access, unchanged
    from when this was a SQLAlchemy model) and as the shape app/cards.py
    converts to/from DynamoDB items."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    french: str = ""
    english: str = ""
    interval_days: int = 0
    due_date: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=_utcnow)
    last_reviewed_at: datetime | None = None
    times_correct: int = 0
    times_wrong: int = 0
    last_grade: str | None = None
    mastered: bool = False


@dataclass
class Stats:
    """Plain in-memory representation of a user's gamification state — one
    per user, keyed by user_id. No ORM/DB binding; app/stats.py converts
    to/from DynamoDB items."""

    user_id: str
    # Profile identity — permanent user preferences, not gamification
    # progress, so deliberately NOT touched by "reset all progress" (same
    # reasoning as total_cards being spared).
    username: str | None = None
    avatar_key: str | None = None
    coins: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: date | None = None
    # Frozen once per calendar day so the Train progress bar survives a
    # page refresh instead of recomputing from the (shrinking) live
    # due-count.
    session_date: date | None = None
    session_initial_due: int = 0
    # Lifetime records for achievements — deliberately NOT reset by any
    # admin reset action, so achievements stay earned even after resetting
    # the spendable `coins` balance.
    lifetime_coins_earned: int = 0
    sessions_completed: int = 0
    current_correct_streak: int = 0
    longest_correct_streak: int = 0
    # Whether any Wrong grade has happened since the last session
    # completion (or start of a new day) — for the "Flawless Session"
    # achievement.
    session_had_wrong: bool = False
    flawless_sessions_completed: int = 0
    # High-water mark of session_initial_due at the moment a session
    # actually completed — for "Marathon".
    largest_session_completed: int = 0
    # Lifetime count of "graded Wrong, then Correct" on the same card's
    # next grade — for "Comeback Kid".
    comebacks: int = 0
    # Lifetime count of cards that have ever crossed the mastery interval
    # threshold — for the "Word Master" family.
    cards_mastered: int = 0
    # One-time flags for the time-of-day achievements, based on local wall
    # clock time.
    trained_before_7am: bool = False
    trained_after_11pm: bool = False
    # Frozen/reset once per calendar day for the Daily Quests feature.
    quest_date: date | None = None
    quest_cards_added_today: int = 0
    quest_correct_today: int = 0
    # Running counters backing the deck-size / lifetime-correct / lifetime-
    # wrong achievement families — incremented at the same call sites as
    # the other counters above (POST /cards, a Correct/Wrong grade) rather
    # than computed via a live aggregate query, since DynamoDB has no SUM/
    # COUNT query the way SQL did. total_cards is deliberately NOT reset by
    # "reset all progress" (mirrors the old live-query behavior — that
    # action doesn't delete cards, only resets scheduling state).
    total_cards: int = 0
    total_correct: int = 0
    total_wrong: int = 0
