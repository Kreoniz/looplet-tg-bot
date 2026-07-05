from __future__ import annotations

import logging
from datetime import UTC, datetime

from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from looplet.commands import register_handlers
from looplet.config import ConfigError, Settings
from looplet.storage.reminders import ReminderStore
from looplet.utils.cooldowns import CooldownManager

LOGGER = logging.getLogger(__name__)


COMMANDS = [
    BotCommand("start", "Show Looplet help"),
    BotCommand("help", "Show commands"),
    BotCommand("ping", "Health check"),
    BotCommand("weather", "Get weather for a city"),
    BotCommand("joke", "Get a dad joke"),
    BotCommand("xkcd", "Show an xkcd comic"),
    BotCommand("trivia", "Send a trivia poll"),
    BotCommand("choose", "Choose between options"),
    BotCommand("roll", "Roll dice"),
    BotCommand("quote", "Send a local quote"),
    BotCommand("remind", "Set a reminder"),
    BotCommand("brief", "Weather plus a fun item"),
]


async def _send_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    store: ReminderStore = context.application.bot_data["reminders"]
    reminder_id = int(context.job.data["reminder_id"])
    reminder = store.get_reminder(reminder_id)
    if reminder is None or reminder.sent_at is not None:
        return

    try:
        await context.bot.send_message(
            chat_id=reminder.chat_id,
            text=f"Reminder: {reminder.text}",
        )
    except Exception:
        LOGGER.exception("Failed to send reminder %s", reminder_id)
        raise
    else:
        store.mark_sent(reminder_id)


def schedule_reminder(application: Application, reminder_id: int) -> None:
    store: ReminderStore = application.bot_data["reminders"]
    reminder = store.get_reminder(reminder_id)
    if reminder is None or reminder.sent_at is not None:
        return

    delay = max((reminder.due_at - datetime.now(UTC)).total_seconds(), 1)
    application.job_queue.run_once(
        _send_reminder_job,
        when=delay,
        data={"reminder_id": reminder_id},
        name=f"reminder:{reminder_id}",
    )


def schedule_pending_reminders(application: Application) -> None:
    store: ReminderStore = application.bot_data["reminders"]
    for reminder in store.pending_reminders():
        schedule_reminder(application, reminder.id)
    LOGGER.info("Scheduled %s pending reminder(s)", len(store.pending_reminders()))


async def _post_init(application: Application) -> None:
    store: ReminderStore = application.bot_data["reminders"]
    store.initialize()
    schedule_pending_reminders(application)
    await application.bot.set_my_commands(COMMANDS)


def build_application(settings: Settings) -> Application:
    reminders = ReminderStore(settings.database_path)

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .connect_timeout(settings.request_timeout_seconds)
        .read_timeout(settings.request_timeout_seconds)
        .write_timeout(settings.request_timeout_seconds)
        .pool_timeout(settings.request_timeout_seconds)
        .post_init(_post_init)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["reminders"] = reminders
    application.bot_data["cooldowns"] = CooldownManager(settings.external_cooldown_seconds)
    application.bot_data["schedule_reminder"] = schedule_reminder
    register_handlers(application)
    return application


def main() -> None:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not settings.allowed_chat_ids:
        LOGGER.warning("ALLOWED_CHAT_IDS is empty; all chats will be rejected")

    application = build_application(settings)
    LOGGER.info("Starting Looplet with long polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
