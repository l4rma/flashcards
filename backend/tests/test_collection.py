import pytest
from fastapi import HTTPException

from app.collection import (
    LOOTBOX_TIERS,
    THEMES,
    TITLES,
    buy_lootbox,
    describe_collection,
    equip_theme,
    equip_title,
    open_lootbox,
    roll_lootbox_reward,
)
from app.models import Stats

TEST_USER_ID = "test-user"


def make_stats(**overrides) -> Stats:
    stats = Stats(user_id=TEST_USER_ID)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return stats


def test_describe_collection_lists_everything_unowned_by_default():
    stats = make_stats()
    collection = describe_collection(stats)

    assert len(collection["titles"]) == len(TITLES)
    assert all(not t["owned"] and not t["equipped"] for t in collection["titles"])
    assert len(collection["themes"]) == len(THEMES)
    assert all(not t["owned"] and not t["equipped"] for t in collection["themes"])
    assert len(collection["lootboxes"]) == len(LOOTBOX_TIERS)
    assert all(box["count"] == 0 for box in collection["lootboxes"])


def test_roll_lootbox_reward_always_grants_something():
    stats = make_stats()
    for _ in range(50):
        reward = roll_lootbox_reward(stats, "bronze")
        assert reward["kind"] in {"coins", "xp", "title", "theme"}


def test_roll_lootbox_reward_never_duplicates_a_title():
    stats = make_stats(owned_titles=[t.key for t in TITLES[:-1]])
    for _ in range(50):
        reward = roll_lootbox_reward(stats, "gold")
        if reward["kind"] == "title":
            assert reward["key"] == TITLES[-1].key
    assert stats.owned_titles.count(TITLES[-1].key) <= 1


def test_roll_lootbox_reward_falls_back_once_all_titles_and_themes_owned():
    stats = make_stats(
        owned_titles=[t.key for t in TITLES],
        owned_themes=[t.key for t in THEMES],
    )
    for _ in range(50):
        reward = roll_lootbox_reward(stats, "gold")
        assert reward["kind"] in {"coins", "xp"}


def test_buy_lootbox_deducts_coins_and_adds_inventory():
    stats = make_stats(coins=1000)
    tier = LOOTBOX_TIERS[0]

    buy_lootbox(stats, tier.key)

    assert stats.coins == 1000 - tier.coin_cost
    assert stats.lootbox_bronze == 1


def test_buy_lootbox_rejects_insufficient_coins():
    stats = make_stats(coins=0)
    with pytest.raises(HTTPException) as exc_info:
        buy_lootbox(stats, "bronze")
    assert exc_info.value.status_code == 400


def test_open_lootbox_requires_inventory():
    stats = make_stats(lootbox_bronze=0)
    with pytest.raises(HTTPException) as exc_info:
        open_lootbox(stats, "bronze")
    assert exc_info.value.status_code == 400


def test_open_lootbox_consumes_one_from_inventory():
    stats = make_stats(lootbox_bronze=2)
    open_lootbox(stats, "bronze")
    assert stats.lootbox_bronze == 1


def test_equip_title_requires_ownership():
    stats = make_stats()
    with pytest.raises(HTTPException):
        equip_title(stats, TITLES[0].key)


def test_equip_title_succeeds_once_owned():
    stats = make_stats(owned_titles=[TITLES[0].key])
    equip_title(stats, TITLES[0].key)
    assert stats.equipped_title == TITLES[0].key


def test_equip_title_none_unequips():
    stats = make_stats(owned_titles=[TITLES[0].key], equipped_title=TITLES[0].key)
    equip_title(stats, None)
    assert stats.equipped_title is None


def test_equip_theme_requires_ownership():
    stats = make_stats()
    with pytest.raises(HTTPException):
        equip_theme(stats, THEMES[0].key)


def test_equip_theme_succeeds_once_owned():
    stats = make_stats(owned_themes=[THEMES[0].key])
    equip_theme(stats, THEMES[0].key)
    assert stats.equipped_theme == THEMES[0].key
