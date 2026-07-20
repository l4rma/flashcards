def test_create_card_with_label(client):
    resp = client.post("/cards", json={"french": "chien", "english": "dog", "label": "animals"})
    assert resp.status_code == 201
    assert resp.json()["label"] == "animals"


def test_create_card_without_label_defaults_to_none(client):
    resp = client.post("/cards", json={"french": "chien", "english": "dog"})
    assert resp.json()["label"] is None


def test_update_card_sets_label(client):
    card = client.post("/cards", json={"french": "chien", "english": "dog"}).json()

    resp = client.patch(f"/cards/{card['id']}", json={"label": "animals"})

    assert resp.json()["label"] == "animals"


def test_update_card_omitting_label_leaves_it_unchanged(client):
    card = client.post("/cards", json={"french": "chien", "english": "dog", "label": "animals"}).json()

    resp = client.patch(f"/cards/{card['id']}", json={"french": "le chien"})

    assert resp.json()["label"] == "animals"
    assert resp.json()["french"] == "le chien"


def test_update_card_null_label_clears_it(client):
    card = client.post("/cards", json={"french": "chien", "english": "dog", "label": "animals"}).json()

    resp = client.patch(f"/cards/{card['id']}", json={"label": None})

    assert resp.json()["label"] is None


def test_update_card_blank_label_also_clears_it(client):
    # The Deck page's edit form has no separate "clear" affordance, just
    # an empty text input — an empty string has to mean the same thing
    # null does.
    card = client.post("/cards", json={"french": "chien", "english": "dog", "label": "animals"}).json()

    resp = client.patch(f"/cards/{card['id']}", json={"label": "   "})

    assert resp.json()["label"] is None


def test_create_card_blank_label_is_treated_as_no_label(client):
    resp = client.post("/cards", json={"french": "chien", "english": "dog", "label": "  "})
    assert resp.json()["label"] is None


def test_label_is_case_normalized_on_create(client):
    resp = client.post("/cards", json={"french": "chien", "english": "dog", "label": "Animals"})
    assert resp.json()["label"] == "animals"


def test_label_is_case_normalized_on_update(client):
    card = client.post("/cards", json={"french": "chien", "english": "dog"}).json()
    resp = client.patch(f"/cards/{card['id']}", json={"label": "ANIMALS"})
    assert resp.json()["label"] == "animals"


def test_differently_cased_labels_group_together(client):
    client.post("/cards", json={"french": "chien", "english": "dog", "label": "Animals"})
    client.post("/cards", json={"french": "chat", "english": "cat", "label": "animals"})
    client.post("/cards", json={"french": "vache", "english": "cow", "label": "ANIMALS"})

    cards = client.get("/cards").json()
    labels = {c["label"] for c in cards}
    assert labels == {"animals"}


def test_list_cards_can_be_grouped_by_label_client_side(client):
    client.post("/cards", json={"french": "chien", "english": "dog", "label": "animals"})
    client.post("/cards", json={"french": "chat", "english": "cat", "label": "animals"})
    client.post("/cards", json={"french": "rouge", "english": "red", "label": "colors"})
    client.post("/cards", json={"french": "bonjour", "english": "hello"})

    cards = client.get("/cards").json()
    labels = {c["label"] for c in cards}
    assert labels == {"animals", "colors", None}
    assert sum(1 for c in cards if c["label"] == "animals") == 2
