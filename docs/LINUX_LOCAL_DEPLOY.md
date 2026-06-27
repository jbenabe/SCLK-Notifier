# Linux Deploy And Redeploy Guide

This guide gets SCLK Notifier running on a Linux machine, including a Raspberry Pi.
It covers first-time setup, running the bot manually, and configuring it as a systemd
service so it starts automatically on boot and restarts on crash.

## Prerequisites

Ensure the following are installed before starting:

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv
```

Verify Python 3.8 or higher is available:

```
python3 --version
```

---

## First-Time Setup

1. Open a terminal.

2. Clone the repo:

```
cd ~
git clone https://github.com/award73/SCLK-Notifier.git
cd SCLK-Notifier/discord-alumni-reminder-bot
```

   If the repo is already cloned:

```
cd ~/SCLK-Notifier/discord-alumni-reminder-bot
```

3. Create and activate a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

4. Install dependencies:

```
pip install -r requirements.txt
```

5. Create `.env`:

```
cp .env.example .env
```

6. Fill in `.env` using a text editor:

```
nano .env
```

   Set the following values:

```
DISCORD_TOKEN=
GUILD_ID=
ANNOUNCEMENT_CHANNEL_ID=
ALUMNI_ROLE_ID=
TIMEZONE=America/New_York
DISCORD_BOT_PERMISSIONS=8462797117848576
REMINDERS_ENABLED=true
```

   Save and exit with `Ctrl+O`, then `Enter`, then `Ctrl+X`.

   Do not commit `.env`.

7. Run local checks:

```
python3 -m py_compile bot.py
python3 -m unittest discover -s tests
```

8. Start the bot manually to confirm it works:

```
python3 bot.py
```

9. Confirm the logs show the bot logged in and synced slash commands.

   Press `Ctrl+C` to stop the bot before continuing to the systemd setup.

---

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

---

## Running as a systemd Service (Recommended for Always-On Hosting)

Setting up a systemd service ensures the bot starts automatically when the machine boots
and restarts automatically if it crashes.

### 1. Find your Python and project paths

While inside the virtual environment, run:

```
which python3
```

This will output something like `/home/pi/SCLK-Notifier/discord-alumni-reminder-bot/.venv/bin/python3`.
Note this path — you will use it in the service file.

Also note your full project path:

```
pwd
```

Expected output: `/home/pi/SCLK-Notifier/discord-alumni-reminder-bot`

### 2. Create the systemd service file

```
sudo nano /etc/systemd/system/sclk-notifier.service
```

Paste the following, replacing `pi` with your actual Linux username and adjusting
paths if your repo is cloned somewhere other than `~/SCLK-Notifier`:

```
[Unit]
Description=SCLK Notifier Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SCLK-Notifier/discord-alumni-reminder-bot
ExecStart=/home/pi/SCLK-Notifier/discord-alumni-reminder-bot/.venv/bin/python3 bot.py
Restart=on-failure
RestartSec=10
EnvironmentFile=/home/pi/SCLK-Notifier/discord-alumni-reminder-bot/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save and exit with `Ctrl+O`, then `Enter`, then `Ctrl+X`.

### 3. Enable and start the service

Reload systemd to pick up the new file:

```
sudo systemctl daemon-reload
```

Enable the service to start on boot:

```
sudo systemctl enable sclk-notifier
```

Start the service now:

```
sudo systemctl start sclk-notifier
```

### 4. Confirm the service is running

```
sudo systemctl status sclk-notifier
```

You should see `Active: active (running)`. If not, check the logs section below.

---

## Viewing Logs

To see live log output from the bot:

```
sudo journalctl -u sclk-notifier -f
```

To see recent log output (last 100 lines):

```
sudo journalctl -u sclk-notifier -n 100
```

To see logs since the last boot:

```
sudo journalctl -u sclk-notifier -b
```

Press `Ctrl+C` to exit log tailing.

---

## Database Integrity And Backups

`alumni_bot.db` is a local SQLite file stored on disk. It is completely independent of
the bot code and is never touched by Git. Updating `bot.py`, pulling new code, or
restarting the service will not affect the database file.

The database is only at risk if:

- You manually delete it.
- The SD card corrupts due to a power loss mid-write (see the Pi notes at the bottom).
- A code change drops or recreates a database table without preserving existing rows.

### Manual backup before any code change

Before pulling new code, take a snapshot of the database:

```
cp ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db \
   ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db.bak
```

### Restore from backup

If something goes wrong after a code update:

```
sudo systemctl stop sclk-notifier
cp ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db.bak \
   ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db
sudo systemctl start sclk-notifier
```

### Verify database integrity

To check that the database file is not corrupted:

```
sqlite3 ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db "PRAGMA integrity_check;"
```

A healthy database responds with `ok`. If you see errors, restore from your backup.

If `sqlite3` is not installed:

```
sudo apt install -y sqlite3
```

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

To automatically back up the database every day at 2am, add a cron job:

```
crontab -e
```

Add this line at the bottom:

```
0 2 * * * cp ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db.bak
```

Save and exit. This overwrites the previous `.bak` file daily, giving you a rolling
24-hour safety net.

---

## Redeploy Existing Bot

Use this when new code has been merged or you want to test a branch.

1. Stop the running service:

```
sudo systemctl stop sclk-notifier
```

2. Back up the database before making any changes:

```
cp ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db \
   ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db.bak
```

3. Update the repo:

```
cd ~/SCLK-Notifier
git switch main
git pull
```

   To test a review branch instead:

```
git switch codex/incremental-prs
git pull
```

4. Activate the venv and update dependencies:

```
cd discord-alumni-reminder-bot
source .venv/bin/activate
pip install -r requirements.txt
```

5. Run tests:

```
python3 -m py_compile bot.py
python3 -m unittest discover -s tests
```

6. Confirm `.env` still has the correct Discord values, `DISCORD_BOT_PERMISSIONS=8462797117848576`, and `REMINDERS_ENABLED=true`.

7. Verify database integrity:

```
sqlite3 alumni_bot.db "PRAGMA integrity_check;"
```

Confirm the output is `ok` before continuing.

8. Restart the service:

```
sudo systemctl start sclk-notifier
```

9. Confirm it is running:

```
sudo systemctl status sclk-notifier
```

10. In Discord, run `/event_sync`, `/event_list`, `/next_meeting`, `/agenda_add`, and `/agenda`.

---

## Emergency Stop

To stop public reminder posts immediately:

**Option 1 — Stop the bot process entirely:**

```
sudo systemctl stop sclk-notifier
```

To also prevent it from restarting on boot:

```
sudo systemctl disable sclk-notifier
```

**Option 2 — Keep the bot alive but disable reminder posts:**

Edit `.env`:

```
nano /home/pi/SCLK-Notifier/discord-alumni-reminder-bot/.env
```

Set:

```
REMINDERS_ENABLED=false
```

Then restart the service to apply the change:

```
sudo systemctl restart sclk-notifier
```

---

## Temporary Rollback

Use this if the latest code fails and you need to fall back to a known-good commit.

1. Stop the service:

```
sudo systemctl stop sclk-notifier
```

2. Restore the database backup taken before the failed deploy:

```
cp ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db.bak \
   ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db
```

3. Verify the restored database is healthy:

```
sqlite3 ~/SCLK-Notifier/discord-alumni-reminder-bot/alumni_bot.db "PRAGMA integrity_check;"
```

Confirm the output is `ok` before continuing.

4. Show recent commits:

```
cd ~/SCLK-Notifier
git log --oneline
```

5. Switch to a known-good commit:

```
git switch --detach <known-good-commit>
```

6. Run from that commit:

```
cd discord-alumni-reminder-bot
source .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 bot.py
```

7. After confirming it works, set it up as the service again:

```
sudo systemctl start sclk-notifier
```

8. To return to the main branch later:

```
cd ~/SCLK-Notifier
git switch main
```

---

## Preventing the Pi from Sleeping

If running on a Raspberry Pi, ensure it does not enter sleep or suspend mode, which
would stop the bot.

Check the current sleep setting:

```
sudo systemctl status sleep.target
```

Disable sleep, suspend, and hibernate:

```
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

---

## Notes

- The bot only runs while the systemd service is active or `python3 bot.py` is running manually.
- If the machine loses internet, reboots, or loses power, the systemd service will restart the bot automatically once the network is back up.
- Keep `.env`, bot tokens, logs, and `alumni_bot.db` private and never commit them.
- `alumni_bot.db` is never touched by Git or by pulling new code. It persists across all deploys automatically.
- Always back up `alumni_bot.db` before pulling code changes and always run `PRAGMA integrity_check` before restarting the service.
- If running on a Pi with an SD card, consider moving the repo and database to a USB drive to reduce SD card wear and lower the risk of corruption on unexpected power loss.