from datetime import date, timedelta

from boto3.dynamodb.conditions import Key

from app.cards import create_card
from app.models import Stats
from app.quests import (
    ADD_CARDS_TARGET,
    TRAIN_CORRECT_CAP,
    TRAIN_FLOOR_START,
    check_and_complete_quests,
    clear_quest_completions,
    list_quests,
    record_quest_card_added,
    record_quest_correct_grade,
)
from app.stats import get_or_create_stats, sync_day

TODAY = date(2026, 7, 15)
TEST_USER_ID = "test-user"


def make_stats(**overrides) -> Stats:
    stats = Stats(user_id=TEST_USER_ID)
    for key, value in overrides.items():
        setattr(stats, key, value)
    return stats


def _completion_count(store, quest_key: str) -> int:
    resp = store.quest_completions.query(KeyConditionExpression=Key("user_id").eq(TEST_USER_ID))
    return sum(1 for item in resp["Items"] if item["quest_key"] == quest_key)


def test_no_quests_completed_with_no_activity(store):
    stats = make_stats()

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}

    assert quests["daily_add_cards"]["progress_current"] == 0
    assert quests["daily_add_cards"]["progress_target"] == ADD_CARDS_TARGET
    assert quests["daily_add_cards"]["completed"] is False
    assert quests["daily_train"]["progress_current"] == 0
    assert quests["daily_train"]["completed"] is False


def test_add_cards_quest_progress_tracks_record_calls(store):
    stats = make_stats()

    for _ in range(3):
        record_quest_card_added(stats)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_add_cards"]["progress_current"] == 3


def test_bulk_inserted_cards_do_not_count_toward_add_cards_quest(store):
    # Regression test: progress used to be a live count of cards created
    # today, which meant cards inserted by any means (not just through the
    # app) satisfied the quest just from timestamp coincidence. Progress
    # must only move via record_quest_card_added.
    stats = make_stats()
    for i in range(ADD_CARDS_TARGET):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_add_cards"]["progress_current"] == 0
    assert quests["daily_add_cards"]["completed"] is False


def test_train_quest_target_caps_at_ten_when_more_cards_are_due(store):
    stats = make_stats()
    for i in range(15):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_train"]["progress_target"] == TRAIN_CORRECT_CAP


def test_train_quest_target_matches_due_count_when_between_floor_and_cap(store):
    stats = make_stats()
    for i in range(7):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_train"]["progress_target"] == 7


def test_train_quest_target_defaults_to_floor_when_no_cards_due(store):
    # Regression test: an empty/small deck used to give a target of 0
    # (trivially "complete"). It should default to the starting floor
    # instead, so the quest still asks for something meaningful.
    stats = make_stats()
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_train"]["progress_target"] == TRAIN_FLOOR_START


def test_train_quest_progress_tracks_correct_grades(store):
    stats = make_stats()
    for i in range(15):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    for _ in range(4):
        record_quest_correct_grade(stats)

    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_train"]["progress_current"] == 4
    assert quests["daily_train"]["progress_target"] == TRAIN_CORRECT_CAP


def test_train_quest_completes_when_correct_reaches_capped_target(store):
    stats = make_stats()
    for i in range(TRAIN_FLOOR_START):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    for _ in range(TRAIN_FLOOR_START):
        record_quest_correct_grade(stats)

    completed = check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)

    assert "daily_train" in completed
    assert stats.coins > 0


def test_add_cards_quest_completes_and_awards_coins(store):
    stats = make_stats()
    for _ in range(ADD_CARDS_TARGET):
        record_quest_card_added(stats)

    completed = check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)

    assert "daily_add_cards" in completed
    assert stats.coins > 0
    assert _completion_count(store, "daily_add_cards") == 1


def test_completing_a_quest_twice_in_a_day_does_not_double_award(store):
    stats = make_stats()
    for _ in range(ADD_CARDS_TARGET + 2):
        record_quest_card_added(stats)

    check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)
    coins_after_first = stats.coins

    check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)

    assert stats.coins == coins_after_first
    assert _completion_count(store, "daily_add_cards") == 1


def test_quest_progress_resets_on_a_new_day(store):
    stats = make_stats()
    for i in range(3):
        create_card(store, TEST_USER_ID, f"mot{i}", f"word{i}", today=TODAY)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)

    record_quest_correct_grade(stats)
    record_quest_card_added(stats)
    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=TODAY)}
    assert quests["daily_train"]["progress_current"] == 1
    assert quests["daily_add_cards"]["progress_current"] == 1

    tomorrow = TODAY + timedelta(days=1)
    sync_day(store, TEST_USER_ID, stats, today=tomorrow)
    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=tomorrow)}
    assert quests["daily_train"]["progress_current"] == 0
    assert quests["daily_add_cards"]["progress_current"] == 0


def test_quest_completion_from_a_previous_day_does_not_carry_over(store):
    stats = make_stats()
    for _ in range(ADD_CARDS_TARGET):
        record_quest_card_added(stats)
    check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)

    tomorrow = TODAY + timedelta(days=1)
    sync_day(store, TEST_USER_ID, stats, today=tomorrow)
    quests = {q["key"]: q for q in list_quests(store, TEST_USER_ID, stats, today=tomorrow)}

    assert quests["daily_add_cards"]["completed"] is False
    assert quests["daily_add_cards"]["progress_current"] == 0


def test_clear_quest_completions_removes_all_rows(store):
    stats = make_stats()
    for _ in range(ADD_CARDS_TARGET):
        record_quest_card_added(stats)
    check_and_complete_quests(store, TEST_USER_ID, stats, today=TODAY)
    assert _completion_count(store, "daily_add_cards") > 0

    clear_quest_completions(store, TEST_USER_ID)

    assert _completion_count(store, "daily_add_cards") == 0


def test_sync_day_is_idempotent_within_the_same_day(store):
    stats = make_stats()
    sync_day(store, TEST_USER_ID, stats, today=TODAY)  # establishes today's baseline first

    record_quest_correct_grade(stats)
    sync_day(store, TEST_USER_ID, stats, today=TODAY)  # same-day re-entry must not reset progress

    assert stats.quest_correct_today == 1
