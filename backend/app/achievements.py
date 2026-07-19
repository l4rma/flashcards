from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable

from boto3.dynamodb.conditions import Key

from app.database import ACHIEVEMENTS_TABLE, STATS_TABLE, Store, serialize_item
from app.models import Stats

# Coin reward by tier position within a family (0 = first/easiest tier).
# Longest family currently has 8 tiers (session); the last value repeats
# for any tier beyond the list. Standalone achievements set coin_reward
# explicitly below instead of going through this scaling.
REWARD_BY_TIER_INDEX = [10, 20, 35, 60, 100, 150, 250, 400]


@dataclass(frozen=True)
class AchievementDef:
    key: str
    title: str
    description: str
    badge: str
    target: int
    current: Callable[[Stats], int]
    # Tiers sharing a family are collapsed in list_achievements() down to
    # just the next not-yet-unlocked tier (or the last tier, if the whole
    # ladder is complete). None means a standalone, single-tier achievement.
    family: str | None = None
    # Coins awarded on unlock. For tiered families this is overwritten by
    # _with_tiered_coin_rewards() below based on tier position — the value
    # given at definition time doesn't matter for those. Standalone
    # achievements must set this explicitly.
    coin_reward: int = 10


ACHIEVEMENTS: list[AchievementDef] = [
    AchievementDef(
        "first_review",
        "First Steps",
        "Grade your very first card.",
        "🌱",
        1,
        lambda stats: stats.total_correct + stats.total_wrong,
    ),
    AchievementDef(
        "streak_7", "Week Warrior", "Reach a 7-day streak.", "🔥", 7,
        lambda stats: stats.longest_streak, family="streak",
    ),
    AchievementDef(
        "streak_30", "Monthly Master", "Reach a 30-day streak.", "🔥", 30,
        lambda stats: stats.longest_streak, family="streak",
    ),
    AchievementDef(
        "streak_60", "Streak Master", "Reach a 60-day streak.", "🔥", 60,
        lambda stats: stats.longest_streak, family="streak",
    ),
    AchievementDef(
        "streak_100", "Centurion", "Reach a 100-day streak.", "🔥", 100,
        lambda stats: stats.longest_streak, family="streak",
    ),
    AchievementDef(
        "streak_365", "Year of Learning", "Reach a 365-day streak.", "🔥", 365,
        lambda stats: stats.longest_streak, family="streak",
    ),
    AchievementDef(
        "correct_10", "Getting Started", "10 lifetime correct answers.", "✅", 10,
        lambda stats: stats.total_correct, family="correct",
    ),
    AchievementDef(
        "correct_100", "Century", "100 lifetime correct answers.", "✅", 100,
        lambda stats: stats.total_correct, family="correct",
    ),
    AchievementDef(
        "correct_500", "High Five Hundred", "500 lifetime correct answers.", "✅", 500,
        lambda stats: stats.total_correct, family="correct",
    ),
    AchievementDef(
        "coins_10", "First Coins", "Earn 10 lifetime coins.", "🪙", 10,
        lambda stats: stats.lifetime_coins_earned, family="coins",
    ),
    AchievementDef(
        "coins_100", "Piggy Bank", "Earn 100 lifetime coins.", "🪙", 100,
        lambda stats: stats.lifetime_coins_earned, family="coins",
    ),
    AchievementDef(
        "coins_500", "Treasure Hoard", "Earn 500 lifetime coins.", "🪙", 500,
        lambda stats: stats.lifetime_coins_earned, family="coins",
    ),
    AchievementDef(
        "deck_1", "First Card", "Add your first card.", "📚", 1,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_10", "Building Your Deck", "Add 10 cards.", "📚", 10,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_30", "Growing Collection", "Add 30 cards.", "📚", 30,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_50", "Vocabulary Builder", "Add 50 cards.", "📚", 50,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_100", "Serious Collector", "Add 100 cards.", "📚", 100,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_250", "Deck Master", "Add 250 cards.", "📚", 250,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "deck_500", "Lexicon Legend", "Add 500 cards.", "📚", 500,
        lambda stats: stats.total_cards, family="deck",
    ),
    AchievementDef(
        "session_complete_1", "Session Complete", "Clear a full day's review queue.", "🏁", 1,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_5", "Getting Into It", "Complete 5 sessions.", "🏁", 5,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_10", "Consistent Learner", "Complete 10 sessions.", "🏁", 10,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_25", "Dedicated", "Complete 25 sessions.", "🏁", 25,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_50", "Habitual", "Complete 50 sessions.", "🏁", 50,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_100", "Century Sessions", "Complete 100 sessions.", "🏁", 100,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_250", "Session Veteran", "Complete 250 sessions.", "🏁", 250,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "session_500", "Session Legend", "Complete 500 sessions.", "🏁", 500,
        lambda stats: stats.sessions_completed, family="session",
    ),
    AchievementDef(
        "correct_streak_3", "Hat Trick", "Get 3 correct answers in a row.", "🎯", 3,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "correct_streak_5", "On a Roll", "Get 5 correct answers in a row.", "🎯", 5,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "correct_streak_10", "Hot Hand", "Get 10 correct answers in a row.", "🎯", 10,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "correct_streak_25", "Unstoppable", "Get 25 correct answers in a row.", "🎯", 25,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "correct_streak_50", "Flawless Focus", "Get 50 correct answers in a row.", "🎯", 50,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "correct_streak_100", "Perfection", "Get 100 correct answers in a row.", "🎯", 100,
        lambda stats: stats.longest_correct_streak, family="correct_streak",
    ),
    AchievementDef(
        "first_wrong", "Nobody's Perfect", "Get one wrong — everyone does sometimes.", "🙈", 1,
        lambda stats: stats.total_wrong,
    ),
    AchievementDef(
        "flawless_session", "Flawless Session", "Complete a full session with zero Wrong grades.", "🌟", 1,
        lambda stats: stats.flawless_sessions_completed, coin_reward=20,
    ),
    AchievementDef(
        "comeback_kid", "Comeback Kid", "Get a card wrong, then right the next time you see it.", "🔄", 1,
        lambda stats: stats.comebacks, coin_reward=15,
    ),
    AchievementDef(
        "early_bird", "Early Bird", "Train between 4am and 7am.", "🌅", 1,
        lambda stats: 1 if stats.trained_before_7am else 0, coin_reward=15,
    ),
    AchievementDef(
        "night_owl", "Night Owl", "Train late at night — 11pm through 4am.", "🦉", 1,
        lambda stats: 1 if stats.trained_after_11pm else 0, coin_reward=15,
    ),
    AchievementDef(
        "mastery_1", "Word Master", "Truly learn 1 word (a card that's survived 64+ days between reviews).",
        "🎓", 1, lambda stats: stats.cards_mastered, family="mastery",
    ),
    AchievementDef(
        "mastery_5", "Vocabulary Expert", "Truly learn 5 words.", "🎓", 5,
        lambda stats: stats.cards_mastered, family="mastery",
    ),
    AchievementDef(
        "mastery_10", "Fluent", "Truly learn 10 words.", "🎓", 10,
        lambda stats: stats.cards_mastered, family="mastery",
    ),
    AchievementDef(
        "mastery_25", "Polyglot in Training", "Truly learn 25 words.", "🎓", 25,
        lambda stats: stats.cards_mastered, family="mastery",
    ),
    AchievementDef(
        "mastery_50", "Master Linguist", "Truly learn 50 words.", "🎓", 50,
        lambda stats: stats.cards_mastered, family="mastery",
    ),
    AchievementDef(
        "marathon_25", "Quarter Marathon", "Clear 25 due cards in one sitting.", "🏃", 25,
        lambda stats: stats.largest_session_completed, family="marathon",
    ),
    AchievementDef(
        "marathon_50", "Marathon", "Clear 50 due cards in one sitting.", "🏃", 50,
        lambda stats: stats.largest_session_completed, family="marathon",
    ),
    AchievementDef(
        "marathon_100", "Ultra Marathon", "Clear 100 due cards in one sitting.", "🏃", 100,
        lambda stats: stats.largest_session_completed, family="marathon",
    ),
    AchievementDef(
        "marathon_200", "Iron Learner", "Clear 200 due cards in one sitting.", "🏃", 200,
        lambda stats: stats.largest_session_completed, family="marathon",
    ),
]


def _with_tiered_coin_rewards(achievements: list[AchievementDef]) -> list[AchievementDef]:
    """Overwrites coin_reward on every tiered-family achievement based on
    its position within that family (0 = first/easiest tier), using
    REWARD_BY_TIER_INDEX. Standalone achievements are left exactly as
    defined above, since they set coin_reward explicitly."""
    family_tier_index: dict[str, int] = {}
    result = []
    for achievement in achievements:
        if achievement.family is None:
            result.append(achievement)
            continue
        index = family_tier_index.get(achievement.family, 0)
        family_tier_index[achievement.family] = index + 1
        reward = REWARD_BY_TIER_INDEX[min(index, len(REWARD_BY_TIER_INDEX) - 1)]
        result.append(replace(achievement, coin_reward=reward))
    return result


ACHIEVEMENTS = _with_tiered_coin_rewards(ACHIEVEMENTS)


def _unlocked_items(store: Store, user_id: str) -> dict[str, str]:
    resp = store.achievements.query(KeyConditionExpression=Key("user_id").eq(user_id))
    return {item["achievement_key"]: item["unlocked_at"] for item in resp["Items"]}


def check_and_unlock_achievements(store: Store, user_id: str, stats: Stats) -> list[str]:
    """Check every not-yet-unlocked achievement against `stats` and record
    any newly met ones. Idempotent — already-unlocked achievements are
    never re-checked or duplicated, and stay unlocked permanently even if
    the underlying stat is later reset (except via the admin "reset all
    progress" action, which explicitly clears achievements too — see
    `clear_achievements`).

    `stats` is the caller's already-fetched (and possibly already-mutated
    this request) Stats object — conditions are evaluated against it as a
    snapshot *before* any reward is applied, and rewards are applied only
    afterward via a single DynamoDB transaction (one Put per newly-unlocked
    achievement plus one Update summing every reward onto Stats.coins/
    lifetime_coins_earned), which also updates `stats` in place to match.
    This snapshot-then-reward ordering matters: awarding coins mid-loop
    could spuriously push a coin-threshold achievement (e.g. "coins_10")
    over its target within the very same check, unlocking it for the
    wrong reason."""
    already_unlocked = set(_unlocked_items(store, user_id))

    newly_unlocked = [
        achievement
        for achievement in ACHIEVEMENTS
        if achievement.key not in already_unlocked and achievement.current(stats) >= achievement.target
    ]
    if not newly_unlocked:
        return []

    total_reward = sum(achievement.coin_reward for achievement in newly_unlocked)
    unlocked_at = datetime.now(timezone.utc).isoformat()
    transact_items = [
        {
            "Put": {
                "TableName": ACHIEVEMENTS_TABLE,
                "Item": serialize_item(
                    {"user_id": user_id, "achievement_key": achievement.key, "unlocked_at": unlocked_at}
                ),
                "ConditionExpression": "attribute_not_exists(achievement_key)",
            }
        }
        for achievement in newly_unlocked
    ]
    transact_items.append(
        {
            "Update": {
                "TableName": STATS_TABLE,
                "Key": serialize_item({"user_id": user_id}),
                # xp mirrors coins 1:1 (see leveling.py) — level-up itself
                # is deliberately *not* computed here; finalize_level()
                # reconciles stats.level from the resulting xp total as a
                # separate, simple step after this transaction commits.
                "UpdateExpression": "ADD coins :r, lifetime_coins_earned :r, xp :r",
                "ExpressionAttributeValues": {":r": {"N": str(total_reward)}},
            }
        }
    )
    store.client.transact_write_items(TransactItems=transact_items)

    stats.coins += total_reward
    stats.lifetime_coins_earned += total_reward
    stats.xp += total_reward
    return [achievement.key for achievement in newly_unlocked]


def describe_achievements(keys: list[str]) -> list[dict]:
    """Look up display info (title/description/badge/coin_reward) for a
    list of achievement keys — used to build the unlock-celebration popup
    payload attached to whichever API response caused the unlock."""
    by_key = {achievement.key: achievement for achievement in ACHIEVEMENTS}
    return [
        {
            "key": achievement.key,
            "title": achievement.title,
            "description": achievement.description,
            "badge": achievement.badge,
            "coin_reward": achievement.coin_reward,
        }
        for key in keys
        if (achievement := by_key.get(key)) is not None
    ]


def _to_dict(achievement: AchievementDef, stats: Stats, unlocks: dict, history: list[dict]) -> dict:
    return {
        "key": achievement.key,
        "title": achievement.title,
        "description": achievement.description,
        "badge": achievement.badge,
        "unlocked": achievement.key in unlocks,
        "unlocked_at": unlocks.get(achievement.key),
        "progress_current": min(achievement.current(stats), achievement.target),
        "progress_target": achievement.target,
        "coin_reward": achievement.coin_reward,
        "history": history,
    }


def list_achievements(store: Store, user_id: str, stats: Stats) -> list[dict]:
    """One entry per standalone achievement. For a tiered family, up to two
    entries instead of one per underlying tier:
    - the highest tier already completed (unlocked, colored in the UI),
      with `history` listing the earlier completed tiers in that family —
      only present once at least one tier is unlocked.
    - the next not-yet-unlocked tier (locked, shown dimmed/shaded in the
      UI) — only present unless the whole ladder is already complete.
    A family with nothing unlocked yet shows only the first tier (locked).
    A fully-completed family shows only its last tier (unlocked, full
    history) — there's no "next" left to show."""
    unlocks = _unlocked_items(store, user_id)

    tiers_by_family: dict[str, list[AchievementDef]] = {}
    for achievement in ACHIEVEMENTS:
        if achievement.family:
            tiers_by_family.setdefault(achievement.family, []).append(achievement)

    result = []
    seen_families = set()
    for achievement in ACHIEVEMENTS:
        if achievement.family is None:
            result.append(_to_dict(achievement, stats, unlocks, []))
            continue
        if achievement.family in seen_families:
            continue
        seen_families.add(achievement.family)

        # Tiers are defined in ascending-target order, and unlocking a tier
        # requires meeting an earlier tier's (lower) target too, so unlocked
        # tiers are always a prefix of this list — this order is relied on
        # below, not just cosmetic.
        tiers = tiers_by_family[achievement.family]
        unlocked_tiers = [t for t in tiers if t.key in unlocks]
        locked_tiers = [t for t in tiers if t.key not in unlocks]

        if unlocked_tiers:
            latest_completed = unlocked_tiers[-1]
            history = [
                {"key": t.key, "title": t.title, "badge": t.badge, "unlocked_at": unlocks[t.key]}
                for t in unlocked_tiers[:-1]
            ]
            result.append(_to_dict(latest_completed, stats, unlocks, history))

        if locked_tiers:
            result.append(_to_dict(locked_tiers[0], stats, unlocks, []))

    return result


def clear_achievements(store: Store, user_id: str) -> None:
    resp = store.achievements.query(KeyConditionExpression=Key("user_id").eq(user_id))
    for item in resp["Items"]:
        store.achievements.delete_item(Key={"user_id": user_id, "achievement_key": item["achievement_key"]})
