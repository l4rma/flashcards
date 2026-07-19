from datetime import date, datetime, timedelta

from app.cards import count_due
from app.database import Store
from app.models import Stats
from app.schemas import Grade

COINS_PER_CORRECT = 1
SESSION_COMPLETE_BONUS = 10
# Early Bird: [EARLY_BIRD_START_HOUR, EARLY_BIRD_HOUR) — training between
# 4am and 7am local time. Night Owl: [NIGHT_OWL_HOUR, 24) or
# [0, EARLY_BIRD_START_HOUR) — 11pm through 4am, spanning midnight. These
# two windows don't overlap.
EARLY_BIRD_START_HOUR = 4
EARLY_BIRD_HOUR = 7
NIGHT_OWL_HOUR = 23


def _stats_to_item(stats: Stats) -> dict:
    def _d(value):
        return value.isoformat() if value is not None else None

    return {
        "user_id": stats.user_id,
        "username": stats.username,
        "avatar_key": stats.avatar_key,
        "xp": stats.xp,
        "level": stats.level,
        "coins": stats.coins,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "last_active_date": _d(stats.last_active_date),
        "session_date": _d(stats.session_date),
        "session_initial_due": stats.session_initial_due,
        "lifetime_coins_earned": stats.lifetime_coins_earned,
        "sessions_completed": stats.sessions_completed,
        "current_correct_streak": stats.current_correct_streak,
        "longest_correct_streak": stats.longest_correct_streak,
        "session_had_wrong": stats.session_had_wrong,
        "flawless_sessions_completed": stats.flawless_sessions_completed,
        "largest_session_completed": stats.largest_session_completed,
        "comebacks": stats.comebacks,
        "cards_mastered": stats.cards_mastered,
        "trained_before_7am": stats.trained_before_7am,
        "trained_after_11pm": stats.trained_after_11pm,
        "quest_date": _d(stats.quest_date),
        "quest_cards_added_today": stats.quest_cards_added_today,
        "quest_correct_today": stats.quest_correct_today,
        "total_cards": stats.total_cards,
        "total_correct": stats.total_correct,
        "total_wrong": stats.total_wrong,
        "owned_titles": stats.owned_titles,
        "owned_themes": stats.owned_themes,
        "equipped_title": stats.equipped_title,
        "equipped_theme": stats.equipped_theme,
        "lootbox_bronze": stats.lootbox_bronze,
        "lootbox_silver": stats.lootbox_silver,
        "lootbox_gold": stats.lootbox_gold,
        "lootboxes_opened": stats.lootboxes_opened,
        "used_label": stats.used_label,
        "practiced_prebuilt_deck": stats.practiced_prebuilt_deck,
        "practiced_own_full_deck": stats.practiced_own_full_deck,
        "practiced_sub_deck": stats.practiced_sub_deck,
        "practice_sessions_completed": stats.practice_sessions_completed,
    }


def _item_to_stats(item: dict) -> Stats:
    def _d(value):
        return date.fromisoformat(value) if value else None

    return Stats(
        user_id=item["user_id"],
        username=item.get("username"),
        avatar_key=item.get("avatar_key"),
        xp=int(item.get("xp", 0)),
        level=int(item.get("level", 1)),
        coins=int(item.get("coins", 0)),
        current_streak=int(item.get("current_streak", 0)),
        longest_streak=int(item.get("longest_streak", 0)),
        last_active_date=_d(item.get("last_active_date")),
        session_date=_d(item.get("session_date")),
        session_initial_due=int(item.get("session_initial_due", 0)),
        lifetime_coins_earned=int(item.get("lifetime_coins_earned", 0)),
        sessions_completed=int(item.get("sessions_completed", 0)),
        current_correct_streak=int(item.get("current_correct_streak", 0)),
        longest_correct_streak=int(item.get("longest_correct_streak", 0)),
        session_had_wrong=bool(item.get("session_had_wrong", False)),
        flawless_sessions_completed=int(item.get("flawless_sessions_completed", 0)),
        largest_session_completed=int(item.get("largest_session_completed", 0)),
        comebacks=int(item.get("comebacks", 0)),
        cards_mastered=int(item.get("cards_mastered", 0)),
        trained_before_7am=bool(item.get("trained_before_7am", False)),
        trained_after_11pm=bool(item.get("trained_after_11pm", False)),
        quest_date=_d(item.get("quest_date")),
        quest_cards_added_today=int(item.get("quest_cards_added_today", 0)),
        quest_correct_today=int(item.get("quest_correct_today", 0)),
        total_cards=int(item.get("total_cards", 0)),
        total_correct=int(item.get("total_correct", 0)),
        total_wrong=int(item.get("total_wrong", 0)),
        owned_titles=list(item.get("owned_titles") or []),
        owned_themes=list(item.get("owned_themes") or []),
        equipped_title=item.get("equipped_title"),
        equipped_theme=item.get("equipped_theme"),
        lootbox_bronze=int(item.get("lootbox_bronze", 0)),
        lootbox_silver=int(item.get("lootbox_silver", 0)),
        lootbox_gold=int(item.get("lootbox_gold", 0)),
        lootboxes_opened=int(item.get("lootboxes_opened", 0)),
        used_label=bool(item.get("used_label", False)),
        practiced_prebuilt_deck=bool(item.get("practiced_prebuilt_deck", False)),
        practiced_own_full_deck=bool(item.get("practiced_own_full_deck", False)),
        practiced_sub_deck=bool(item.get("practiced_sub_deck", False)),
        practice_sessions_completed=int(item.get("practice_sessions_completed", 0)),
    )


def get_or_create_stats(store: Store, user_id: str) -> Stats:
    resp = store.stats.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    if item is None:
        return Stats(user_id=user_id)
    return _item_to_stats(item)


def save_stats(store: Store, stats: Stats) -> None:
    store.stats.put_item(Item=_stats_to_item(stats))


def sync_day(store: Store, user_id: str, stats: Stats, today: date | None = None) -> Stats:
    """Combines the due-count query (I/O) with the pure freeze-once-per-day
    logic for both the Train page's session baseline and the daily quest
    counters — the single place that establishes "today's baseline" for
    all three, regardless of which route/page triggers it first today.
    (Replaces the old separate stats.sync_session/quests.sync_quest_day
    pair, which always ran together anyway.)

    Note: due_count comes from a GSI query, and DynamoDB doesn't support
    strongly-consistent reads on GSIs — immediately after adding a card,
    this could in rare cases briefly under-count by one before the index
    catches up. Accepted as a minor, self-correcting cosmetic edge case
    rather than engineering around it."""
    today = today or date.today()
    if stats.session_date != today:
        due_count_today = count_due(store, user_id, today)
        stats.session_date = today
        stats.session_initial_due = due_count_today
        stats.session_had_wrong = False
    if stats.quest_date != today:
        stats.quest_date = today
        stats.quest_cards_added_today = 0
        stats.quest_correct_today = 0
    return stats


def record_training_activity(
    stats: Stats, grade: Grade, today: date | None = None, now: datetime | None = None
) -> Stats:
    today = today or date.today()
    now = now or datetime.now()

    if stats.last_active_date is None or stats.last_active_date == today - timedelta(days=1):
        stats.current_streak += 1
    elif stats.last_active_date == today:
        pass  # already active today, streak unchanged
    else:
        stats.current_streak = 1
    stats.last_active_date = today
    stats.longest_streak = max(stats.longest_streak, stats.current_streak)

    if grade == Grade.correct:
        stats.coins += COINS_PER_CORRECT
        stats.lifetime_coins_earned += COINS_PER_CORRECT
        stats.xp += COINS_PER_CORRECT
        stats.current_correct_streak += 1
        stats.longest_correct_streak = max(stats.longest_correct_streak, stats.current_correct_streak)
        stats.total_correct += 1
    else:
        stats.current_correct_streak = 0
        stats.session_had_wrong = True
        stats.total_wrong += 1

    if EARLY_BIRD_START_HOUR <= now.hour < EARLY_BIRD_HOUR:
        stats.trained_before_7am = True
    if now.hour >= NIGHT_OWL_HOUR or now.hour < EARLY_BIRD_START_HOUR:
        stats.trained_after_11pm = True

    return stats


def record_card_added(stats: Stats) -> Stats:
    stats.total_cards += 1
    return stats


def record_comeback(stats: Stats) -> Stats:
    stats.comebacks += 1
    return stats


def record_card_mastered(stats: Stats) -> Stats:
    stats.cards_mastered += 1
    return stats


def award_session_complete(stats: Stats) -> Stats:
    stats.coins += SESSION_COMPLETE_BONUS
    stats.lifetime_coins_earned += SESSION_COMPLETE_BONUS
    stats.xp += SESSION_COMPLETE_BONUS
    stats.sessions_completed += 1
    if not stats.session_had_wrong:
        stats.flawless_sessions_completed += 1
    stats.largest_session_completed = max(stats.largest_session_completed, stats.session_initial_due)
    stats.session_had_wrong = False  # ready for a fresh flawless check
    return stats


def reset_all_stats(stats: Stats) -> Stats:
    """Full reset of every Stats field except total_cards — used by the
    single Admin "Reset all progress" action alongside resetting each
    card's scheduling and clearing achievements/quest completions.
    total_cards deliberately survives (mirrors the deck-size achievements'
    documented exception: this action doesn't delete cards, only resets
    scheduling state, so the count of cards that exist shouldn't drop)."""
    stats.xp = 0
    stats.level = 1
    stats.coins = 0
    stats.current_streak = 0
    stats.longest_streak = 0
    stats.last_active_date = None
    stats.session_date = None
    stats.session_initial_due = 0
    stats.lifetime_coins_earned = 0
    stats.sessions_completed = 0
    stats.current_correct_streak = 0
    stats.longest_correct_streak = 0
    stats.session_had_wrong = False
    stats.flawless_sessions_completed = 0
    stats.largest_session_completed = 0
    stats.comebacks = 0
    stats.cards_mastered = 0
    stats.trained_before_7am = False
    stats.trained_after_11pm = False
    stats.quest_date = None
    stats.quest_cards_added_today = 0
    stats.quest_correct_today = 0
    stats.total_correct = 0
    stats.total_wrong = 0
    stats.owned_titles = []
    stats.owned_themes = []
    stats.equipped_title = None
    stats.equipped_theme = None
    stats.lootbox_bronze = 0
    stats.lootbox_silver = 0
    stats.lootbox_gold = 0
    stats.lootboxes_opened = 0
    stats.used_label = False
    stats.practiced_prebuilt_deck = False
    stats.practiced_own_full_deck = False
    stats.practiced_sub_deck = False
    stats.practice_sessions_completed = 0
    return stats
