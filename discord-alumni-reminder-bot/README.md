# Discord Alumni Reminder Bot

A simple Discord bot for alumni association meeting reminders and agenda collection.

Native Discord Scheduled Events are the source of truth. Admins create and edit meetings using Discord's normal Event UI, and this bot reads those events, tracks reminder state locally in SQLite, and posts custom reminders to the configured announcement channel.

The bot does not create Discord Events, manage RSVPs, or sync with Google Calendar.

## What It Does

- Reads native Discord Scheduled Events from one configured server
- Tracks upcoming scheduled or active Discord events
- Sends reminders to the configured alumni role 7 days before, 1 day before, and around 4:00 PM local time on the event day
- Includes the Discord event link in reminder messages
- Lets members add agenda items without copying IDs
- Stores reminder flags and agenda items in `alumni_bot.db`
- Uses guild-specific slash command sync so commands appear quickly
- Keeps member-triggered responses ephemeral and applies local safety controls to reduce bot-amplified spam

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

The bot automatically attaches the agenda item to the next upcoming visible Discord event. Members do not need to know event IDs, server IDs, channel IDs, role IDs, or database IDs.

## For Admins

Admin commands require the Discord **Manage Server** permission.

1. Create the recurring alumni meeting using Discord's normal Event UI.
2. Run:

```text
/event_sync
```

3. Confirm the bot sees the event:

```text
/event_list
```

After that, the bot handles reminders automatically while it is running.

Admin commands:

| Command | Description |
| --- | --- |
| `/event_sync` | Fetches visible Discord Scheduled Events and tracks them locally. |
| `/event_list` | Shows upcoming tracked events, reminder status, agenda count, event links, and admin-only technical details. |
| `/event_reset_reminders` | Resets reminder flags for the selected meeting, or the next meeting by default. |
| `/test_notify` | Posts a production-shaped test notification mentioning only the admin who ran it. |
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
DISCORD_BOT_PERMISSIONS=8462797117848576
REMINDERS_ENABLED=true
```

Field meanings:

- `DISCORD_TOKEN`: Discord bot token.
- `GUILD_ID`: Discord server ID.
- `ANNOUNCEMENT_CHANNEL_ID`: Channel where reminders should be posted.
- `ALUMNI_ROLE_ID`: Role ID for the alumni role to ping.
- `TIMEZONE`: Default timezone for readable admin labels.
- `DISCORD_BOT_PERMISSIONS`: Bot invite permission integer. Use `8462797117848576` when regenerating the OAuth2 invite URL.
- `REMINDERS_ENABLED`: Optional emergency stop for public reminder posting. Defaults to `true`; set to `false` and restart the bot to prevent reminder posts.

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

Member-submitted agenda text is displayed with Discord mentions and markdown neutralized so compromised accounts cannot use the bot to ping roles, `@everyone`, `@here`, users, or channels.

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
8. Use this bot permissions integer:
   - `8462797117848576`
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
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation because of execution policy, enable it only for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
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

- It syncs before slash command responses and tracks any upcoming scheduled or active Discord event in the configured server.
- It sends a 7-day reminder when the event is 7 days away or less.
- It sends a 1-day reminder when the event is 1 day away or less.
- It sends a day-of reminder around 4:00 PM in `TIMEZONE` if the event has not started.
- It marks each reminder as sent in SQLite.
- It can be prevented from posting public reminders by setting `REMINDERS_ENABLED=false`.
- Restarting the bot does not resend reminders already marked sent.
- If the bot was offline at the exact reminder time, it sends the reminder after it comes back online as long as the event has not already started.
- It does not send reminders after the event has started.

Reminder messages include:

- Alumni role ping
- Meeting time using Discord timestamp formatting
- Native Discord event link
- Current agenda items, if any
- RSVP prompt for the native Discord event

## Safe Notification Testing

Admins can post a test notification without pinging the alumni role:

```text
/test_notify
```

This posts the same production-shaped notification body to the announcement channel, but mentions only the admin who ran the command.

## Agenda Behavior

Members add agenda items with:

```text
/agenda_add item:"Your topic here"
```

Validation rules:

- The bot must be able to find an upcoming visible Discord event.
- The event must not have started.
- Agenda items must not be empty.
- Agenda items must be 500 characters or fewer.
- Agenda submissions are rate limited per user.
- Each user may add up to 3 active items per meeting.
- Each meeting may have up to 25 active agenda items.
- Repeated rejected write attempts can temporarily block more agenda writes.
- Displayed agenda text is sanitized so mentions and markdown cannot create pings or deceptive formatting.

Admins can remove agenda items with `/agenda_remove`. Removed items are marked inactive in SQLite rather than deleted.

## Abuse Controls And Emergency Stop

This bot assumes member accounts may occasionally be compromised. To avoid bot-amplified spam:

- Member command responses are ephemeral.
- Member agenda writes have cooldowns and quotas.
- Reminder agenda output is capped and truncated when needed.
- Abuse-relevant events such as rate-limit hits, denied permissions, agenda removals, reminder sends, and send failures are stored in SQLite.

To stop public posting immediately, stop the bot process or remove its Send Messages permission in the announcement channel. To keep the process running but disable reminder posts, set:

```text
REMINDERS_ENABLED=false
```

Then restart the bot.

## Troubleshooting

If `/event_sync` finds no upcoming events, check:

- The event is in the configured server.
- The event is scheduled for the future.
- The event status is scheduled or active.
- The bot can view/fetch server scheduled events.

If the bot logs `Fetched 0 events`, Discord returned no scheduled events to the bot. Check that the event is in the same server as `GUILD_ID`, that the bot is invited to that server, and that the event is visible to the bot. Recurring events should still be created and edited in Discord; the bot relies on Discord to expose the next concrete scheduled occurrence.

If a slash command times out or Discord reports `Unknown interaction`, the command likely took too long before acknowledgement. Slow commands now defer ephemerally before fetching Discord data; check logs for Discord API errors around the command time.

Warnings about `PyNaCl`, `davey`, or voice support can be ignored. This bot does not use Discord voice.

## Discord Smoke Test

1. Start the bot and confirm slash command sync appears in the logs.
2. Create a future Discord Scheduled Event in the configured server.
3. Run `/event_sync` as an admin and confirm the event is tracked.
4. Run `/next_meeting`, `/agenda_add`, and `/agenda`.
5. Run `/test_notify` and confirm the announcement channel message mentions only you.
6. Add a test agenda item containing `@everyone`, `@here`, a role mention, a user mention, a channel mention, a link, and markdown. Confirm no ping occurs when viewing `/agenda`.
7. Repeatedly submit agenda items as the same test user and confirm cooldowns or quotas stop additional writes without public messages.
8. Set `REMINDERS_ENABLED=false`, restart, and confirm reminder checks do not post public reminders.

## Hosting Notes

The bot only works while the Python process is running. If you run it on a laptop, reminders stop when the laptop sleeps, shuts down, loses internet, or the script closes.

For always-on use, host it later on a service such as Railway, a paid Render instance, Fly.io, or a cheap VPS.

You do not need Docker for the MVP.
