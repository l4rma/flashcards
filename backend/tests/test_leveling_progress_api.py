from app.leveling import LEVEL_XP_STEP


def test_xp_progress_starts_at_zero_of_step(client):
    stats = client.get("/stats").json()
    assert stats["xp_into_level"] == 0
    assert stats["xp_for_next_level"] == LEVEL_XP_STEP


def test_xp_progress_tracks_partial_progress_into_a_level(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    stats = client.get("/stats").json()
    assert stats["xp_into_level"] == stats["xp"]
    assert stats["xp_for_next_level"] == LEVEL_XP_STEP


def test_xp_progress_resets_relative_to_new_level_after_leveling_up(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()

    for _ in range(400):
        graded = client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).json()
        client.post(f"/cards/{card['id']}/grade", json={"grade": "wrong"})
        if graded["newly_leveled_up"]:
            break

    stats = client.get("/stats").json()
    assert stats["level"] > 1
    assert 0 <= stats["xp_into_level"] < stats["xp_for_next_level"]
