from datetime import date, datetime

from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

from app.database import Store
from app.models import Card


def _card_to_item(card: Card) -> dict:
    return {
        "user_id": card.user_id,
        "id": card.id,
        "french": card.french,
        "english": card.english,
        "interval_days": card.interval_days,
        "due_date": card.due_date.isoformat(),
        "created_at": card.created_at.isoformat(),
        "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
        "times_correct": card.times_correct,
        "times_wrong": card.times_wrong,
        "last_grade": card.last_grade,
        "mastered": card.mastered,
        "label": card.label,
    }


def _item_to_card(item: dict) -> Card:
    return Card(
        id=item["id"],
        user_id=item["user_id"],
        french=item["french"],
        english=item["english"],
        interval_days=int(item["interval_days"]),
        due_date=date.fromisoformat(item["due_date"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        last_reviewed_at=datetime.fromisoformat(item["last_reviewed_at"])
        if item.get("last_reviewed_at")
        else None,
        times_correct=int(item["times_correct"]),
        times_wrong=int(item["times_wrong"]),
        last_grade=item.get("last_grade"),
        mastered=bool(item["mastered"]),
        label=item.get("label"),
    )


def create_card(
    store: Store,
    user_id: str,
    french: str,
    english: str,
    label: str | None = None,
    today: date | None = None,
) -> Card:
    today = today or date.today()
    card = Card(user_id=user_id, french=french, english=english, label=label, due_date=today)
    store.cards.put_item(Item=_card_to_item(card))
    return card


def list_cards(store: Store, user_id: str) -> list[Card]:
    resp = store.cards.query(KeyConditionExpression=Key("user_id").eq(user_id))
    cards = [_item_to_card(item) for item in resp["Items"]]
    cards.sort(key=lambda c: c.created_at)
    return cards


def list_due_cards(store: Store, user_id: str, today: date | None = None) -> list[Card]:
    today = today or date.today()
    resp = store.cards.query(
        IndexName="due-index",
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("due_date").lte(today.isoformat()),
    )
    cards = [_item_to_card(item) for item in resp["Items"]]
    cards.sort(key=lambda c: c.due_date)
    return cards


def count_due(store: Store, user_id: str, today: date | None = None) -> int:
    today = today or date.today()
    resp = store.cards.query(
        IndexName="due-index",
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("due_date").lte(today.isoformat()),
        Select="COUNT",
    )
    return resp["Count"]


def get_card_or_404(store: Store, user_id: str, card_id: str) -> Card:
    resp = store.cards.get_item(Key={"user_id": user_id, "id": card_id})
    item = resp.get("Item")
    if item is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return _item_to_card(item)


def save_card(store: Store, card: Card) -> None:
    store.cards.put_item(Item=_card_to_item(card))


def delete_card(store: Store, user_id: str, card_id: str) -> None:
    get_card_or_404(store, user_id, card_id)  # raises 404 if missing/not owned
    store.cards.delete_item(Key={"user_id": user_id, "id": card_id})


def delete_all_cards(store: Store, user_id: str) -> None:
    for card in list_cards(store, user_id):
        store.cards.delete_item(Key={"user_id": user_id, "id": card.id})
