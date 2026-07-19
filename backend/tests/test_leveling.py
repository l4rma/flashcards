from app.leveling import LEVEL_UP_COIN_REWARD, LEVEL_XP_STEP, finalize_level, level_for_xp, xp_for_level
from app.models import Stats

TEST_USER_ID = "test-user"


def make_stats(**overrides) -> Stats:
    stats = Stats(user_id=TEST_USER_ID)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return stats


def test_xp_for_level_one_is_zero():
    assert xp_for_level(1) == 0


def test_xp_for_level_matches_step_curve():
    assert xp_for_level(2) == LEVEL_XP_STEP
    assert xp_for_level(3) == LEVEL_XP_STEP * 3
    assert xp_for_level(4) == LEVEL_XP_STEP * 6


def test_level_for_xp_stays_at_one_below_threshold():
    assert level_for_xp(0) == 1
    assert level_for_xp(LEVEL_XP_STEP - 1) == 1


def test_level_for_xp_advances_exactly_at_threshold():
    assert level_for_xp(LEVEL_XP_STEP) == 2
    assert level_for_xp(xp_for_level(3)) == 3


def test_level_for_xp_can_jump_multiple_levels():
    assert level_for_xp(xp_for_level(5)) == 5


def test_finalize_level_does_nothing_below_threshold(store):
    stats = make_stats(xp=LEVEL_XP_STEP - 1)
    levels_gained = finalize_level(store, TEST_USER_ID, stats)
    assert levels_gained == 0
    assert stats.level == 1
    assert stats.coins == 0


def test_finalize_level_awards_bonus_coins_on_level_up(store):
    stats = make_stats(xp=LEVEL_XP_STEP, coins=5, lifetime_coins_earned=5)
    levels_gained = finalize_level(store, TEST_USER_ID, stats)
    assert levels_gained == 1
    assert stats.level == 2
    assert stats.coins == 5 + LEVEL_UP_COIN_REWARD
    assert stats.lifetime_coins_earned == 5 + LEVEL_UP_COIN_REWARD


def test_finalize_level_sums_bonus_across_multiple_levels_gained_at_once(store):
    stats = make_stats(xp=xp_for_level(5))
    levels_gained = finalize_level(store, TEST_USER_ID, stats)
    assert levels_gained == 4
    assert stats.level == 5
    assert stats.coins == LEVEL_UP_COIN_REWARD * 4


def test_finalize_level_is_idempotent_once_level_matches_xp(store):
    stats = make_stats(xp=LEVEL_XP_STEP, level=2)
    levels_gained = finalize_level(store, TEST_USER_ID, stats)
    assert levels_gained == 0
    assert stats.coins == 0
