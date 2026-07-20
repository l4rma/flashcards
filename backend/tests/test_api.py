from datetime import date, timedelta

from app.quests import ADD_CARDS_TARGET, TRAIN_TARGET


def test_create_and_list_card(client):
    resp = client.post("/cards", json={"french": "chien", "english": "dog"})
    assert resp.status_code == 201
    card = resp.json()
    assert card["french"] == "chien"
    assert card["interval_days"] == 0

    resp = client.get("/cards")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_new_card_is_due_immediately(client):
    client.post("/cards", json={"french": "chat", "english": "cat"})
    resp = client.get("/cards/due")
    assert len(resp.json()) == 1


def test_create_card_reports_newly_unlocked_achievements(client):
    # First card ever added crosses both "First Card" (deck_1) and "First
    # Steps" is grade-only, so only deck_1 fires here.
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    keys = {a["key"] for a in card["newly_unlocked_achievements"]}
    assert "deck_1" in keys
    notice = next(a for a in card["newly_unlocked_achievements"] if a["key"] == "deck_1")
    assert notice["title"]
    assert notice["badge"]
    assert notice["coin_reward"] > 0


def test_create_card_reports_no_unlocks_once_already_unlocked(client):
    client.post("/cards", json={"french": "chat", "english": "cat"})
    second = client.post("/cards", json={"french": "chien", "english": "dog"}).json()
    assert "deck_1" not in {a["key"] for a in second["newly_unlocked_achievements"]}


def test_grade_card_reports_newly_unlocked_achievements(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    graded = client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).json()
    # Grading the very first card ever unlocks "First Steps" (grade-based).
    assert "first_review" in {a["key"] for a in graded["newly_unlocked_achievements"]}


def test_create_card_reports_newly_completed_quests(client):
    for i in range(4):
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"})
    fifth = client.post("/cards", json={"french": "mot5", "english": "word5"}).json()
    keys = {q["key"] for q in fifth["newly_completed_quests"]}
    assert "daily_add_cards" in keys
    notice = next(q for q in fifth["newly_completed_quests"] if q["key"] == "daily_add_cards")
    assert notice["title"]
    assert notice["badge"]
    assert notice["coin_reward"] > 0


def test_grade_card_reports_newly_completed_quests(client):
    cards = [
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"}).json()
        for i in range(TRAIN_TARGET)
    ]
    for card in cards[:-1]:
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})
    graded = client.post(f"/cards/{cards[-1]['id']}/grade", json={"grade": "correct"}).json()
    assert "daily_train" in {q["key"] for q in graded["newly_completed_quests"]}


def test_completing_every_daily_quest_awards_a_bonus_lootbox(client):
    cards = [
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"}).json()
        for i in range(max(ADD_CARDS_TARGET, TRAIN_TARGET))
    ]
    # The add-cards quest completes as a side effect of creating the cards
    # above; grading them all Correct completes the train quest last, so
    # the bonus notice should land on the final grade call.
    for card in cards[:-1]:
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})
    graded = client.post(f"/cards/{cards[-1]['id']}/grade", json={"grade": "correct"}).json()

    bonus = graded["newly_awarded_daily_bonus"]
    assert len(bonus) == 1
    assert bonus[0]["lootbox_tier"] == "silver"
    assert bonus[0]["title"]
    assert bonus[0]["badge"]

    collection = client.get("/collection").json()
    silver = next(box for box in collection["lootboxes"] if box["tier"] == "silver")
    assert silver["count"] == 1


def test_daily_bonus_is_not_reported_again_the_same_day(client):
    cards = [
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"}).json()
        for i in range(max(ADD_CARDS_TARGET, TRAIN_TARGET))
    ]
    for card in cards:
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    extra_card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    graded = client.post(f"/cards/{extra_card['id']}/grade", json={"grade": "correct"}).json()

    assert graded["newly_awarded_daily_bonus"] == []


def test_grade_correct_moves_card_out_of_due(client):
    create = client.post("/cards", json={"french": "chat", "english": "cat"})
    card_id = create.json()["id"]

    grade = client.post(f"/cards/{card_id}/grade", json={"grade": "correct"})
    assert grade.status_code == 200
    body = grade.json()
    assert body["interval_days"] == 2
    assert body["due_date"] == str(date.today() + timedelta(days=2))

    due = client.get("/cards/due")
    assert due.json() == []


def test_grade_wrong_keeps_card_due(client):
    create = client.post("/cards", json={"french": "chat", "english": "cat"})
    card_id = create.json()["id"]

    grade = client.post(f"/cards/{card_id}/grade", json={"grade": "wrong"})
    assert grade.status_code == 200
    assert grade.json()["interval_days"] == 0

    due = client.get("/cards/due")
    assert len(due.json()) == 1


def test_update_and_delete_card(client):
    create = client.post("/cards", json={"french": "chat", "english": "cat"})
    card_id = create.json()["id"]

    patch = client.patch(f"/cards/{card_id}", json={"english": "kitty"})
    assert patch.json()["english"] == "kitty"

    delete = client.delete(f"/cards/{card_id}")
    assert delete.status_code == 204
    assert client.get("/cards").json() == []


def test_reset_progress_makes_all_cards_due_again(client):
    ids = []
    for french, english in [("chat", "cat"), ("chien", "dog")]:
        card = client.post("/cards", json={"french": french, "english": english}).json()
        ids.append(card["id"])
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    assert client.get("/cards/due").json() == []  # both scheduled 2 days out

    reset = client.post("/reset-all-progress")
    assert reset.status_code == 204

    due = client.get("/cards/due").json()
    assert {c["id"] for c in due} == set(ids)
    assert all(
        c["interval_days"] == 0
        and c["last_reviewed_at"] is None
        and c["times_correct"] == 0
        and c["times_wrong"] == 0
        for c in due
    )


def test_reset_progress_also_clears_achievements(client):
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    achievements = client.get("/achievements").json()
    assert any(a["unlocked"] for a in achievements)  # first_review, deck_1 etc.

    client.post("/reset-all-progress")

    achievements = client.get("/achievements").json()
    assert all(not a["unlocked"] for a in achievements)


def test_quests_endpoint_reflects_activity(client):
    quests = {q["key"]: q for q in client.get("/quests").json()}
    assert quests["daily_add_cards"]["progress_current"] == 0
    assert quests["daily_train"]["completed"] is False

    for i in range(5):
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"})

    quests = {q["key"]: q for q in client.get("/quests").json()}
    assert quests["daily_add_cards"]["progress_current"] == 5
    assert quests["daily_add_cards"]["completed"] is True


def test_grading_correct_progresses_the_train_quest(client):
    # Target is fixed at TRAIN_TARGET regardless of how few cards are due
    # — same countdown as the Train page's own progress bar.
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    quests = {q["key"]: q for q in client.get("/quests").json()}
    assert quests["daily_train"]["progress_target"] == TRAIN_TARGET
    assert quests["daily_train"]["progress_current"] == 1
    assert quests["daily_train"]["completed"] is False


def test_reset_progress_also_clears_quest_completions(client):
    cards = [
        client.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"}).json()
        for i in range(TRAIN_TARGET)
    ]
    for card in cards:
        client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})
    assert any(q["completed"] for q in client.get("/quests").json())

    client.post("/reset-all-progress")

    quests = {q["key"]: q for q in client.get("/quests").json()}
    assert all(not q["completed"] for q in quests.values())
    # daily_train's progress is Stats-backed, so it genuinely goes back to 0
    # (unlike daily_add_cards, which is a live card count — cards aren't
    # deleted by this action, mirroring the deck achievements' same caveat).
    assert quests["daily_train"]["progress_current"] == 0


def test_reset_progress_does_not_leave_achievements_ready_to_instantly_reunlock(client):
    # Regression test: originally "reset all progress" left lifetime
    # achievement-tracking fields (lifetime_coins_earned, etc.) untouched,
    # so an achievement could re-unlock from a single new card/grade right
    # after a reset, with its progress bar showing a number far past 0 —
    # exactly the bug reported in practice.
    card = client.post("/cards", json={"french": "chat", "english": "cat"}).json()
    client.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    client.post("/reset-all-progress")

    achievements = {a["key"]: a for a in client.get("/achievements").json()}
    coins_tier = achievements.get("coins_10") or achievements.get("coins_100") or achievements.get("coins_500")
    assert coins_tier["progress_current"] == 0
    assert coins_tier["unlocked"] is False


# --- Cross-user isolation (multi-tenancy) ---------------------------------


def test_cards_are_isolated_between_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    user_a.post("/cards", json={"french": "chat", "english": "cat"})

    assert len(user_a.get("/cards").json()) == 1
    assert user_b.get("/cards").json() == []


def test_user_cannot_access_another_users_card_by_id(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    card = user_a.post("/cards", json={"french": "chat", "english": "cat"}).json()

    assert user_b.patch(f"/cards/{card['id']}", json={"english": "kitty"}).status_code == 404
    assert user_b.delete(f"/cards/{card['id']}").status_code == 404
    assert user_b.post(f"/cards/{card['id']}/grade", json={"grade": "correct"}).status_code == 404

    # user A's card is untouched by user B's attempts
    assert user_a.get("/cards").json()[0]["english"] == "cat"


def test_deleting_all_cards_does_not_affect_other_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    user_a.post("/cards", json={"french": "chat", "english": "cat"})
    user_b.post("/cards", json={"french": "chien", "english": "dog"})

    user_a.delete("/cards")

    assert user_a.get("/cards").json() == []
    assert len(user_b.get("/cards").json()) == 1


def test_stats_are_isolated_between_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    card = user_a.post("/cards", json={"french": "chat", "english": "cat"}).json()
    user_a.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    assert user_a.get("/stats").json()["coins"] > 0
    assert user_b.get("/stats").json()["coins"] == 0


def test_achievements_are_isolated_between_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    card = user_a.post("/cards", json={"french": "chat", "english": "cat"}).json()
    user_a.post(f"/cards/{card['id']}/grade", json={"grade": "correct"})

    a_achievements = {a["key"]: a for a in user_a.get("/achievements").json()}
    b_achievements = {a["key"]: a for a in user_b.get("/achievements").json()}
    assert a_achievements["first_review"]["unlocked"] is True
    assert b_achievements["first_review"]["unlocked"] is False


def test_quests_are_isolated_between_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    for i in range(5):
        user_a.post("/cards", json={"french": f"mot{i}", "english": f"word{i}"})

    a_quests = {q["key"]: q for q in user_a.get("/quests").json()}
    b_quests = {q["key"]: q for q in user_b.get("/quests").json()}
    assert a_quests["daily_add_cards"]["completed"] is True
    assert b_quests["daily_add_cards"]["completed"] is False


def test_reset_all_progress_does_not_affect_other_users(make_client):
    user_a = make_client("user-a")
    user_b = make_client("user-b")

    card_a = user_a.post("/cards", json={"french": "chat", "english": "cat"}).json()
    user_a.post(f"/cards/{card_a['id']}/grade", json={"grade": "correct"})

    card_b = user_b.post("/cards", json={"french": "chien", "english": "dog"}).json()
    user_b.post(f"/cards/{card_b['id']}/grade", json={"grade": "correct"})

    user_a.post("/reset-all-progress")

    assert user_a.get("/stats").json()["coins"] == 0
    b_cards = user_b.get("/cards").json()
    assert b_cards[0]["times_correct"] == 1
    assert user_b.get("/stats").json()["coins"] > 0
    b_achievements = {a["key"]: a for a in user_b.get("/achievements").json()}
    assert b_achievements["first_review"]["unlocked"] is True
