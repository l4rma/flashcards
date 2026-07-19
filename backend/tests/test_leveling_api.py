from app.leveling import LEVEL_XP_STEP, level_for_xp


def test_stats_reports_starting_xp_and_level(client):
    stats = client.get("/stats").json()
    assert stats["xp"] == 0
    assert stats["level"] == 1


def test_grading_correct_earns_xp(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    xp_before = client.get("/stats").json()["xp"]

    graded = client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).json()

    xp_after = client.get("/stats").json()["xp"]
    assert xp_after > xp_before
    # Not yet enough XP (routine + whatever achievements this triggers,
    # both far below LEVEL_XP_STEP) to cross a level on a single grade.
    assert graded["newly_leveled_up"] == []


def test_reset_all_progress_resets_xp_and_level(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    client.post("/reset-all-progress")

    stats = client.get("/stats").json()
    assert stats["xp"] == 0
    assert stats["level"] == 1


def test_session_complete_bonus_earns_xp(client):
    xp_before = client.get("/stats").json()["xp"]

    resp = client.post("/stats/session-complete").json()

    assert resp["xp"] > xp_before


def test_achievement_coin_reward_also_earns_xp(client):
    # Adding the very first card unlocks "deck_1" (10 coins) — that
    # reward should land in xp too, on top of whatever routine amount (0
    # for just adding a card — xp only accrues from grading/session-
    # complete, not from adding cards directly).
    xp_before = client.get("/stats").json()["xp"]

    created = client.post("/cards", json={"french": "chat", "english": "cat"}).json()

    assert "deck_1" in {a["key"] for a in created["newly_unlocked_achievements"]}
    xp_after = client.get("/stats").json()["xp"]
    assert xp_after == xp_before + 10


def test_leveling_up_reports_a_celebration_notice_and_stays_consistent(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()

    saw_level_up = False
    for _ in range(400):  # comfortably enough routine + achievement XP to cross a level
        graded = client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).json()
        if graded["newly_leveled_up"]:
            saw_level_up = True
        # Grading Wrong resets interval_days back to 0 — without this, the
        # same card graded Correct hundreds of times in a row doubles
        # interval_days each time and overflows datetime.date's range.
        client.post(f"/cards/{card['id']}/grade", json={"grade": "wrong"})

    assert saw_level_up

    stats = client.get("/stats").json()
    assert stats["level"] > 1
    # Whatever the exact XP total ended up being (routine + achievement
    # cascade), the reported level must always match what the formula
    # derives from it — that consistency is the actual thing being tested
    # here, not a specific hardcoded level number.
    assert stats["level"] == level_for_xp(stats["xp"])
    assert stats["xp"] >= LEVEL_XP_STEP
