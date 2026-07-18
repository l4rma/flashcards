import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth import get_current_user_id
from app.database import Store, create_tables, get_store
from app.main import app

TEST_USER_ID = "test-user"


@pytest.fixture()
def store():
    """A Store backed by moto-mocked DynamoDB tables — no real AWS access,
    no Docker, no local server."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        create_tables(resource)
        yield Store(resource=resource)


@pytest.fixture()
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_client(store):
    """Like `client`, but returns a factory for creating multiple
    user-scoped clients sharing one Store — for cross-user isolation
    tests. `get_current_user_id`'s override is global (attached to the one
    `app` object), so each returned client re-sets it immediately before
    every request rather than once at creation time — this lets calls on
    different clients be freely interleaved in any order within a test."""
    app.dependency_overrides[get_store] = lambda: store
    shared_client = TestClient(app)

    class _UserClient:
        def __init__(self, user_id: str):
            self.user_id = user_id

        def _use(self):
            app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        def get(self, *args, **kwargs):
            self._use()
            return shared_client.get(*args, **kwargs)

        def post(self, *args, **kwargs):
            self._use()
            return shared_client.post(*args, **kwargs)

        def patch(self, *args, **kwargs):
            self._use()
            return shared_client.patch(*args, **kwargs)

        def delete(self, *args, **kwargs):
            self._use()
            return shared_client.delete(*args, **kwargs)

    yield _UserClient
    app.dependency_overrides.clear()
