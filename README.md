# Looplet

Looplet is a small Telegram bot for a private group of friends. It runs with long polling, stores lightweight state in SQLite, and is packaged for Docker Compose on a small VPS.

## Commands

- `/start` and `/help` - show the command list.
- `/ping` - health check.
- `/weather <city>` - current weather and short forecast from Open-Meteo.
- `/joke` - dad joke from icanhazdadjoke.
- `/xkcd latest`, `/xkcd random`, `/xkcd <number>` - send an xkcd comic.
- `/trivia` - multiple-choice trivia poll from Open Trivia DB.
- `/choose option1 | option2 | option3` - pick one option.
- `/roll 2d6` or `/roll d20` - roll dice.
- `/quote` - return a local quote from the committed quote file.
- `/remind <duration> <text>` - save a reminder and send it later, for example `/remind 30m check soup`.
- `/brief` - default city weather plus one fun item.

## BotFather Setup

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`, choose a display name, then choose a username ending in `bot`.
3. Copy the token into your server-side `.env` file as `TELEGRAM_BOT_TOKEN`.
4. Do not commit `.env` or paste the token into GitHub issues, chat logs, or screenshots.

## Telegram Group Privacy Mode

Telegram bots in groups usually see only commands, replies to the bot, and service messages when privacy mode is enabled. That is enough for Looplet because all features are command-driven.

If you later add non-command message features, ask `@BotFather` for `/setprivacy` and disable privacy mode for this bot. For this project, leaving privacy mode enabled is the simpler and safer default.

## Environment Variables

Copy `.env.example` to `.env` on the server and fill in the values.

- `TELEGRAM_BOT_TOKEN` - required BotFather token.
- `ALLOWED_CHAT_IDS` - comma-separated Telegram chat IDs allowed to use the bot, such as `123456789,-1001234567890`. Empty means no chat is allowed.
- `DEFAULT_CITY` - city used by `/brief`.
- `DATABASE_PATH` - SQLite file path. The Docker Compose default is `/app/data/looplet.sqlite3`.
- `REQUEST_TIMEOUT_SECONDS` - timeout for external HTTP APIs.
- `EXTERNAL_COOLDOWN_SECONDS` - per-user cooldown for external API commands.
- `LOG_LEVEL` - Python logging level.

To discover a chat ID, start the bot with `ALLOWED_CHAT_IDS` empty, send `/ping`, and check the logs for the rejected `chat_id`. Add only your private chat and group IDs to `ALLOWED_CHAT_IDS` before leaving it running.

## Local Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m looplet
```

Run tests:

```bash
pytest
```

## Docker Compose Deployment

On the VPS:

```bash
git clone https://github.com/YOUR_USERNAME/looplet-tg-bot.git
cd looplet-tg-bot
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f
```

The compose file mounts `./data` into the container so reminders survive restarts.

Update later with:

```bash
git pull
docker compose up -d --build
```

## GitHub Publishing

If GitHub CLI is authenticated, the repo can be created with:

```bash
gh repo create looplet-tg-bot --private --source=. --remote=origin --push
```

Without GitHub CLI, initialize and push manually:

```bash
git init
git add .
git commit -m "Initial Looplet bot"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/looplet-tg-bot.git
git push -u origin main
```

## Notes

Looplet uses long polling, not webhooks, so the VPS does not need public HTTPS. Secrets are read from environment variables only. External API commands have in-memory cooldowns and request timeouts; reminders and settings use SQLite.
