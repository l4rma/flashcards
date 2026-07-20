from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from app.leveling import xp_for_level
from app.profile import AVATAR_KEYS, USERNAME_MAX_LENGTH


class Grade(str, Enum):
    wrong = "wrong"
    correct = "correct"


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _normalize_label(value: str | None) -> str | None:
    """Labels are case-insensitive sub-decks — "Animals"/"animals"/
    "ANIMALS" must all group as the same one, so the label is lowercased
    at write time (the single canonical form) rather than trying to do
    case-insensitive comparison at every read site (the Deck page's
    filter pills, Extra Training's sub-deck picker, the "used_label"
    achievement — none of them would agree independently)."""
    value = _blank_to_none(value)
    return value.lower() if value is not None else None


class CardCreate(BaseModel):
    french: str
    english: str
    label: str | None = None

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str | None) -> str | None:
        return _normalize_label(value)


class CardUpdate(BaseModel):
    french: str | None = None
    english: str | None = None
    # Omit to leave unchanged, send null to clear (same omit-vs-null
    # convention as ProfileUpdate/EquipRequest) — unlike french/english,
    # which are never legitimately cleared, removing a card from its
    # sub-deck is a real action, so label needs the "was this field sent
    # at all" distinction main.py checks via model_fields_set. A blank
    # string is treated the same as null (clears it) — the frontend's
    # edit form has no separate "clear" affordance, just an empty text
    # input, so an empty string has to mean the same thing null does.
    label: str | None = None

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str | None) -> str | None:
        return _normalize_label(value)


class GradeRequest(BaseModel):
    grade: Grade


class ProfileUpdate(BaseModel):
    """PATCH /profile body. Both fields optional/independently settable —
    omit one to leave it unchanged, send null to clear it. No uniqueness
    check on username (see SPEC.md Open decisions) — this is a
    personal/small-multi-user app, not a public directory."""

    username: str | None = None
    avatar_key: str | None = None

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if len(value) > USERNAME_MAX_LENGTH:
            raise ValueError(f"Username must be at most {USERNAME_MAX_LENGTH} characters")
        return value

    @field_validator("avatar_key")
    @classmethod
    def _validate_avatar_key(cls, value: str | None) -> str | None:
        if value is not None and value not in AVATAR_KEYS:
            raise ValueError(f"Unknown avatar_key {value!r}")
        return value


class AchievementUnlockNotice(BaseModel):
    """Display info for a just-unlocked achievement — attached to the
    response of whichever action caused it (add/grade a card, complete a
    session), so the frontend can pop a celebration without a separate
    request. Empty unless that particular call actually unlocked something."""

    key: str
    title: str
    description: str
    badge: str
    coin_reward: int


class LevelUpNotice(BaseModel):
    """Display info for a level-up celebration — same shape as
    AchievementUnlockNotice/QuestCompletionNotice (key/title/description/
    badge/coin_reward) so the frontend's CelebrationModal needs no
    special-casing. `key` is synthesized from the new level, not looked
    up from a static definitions list the way achievements/quests are,
    since a level has no fixed catalog entry."""

    key: str
    title: str
    description: str
    badge: str
    coin_reward: int


class QuestCompletionNotice(BaseModel):
    """Display info for a just-completed daily quest — same idea as
    AchievementUnlockNotice, attached to the response of whichever action
    caused the completion (add a card, grade a card correct)."""

    key: str
    title: str
    description: str
    badge: str
    coin_reward: int


class DailyQuestBonusNotice(BaseModel):
    """Display info for the "completed every quest today" bonus — a
    lootbox, not coins, so it doesn't share AchievementUnlockNotice/
    QuestCompletionNotice/LevelUpNotice's exact shape (`coin_reward` is
    swapped for `lootbox_tier`); CelebrationModal branches on whichever
    field is present to decide what reward line to render."""

    key: str
    title: str
    description: str
    badge: str
    lootbox_tier: str


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    french: str
    english: str
    interval_days: int
    due_date: date
    created_at: datetime
    last_reviewed_at: datetime | None
    times_correct: int
    times_wrong: int
    mastered: bool = False
    label: str | None = None
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []
    newly_completed_quests: list[QuestCompletionNotice] = []
    newly_leveled_up: list[LevelUpNotice] = []
    newly_awarded_daily_bonus: list[DailyQuestBonusNotice] = []


class StatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str | None = None
    avatar_key: str | None = None
    equipped_title: str | None = None
    equipped_theme: str | None = None
    xp: int
    level: int
    coins: int
    current_streak: int
    longest_streak: int
    last_active_date: date | None
    session_initial_due: int
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []
    newly_leveled_up: list[LevelUpNotice] = []

    @computed_field
    @property
    def xp_into_level(self) -> int:
        """Progress toward the *next* level — `progress_current` for the
        Profile page's XP bar. Computed here (not stored) so every
        StatsOut-returning endpoint gets it for free, same reasoning as
        achievements'/quests' progress_current/progress_target."""
        return self.xp - xp_for_level(self.level)

    @computed_field
    @property
    def xp_for_next_level(self) -> int:
        """`progress_target` for the XP bar — total XP needed to go from
        the current level to the next."""
        return xp_for_level(self.level + 1) - xp_for_level(self.level)


class AchievementHistoryEntry(BaseModel):
    key: str
    title: str
    badge: str
    unlocked_at: datetime


class AchievementOut(BaseModel):
    key: str
    title: str
    description: str
    badge: str
    unlocked: bool
    unlocked_at: datetime | None
    progress_current: int
    progress_target: int
    coin_reward: int
    history: list[AchievementHistoryEntry]


class QuestOut(BaseModel):
    key: str
    title: str
    description: str
    badge: str
    completed: bool
    progress_current: int
    progress_target: int
    coin_reward: int


class LootboxTier(str, Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"


class EquipRequest(BaseModel):
    """POST /collection/equip body. Both fields optional/independently
    settable, same omit-vs-null convention as ProfileUpdate — omit a
    field to leave it unchanged, send null to un-equip. Ownership is
    checked in collection.equip_title/equip_theme (needs the current
    Stats, not just the request body, so it can't be a field_validator
    here)."""

    title: str | None = None
    theme: str | None = None


class TitleOut(BaseModel):
    key: str
    name: str
    rarity: str
    owned: bool
    equipped: bool


class ThemeOut(BaseModel):
    key: str
    name: str
    rarity: str
    colors: dict[str, str]
    font_display: str | None
    owned: bool
    equipped: bool


class LootboxTierOut(BaseModel):
    tier: str
    name: str
    coin_cost: int
    count: int


class CollectionOut(BaseModel):
    titles: list[TitleOut]
    themes: list[ThemeOut]
    lootboxes: list[LootboxTierOut]


class LootboxOpenResult(BaseModel):
    """Response of POST /collection/lootboxes/{tier}/open — describes what
    was won (kind is "coins" | "xp" | "title" | "theme"; key/name are set
    only for title/theme wins, amount only for coins/xp wins) plus any
    achievement unlocks or level-ups the reward happened to trigger (a
    coin/xp windfall can cross either threshold, same as any other
    coin/xp-earning action)."""

    kind: str
    key: str | None = None
    name: str | None = None
    amount: int | None = None
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []
    newly_leveled_up: list[LevelUpNotice] = []


class PrebuiltDeckSummary(BaseModel):
    key: str
    title: str
    card_count: int


class PrebuiltCardOut(BaseModel):
    english: str
    french: str


class PrebuiltDeckOut(BaseModel):
    key: str
    title: str
    cards: list[PrebuiltCardOut]


class PracticeSource(str, Enum):
    own_deck = "own_deck"
    sub_deck = "sub_deck"
    prebuilt = "prebuilt"


class PracticeCompletedRequest(BaseModel):
    """POST /practice/completed body — sent once, by PracticeSession.jsx,
    when a practice round finishes a full linear pass (not on early exit
    via the ✕). This is the *only* signal the backend ever gets that
    Extra Training happened at all — grading itself makes no API call
    (see SPEC.md's Extra Training section) — so it exists purely to back
    the practice-related achievements, not to award coins/xp for the
    round itself."""

    source: PracticeSource


class PracticeCompletedResult(BaseModel):
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []
    newly_leveled_up: list[LevelUpNotice] = []
