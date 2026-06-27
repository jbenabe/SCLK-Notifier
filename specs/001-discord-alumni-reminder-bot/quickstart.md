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
   TIMEZONE=America/New_York
   EVENT_NAME_FILTER=Alumni Association Monthly Meeting
   ```

5. Run the bot:

   ```powershell
   python bot.py
   ```

## Discord Smoke Test

1. Confirm the bot logs in and reports slash command sync.
2. Create a future Discord Scheduled Event in the configured guild.
3. Ensure the event name contains the exact configured `EVENT_NAME_FILTER` text, ignoring case.
4. Run `/event_sync` as a Manage Server admin.
5. Run `/event_list` and confirm the event appears.
6. Run `/next_meeting` as a normal member.
7. Run `/agenda_add item:"Test agenda item"`.
8. Run `/agenda` and confirm the item appears.

## Troubleshooting Checklist

### `/event_sync` Finds Zero Events

- Confirm the event is in the same server as `GUILD_ID`.
- Confirm the event is scheduled for the future.
- Confirm the event status is scheduled or active.
- Confirm the event name contains `EVENT_NAME_FILTER`.
- Confirm the bot has access to view/fetch server scheduled events.

### Command Fails With `Unknown interaction`

- This usually means the bot did not acknowledge the slash command quickly enough.
- Commands that fetch Discord data should defer before doing slow work.
- Check logs around the command timestamp for a Discord API delay or exception.

### Reminder Does Not Send

- Confirm the bot process is still running.
- Confirm the event is tracked in `/event_list`.
- Confirm the reminder flag has not already been marked sent.
- Confirm `ANNOUNCEMENT_CHANNEL_ID` points to a channel where the bot can send messages.
- Confirm the bot can mention the configured alumni role.
