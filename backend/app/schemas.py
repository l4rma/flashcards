from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Grade(str, Enum):
    wrong = "wrong"
    correct = "correct"


class CardCreate(BaseModel):
    french: str
    english: str


class CardUpdate(BaseModel):
    french: str | None = None
    english: str | None = None


class GradeRequest(BaseModel):
    grade: Grade


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


class QuestCompletionNotice(BaseModel):
    """Display info for a just-completed daily quest — same idea as
    AchievementUnlockNotice, attached to the response of whichever action
    caused the completion (add a card, grade a card correct)."""

    key: str
    title: str
    description: str
    badge: str
    coin_reward: int


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
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []
    newly_completed_quests: list[QuestCompletionNotice] = []


class StatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coins: int
    current_streak: int
    longest_streak: int
    last_active_date: date | None
    session_initial_due: int
    newly_unlocked_achievements: list[AchievementUnlockNotice] = []


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
