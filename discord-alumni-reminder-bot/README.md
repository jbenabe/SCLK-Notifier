# Discord Alumni Reminder Bot

A simple Discord bot for alumni association meeting reminders and agenda collection.

Native Discord Scheduled Events are the source of truth. Admins create and edit meetings using Discord's normal Event UI, and this bot reads those events, tracks reminder state locally in SQLite, and posts custom reminders to the configured announcement channel.

The bot does not create Discord Events, manage RSVPs, or sync with Google Calendar.

## What It Does

- Reads native Discord Scheduled Events from one configured server
- Tracks events whose names contain `EVENT_NAME_FILTER`
- Sends reminders to the configured alumni role 7 days before and 1 hour before each tracked event
- Includes the Discord event link in reminder messages
- Lets members add agenda items without copying IDs
- Stores reminder flags and agenda items in `alumni_bot.db`
- Uses guild-specific slash command sync so commands appear quickly

## For Server Members

Normal members only need these commands:

```text
/next_meeting
/agenda
/agenda_add item:"Your topic here"
```

Use `/next_meeting` to see the next alumni meeting.

Use `/agenda` to view the current agenda for the next meeting.

Use `/agenda_add` to add an agenda item:

```text
/agenda_add item:"Discuss Derby Days fundraiser planning"
```

The bot automatically attaches the agenda item to the next upcoming matching Discord event. Members do not need to know event IDs, server IDs, channel IDs, role IDs, or database IDs.

## For Admins

Admin commands require the Discord **Manage Server** permission.

1. Create the recurring alumni meeting using Discord's normal Event UI.
2. Make sure the event name contains the configured `EVENT_NAME_FILTER`.
3. Run:

```text
/event_sync
```

4. Confirm the bot sees the event:

```text
/event_list
```

After that, the bot handles reminders automatically while it is running.

Admin commands:

| Command | Description |
| --- | --- |
| `/event_sync` | Fetches matching Discord Scheduled Events and tracks them locally. |
| `/event_list` | Shows upcoming tracked events, reminder status, agenda count, event links, and admin-only technical details. |
| `/event_reset_reminders` | Resets reminder flags for the selected meeting, or the next meeting by default. |
| `/agenda_remove` | Removes an agenda item. Uses autocomplete for agenda item choices where available. |

Use `/event_reset_reminders` if an event time changes and you want the bot to be able to send reminders again.

## Environment Variables

Create a local `.env` file:

```text
DISCORD_TOKEN=
GUILD_ID=
ANNOUNCEMENT_CHANNEL_ID=
ALUMNI_ROLE_ID=
TIMEZONE=America/New_York
EVENT_NAME_FILTER=Alumni Association Monthly Meeting
```

Field meanings:

- `DISCORD_TOKEN`: Discord bot token.
- `GUILD_ID`: Discord server ID.
- `ANNOUNCEMENT_CHANNEL_ID`: Channel where reminders should be posted.
- `ALUMNI_ROLE_ID`: Role ID for the alumni role to ping.
- `TIMEZONE`: Default timezone for readable admin labels.
- `EVENT_NAME_FILTER`: Case-insensitive text used to identify alumni meeting Discord Events.

Keep `.env` private. Do not commit it.

## Bot Permissions

The bot should only need:

- Send Messages
- Use Slash Commands
- Read Message History
- Mention Roles
- Access to view/fetch server scheduled events

It does not need Administrator permission.

When reminders are sent, the bot allows only role mentions so the configured alumni role can be pinged safely.

## Create and Invite the Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Select **New Application**.
3. Open **Bot** in the left sidebar.
4. Select **Add Bot**.
5. Copy the bot token into `.env` as `DISCORD_TOKEN`.
6. Open **OAuth2** and then **URL Generator**.
7. Select scopes:
   - `bot`
   - `applications.commands`
8. Select the bot permissions listed above.
9. Open the generated URL and invite the bot to your server.

## Copy Discord IDs

Enable Developer Mode:

1. Open Discord.
2. Go to **User Settings**.
3. Open **Advanced**.
4. Enable **Developer Mode**.

Copy IDs:

- Server ID: right-click the server name and choose **Copy Server ID**.
- Channel ID: right-click the reminder channel and choose **Copy Channel ID**.
- Role ID: go to server settings roles, right-click the alumni role, and choose **Copy Role ID**.

These IDs are only needed in `.env`; normal members never need them.

## Install Locally

Create a virtual environment:

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\activate
```

Activate on Mac/Linux:

```bash
source .venv/bin/activate
```

Install requirements:

```bash
pip install -r requirements.txt
```

The `tzdata` package is included so Python's `zoneinfo` module can resolve `America/New_York` reliably on Windows.

Run the bot:

```bash
python bot.py
```

The bot creates `alumni_bot.db` automatically the first time it starts.

## Reminder Behavior

The bot syncs Discord Scheduled Events every 5 minutes and checks reminders every 60 seconds.

- It tracks scheduled or active Discord events whose names contain `EVENT_NAME_FILTER`.
- It sends a 7-day reminder when the event is 7 days away or less.
- It sends a 1-hour reminder when the event is 1 hour away or less.
- It marks each reminder as sent in SQLite.
- Restarting the bot does not resend reminders already marked sent.
- If the bot was offline at the exact reminder time, it sends the reminder after it comes back online as long as the event has not already started.
- It does not send reminders after the event has started.

Reminder messages include:

- Alumni role ping
- Meeting time using Discord timestamp formatting
- Native Discord event link
- Current agenda items, if any
- RSVP prompt for the native Discord event

## Agenda Behavior

Members add agenda items with:

```text
/agenda_add item:"Your topic here"
```

Validation rules:

- The bot must be able to find an upcoming matching Discord event.
- The event must not have started.
- Agenda items must not be empty.
- Agenda items must be 500 characters or fewer.

Admins can remove agenda items with `/agenda_remove`. Removed items are marked inactive in SQLite rather than deleted.

## Hosting Notes

The bot only works while the Python process is running. If you run it on a laptop, reminders stop when the laptop sleeps, shuts down, loses internet, or the script closes.

For always-on use, host it later on a service such as Railway, a paid Render instance, Fly.io, or a cheap VPS.

You do not need Docker for the MVP.
