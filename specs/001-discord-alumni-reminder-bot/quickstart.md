# Quickstart: Discord Alumni Reminder Bot

## Local Setup

1. Open the project directory:

   ```powershell
   cd C:\Users\andre\Documents\SCLK-Notifier\discord-alumni-reminder-bot
   ```

2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create `.env` from `.env.example` and fill in Discord values:

   ```text
   DISCORD_TOKEN=
   GUILD_ID=
   ANNOUNCEMENT_CHANNEL_ID=
   ALUMNI_ROLE_ID=
   ALUMNI_BOARD_ROLE_ID=
   TIMEZONE=America/New_York
   REMINDERS_ENABLED=true
   ```

5. Run the bot:

   ```powershell
   python bot.py
   ```

## Discord Smoke Test

1. Confirm the bot logs in and reports slash command sync.
2. Create a future Discord Scheduled Event in the configured guild.
3. Run `/event_sync` as a user with the configured Alumni Board role.
4. Run `/event_list` and confirm the event appears.
5. Run `/next_meeting` as a normal member.
6. Run `/agenda_add item:"Test agenda item"`.
7. Run `/agenda` and confirm the item appears.

## Troubleshooting Checklist

### `/event_sync` Finds Zero Events

- Confirm the event is in the same server as `GUILD_ID`.
- Confirm the event is scheduled for the future.
- Confirm the event status is scheduled or active.
- Confirm the bot has access to view/fetch server scheduled events.

### Command Fails With `Unknown interaction`

- This usually means the bot did not acknowledge the slash command quickly enough.
- Commands that fetch Discord data should defer before doing slow work.
- Check logs around the command timestamp for a Discord API delay or exception.

### Reminder Does Not Send

- Confirm the bot process is still running.
- Confirm the event is tracked in `/event_list`.
- Confirm the reminder flag has not already been marked sent.
- Confirm `ANNOUNCEMENT_CHANNEL_ID` points to the intended notification channel, currently `meeting` or `alumni-announcements`.
- Confirm the bot has View Channel and Send Messages access in `ANNOUNCEMENT_CHANNEL_ID`.
- Confirm the bot can mention the configured alumni role.
- Confirm elevated command users have the configured Alumni Board role.

### Emergency Stop For Public Posting

- Stop the bot process to immediately prevent all future public posts.
- Remove or restrict the bot's Send Messages permission in the announcement channel if the process cannot be reached.
- Set `REMINDERS_ENABLED=false` and restart the bot to keep the process running while skipping public reminder posts.

### Abuse Safety Smoke Test

- Add a test agenda item containing `@everyone`, `@here`, a role mention, a user mention, a channel mention, a link, and markdown.
- Confirm `/agenda` displays the item without pinging anyone.
- Confirm reminder output either sanitizes the item safely or truncates it while preserving the meeting time and Discord event link.
- Repeatedly submit agenda items as the same test user and confirm cooldowns or quotas stop additional writes without public messages.
