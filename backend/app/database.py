import os

import boto3
from boto3.dynamodb.types import TypeSerializer

# Real deployed table names come from Terraform via these env vars; the
# plain defaults below are only ever used by tests (against a moto mock).
CARDS_TABLE = os.environ.get("CARDS_TABLE", "Cards")
STATS_TABLE = os.environ.get("STATS_TABLE", "Stats")
ACHIEVEMENTS_TABLE = os.environ.get("ACHIEVEMENTS_TABLE", "Achievements")
QUEST_COMPLETIONS_TABLE = os.environ.get("QUEST_COMPLETIONS_TABLE", "QuestCompletions")

_serializer = TypeSerializer()


def serialize_item(item: dict) -> dict:
    """Converts a plain Python dict into DynamoDB's low-level AttributeValue
    format. Needed only for transact_write_items (used by achievements.py/
    quests.py to atomically record an unlock/completion alongside its coin
    reward) — every other call in this app goes through the Table resource's
    high-level API (get_item/put_item/query/delete_item), which accepts
    plain dicts directly and needs no such conversion."""
    return {k: _serializer.serialize(v) for k, v in item.items()}


class Store:
    """Bundles the four DynamoDB table resources (+ the low-level client,
    needed for transact_write_items) used across the app. A thin
    dependency-injection seam so tests can point it at moto-mocked tables
    instead of real AWS ones."""

    def __init__(self, resource=None, client=None):
        resource = resource or boto3.resource("dynamodb")
        self.resource = resource
        # Deliberately a *separate*, plain low-level client for
        # transact_write_items — not resource.meta.client. boto3 resources
        # register serialization hooks on their own client that transform
        # Python-native values (int/str/bool/etc.) into DynamoDB's
        # AttributeValue format for Table-level calls (put_item, query,
        # etc.). Reusing that same client for a raw transact_write_items
        # call — which needs already-low-level AttributeValue dicts, built
        # here via serialize_item — double-serializes them (e.g. a string
        # becomes `{"M": {"S": {"S": "value"}}}` instead of `{"S": "value"}`),
        # which DynamoDB (and moto) reject. A plain client has no such hooks.
        self.client = client or boto3.client("dynamodb", region_name=resource.meta.client.meta.region_name)
        self.cards = resource.Table(CARDS_TABLE)
        self.stats = resource.Table(STATS_TABLE)
        self.achievements = resource.Table(ACHIEVEMENTS_TABLE)
        self.quest_completions = resource.Table(QUEST_COMPLETIONS_TABLE)


def get_store() -> Store:
    return Store()


def create_tables(resource) -> None:
    """Creates all 4 application tables against the given DynamoDB
    resource. Used by tests (against a moto mock) — the real deployed
    tables are created by Terraform, not this function."""
    resource.create_table(
        TableName=CARDS_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "due_date", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "due-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "due_date", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=STATS_TABLE,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=ACHIEVEMENTS_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "achievement_key", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "achievement_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    resource.create_table(
        TableName=QUEST_COMPLETIONS_TABLE,
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "sort_key", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "sort_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
