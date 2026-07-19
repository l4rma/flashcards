from app.profile import AVATAR_KEYS, USERNAME_MAX_LENGTH


def test_stats_defaults_to_no_username_or_avatar(client):
    stats = client.get("/stats").json()
    assert stats["username"] is None
    assert stats["avatar_key"] is None


def test_update_profile_sets_username_and_avatar(client):
    resp = client.patch("/profile", json={"username": "Lars", "avatar_key": AVATAR_KEYS[0]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "Lars"
    assert body["avatar_key"] == AVATAR_KEYS[0]

    stats = client.get("/stats").json()
    assert stats["username"] == "Lars"
    assert stats["avatar_key"] == AVATAR_KEYS[0]


def test_update_profile_field_omitted_leaves_it_unchanged(client):
    client.patch("/profile", json={"username": "Lars", "avatar_key": AVATAR_KEYS[0]})

    resp = client.patch("/profile", json={"avatar_key": AVATAR_KEYS[1]})

    assert resp.json()["username"] == "Lars"
    assert resp.json()["avatar_key"] == AVATAR_KEYS[1]


def test_update_profile_null_clears_the_field(client):
    client.patch("/profile", json={"username": "Lars"})

    resp = client.patch("/profile", json={"username": None})

    assert resp.json()["username"] is None


def test_update_profile_trims_whitespace(client):
    resp = client.patch("/profile", json={"username": "  Lars  "})
    assert resp.json()["username"] == "Lars"


def test_update_profile_blank_username_is_treated_as_clearing_it(client):
    resp = client.patch("/profile", json={"username": "   "})
    assert resp.status_code == 200
    assert resp.json()["username"] is None


def test_update_profile_rejects_too_long_username(client):
    resp = client.patch("/profile", json={"username": "x" * (USERNAME_MAX_LENGTH + 1)})
    assert resp.status_code == 422


def test_update_profile_rejects_unknown_avatar_key(client):
    resp = client.patch("/profile", json={"avatar_key": "not-a-real-avatar"})
    assert resp.status_code == 422


def test_reset_all_progress_does_not_clear_profile_identity(client):
    client.patch("/profile", json={"username": "Lars", "avatar_key": AVATAR_KEYS[0]})

    client.post("/reset-all-progress")

    stats = client.get("/stats").json()
    assert stats["username"] == "Lars"
    assert stats["avatar_key"] == AVATAR_KEYS[0]


def test_profile_is_isolated_between_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    user_a.patch("/profile", json={"username": "Alice"})

    assert user_a.get("/stats").json()["username"] == "Alice"
    assert user_b.get("/stats").json()["username"] is None
