import { pronounce } from "./api";

// Module-level (not component-level) cache — FlipCard remounts per card
// (key={current.id} in Train/PracticeSession), so a per-component cache
// wouldn't survive moving to the next card. Same "plain module-level
// state" pattern as theme.js. Caches the in-flight Promise too, not just
// the resolved URL, so tapping the speaker icon twice quickly before the
// first request resolves doesn't fire a second request.
const cache = new Map();

export function getPronunciationUrl(text) {
  const key = text.trim().toLowerCase();
  if (!cache.has(key)) {
    const promise = pronounce(text).then((res) => res.url);
    // A failed request (network blip, etc.) shouldn't poison the cache
    // forever — let the next tap retry instead of always re-rejecting.
    promise.catch(() => cache.delete(key));
    cache.set(key, promise);
  }
  return cache.get(key);
}
