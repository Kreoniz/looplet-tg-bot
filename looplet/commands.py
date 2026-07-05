from __future__ import annotations

import html
import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

from looplet.api.base import ApiError
from looplet.api.jokes import fetch_dad_joke
from looplet.api.trivia import fetch_trivia_question
from looplet.api.weather import fetch_weather_report, format_weather_report
from looplet.api.xkcd import fetch_xkcd
from looplet.config import Settings
from looplet.storage.reminders import ReminderStore
from looplet.utils.choices import parse_choices
from looplet.utils.cooldowns import CooldownManager
from looplet.utils.dice import DiceParseError, format_roll, roll_dice
from looplet.utils.duration import DurationParseError, format_duration, parse_duration
from looplet.utils.quotes import random_quote

LOGGER = logging.getLogger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]

HELP_TEXT = """Looplet commands:
/ping - health check
/weather <city> - current weather
/joke - dad joke
/xkcd latest|random|<number> - comic
/trivia - trivia poll
/choose tea | coffee | water - pick one
/roll 2d6 or /roll d20 - roll dice
/quote - local quote
/remind 30m take a break - reminder
/brief - weather plus a fun item"""


def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.application.bot_data["settings"]


def _chat_allowed(update: Update, settings: Settings) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id in settings.allowed_chat_ids


async def _reply(update: Update, text: str, **kwargs: object) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(text, **kwargs)


def _restricted(handler: Handler) -> Handler:
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        settings = _settings(context)
        if not _chat_allowed(update, settings):
            chat_id = update.effective_chat.id if update.effective_chat else None
            LOGGER.warning("Rejected command from chat_id=%s", chat_id)
            await _reply(update, "Looplet is not enabled for this chat.")
            return
        await handler(update, context)

    return wrapper


async def _check_cooldown(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command_name: str,
) -> bool:
    settings = _settings(context)
    cooldowns: CooldownManager = context.application.bot_data["cooldowns"]
    chat_id = update.effective_chat.id if update.effective_chat else 0
    user_id = update.effective_user.id if update.effective_user else 0
    remaining = cooldowns.hit(
        (chat_id, user_id, command_name),
        cooldown_seconds=settings.external_cooldown_seconds,
    )
    if remaining is None:
        return True

    await _reply(update, f"Give that command {remaining:.0f}s to cool down.")
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, f"Hi, I am Looplet.\n\n{HELP_TEXT}")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, "pong")


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_cooldown(update, context, "weather"):
        return
    city = " ".join(context.args).strip()
    if not city:
        await _reply(update, "Usage: /weather <city>")
        return

    try:
        report = await fetch_weather_report(city, timeout=_settings(context).request_timeout_seconds)
    except ApiError as exc:
        await _reply(update, f"Weather is unavailable: {exc}")
        return

    await _reply(update, format_weather_report(report))


async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_cooldown(update, context, "joke"):
        return
    try:
        await _reply(update, await fetch_dad_joke(timeout=_settings(context).request_timeout_seconds))
    except ApiError as exc:
        await _reply(update, f"Joke service is unavailable: {exc}")


async def xkcd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_cooldown(update, context, "xkcd"):
        return

    selector = context.args[0].lower() if context.args else "latest"
    try:
        comic = await fetch_xkcd(selector, timeout=_settings(context).request_timeout_seconds)
    except ApiError as exc:
        await _reply(update, f"xkcd is unavailable: {exc}")
        return

    caption = (
        f"<b>{html.escape(comic.title)}</b> (#{comic.number})\n"
        f"{html.escape(comic.alt[:220])}\n"
        f"https://xkcd.com/{comic.number}/"
    )
    try:
        if update.effective_chat is None:
            return
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=comic.image_url,
            caption=caption,
            parse_mode="HTML",
        )
    except TelegramError:
        LOGGER.exception("Failed to send xkcd image")
        await _reply(update, f"{comic.title}: https://xkcd.com/{comic.number}/")


async def trivia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_cooldown(update, context, "trivia"):
        return

    try:
        question = await fetch_trivia_question(timeout=_settings(context).request_timeout_seconds)
    except ApiError as exc:
        await _reply(update, f"Trivia is unavailable: {exc}")
        return

    try:
        if update.effective_chat is None:
            return
        await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question.question[:300],
            options=[option[:100] for option in question.options],
            type="quiz",
            correct_option_id=question.correct_option_id,
            is_anonymous=False,
        )
    except TelegramError:
        LOGGER.exception("Failed to send trivia poll")
        options = "\n".join(f"- {option}" for option in question.options)
        await _reply(update, f"{question.question}\n{options}")


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        options = parse_choices(" ".join(context.args))
    except ValueError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, random.choice(options))


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    expression = context.args[0] if context.args else ""
    try:
        result = roll_dice(expression)
    except DiceParseError as exc:
        await _reply(update, str(exc))
        return
    await _reply(update, format_roll(result))


async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, random_quote())


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await _reply(update, "Usage: /remind <duration> <text>")
        return
    try:
        seconds = parse_duration(context.args[0])
    except DurationParseError as exc:
        await _reply(update, str(exc))
        return

    text = " ".join(context.args[1:]).strip()
    if not text:
        await _reply(update, "Reminder text cannot be empty.")
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    user_id = update.effective_user.id if update.effective_user else None
    due_at = datetime.now(UTC) + timedelta(seconds=seconds)

    store: ReminderStore = context.application.bot_data["reminders"]
    reminder_id = store.add_reminder(chat_id=chat_id, user_id=user_id, text=text, due_at=due_at)
    context.application.bot_data["schedule_reminder"](context.application, reminder_id)

    await _reply(update, f"Reminder set for {format_duration(seconds)} from now.")


async def brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_cooldown(update, context, "brief"):
        return

    settings = _settings(context)
    try:
        weather_report = await fetch_weather_report(
            settings.default_city,
            timeout=settings.request_timeout_seconds,
        )
        weather_text = format_weather_report(weather_report)
    except ApiError as exc:
        weather_text = f"Weather for {settings.default_city} is unavailable: {exc}"

    try:
        fun_text = await fetch_dad_joke(timeout=settings.request_timeout_seconds)
    except ApiError:
        fun_text = random_quote()

    await _reply(update, f"{weather_text}\n\n{fun_text}")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled bot error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message is not None:
        await update.effective_message.reply_text("Something went wrong. Try again in a moment.")


def register_handlers(application: Application) -> None:
    handlers: list[tuple[str, Handler]] = [
        ("start", start),
        ("help", start),
        ("ping", ping),
        ("weather", weather),
        ("joke", joke),
        ("xkcd", xkcd),
        ("trivia", trivia),
        ("choose", choose),
        ("roll", roll),
        ("quote", quote),
        ("remind", remind),
        ("brief", brief),
    ]
    for command, handler in handlers:
        application.add_handler(CommandHandler(command, _restricted(handler)))
    application.add_error_handler(on_error)
