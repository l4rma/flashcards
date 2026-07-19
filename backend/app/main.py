from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app import achievements as achievements_mod
from app import cards as cards_mod
from app import collection as collection_mod
from app import leveling as leveling_mod
from app import prebuilt_decks as prebuilt_decks_mod
from app import quests as quests_mod
from app import stats as stats_mod
from app.auth import get_current_user_id
from app.database import Store, get_store
from app.scheduling import apply_grade, reset_card_progress
from app.schemas import (
    AchievementOut,
    AchievementUnlockNotice,
    CardCreate,
    CardOut,
    CardUpdate,
    CollectionOut,
    EquipRequest,
    Grade,
    GradeRequest,
    LevelUpNotice,
    LootboxOpenResult,
    LootboxTier,
    PrebuiltDeckOut,
    PrebuiltDeckSummary,
    ProfileUpdate,
    QuestCompletionNotice,
    QuestOut,
    StatsOut,
)

app = FastAPI(title="Flash Cards API")

# CloudFront proxies /api/* to this API under the same origin as the
# frontend in production, so this is mostly defense-in-depth rather than
# something the deployed app actually relies on for same-origin calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _unlock_notices(keys: list[str]) -> list[AchievementUnlockNotice]:
    return [AchievementUnlockNotice(**notice) for notice in achievements_mod.describe_achievements(keys)]


def _quest_notices(keys: list[str]) -> list[QuestCompletionNotice]:
    return [QuestCompletionNotice(**notice) for notice in quests_mod.describe_quests(keys)]


def _finalize_level(store: Store, user_id: str, stats) -> list[LevelUpNotice]:
    """Call after every other stats-mutating step in a request (achievement/
    quest checks included, since their reward transactions also add xp) —
    see leveling.finalize_level for why this is a separate, simple step
    rather than folded into those transactions."""
    levels_gained = leveling_mod.finalize_level(store, user_id, stats)
    if levels_gained <= 0:
        return []
    bonus = leveling_mod.LEVEL_UP_COIN_REWARD * levels_gained
    return [
        LevelUpNotice(
            key=f"level_{stats.level}",
            title=f"Level {stats.level}!",
            description="Keep training to level up again.",
            badge="⭐",
            coin_reward=bonus,
        )
    ]


@app.post("/cards", response_model=CardOut, status_code=201)
def create_card(
    payload: CardCreate, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)
):
    card = cards_mod.create_card(store, user_id, payload.french, payload.english, label=payload.label)

    today = date.today()
    stats = stats_mod.get_or_create_stats(store, user_id)
    # sync_day's due-count query must run after create_card's put_item
    # above so a freeze happening today already reflects this new card
    # (modulo the GSI eventual-consistency caveat documented in sync_day).
    stats_mod.sync_day(store, user_id, stats, today)
    stats_mod.record_card_added(stats)
    quests_mod.record_quest_card_added(stats)
    stats_mod.save_stats(store, stats)

    newly_unlocked = achievements_mod.check_and_unlock_achievements(store, user_id, stats)
    newly_completed_quests = quests_mod.check_and_complete_quests(store, user_id, stats, today)
    newly_leveled_up = _finalize_level(store, user_id, stats)

    result = CardOut.model_validate(card)
    result.newly_unlocked_achievements = _unlock_notices(newly_unlocked)
    result.newly_completed_quests = _quest_notices(newly_completed_quests)
    result.newly_leveled_up = newly_leveled_up
    return result


@app.get("/cards", response_model=list[CardOut])
def list_cards(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    return [CardOut.model_validate(card) for card in cards_mod.list_cards(store, user_id)]


@app.get("/cards/due", response_model=list[CardOut])
def list_due_cards(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    return [CardOut.model_validate(card) for card in cards_mod.list_due_cards(store, user_id)]


@app.patch("/cards/{card_id}", response_model=CardOut)
def update_card(
    card_id: str,
    payload: CardUpdate,
    store: Store = Depends(get_store),
    user_id: str = Depends(get_current_user_id),
):
    card = cards_mod.get_card_or_404(store, user_id, card_id)
    if payload.french is not None:
        card.french = payload.french
    if payload.english is not None:
        card.english = payload.english
    if "label" in payload.model_fields_set:
        card.label = payload.label
    cards_mod.save_card(store, card)
    return CardOut.model_validate(card)


@app.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: str, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    cards_mod.delete_card(store, user_id, card_id)


@app.delete("/cards", status_code=204)
def delete_all_cards(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    cards_mod.delete_all_cards(store, user_id)


@app.post("/cards/{card_id}/grade", response_model=CardOut)
def grade_card(
    card_id: str,
    payload: GradeRequest,
    store: Store = Depends(get_store),
    user_id: str = Depends(get_current_user_id),
):
    card = cards_mod.get_card_or_404(store, user_id, card_id)
    was_wrong_before = card.last_grade == "wrong"
    newly_mastered = apply_grade(card, payload.grade)
    cards_mod.save_card(store, card)

    today = date.today()
    stats = stats_mod.get_or_create_stats(store, user_id)
    stats_mod.sync_day(store, user_id, stats, today)
    stats_mod.record_training_activity(stats, payload.grade, today=today)
    if payload.grade == Grade.correct:
        quests_mod.record_quest_correct_grade(stats)
    if was_wrong_before and payload.grade == Grade.correct:
        stats_mod.record_comeback(stats)
    if newly_mastered:
        stats_mod.record_card_mastered(stats)
    stats_mod.save_stats(store, stats)

    newly_unlocked = achievements_mod.check_and_unlock_achievements(store, user_id, stats)
    newly_completed_quests = quests_mod.check_and_complete_quests(store, user_id, stats, today)
    newly_leveled_up = _finalize_level(store, user_id, stats)

    result = CardOut.model_validate(card)
    result.newly_unlocked_achievements = _unlock_notices(newly_unlocked)
    result.newly_completed_quests = _quest_notices(newly_completed_quests)
    result.newly_leveled_up = newly_leveled_up
    return result


@app.get("/stats", response_model=StatsOut)
def read_stats(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    stats = stats_mod.get_or_create_stats(store, user_id)
    stats_mod.sync_day(store, user_id, stats, date.today())
    stats_mod.save_stats(store, stats)
    return StatsOut.model_validate(stats)


@app.patch("/profile", response_model=StatsOut)
def update_profile(
    payload: ProfileUpdate, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)
):
    """Sets username/avatar_key — both optional/independent (omit a field
    to leave it unchanged). Profile identity lives on Stats (see
    models.py) but isn't gamification progress, so it's untouched by
    reset-all-progress."""
    stats = stats_mod.get_or_create_stats(store, user_id)
    if "username" in payload.model_fields_set:
        stats.username = payload.username
    if "avatar_key" in payload.model_fields_set:
        stats.avatar_key = payload.avatar_key
    stats_mod.save_stats(store, stats)
    return StatsOut.model_validate(stats)


@app.post("/stats/session-complete", response_model=StatsOut)
def session_complete(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    stats = stats_mod.get_or_create_stats(store, user_id)
    stats_mod.award_session_complete(stats)
    stats_mod.save_stats(store, stats)

    newly_unlocked = achievements_mod.check_and_unlock_achievements(store, user_id, stats)
    newly_leveled_up = _finalize_level(store, user_id, stats)

    result = StatsOut.model_validate(stats)
    result.newly_unlocked_achievements = _unlock_notices(newly_unlocked)
    result.newly_leveled_up = newly_leveled_up
    return result


@app.post("/reset-all-progress", status_code=204)
def reset_all_progress(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    """The Admin page's single full-reset action: every Stats field
    (streak, coins, session baseline, and the lifetime achievement-tracking
    fields) except total_cards, every card's scheduling *and* lifetime
    counters, and all achievement/quest unlocks — scoped to the current
    user only. Cards themselves are kept."""
    stats = stats_mod.get_or_create_stats(store, user_id)
    stats_mod.reset_all_stats(stats)
    stats_mod.save_stats(store, stats)
    for card in cards_mod.list_cards(store, user_id):
        reset_card_progress(card)
        cards_mod.save_card(store, card)
    achievements_mod.clear_achievements(store, user_id)
    quests_mod.clear_quest_completions(store, user_id)


@app.get("/achievements", response_model=list[AchievementOut])
def read_achievements(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    stats = stats_mod.get_or_create_stats(store, user_id)
    return achievements_mod.list_achievements(store, user_id, stats)


@app.get("/quests", response_model=list[QuestOut])
def read_quests(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    stats = stats_mod.get_or_create_stats(store, user_id)
    stats_mod.sync_day(store, user_id, stats, date.today())
    stats_mod.save_stats(store, stats)
    return quests_mod.list_quests(store, user_id, stats)


@app.get("/collection", response_model=CollectionOut)
def read_collection(store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)):
    stats = stats_mod.get_or_create_stats(store, user_id)
    return collection_mod.describe_collection(stats)


@app.post("/collection/equip", response_model=StatsOut)
def equip_collectible(
    payload: EquipRequest, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)
):
    """Sets equipped_title/equipped_theme — both optional/independent, same
    omit-vs-null convention as PATCH /profile. Raises 400 if a given key
    isn't owned (collection.equip_title/equip_theme)."""
    stats = stats_mod.get_or_create_stats(store, user_id)
    if "title" in payload.model_fields_set:
        collection_mod.equip_title(stats, payload.title)
    if "theme" in payload.model_fields_set:
        collection_mod.equip_theme(stats, payload.theme)
    stats_mod.save_stats(store, stats)
    return StatsOut.model_validate(stats)


@app.post("/collection/lootboxes/{tier}/buy", response_model=CollectionOut)
def buy_lootbox(
    tier: LootboxTier, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)
):
    stats = stats_mod.get_or_create_stats(store, user_id)
    collection_mod.buy_lootbox(stats, tier.value)
    stats_mod.save_stats(store, stats)
    return collection_mod.describe_collection(stats)


@app.post("/collection/lootboxes/{tier}/open", response_model=LootboxOpenResult)
def open_lootbox(
    tier: LootboxTier, store: Store = Depends(get_store), user_id: str = Depends(get_current_user_id)
):
    stats = stats_mod.get_or_create_stats(store, user_id)
    reward = collection_mod.open_lootbox(stats, tier.value)
    stats_mod.save_stats(store, stats)

    # A coin/xp reward can cross an achievement or level threshold, same
    # as any other coin/xp-earning action in this app.
    newly_unlocked = achievements_mod.check_and_unlock_achievements(store, user_id, stats)
    newly_leveled_up = _finalize_level(store, user_id, stats)

    return LootboxOpenResult(
        **reward,
        newly_unlocked_achievements=_unlock_notices(newly_unlocked),
        newly_leveled_up=newly_leveled_up,
    )


@app.get("/prebuilt-decks", response_model=list[PrebuiltDeckSummary])
def list_prebuilt_decks():
    """No auth dependency needed — every request already passed API
    Gateway's JWT authorizer before Lambda runs (see terraform/
    api_gateway.tf's single $default route), and this content isn't
    scoped to a user anyway (see SPEC.md's Open decisions #11 — browsable
    practice content, not something stored per-user)."""
    return [
        PrebuiltDeckSummary(key=deck.key, title=deck.title, card_count=len(deck.cards))
        for deck in prebuilt_decks_mod.DECKS
    ]


@app.get("/prebuilt-decks/{key}", response_model=PrebuiltDeckOut)
def read_prebuilt_deck(key: str):
    deck = prebuilt_decks_mod.get_deck(key)
    if deck is None:
        raise HTTPException(status_code=404, detail="Pre-built deck not found")
    return PrebuiltDeckOut(
        key=deck.key,
        title=deck.title,
        cards=[{"english": c.english, "french": c.french} for c in deck.cards],
    )


handler = Mangum(app, api_gateway_base_path="/api")
