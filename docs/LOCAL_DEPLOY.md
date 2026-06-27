# Local Deploy And Redeploy Guide

This guide gets SCLK Notifier running from a Windows PC. It is the MVP deployment path until an always-on host is selected.

## First-Time Setup

1. Open PowerShell.

2. Clone the repo:

```
cd C:\Users\andre\Documents
git clone https://github.com/award73/SCLK-Notifier.git
cd SCLK-Notifier\discord-alumni-reminder-bot
```

   If the repo is already cloned:

```
cd C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot
```

3. Create and activate a virtual environment:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

   If PowerShell blocks activation because of execution policy, enable it only for the current terminal session:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```
pip install -r requirements.txt
```

5. Create `.env`:

```
Copy-Item .env.example .env
```

6. Fill in `.env`:

```
DISCORD_TOKEN=
GUILD_ID=
ANNOUNCEMENT_CHANNEL_ID=
ALUMNI_ROLE_ID=
TIMEZONE=America/New_York
DISCORD_BOT_PERMISSIONS=8462797117848576
REMINDERS_ENABLED=true
```

   Do not commit `.env`.

7. Run local checks:

```
python -m py_compile bot.py
python -m unittest discover -s tests
```

8. Start the bot:

```
python bot.py
```

9. Confirm the logs show the bot logged in and synced slash commands.

## Discord Smoke Test

In Discord:

1. Create a future native Discord Scheduled Event.
2. As a Manage Server admin, run `/event_sync`.
3. Run `/event_list`.
4. Run `/next_meeting`.
5. Run `/test_notify` and confirm the announcement channel gets a production-shaped message mentioning only you.
6. Run `/agenda_add item:"Test agenda item"`.
7. Run `/agenda`.
8. Add a test item containing `@everyone`, `@here`, a role mention, a user mention, a channel mention, a link, and markdown. Confirm no ping occurs when viewing `/agenda`.

## Database Integrity And Backups

`alumni_bot.db` is a local SQLite file stored on disk. It is completely independent of
the bot code and is never touched by Git. Updating `bot.py`, pulling new code, or
restarting the bot will not affect the database file.

### Manual backup before any code change

Before pulling new code, open PowerShell and take a snapshot of the database:

```
Copy-Item C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db `
          C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db.bak
```

### Restore from backup

If something goes wrong after a code update, stop the bot and restore:

```
Copy-Item C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db.bak `
          C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db
```

Then restart the bot normally.

### Verify database integrity

To check that the database file is not corrupted, run from inside `discord-alumni-reminder-bot\`:

```
python -c "import sqlite3; conn = sqlite3.connect('alumni_bot.db'); print(conn.execute('PRAGMA integrity_check;').fetchone()[0]); conn.close()"
```

A healthy database prints `ok`. If you see anything else, restore from your backup before restarting the bot.

### Safe schema changes

If a code update adds or changes database tables, use `ALTER TABLE` to add new columns
rather than dropping and recreating the table, which would wipe existing rows:

```sql
-- Safe: adds a column without touching existing data
ALTER TABLE events ADD COLUMN new_field TEXT DEFAULT '';

-- Unsafe: drops all existing rows
DROP TABLE events;
CREATE TABLE events (...);
```

If you are unsure whether a code change touches the schema, back up the database first.

### Automated daily backup (optional)

To automatically back up the database every day, use Windows Task Scheduler with a
simple PowerShell script.

Create a file called `backup_db.ps1` anywhere convenient, for example
`C:\Users\andre\Documents\backup_db.ps1`, with this content:

```
Copy-Item C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db `
          C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db.bak
```

Then in Task Scheduler:

1. Open **Task Scheduler** from the Start menu.
2. Click **Create Basic Task**.
3. Name it `SCLK DB Backup` and click **Next**.
4. Set the trigger to **Daily** at a time the bot is unlikely to be writing, such as 2:00 AM.
5. Set the action to **Start a program**.
6. Program: `powershell.exe`
7. Arguments: `-ExecutionPolicy Bypass -File "C:\Users\andre\Documents\backup_db.ps1"`
8. Click **Finish**.

This overwrites the previous `.bak` file daily, giving you a rolling 24-hour safety net.

## Redeploy Existing Local Bot

Use this when new code has been merged or you want to test a branch.

1. Stop the running bot process.

   In the PowerShell window running the bot, press `Ctrl+C`.

2. Back up the database before making any changes:

```
Copy-Item C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db `
          C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db.bak
```

3. Update the repo:

```
cd C:\Users\andre\Documents\SCLK-Notifier
git switch main
git pull
```

   To test a review branch instead:

```
git switch codex/incremental-prs
git pull
```

4. Activate the venv:

```
cd discord-alumni-reminder-bot
.\.venv\Scripts\Activate.ps1
```

5. Update dependencies:

```
pip install -r requirements.txt
```

6. Run tests:

```
python -m py_compile bot.py
python -m unittest discover -s tests
```

7. Confirm `.env` still has the correct Discord values, `DISCORD_BOT_PERMISSIONS=8462797117848576`, and `REMINDERS_ENABLED=true`.

8. Verify database integrity:

```
python -c "import sqlite3; conn = sqlite3.connect('alumni_bot.db'); print(conn.execute('PRAGMA integrity_check;').fetchone()[0]); conn.close()"
```

Confirm the output is `ok` before continuing.

9. Restart the bot:

```
python bot.py
```

10. In Discord, run `/event_sync`, `/event_list`, `/next_meeting`, `/agenda_add`, and `/agenda`.

## Emergency Stop

To stop public reminder posts immediately:

1. Stop the bot process with `Ctrl+C`, or remove the bot's Send Messages permission in the announcement channel.

2. To keep the bot running but stop reminder posts, set this in `.env`:

```
REMINDERS_ENABLED=false
```

3. Restart the bot.

## Temporary Rollback

Use this if the latest code fails and you need to test a known-good commit.

1. Stop the bot process.

2. Restore the database backup taken before the failed deploy:

```
Copy-Item C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db.bak `
          C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot\alumni_bot.db
```

3. Verify the restored database is healthy:

```
cd C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot
python -c "import sqlite3; conn = sqlite3.connect('alumni_bot.db'); print(conn.execute('PRAGMA integrity_check;').fetchone()[0]); conn.close()"
```

Confirm the output is `ok` before continuing.

4. Show recent commits:

```
cd C:\Users\andre\Documents\SCLK-Notifier
git log --oneline
```

5. Switch to a known-good commit:

```
git switch --detach <known-good-commit>
```

6. Run from that commit:

```
cd discord-alumni-reminder-bot
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests
python bot.py
```

7. After testing, return to a branch:

```
cd C:\Users\andre\Documents\SCLK-Notifier
git switch main
```

## Notes

- The bot only runs while `python bot.py` is running.
- If the PC sleeps, shuts down, loses internet, or the process stops, reminders will not send.
- Choose an always-on host before adding true automatic deployment.