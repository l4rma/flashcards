// Preset avatar set — keys must exactly match backend/app/profile.py's
// AVATAR_KEYS (the backend validates avatar_key against that list; this
// file just maps each key to what's actually rendered). Emoji for now,
// swappable for real SVGs later without a data migration — see TASKS.md
// Phase 16 (blocked on artwork).
export const AVATARS = [
  { key: "fox", emoji: "🦊" },
  { key: "cat", emoji: "🐱" },
  { key: "dog", emoji: "🐶" },
  { key: "rabbit", emoji: "🐰" },
  { key: "owl", emoji: "🦉" },
  { key: "panda", emoji: "🐼" },
  { key: "koala", emoji: "🐨" },
  { key: "lion", emoji: "🦁" },
  { key: "tiger", emoji: "🐯" },
  { key: "bear", emoji: "🐻" },
  { key: "monkey", emoji: "🐵" },
  { key: "penguin", emoji: "🐧" },
];

const BY_KEY = Object.fromEntries(AVATARS.map((a) => [a.key, a.emoji]));

export function avatarEmoji(avatarKey) {
  return (avatarKey && BY_KEY[avatarKey]) || "🙂";
}
