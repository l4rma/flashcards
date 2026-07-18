from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable

from boto3.dynamodb.conditions import Key

from app.database import QUEST_COMPLETIONS_TABLE, STATS_TABLE, Store, serialize_item
from app.models import Stats

ADD_CARDS_TARGET = 5
TRAIN_CORRECT_CAP = 10
# daily_train's target floor — a small/empty deck would otherwise give a
# trivial (or 0) target, so it starts at TRAIN_FLOOR_START and grows +5/day
# (Stats.sync_day) up to TRAIN_FLOOR_MAX, deliberately outgrowing a small
# deck's natural due count to nudge the user toward building a bigger one.
# TRAIN_FLOOR_START must match Stats.quest_train_floor's dataclass default
# in models.py (can't import it from there — models.py has no reverse
# dependency on this module, and it shouldn't gain one just for this).
TRAIN_FLOOR_START = 5
TRAIN_FLOOR_GROWTH = 5
TRAIN_FLOOR_MAX = 50


@dataclass(frozen=True)
class QuestDef:
    key: str
    title: str
    description: str
    badge: str
    target: Callable[[Stats], int]
    current: Callable[[Stats], int]
    coin_reward: int = 10


# Static for now — designed to evolve/rotate in the future (see SPEC.md).
DAILY_QUESTS: list[QuestDef] = [
    QuestDef(
        "daily_add_cards",
        "Deck Builder",
        f"Add {ADD_CARDS_TARGET} cards today.",
        "📚",
        lambda stats: ADD_CARDS_TARGET,
        lambda stats: stats.quest_cards_added_today,
    ),
    QuestDef(
        "daily_train",
        "Daily Training",
        "Mark cards correct in Train.",
        "🎯",
        lambda stats: max(stats.quest_train_floor, min(TRAIN_CORRECT_CAP, stats.session_initial_due)),
        lambda stats: stats.quest_correct_today,
    ),
]


def record_quest_card_added(stats: Stats) -> Stats:
    """Increments the "cards added today" counter — called only from the
    POST /cards endpoint, after the caller has already run stats.sync_day
    for today. Deliberately a Stats counter incremented on the actual add
    action, not a live count of cards created today: the latter would also
    count cards inserted by other means, bypassing the app entirely."""
    stats.quest_cards_added_today += 1
    return stats


def record_quest_correct_grade(stats: Stats) -> Stats:
    """Increments the "correct today" counter — called only from
    POST /cards/{id}/grade on a Correct grade, after the caller has
    already run stats.sync_day for today."""
    stats.quest_correct_today += 1
    return stats


def _sort_key(today: date, quest_key: str) -> str:
    return f"{today.isoformat()}#{quest_key}"


def _completed_today(store: Store, user_id: str, today: date) -> set[str]:
    resp = store.quest_completions.query(
        KeyConditionExpression=Key("user_id").eq(user_id)
        & Key("sort_key").begins_with(f"{today.isoformat()}#")
    )
    return {item["quest_key"] for item in resp["Items"]}


def check_and_complete_quests(store: Store, user_id: str, stats: Stats, today: date | None = None) -> list[str]:
    """Same snapshot-then-reward pattern as
    achievements.check_and_unlock_achievements, for the same reason:
    awarding coins for one quest shouldn't spuriously satisfy another
    quest's condition within the same check. A QuestCompletions row is
    what actually gates the reward to "once per quest per day" — the
    underlying progress counters can keep climbing past the target the
    rest of the day without re-awarding."""
    today = today or date.today()
    already_completed_today = _completed_today(store, user_id, today)

    newly_completed = [
        quest
        for quest in DAILY_QUESTS
        if quest.key not in already_completed_today and quest.current(stats) >= quest.target(stats)
    ]
    if not newly_completed:
        return []

    total_reward = sum(quest.coin_reward for quest in newly_completed)
    completed_at = datetime.now(timezone.utc).isoformat()
    transact_items = [
        {
            "Put": {
                "TableName": QUEST_COMPLETIONS_TABLE,
                "Item": serialize_item(
                    {
                        "user_id": user_id,
                        "sort_key": _sort_key(today, quest.key),
                        "quest_key": quest.key,
                        "completed_date": today.isoformat(),
                        "completed_at": completed_at,
                    }
                ),
                "ConditionExpression": "attribute_not_exists(sort_key)",
            }
        }
        for quest in newly_completed
    ]
    transact_items.append(
        {
            "Update": {
                "TableName": STATS_TABLE,
                "Key": serialize_item({"user_id": user_id}),
                "UpdateExpression": "ADD coins :r, lifetime_coins_earned :r",
                "ExpressionAttributeValues": {":r": {"N": str(total_reward)}},
            }
        }
    )
    store.client.transact_write_items(TransactItems=transact_items)

    stats.coins += total_reward
    stats.lifetime_coins_earned += total_reward
    return [quest.key for quest in newly_completed]


def describe_quests(keys: list[str]) -> list[dict]:
    """Look up display info (title/description/badge/coin_reward) for a
    list of quest keys — used to build the completion-celebration popup
    payload attached to whichever API response caused the completion."""
    by_key = {quest.key: quest for quest in DAILY_QUESTS}
    return [
        {
            "key": quest.key,
            "title": quest.title,
            "description": quest.description,
            "badge": quest.badge,
            "coin_reward": quest.coin_reward,
        }
        for key in keys
        if (quest := by_key.get(key)) is not None
    ]


def list_quests(store: Store, user_id: str, stats: Stats, today: date | None = None) -> list[dict]:
    today = today or date.today()
    completed_today = _completed_today(store, user_id, today)
    return [
        {
            "key": quest.key,
            "title": quest.title,
            "description": quest.description,
            "badge": quest.badge,
            "completed": quest.key in completed_today,
            "progress_current": min(quest.current(stats), quest.target(stats)),
            "progress_target": quest.target(stats),
            "coin_reward": quest.coin_reward,
        }
        for quest in DAILY_QUESTS
    ]


def clear_quest_completions(store: Store, user_id: str) -> None:
    resp = store.quest_completions.query(KeyConditionExpression=Key("user_id").eq(user_id))
    for item in resp["Items"]:
        store.quest_completions.delete_item(Key={"user_id": user_id, "sort_key": item["sort_key"]})
