import pytest
from fastapi import HTTPException

import app.pronunciation as pronunciation_mod
from app.pronunciation import AUDIO_CDN_DOMAIN, get_or_create_audio_url


def _spy_on_synthesize(monkeypatch):
    calls = []
    original = pronunciation_mod._synthesize

    def wrapper(audio_store, text):
        calls.append(text)
        return original(audio_store, text)

    monkeypatch.setattr(pronunciation_mod, "_synthesize", wrapper)
    return calls


def test_first_call_synthesizes_and_returns_a_cdn_url(audio_store, monkeypatch):
    calls = _spy_on_synthesize(monkeypatch)

    url = get_or_create_audio_url(audio_store, "bonjour")

    assert url.startswith(f"https://{AUDIO_CDN_DOMAIN}/audio/")
    assert url.endswith(".mp3")
    assert calls == ["bonjour"]


def test_repeat_call_with_same_text_does_not_re_synthesize(audio_store, monkeypatch):
    calls = _spy_on_synthesize(monkeypatch)

    first = get_or_create_audio_url(audio_store, "bonjour")
    second = get_or_create_audio_url(audio_store, "bonjour")

    assert first == second
    assert calls == ["bonjour"]  # only the first call actually hit Polly


def test_different_text_gets_a_different_url(audio_store, monkeypatch):
    _spy_on_synthesize(monkeypatch)

    bonjour_url = get_or_create_audio_url(audio_store, "bonjour")
    au_revoir_url = get_or_create_audio_url(audio_store, "au revoir")

    assert bonjour_url != au_revoir_url


def test_cache_key_normalizes_case_and_surrounding_whitespace(audio_store, monkeypatch):
    calls = _spy_on_synthesize(monkeypatch)

    lower = get_or_create_audio_url(audio_store, "bonjour")
    upper_padded = get_or_create_audio_url(audio_store, "  Bonjour  ")

    assert lower == upper_padded
    assert calls == ["bonjour"]  # second call was a cache hit, never reached Polly


def test_empty_text_is_rejected(audio_store):
    with pytest.raises(HTTPException) as exc_info:
        get_or_create_audio_url(audio_store, "   ")
    assert exc_info.value.status_code == 400


def test_overly_long_text_is_rejected(audio_store):
    too_long = "a" * (pronunciation_mod.MAX_TEXT_LENGTH + 1)
    with pytest.raises(HTTPException) as exc_info:
        get_or_create_audio_url(audio_store, too_long)
    assert exc_info.value.status_code == 400


def test_pronounce_endpoint_returns_a_url(client):
    resp = client.get("/pronounce", params={"text": "bonjour"})
    assert resp.status_code == 200
    assert resp.json()["url"].endswith(".mp3")


def test_pronounce_endpoint_rejects_empty_text(client):
    resp = client.get("/pronounce", params={"text": "   "})
    assert resp.status_code == 400
