import hashlib
import os

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

# Real values come from Terraform via these env vars in prod; the plain
# defaults are only ever hit by tests (against a moto mock) — same
# convention as database.py's *_TABLE constants.
AUDIO_BUCKET = os.environ.get("AUDIO_BUCKET", "flash-cards-audio")
AUDIO_CDN_DOMAIN = os.environ.get("AUDIO_CDN_DOMAIN", "audio.example.com")

VOICE_ID = "Lea"
LANGUAGE_CODE = "fr-FR"
ENGINE = "neural"
MAX_TEXT_LENGTH = 200


class AudioStore:
    """Bundles the S3 + Polly clients used by this module — a thin
    dependency-injection seam so tests can point it at moto-mocked
    clients instead of real AWS ones, exactly like database.py's Store.
    Deliberately constructed fresh per request (not at import time) —
    moto's mock_aws() only intercepts boto3 clients created *inside* its
    context, so a module-level client here would silently bypass the
    mock in tests."""

    def __init__(self, s3=None, polly=None):
        self.s3 = s3 or boto3.client("s3")
        self.polly = polly or boto3.client("polly")


def get_audio_store() -> AudioStore:
    return AudioStore()


def _cache_key(text: str) -> str:
    """Hash of the *normalized* text, not the card's id — the same French
    word appears on many different cards (yours, other users', pre-built
    decks), so hashing the text means it's synthesized once ever, no
    matter how many cards reference it. Also sidesteps pre-built/practice
    cards not having a real Card id at all (see PrebuiltCardOut). Editing
    a card's French text naturally invalidates itself — new text, new
    hash — with no explicit cache-busting needed.

    This is also the exact filename used both as the S3 object key
    (prefixed with "audio/" below) and as the public URL's path segment
    after "/audio/" — deliberately identical, so CloudFront's `/audio/*`
    behavior can forward requests to S3 completely unrewritten. Stripping
    a URL prefix *in* CloudFront (a Function rewriting the request path)
    was tried for /api/* and caused a real, hard-to-diagnose bug there
    (see frontend.tf) — the fix each time is to make the object's actual
    location match the requested path instead of rewriting anything."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() + ".mp3"


def _s3_key(cache_key: str) -> str:
    return f"audio/{cache_key}"


def _exists(audio_store: AudioStore, s3_key: str) -> bool:
    """head_object raises a generic ClientError (code 404) for a missing
    key — S3 clients don't expose a NoSuchKey exception for this call the
    way get_object does, so this has to check the error code rather than
    catch a specific exception class."""
    try:
        audio_store.s3.head_object(Bucket=AUDIO_BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def _synthesize(audio_store: AudioStore, text: str) -> bytes:
    response = audio_store.polly.synthesize_speech(
        Engine=ENGINE,
        LanguageCode=LANGUAGE_CODE,
        VoiceId=VOICE_ID,
        OutputFormat="mp3",
        Text=text,
    )
    return response["AudioStream"].read()


def get_or_create_audio_url(audio_store: AudioStore, text: str) -> str:
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"text must be {MAX_TEXT_LENGTH} characters or fewer")

    key = _cache_key(text)
    s3_key = _s3_key(key)
    if not _exists(audio_store, s3_key):
        audio_bytes = _synthesize(audio_store, text)
        audio_store.s3.put_object(
            Bucket=AUDIO_BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/mpeg",
        )
    return f"https://{AUDIO_CDN_DOMAIN}/audio/{key}"
