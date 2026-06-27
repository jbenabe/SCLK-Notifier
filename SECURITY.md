# Security

This bot uses a Discord bot token and server-specific IDs. Treat those values as private.

## Do Not Commit

- `.env`
- Discord bot tokens
- `alumni_bot.db`
- log files
- screenshots or console output that expose secrets

## If A Token Leaks

1. Go to the Discord Developer Portal.
2. Open the bot application.
3. Go to **Bot**.
4. Select **Reset Token**.
5. Update `.env` on the machine running the bot.
6. Restart the bot.
7. Review recent commits, logs, and GitHub Actions output for exposed values.

## Reporting Security Issues

For now, report security issues privately to the repository owner instead of opening a public issue.

Good security reports include:

- What happened.
- Which command or workflow is involved.
- Whether a token, role mention, or public post was exposed.
- Steps to reproduce using a test server, if possible.

## Bot Safety Expectations

- Member-triggered responses should stay ephemeral.
- User-submitted agenda text must not create Discord pings.
- Public reminders should be idempotent and rate-limited by persisted state.
- `REMINDERS_ENABLED=false` is the emergency stop for reminder posting while keeping the process alive.
