import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv


DB_PATH = Path(__file__).with_name("alumni_bot.db")
AGENDA_ITEM_LIMIT = 500

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("alumni_reminder_bot")


@dataclass(frozen=True)
class Config:
    discord_token: str
    guild_id: int
    announcement_channel_id: int
    alumni_role_id: int
    timezone_name: str
    timezone: ZoneInfo
    event_name_filter: str


def load_config() -> Config:
    load_dotenv()

    required_vars = [
        "DISCORD_TOKEN",
        "GUILD_ID",
        "ANNOUNCEMENT_CHANNEL_ID",
        "ALUMNI_ROLE_ID",
        "TIMEZONE",
        "EVENT_NAME_FILTER",
    ]
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing required .env variables: {', '.join(missing)}")

    try:
        timezone_name = os.environ["TIMEZONE"]
        bot_timezone = ZoneInfo(timezone_name)
        return Config(
            discord_token=os.environ["DISCORD_TOKEN"],
            guild_id=int(os.environ["GUILD_ID"]),
            announcement_channel_id=int(os.environ["ANNOUNCEMENT_CHANNEL_ID"]),
            alumni_role_id=int(os.environ["ALUMNI_ROLE_ID"]),
            timezone_name=timezone_name,
            timezone=bot_timezone,
            event_name_filter=os.environ["EVENT_NAME_FILTER"].strip(),
        )
    except ValueError as exc:
        raise ValueError("GUILD_ID, ANNOUNCEMENT_CHANNEL_ID, and ALUMNI_ROLE_ID must be numeric IDs.") from exc
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid TIMEZONE value: {os.environ['TIMEZONE']}") from exc


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tracked_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_event_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                start_time_utc TEXT NOT NULL,
                end_time_utc TEXT,
                location TEXT,
                status TEXT,
                seven_day_sent INTEGER NOT NULL DEFAULT 0,
                one_hour_sent INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                first_seen_at_utc TEXT NOT NULL,
                last_synced_at_utc TEXT NOT NULL
            )
            """
        )

        agenda_columns = conn.execute("PRAGMA table_info(agenda_items)").fetchall()
        if agenda_columns and "discord_event_id" not in {row["name"] for row in agenda_columns}:
            logger.info("Renaming legacy agenda_items table to agenda_items_legacy.")
            conn.execute("ALTER TABLE agenda_items RENAME TO agenda_items_legacy")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agenda_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_event_id TEXT NOT NULL,
                item_text TEXT NOT NULL,
                submitted_by_user_id TEXT NOT NULL,
                submitted_by_display_name TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at_utc TEXT NOT NULL,
                FOREIGN KEY (discord_event_id) REFERENCES tracked_events(discord_event_id)
            )
            """
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def datetime_to_db(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def datetime_from_db(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def optional_datetime_to_db(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return datetime_to_db(value)


def to_discord_timestamp(value: datetime, style: str = "F") -> str:
    return f"<t:{int(value.timestamp())}:{style}>"


def event_status_name(status: object) -> str:
    return getattr(status, "name", str(status)).replace("_", " ").title()


def event_is_eligible(event: discord.ScheduledEvent, config: Config) -> bool:
    if not event.start_time:
        return False

    status = event_status_name(event.status).lower()
    if status not in {"scheduled", "active"}:
        return False

    if event.start_time.astimezone(timezone.utc) <= utc_now():
        return False

    return config.event_name_filter.lower() in event.name.lower()


def event_link(guild_id: int, discord_event_id: str) -> str:
    return f"https://discord.com/events/{guild_id}/{discord_event_id}"


def upsert_tracked_event(event: discord.ScheduledEvent) -> None:
    now = datetime_to_db(utc_now())
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO tracked_events (
                discord_event_id, name, description, start_time_utc, end_time_utc,
                location, status, first_seen_at_utc, last_synced_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(discord_event_id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                start_time_utc = excluded.start_time_utc,
                end_time_utc = excluded.end_time_utc,
                location = excluded.location,
                status = excluded.status,
                active = 1,
                last_synced_at_utc = excluded.last_synced_at_utc
            """,
            (
                str(event.id),
                event.name,
                event.description,
                datetime_to_db(event.start_time),
                optional_datetime_to_db(event.end_time),
                event.location,
                event_status_name(event.status),
                now,
                now,
            ),
        )


def mark_unseen_events_inactive(seen_event_ids: set[str]) -> None:
    with get_db() as conn:
        if seen_event_ids:
            placeholders = ",".join("?" for _ in seen_event_ids)
            conn.execute(
                f"UPDATE tracked_events SET active = 0 WHERE active = 1 AND discord_event_id NOT IN ({placeholders})",
                tuple(seen_event_ids),
            )
        else:
            conn.execute("UPDATE tracked_events SET active = 0 WHERE active = 1")


def mark_started_events_inactive() -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE tracked_events SET active = 0 WHERE active = 1 AND start_time_utc <= ?",
            (datetime_to_db(utc_now()),),
        )


def get_tracked_event(discord_event_id: str) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM tracked_events WHERE discord_event_id = ? AND active = 1",
            (discord_event_id,),
        ).fetchone()


def get_next_tracked_event() -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM tracked_events
            WHERE active = 1 AND start_time_utc > ?
            ORDER BY start_time_utc ASC
            LIMIT 1
            """,
            (datetime_to_db(utc_now()),),
        ).fetchone()


def list_tracked_events() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT
                tracked_events.*,
                COUNT(agenda_items.id) AS agenda_count
            FROM tracked_events
            LEFT JOIN agenda_items
                ON agenda_items.discord_event_id = tracked_events.discord_event_id
                AND agenda_items.active = 1
            WHERE tracked_events.active = 1
              AND tracked_events.start_time_utc > ?
            GROUP BY tracked_events.id
            ORDER BY tracked_events.start_time_utc ASC
            """,
            (datetime_to_db(utc_now()),),
        ).fetchall()


def reset_reminder_flags(discord_event_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE tracked_events
            SET seven_day_sent = 0, one_hour_sent = 0
            WHERE discord_event_id = ? AND active = 1
            """,
            (discord_event_id,),
        )
        return cursor.rowcount > 0


def mark_reminder_sent(discord_event_id: str, reminder_column: str) -> None:
    if reminder_column not in {"seven_day_sent", "one_hour_sent"}:
        raise ValueError("Invalid reminder column.")

    with get_db() as conn:
        conn.execute(
            f"UPDATE tracked_events SET {reminder_column} = 1 WHERE discord_event_id = ?",
            (discord_event_id,),
        )


def add_agenda_item(
    discord_event_id: str,
    item_text: str,
    submitted_by_user_id: int,
    submitted_by_display_name: str,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agenda_items (
                discord_event_id, item_text, submitted_by_user_id,
                submitted_by_display_name, created_at_utc
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                discord_event_id,
                item_text.strip(),
                str(submitted_by_user_id),
                submitted_by_display_name,
                datetime_to_db(utc_now()),
            ),
        )
        return int(cursor.lastrowid)


def list_agenda_items(discord_event_id: str) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM agenda_items
            WHERE discord_event_id = ? AND active = 1
            ORDER BY created_at_utc ASC
            """,
            (discord_event_id,),
        ).fetchall()


def remove_agenda_item(agenda_item_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE agenda_items SET active = 0 WHERE id = ? AND active = 1",
            (agenda_item_id,),
        )
        return cursor.rowcount > 0


def format_agenda_lines(discord_event_id: str, include_submitters: bool = False) -> list[str]:
    items = list_agenda_items(discord_event_id)
    lines = []
    for index, row in enumerate(items, start=1):
        if include_submitters:
            submitter = row["submitted_by_display_name"] or "Unknown"
            lines.append(f"{index}. {row['item_text']} - submitted by {submitter}")
        else:
            lines.append(f"{index}. {row['item_text']}")
    return lines


def user_can_manage_guild(interaction: discord.Interaction) -> bool:
    permissions = getattr(interaction.user, "guild_permissions", None)
    return bool(permissions and permissions.manage_guild)


async def require_manage_guild(interaction: discord.Interaction) -> bool:
    if user_can_manage_guild(interaction):
        return True

    logger.info("Permission denied for user %s on admin command.", interaction.user.id)
    await interaction.response.send_message(
        "Only server admins can use this command.",
        ephemeral=True,
    )
    return False


def short_event_label(row: sqlite3.Row, config: Config) -> str:
    start_time = datetime_from_db(row["start_time_utc"]).astimezone(config.timezone)
    return f"{row['name']} - {start_time:%b %d, %Y at %I:%M %p}"


class AlumniReminderBot(commands.Bot):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.guild_object = discord.Object(id=config.guild_id)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=self.guild_object)
        synced = await self.tree.sync(guild=self.guild_object)
        logger.info("Synced %s slash commands to guild %s.", len(synced), self.config.guild_id)
        self.event_sync_loop.start()
        self.reminder_loop.start()

    async def on_ready(self) -> None:
        logger.info("Logged in as %s.", self.user)

    async def get_configured_guild(self) -> Optional[discord.Guild]:
        guild = self.get_guild(self.config.guild_id)
        if guild:
            return guild

        try:
            return await self.fetch_guild(self.config.guild_id)
        except discord.DiscordException:
            logger.exception("Could not fetch configured guild %s.", self.config.guild_id)
            return None

    async def get_announcement_channel(self) -> Optional[discord.abc.Messageable]:
        channel = self.get_channel(self.config.announcement_channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(self.config.announcement_channel_id)
            except discord.DiscordException:
                logger.exception("Could not fetch announcement channel %s.", self.config.announcement_channel_id)
                return None

        if not hasattr(channel, "send"):
            logger.error("Configured announcement channel %s cannot receive messages.", self.config.announcement_channel_id)
            return None

        return channel

    async def sync_events(self) -> tuple[int, list[discord.ScheduledEvent]]:
        guild = await self.get_configured_guild()
        if guild is None:
            return 0, []

        try:
            scheduled_events = await guild.fetch_scheduled_events()
        except discord.DiscordException:
            logger.exception("Could not fetch scheduled events for guild %s.", self.config.guild_id)
            return 0, []

        matching_events = [event for event in scheduled_events if event_is_eligible(event, self.config)]
        seen_event_ids = {str(event.id) for event in matching_events}

        for event in matching_events:
            upsert_tracked_event(event)
            logger.info("Tracked Discord event %s: %s.", event.id, event.name)

        mark_unseen_events_inactive(seen_event_ids)
        mark_started_events_inactive()
        logger.info("Event sync complete. Found %s matching events.", len(matching_events))
        return len(matching_events), matching_events

    async def get_next_event_with_sync(self) -> Optional[sqlite3.Row]:
        event = get_next_tracked_event()
        if event:
            return event

        await self.sync_events()
        return get_next_tracked_event()

    async def send_reminder(self, event: sqlite3.Row, reminder_type: str) -> bool:
        start_time = datetime_from_db(event["start_time_utc"])
        role_mention = f"<@&{self.config.alumni_role_id}>"
        timestamp = to_discord_timestamp(start_time)
        link = event_link(self.config.guild_id, event["discord_event_id"])
        agenda_lines = format_agenda_lines(event["discord_event_id"])

        if reminder_type == "seven_day":
            lines = [
                f"{role_mention} Reminder: {event['name']} is in 7 days.",
                "",
                f"Meeting time: {timestamp}",
                "",
                "Discord event:",
                link,
                "",
            ]
            if agenda_lines:
                lines.extend(["Current agenda:", *agenda_lines, ""])
            else:
                lines.extend(["No agenda items have been added yet.", ""])
            lines.extend(
                [
                    "Add an agenda item with:",
                    '/agenda_add item:"Your topic here"',
                    "",
                    "Please RSVP on the Discord event.",
                ]
            )
        else:
            lines = [
                f"{role_mention} Reminder: {event['name']} starts in 1 hour.",
                "",
                f"Meeting time: {timestamp}",
                "",
                "Discord event:",
                link,
            ]
            if agenda_lines:
                lines.extend(["", "Agenda:", *agenda_lines])
            else:
                lines.extend(["", "No agenda items have been added yet."])

        channel = await self.get_announcement_channel()
        if channel is None:
            return False

        try:
            await channel.send(
                "\n".join(lines),
                allowed_mentions=discord.AllowedMentions(roles=True, everyone=False, users=False),
            )
            return True
        except discord.DiscordException:
            logger.exception("Failed to send %s reminder for event %s.", reminder_type, event["discord_event_id"])
            return False

    @tasks.loop(minutes=5)
    async def event_sync_loop(self) -> None:
        await self.sync_events()

    @event_sync_loop.before_loop
    async def before_event_sync_loop(self) -> None:
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def reminder_loop(self) -> None:
        await check_reminders(self)

    @reminder_loop.before_loop
    async def before_reminder_loop(self) -> None:
        await self.wait_until_ready()


async def check_reminders(bot: AlumniReminderBot) -> None:
    now = utc_now()
    with get_db() as conn:
        events = conn.execute(
            """
            SELECT * FROM tracked_events
            WHERE active = 1
              AND start_time_utc > ?
              AND (seven_day_sent = 0 OR one_hour_sent = 0)
            ORDER BY start_time_utc ASC
            """,
            (datetime_to_db(now),),
        ).fetchall()

    for event in events:
        discord_event_id = event["discord_event_id"]
        start_time = datetime_from_db(event["start_time_utc"])

        if not event["seven_day_sent"] and now >= start_time - timedelta(days=7):
            if await bot.send_reminder(event, "seven_day"):
                mark_reminder_sent(discord_event_id, "seven_day_sent")
                logger.info("Sent 7-day reminder for Discord event %s.", discord_event_id)

        if not event["one_hour_sent"] and now >= start_time - timedelta(hours=1):
            if await bot.send_reminder(event, "one_hour"):
                mark_reminder_sent(discord_event_id, "one_hour_sent")
                logger.info("Sent 1-hour reminder for Discord event %s.", discord_event_id)


config = load_config()
bot = AlumniReminderBot(config)


@bot.tree.command(name="agenda_add", description="Add an item to the next alumni meeting agenda.")
@app_commands.describe(item="Agenda item to add")
async def agenda_add(interaction: discord.Interaction, item: str) -> None:
    clean_item = item.strip()
    if not clean_item:
        await interaction.response.send_message("Please enter an agenda item.", ephemeral=True)
        return

    if len(clean_item) > AGENDA_ITEM_LIMIT:
        await interaction.response.send_message(
            f"That agenda item is too long. Please keep agenda items under {AGENDA_ITEM_LIMIT} characters.",
            ephemeral=True,
        )
        return

    event = await bot.get_next_event_with_sync()
    if event is None:
        await interaction.response.send_message(
            "I could not find an upcoming Alumni Association meeting to attach this agenda item to.\n\n"
            "An admin may need to run:\n/event_sync",
            ephemeral=True,
        )
        return

    start_time = datetime_from_db(event["start_time_utc"])
    if start_time <= utc_now():
        await interaction.response.send_message(
            "This meeting has already started, so new agenda items are closed.",
            ephemeral=True,
        )
        return

    add_agenda_item(
        event["discord_event_id"],
        clean_item,
        interaction.user.id,
        interaction.user.display_name,
    )
    logger.info("User %s added agenda item to event %s.", interaction.user.id, event["discord_event_id"])

    await interaction.response.send_message(
        f"Added to the agenda for {event['name']}:\n"
        f"Meeting time: {to_discord_timestamp(start_time)}\n\n"
        f'"{clean_item}"',
        ephemeral=True,
    )


@bot.tree.command(name="agenda", description="View the next alumni meeting agenda.")
async def agenda(interaction: discord.Interaction) -> None:
    event = await bot.get_next_event_with_sync()
    if event is None:
        await interaction.response.send_message(
            "I could not find an upcoming Alumni Association meeting.\n\n"
            "An admin should check that the Discord event exists, then run:\n/event_sync",
            ephemeral=True,
        )
        return

    start_time = datetime_from_db(event["start_time_utc"])
    agenda_lines = format_agenda_lines(event["discord_event_id"], include_submitters=True)
    if agenda_lines:
        body = "\n".join(agenda_lines)
    else:
        body = (
            f"No agenda items have been added yet for the next {config.event_name_filter}.\n\n"
            'Add one with:\n/agenda_add item:"Your topic here"'
        )

    await interaction.response.send_message(
        f"Agenda for {event['name']}\n"
        f"Meeting time: {to_discord_timestamp(start_time)}\n\n"
        f"{body}",
        ephemeral=True,
    )


@bot.tree.command(name="next_meeting", description="Show the next alumni meeting.")
async def next_meeting(interaction: discord.Interaction) -> None:
    event = await bot.get_next_event_with_sync()
    if event is None:
        await interaction.response.send_message(
            "I could not find an upcoming Alumni Association meeting.\n\n"
            "An admin should check that the Discord event exists, then run:\n/event_sync",
            ephemeral=True,
        )
        return

    start_time = datetime_from_db(event["start_time_utc"])
    agenda_count = len(list_agenda_items(event["discord_event_id"]))
    lines = [
        f"Next meeting: {event['name']}",
        f"Time: {to_discord_timestamp(start_time)}",
        f"Discord event: {event_link(config.guild_id, event['discord_event_id'])}",
        "",
        f"Agenda items added so far: {agenda_count}",
        "",
        "Add an agenda item with:",
        '/agenda_add item:"Your topic here"',
    ]

    if user_can_manage_guild(interaction):
        lines.extend(
            [
                "",
                "Admin reminder status:",
                f"7-day reminder: {'Sent' if event['seven_day_sent'] else 'Not sent'}",
                f"1-hour reminder: {'Sent' if event['one_hour_sent'] else 'Not sent'}",
            ]
        )

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@bot.tree.command(name="event_sync", description="Sync native Discord events for alumni reminders.")
async def event_sync(interaction: discord.Interaction) -> None:
    if not await require_manage_guild(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    count, events = await bot.sync_events()
    if not events:
        await interaction.followup.send(
            "No matching Discord events found.\n\n"
            "I am looking for events whose name contains:\n"
            f'"{config.event_name_filter}"\n\n'
            "Check that the Discord event exists and that EVENT_NAME_FILTER is set correctly.",
            ephemeral=True,
        )
        return

    lines = ["Event sync complete.", "", f"Found {count} matching event{'s' if count != 1 else ''}:"]
    for event in events:
        lines.append(f"{event.name} - {to_discord_timestamp(event.start_time)}")
    lines.extend(["", "These events are now being tracked for 7-day and 1-hour reminders."])
    await interaction.followup.send("\n".join(lines), ephemeral=True)


@bot.tree.command(name="event_list", description="List tracked alumni events.")
async def event_list(interaction: discord.Interaction) -> None:
    if not await require_manage_guild(interaction):
        return

    await bot.sync_events()
    events = list_tracked_events()
    if not events:
        await interaction.response.send_message(
            "No upcoming tracked alumni meetings found.\n\n"
            "Create the Discord event first, then run:\n/event_sync",
            ephemeral=True,
        )
        return

    lines = ["Tracked Events"]
    for index, row in enumerate(events, start=1):
        start_time = datetime_from_db(row["start_time_utc"])
        lines.extend(
            [
                "",
                f"{index}. {row['name']}",
                f"Time: {to_discord_timestamp(start_time)}",
                f"Status: {row['status']}",
                f"7-day reminder: {'Sent' if row['seven_day_sent'] else 'Not sent'}",
                f"1-hour reminder: {'Sent' if row['one_hour_sent'] else 'Not sent'}",
                f"Agenda items: {row['agenda_count']}",
                f"Event link: {event_link(config.guild_id, row['discord_event_id'])}",
                "",
                "Technical details:",
                f"Discord Event ID: {row['discord_event_id']}",
            ]
        )

    await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def event_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    rows = list_tracked_events()
    current_lower = current.lower()
    choices = []
    for row in rows:
        label = short_event_label(row, config)
        if current_lower and current_lower not in label.lower():
            continue
        choices.append(app_commands.Choice(name=label[:100], value=row["discord_event_id"]))
    return choices[:25]


@bot.tree.command(name="event_reset_reminders", description="Reset reminder flags for an alumni meeting.")
@app_commands.describe(meeting="Optional meeting; defaults to the next upcoming alumni meeting")
@app_commands.autocomplete(meeting=event_autocomplete)
async def event_reset_reminders(interaction: discord.Interaction, meeting: Optional[str] = None) -> None:
    if not await require_manage_guild(interaction):
        return

    event = get_tracked_event(meeting) if meeting else await bot.get_next_event_with_sync()
    if event is None:
        await interaction.response.send_message(
            "I could not find an upcoming Alumni Association meeting to reset.",
            ephemeral=True,
        )
        return

    if reset_reminder_flags(event["discord_event_id"]):
        await interaction.response.send_message(
            f"Reminder flags reset for:\n\n"
            f"{event['name']}\n"
            f"Time: {to_discord_timestamp(datetime_from_db(event['start_time_utc']))}\n\n"
            "The bot may now send the 7-day and 1-hour reminders again if those reminder times are still valid.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message("I could not reset reminders for that meeting.", ephemeral=True)


async def agenda_item_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[int]]:
    event = get_next_tracked_event()
    if event is None:
        return []

    current_lower = current.lower()
    choices = []
    for row in list_agenda_items(event["discord_event_id"]):
        submitter = row["submitted_by_display_name"] or "Unknown"
        label = f"[{row['id']}] {row['item_text']} - {submitter}"
        if current_lower and current_lower not in label.lower():
            continue
        choices.append(app_commands.Choice(name=label[:100], value=int(row["id"])))
    return choices[:25]


@bot.tree.command(name="agenda_remove", description="Remove an agenda item from the next meeting.")
@app_commands.describe(agenda_item="Agenda item to remove")
@app_commands.autocomplete(agenda_item=agenda_item_autocomplete)
async def agenda_remove(interaction: discord.Interaction, agenda_item: int) -> None:
    if not await require_manage_guild(interaction):
        return

    if remove_agenda_item(agenda_item):
        logger.info("User %s removed agenda item %s.", interaction.user.id, agenda_item)
        await interaction.response.send_message(f"Removed agenda item {agenda_item}.", ephemeral=True)
    else:
        await interaction.response.send_message("I could not find that active agenda item.", ephemeral=True)


def main() -> None:
    init_db()
    bot.run(config.discord_token)


if __name__ == "__main__":
    main()
