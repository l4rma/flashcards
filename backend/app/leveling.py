from app.database import Store
from app.models import Stats

# XP required to advance from level L to L+1 is LEVEL_XP_STEP * L — a
# simple linear-growth curve (100, 200, 300, ... more XP each level), not
# a fixed step, so leveling feels quick early and slows down later, same
# shape as the achievement tiers' own escalating targets. XP mirrors
# coin-earning 1:1 (every action that earns coins earns the same amount
# of XP) — see stats.py's record_training_activity/award_session_complete
# and the `xp` ADD folded into achievements.py/quests.py's existing
# reward transactions.
LEVEL_XP_STEP = 100
# Flat coin bonus per level gained, on top of whatever XP-earning action
# triggered the level-up — awarded by finalize_level below, separate from
# the achievement/quest tier reward scale (REWARD_BY_TIER_INDEX).
LEVEL_UP_COIN_REWARD = 20


def xp_for_level(level: int) -> int:
    """Cumulative XP required to *reach* `level` (level 1 = 0 XP)."""
    return LEVEL_XP_STEP * (level - 1) * level // 2


def level_for_xp(xp: int) -> int:
    level = 1
    while xp >= xp_for_level(level + 1):
        level += 1
    return level


def finalize_level(store: Store, user_id: str, stats: Stats) -> int:
    """Recomputes stats.level from stats.xp (already incremented earlier
    in this request by whichever actions ran — a Correct grade, a
    session-complete bonus, or an achievement/quest coin reward, all of
    which add to xp 1:1 with coins) and, if it went up, awards a flat coin
    bonus per level gained and persists both. Call once per request,
    *after* every other stats-mutating step, no matter how many separate
    XP sources fired in that request — level is purely derived from the
    final xp total, not tracked incrementally itself, so this is safe to
    call unconditionally (a no-op, returning 0, when xp didn't cross a
    new level's threshold).

    Deliberately not folded into achievements.py/quests.py's atomic
    unlock transactions — level-up isn't gated by a completion-row the
    way unlocks are (there's nothing to guard against double-awarding: a
    given xp total always derives the same level), so a second small
    plain update is simpler and safer than extending those transactions
    to also compute a level-up bonus before they're built."""
    new_level = level_for_xp(stats.xp)
    levels_gained = new_level - stats.level
    if levels_gained <= 0:
        return 0

    bonus = LEVEL_UP_COIN_REWARD * levels_gained
    store.stats.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET #level = :level ADD coins :bonus, lifetime_coins_earned :bonus",
        ExpressionAttributeNames={"#level": "level"},
        ExpressionAttributeValues={":level": new_level, ":bonus": bonus},
    )
    stats.level = new_level
    stats.coins += bonus
    stats.lifetime_coins_earned += bonus
    return levels_gained
