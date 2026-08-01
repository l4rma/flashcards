import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth import get_current_user_id
from app.database import Store, create_tables, get_store
from app.main import app
from app.pronunciation import AUDIO_BUCKET, AudioStore, get_audio_store

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
def audio_store(store, monkeypatch):
    """An AudioStore backed by moto-mocked S3 + Polly. Takes `store` only
    to piggyback on the mock_aws() context it already opened — moto mocks
    every boto3 client created inside that context, not just DynamoDB's,
    so a second independent mock_aws() here would be redundant.

    The monkeypatch works around a genuine moto bug, not an app issue:
    moto's SynthesizeSpeech validates VoiceId against voices' display
    *Name* ("Léa", accented) instead of the actual API *Id* ("Lea", the
    real value botocore's own service model — and real AWS — accept,
    confirmed by inspecting botocore's polly service-2.json directly).
    Left as-is, every real VoiceId with an accented display name would
    spuriously fail only in tests. Rebuilds moto's voice-id allowlist
    from the correct field."""
    import moto.polly.responses as moto_polly_responses
    from moto.polly.resources import VOICE_DATA

    monkeypatch.setattr(moto_polly_responses, "VOICE_IDS", {voice["Id"] for voice in VOICE_DATA})

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=AUDIO_BUCKET)
    polly = boto3.client("polly", region_name="us-east-1")
    return AudioStore(s3=s3, polly=polly)


@pytest.fixture()
def client(store, audio_store):
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_audio_store] = lambda: audio_store
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_client(store, audio_store):
    """Like `client`, but returns a factory for creating multiple
    user-scoped clients sharing one Store — for cross-user isolation
    tests. `get_current_user_id`'s override is global (attached to the one
    `app` object), so each returned client re-sets it immediately before
    every request rather than once at creation time — this lets calls on
    different clients be freely interleaved in any order within a test."""
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_audio_store] = lambda: audio_store
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
