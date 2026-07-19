from app.prebuilt_decks import DECKS


def test_at_least_one_prebuilt_deck_is_bundled():
    assert len(DECKS) > 0


def test_every_deck_has_a_title_and_cards():
    for deck in DECKS:
        assert deck.title
        assert len(deck.cards) > 0
        for card in deck.cards:
            assert card.english
            assert card.french


def test_list_prebuilt_decks_api(client):
    resp = client.get("/prebuilt-decks")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(DECKS)
    for entry in body:
        assert entry["card_count"] > 0
        assert entry["title"]


def test_read_prebuilt_deck_api(client):
    key = DECKS[0].key
    resp = client.get(f"/prebuilt-decks/{key}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["key"] == key
    assert body["title"] == DECKS[0].title
    assert len(body["cards"]) == len(DECKS[0].cards)
    assert set(body["cards"][0].keys()) == {"english", "french"}


def test_read_unknown_prebuilt_deck_404s(client):
    resp = client.get("/prebuilt-decks/does-not-exist")
    assert resp.status_code == 404


def test_prebuilt_decks_never_touch_the_cards_table(client):
    client.get("/prebuilt-decks")
    client.get(f"/prebuilt-decks/{DECKS[0].key}")
    assert client.get("/cards").json() == []
