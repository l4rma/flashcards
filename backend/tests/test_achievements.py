from boto3.dynamodb.conditions import Key

from app.achievements import (
    ACHIEVEMENTS,
    REWARD_BY_TIER_INDEX,
    check_and_unlock_achievements,
    clear_achievements,
    list_achievements,
)
from app.models import Stats
from app.stats import get_or_create_stats

TEST_USER_ID = "test-user"


def make_stats(**overrides) -> Stats:
    stats = Stats(user_id=TEST_USER_ID)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return stats


def _unlock_count(store, achievement_key: str) -> int:
    resp = store.achievements.query(KeyConditionExpression=Key("user_id").eq(TEST_USER_ID))
    return sum(1 for item in resp["Items"] if item["achievement_key"] == achievement_key)


def _expected_collapsed_count() -> int:
    families = {a.family for a in ACHIEVEMENTS if a.family}
    standalone = [a for a in ACHIEVEMENTS if a.family is None]
    return len(families) + len(standalone)


def test_all_achievements_locked_with_no_activity(store):
    stats = make_stats()

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert unlocked == []
    achievements = list_achievements(store, TEST_USER_ID, stats)
    # One entry per family (collapsed to its first tier) + standalones —
    # not one entry per underlying AchievementDef.
    assert len(achievements) == _expected_collapsed_count()
    assert all(not a["unlocked"] for a in achievements)
    assert all(a["unlocked_at"] is None for a in achievements)
    assert all(a["progress_current"] == 0 for a in achievements)
    assert all(a["history"] == [] for a in achievements)


def test_progress_reflects_live_values_and_caps_at_target(store):
    stats = make_stats(total_correct=4)

    achievements = {a["key"]: a for a in list_achievements(store, TEST_USER_ID, stats)}

    assert achievements["correct_10"]["progress_current"] == 4
    assert achievements["correct_10"]["progress_target"] == 10
    assert achievements["first_review"]["progress_current"] == 1  # capped at target
    assert achievements["first_review"]["progress_target"] == 1


def test_first_review_unlocks_on_first_grade(store):
    stats = make_stats(total_correct=1)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "first_review" in unlocked
    assert "correct_10" not in unlocked


def test_correct_10_unlocks_at_threshold(store):
    stats = make_stats(total_correct=10)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "correct_10" in unlocked
    assert "correct_100" not in unlocked


def test_streak_achievement_unlocks_from_longest_streak(store):
    stats = make_stats(longest_streak=7)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "streak_7" in unlocked
    assert "streak_30" not in unlocked


def test_coin_achievement_uses_lifetime_not_spendable_coins(store):
    stats = make_stats(coins=0, lifetime_coins_earned=100)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "coins_10" in unlocked
    assert "coins_100" in unlocked
    assert "coins_500" not in unlocked


def test_deck_achievement_ladder(store):
    stats = make_stats(total_cards=30)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "deck_1" in unlocked
    assert "deck_10" in unlocked
    assert "deck_30" in unlocked
    assert "deck_50" not in unlocked
    assert "deck_100" not in unlocked
    assert "deck_250" not in unlocked
    assert "deck_500" not in unlocked


def test_session_complete_achievement(store):
    stats = make_stats(sessions_completed=1)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "session_complete_1" in unlocked


def test_session_ladder(store):
    stats = make_stats(sessions_completed=25)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "session_complete_1" in unlocked
    assert "session_5" in unlocked
    assert "session_10" in unlocked
    assert "session_25" in unlocked
    assert "session_50" not in unlocked
    assert "session_100" not in unlocked
    assert "session_250" not in unlocked
    assert "session_500" not in unlocked


def test_correct_streak_ladder(store):
    stats = make_stats(longest_correct_streak=10)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "correct_streak_3" in unlocked
    assert "correct_streak_5" in unlocked
    assert "correct_streak_10" in unlocked
    assert "correct_streak_25" not in unlocked
    assert "correct_streak_50" not in unlocked
    assert "correct_streak_100" not in unlocked


def test_first_wrong_achievement(store):
    stats = make_stats(total_wrong=1)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "first_wrong" in unlocked


def test_checking_twice_does_not_duplicate_or_error(store):
    stats = make_stats(longest_streak=7)

    first = check_and_unlock_achievements(store, TEST_USER_ID, stats)
    second = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "streak_7" in first
    # streak_7's own coin reward can legitimately push a coin-threshold
    # achievement (e.g. coins_10) over its target by the second call — that's
    # a real cascade across separate calls, not a re-report. What matters
    # here is that streak_7 itself is never reported/inserted twice.
    assert "streak_7" not in second
    assert _unlock_count(store, "streak_7") == 1


def test_achievement_stays_unlocked_after_condition_becomes_false(store):
    stats = make_stats(longest_streak=7)
    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    # Simulate an admin streak reset — the underlying stat drops back to 0.
    stats.longest_streak = 0

    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    # streak_7 stays unlocked and still shows as its own (colored) tile;
    # streak_30 shows alongside it as the next (shaded) tile to work on.
    achievements = {a["key"]: a for a in list_achievements(store, TEST_USER_ID, stats)}
    assert "streak_7" in achievements
    assert achievements["streak_7"]["unlocked"] is True
    assert "streak_30" in achievements
    assert achievements["streak_30"]["unlocked"] is False


def test_partial_family_shows_completed_tile_plus_next_tile(store):
    stats = make_stats(total_cards=10)
    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    achievements = {a["key"]: a for a in list_achievements(store, TEST_USER_ID, stats)}

    # deck_1 and deck_10 are both unlocked (10 cards >= both thresholds).
    # The colored tile is the highest completed tier (deck_10), carrying
    # deck_1 in its history; the shaded tile is the next one up (deck_30).
    # deck_1 does not appear as its own top-level entry.
    assert "deck_1" not in achievements
    assert "deck_10" in achievements
    assert achievements["deck_10"]["unlocked"] is True
    assert {h["key"] for h in achievements["deck_10"]["history"]} == {"deck_1"}

    assert "deck_30" in achievements
    assert achievements["deck_30"]["unlocked"] is False
    assert achievements["deck_30"]["history"] == []


def test_fully_completed_family_shows_last_tier_with_full_history(store):
    stats = make_stats(total_cards=500)
    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    achievements = {a["key"]: a for a in list_achievements(store, TEST_USER_ID, stats)}

    assert "deck_500" in achievements
    assert achievements["deck_500"]["unlocked"] is True
    history_keys = {h["key"] for h in achievements["deck_500"]["history"]}
    assert history_keys == {"deck_1", "deck_10", "deck_30", "deck_50", "deck_100", "deck_250"}


def test_clear_achievements_removes_all_unlocks(store):
    stats = make_stats(longest_streak=30)
    check_and_unlock_achievements(store, TEST_USER_ID, stats)
    assert _unlock_count(store, "streak_7") == 1

    clear_achievements(store, TEST_USER_ID)

    assert _unlock_count(store, "streak_7") == 0
    assert all(not a["unlocked"] for a in list_achievements(store, TEST_USER_ID, stats))


def test_streak_ladder_extended_tiers(store):
    stats = make_stats(longest_streak=100)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "streak_60" in unlocked
    assert "streak_100" in unlocked
    assert "streak_365" not in unlocked


def test_session_ladder_extended_tiers(store):
    stats = make_stats(sessions_completed=250)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "session_250" in unlocked
    assert "session_500" not in unlocked


def test_flawless_session_achievement(store):
    stats = make_stats(flawless_sessions_completed=1)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "flawless_session" in unlocked


def test_comeback_kid_achievement(store):
    stats = make_stats(comebacks=1)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "comeback_kid" in unlocked


def test_early_bird_and_night_owl_achievements(store):
    stats = make_stats(trained_before_7am=True)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "early_bird" in unlocked
    assert "night_owl" not in unlocked


def test_mastery_ladder(store):
    stats = make_stats(cards_mastered=7)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "mastery_1" in unlocked
    assert "mastery_5" in unlocked
    assert "mastery_10" not in unlocked
    assert "mastery_25" not in unlocked
    assert "mastery_50" not in unlocked


def test_marathon_ladder(store):
    stats = make_stats(largest_session_completed=60)

    unlocked = check_and_unlock_achievements(store, TEST_USER_ID, stats)

    assert "marathon_25" in unlocked
    assert "marathon_50" in unlocked
    assert "marathon_100" not in unlocked
    assert "marathon_200" not in unlocked


def test_unlocking_an_achievement_awards_its_coin_reward(store):
    stats = make_stats(longest_streak=7)  # unlocks streak_7 only

    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    streak_7 = next(a for a in ACHIEVEMENTS if a.key == "streak_7")
    assert stats.coins == streak_7.coin_reward
    assert stats.lifetime_coins_earned == streak_7.coin_reward
    # Also verify the reward was actually persisted to DynamoDB via the
    # transaction, not just mutated on the in-memory object.
    persisted = get_or_create_stats(store, TEST_USER_ID)
    assert persisted.coins == streak_7.coin_reward


def test_multiple_simultaneous_unlocks_sum_their_rewards(store):
    # 30 cards crosses deck_1, deck_10, and deck_30 all at once.
    stats = make_stats(total_cards=30)

    check_and_unlock_achievements(store, TEST_USER_ID, stats)

    deck_tiers = {a.key: a for a in ACHIEVEMENTS if a.family == "deck"}
    expected = deck_tiers["deck_1"].coin_reward + deck_tiers["deck_10"].coin_reward + deck_tiers["deck_30"].coin_reward
    assert stats.coins == expected


def test_tiered_reward_increases_with_tier_position():
    deck_tiers = [a for a in ACHIEVEMENTS if a.family == "deck"]
    rewards = [a.coin_reward for a in deck_tiers]

    assert rewards == REWARD_BY_TIER_INDEX[: len(deck_tiers)]
    assert rewards == sorted(rewards)  # strictly non-decreasing, harder = more (or equal)


def test_standalone_achievements_keep_their_explicit_reward():
    by_key = {a.key: a for a in ACHIEVEMENTS if a.family is None}

    assert by_key["first_review"].coin_reward == 10
    assert by_key["flawless_session"].coin_reward == 20
    assert by_key["comeback_kid"].coin_reward == 15
