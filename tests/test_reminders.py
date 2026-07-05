from datetime import UTC, datetime, timedelta

from looplet.storage.reminders import ReminderStore


def test_reminder_store_adds_and_marks_reminders(tmp_path) -> None:
    store = ReminderStore(tmp_path / "looplet.sqlite3")
    store.initialize()

    due_at = datetime.now(UTC) + timedelta(minutes=5)
    reminder_id = store.add_reminder(
        chat_id=123,
        user_id=456,
        text="take a break",
        due_at=due_at,
    )

    reminder = store.get_reminder(reminder_id)
    assert reminder is not None
    assert reminder.chat_id == 123
    assert reminder.user_id == 456
    assert reminder.text == "take a break"
    assert store.pending_reminders()[0].id == reminder_id

    store.mark_sent(reminder_id)
    assert store.get_reminder(reminder_id).sent_at is not None
    assert store.pending_reminders() == []


def test_settings_round_trip(tmp_path) -> None:
    store = ReminderStore(tmp_path / "looplet.sqlite3")
    store.initialize()

    store.set_setting("default_city", "Omsk")

    assert store.get_setting("default_city") == "Omsk"
