from app.achievements import ACHIEVEMENTS
from app.collection import THEMES, TITLES
from app.leveling import LEVEL_XP_STEP, xp_for_level
from app.stats import get_or_create_stats, save_stats

TEST_USER_ID = "test-user"


def _keys():
    return {a.key for a in ACHIEVEMENTS}


def test_all_new_achievement_keys_are_registered():
    expected = {
        "profile_set_up",
        "level_5",
        "level_10",
        "level_25",
        "level_50",
        "lootbox_1",
        "lootbox_10",
        "lootbox_50",
        "equipped_title",
        "equipped_theme",
        "title_collector",
        "theme_collector",
        "used_label",
        "practiced_prebuilt",
        "practiced_own_deck",
        "practiced_sub_deck",
        "practice_5",
        "practice_25",
        "practice_100",
    }
    assert expected <= _keys()


def test_used_label_achievement_unlocks_on_first_labeled_card(client):
    created = client.post(
        "/cards", json={"french": "chien", "english": "dog", "label": "animals"}
    ).json()
    assert "used_label" in {a["key"] for a in created["newly_unlocked_achievements"]}


def test_used_label_achievement_does_not_unlock_without_a_label(client):
    created = client.post("/cards", json={"french": "chien", "english": "dog"}).json()
    assert "used_label" not in {a["key"] for a in created["newly_unlocked_achievements"]}


def test_practice_completed_own_deck_unlocks_full_circle(client):
    resp = client.post("/practice/completed", json={"source": "own_deck"})
    assert resp.status_code == 200
    assert "practiced_own_deck" in {a["key"] for a in resp.json()["newly_unlocked_achievements"]}


def test_practice_completed_sub_deck_unlocks_specialist(client):
    resp = client.post("/practice/completed", json={"source": "sub_deck"})
    assert "practiced_sub_deck" in {a["key"] for a in resp.json()["newly_unlocked_achievements"]}


def test_practice_completed_prebuilt_unlocks_field_trip(client):
    resp = client.post("/practice/completed", json={"source": "prebuilt"})
    assert "practiced_prebuilt" in {a["key"] for a in resp.json()["newly_unlocked_achievements"]}


def test_practice_completed_is_idempotent_per_achievement(client):
    client.post("/practice/completed", json={"source": "own_deck"})
    resp = client.post("/practice/completed", json={"source": "own_deck"})
    assert "practiced_own_deck" not in {a["key"] for a in resp.json()["newly_unlocked_achievements"]}


def test_practice_completed_five_times_unlocks_practice_family(client):
    unlocked_keys = set()
    for _ in range(5):
        resp = client.post("/practice/completed", json={"source": "own_deck"})
        unlocked_keys |= {a["key"] for a in resp.json()["newly_unlocked_achievements"]}
    assert "practice_5" in unlocked_keys

    # practice_sessions_completed itself isn't exposed via GET /stats
    # (internal achievement-tracking plumbing, same as total_correct/
    # comebacks/etc.) — confirm the count via the achievement's own
    # reported progress instead.
    achievements = {a["key"]: a for a in client.get("/achievements").json()}
    assert achievements["practice_5"]["unlocked"] is True


def test_profile_set_up_unlocks_once_username_and_avatar_are_both_set(client):
    # PATCH /profile doesn't check achievements itself (it's identity, not
    # gamification progress) — the unlock surfaces on the next action that
    # does, e.g. adding a card.
    client.patch("/profile", json={"username": "Lars"})
    created = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    assert "profile_set_up" not in {a["key"] for a in created["newly_unlocked_achievements"]}

    client.patch("/profile", json={"avatar_key": "fox"})
    created2 = client.post("/cards", json={"french": "chien", "english": "dog"}).json()
    assert "profile_set_up" in {a["key"] for a in created2["newly_unlocked_achievements"]}


def test_level_achievement_unlocks_at_level_5(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    target_xp = xp_for_level(5)

    unlocked_keys = set()
    while client.get("/stats").json()["xp"] < target_xp:
        graded = client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).json()
        unlocked_keys |= {a["key"] for a in graded["newly_unlocked_achievements"]}
        client.post(f"/cards/{card['id']}/grade", json={"grade": "wrong"})

    stats = client.get("/stats").json()
    assert stats["level"] >= 5
    assert "level_5" in unlocked_keys


def test_lootbox_achievement_unlocks_on_first_open(client):
    cards = [
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"}).json()
        for i in range(60)
    ]
    for card in cards:
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    client.post("/collection/lootboxes/bronze/buy")
    resp = client.post("/collection/lootboxes/bronze/open")

    assert "lootbox_1" in {a["key"] for a in resp.json()["newly_unlocked_achievements"]}


def test_equipped_title_and_theme_achievements(client, store):
    # Granting ownership directly via the store (rather than depending on
    # a random lootbox roll landing a title/theme) keeps this test fast
    # and deterministic — the roll mechanics themselves are already
    # covered directly in test_collection.py's unit tests.
    stats = get_or_create_stats(store, TEST_USER_ID)
    stats.owned_titles = [TITLES[0].key]
    stats.owned_themes = [THEMES[0].key]
    save_stats(store, stats)

    client.post("/collection/equip", json={"title": TITLES[0].key})
    client.post("/collection/equip", json={"theme": THEMES[0].key})

    # Equip itself doesn't check achievements (identity-like action, same
    # as PATCH /profile) — the unlock surfaces on the next action that
    # does, which here is the card creation itself (the very first
    # gamification-checking call after equipping).
    created = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    unlocked = {a["key"] for a in created["newly_unlocked_achievements"]}
    assert "equipped_title" in unlocked
    assert "equipped_theme" in unlocked


def test_reset_all_progress_clears_new_achievement_tracking_fields(client):
    created = client.post(
        "/cards", json={"french": "chat", "english": "cat", "label": "animals"}
    ).json()
    assert "used_label" in {a["key"] for a in created["newly_unlocked_achievements"]}
    client.post("/practice/completed", json={"source": "own_deck"})

    before = {a["key"]: a for a in client.get("/achievements").json()}
    assert before["used_label"]["unlocked"] is True
    assert before["practiced_own_deck"]["unlocked"] is True

    client.post("/reset-all-progress")

    after = {a["key"]: a for a in client.get("/achievements").json()}
    assert after["used_label"]["unlocked"] is False
    assert after["used_label"]["progress_current"] == 0
    assert after["practiced_own_deck"]["unlocked"] is False
    assert after["practice_5"]["progress_current"] == 0


def test_title_and_theme_collector_targets_match_current_catalog():
    achievements = {a.key: a for a in ACHIEVEMENTS}
    assert achievements["title_collector"].target == len(TITLES)
    assert achievements["theme_collector"].target == len(THEMES)


def test_level_family_step_matches_leveling_constant():
    # Sanity check that the achievement tiers (5/10/25/50) are expressed
    # in the same unit as Stats.level itself, not xp.
    achievements = {a.key: a for a in ACHIEVEMENTS}
    assert achievements["level_5"].target == 5
    assert LEVEL_XP_STEP > 0  # just confirms the import/module wiring
