# Data Model: Discord Alumni Reminder Bot

## tracked_events

Local cache of eligible Discord Scheduled Events.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Local SQLite primary key. |
| `discord_event_id` | text | yes | Unique Discord Scheduled Event ID. |
| `name` | text | yes | Copied from Discord. |
| `description` | text | no | Copied from Discord. |
| `start_time_utc` | text | yes | ISO 8601 UTC timestamp. |
| `end_time_utc` | text | no | ISO 8601 UTC timestamp. |
| `location` | text | no | Discord event location when available. |
| `status` | text | no | Human-readable Discord status. |
| `seven_day_sent` | integer | yes | Boolean flag, default `0`. |
| `one_hour_sent` | integer | yes | Boolean flag, default `0`. |
| `active` | integer | yes | Boolean flag, default `1`. |
| `first_seen_at_utc` | text | yes | First local sync timestamp. |
| `last_synced_at_utc` | text | yes | Last local sync timestamp. |

### Invariants

- `discord_event_id` is the stable identity for syncing and reminders.
- Active tracked events must have `start_time_utc` in the future.
- Reminder flags must only change from `0` to `1` after a successful Discord message send, unless an admin resets them.
- Sync updates may refresh event metadata but must not clear reminder flags automatically.

## agenda_items

Member-submitted agenda entries associated with one tracked Discord event.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Local SQLite primary key. |
| `discord_event_id` | text | yes | Foreign key to `tracked_events.discord_event_id`. |
| `item_text` | text | yes | Trimmed, 1 to 500 characters. |
| `submitted_by_user_id` | text | yes | Discord user ID as text. |
| `submitted_by_display_name` | text | no | Display name at submission time. |
| `active` | integer | yes | Boolean flag, default `1`. |
| `created_at_utc` | text | yes | ISO 8601 UTC timestamp. |

### Invariants

- Agenda rows are soft-deleted by setting `active = 0`.
- Active agenda items for a meeting are listed by `created_at_utc ASC`.
- Agenda additions are allowed only before the linked meeting starts.

## Sync Result

Structured in-memory result returned by event sync.

| Field | Type | Notes |
| --- | --- | --- |
| `fetched_count` | integer | Number of Discord events returned by API. |
| `matched_count` | integer | Number of events accepted by eligibility rules. |
| `matched_events` | list | Event ID, name, status, and start time summaries. |
| `non_matching_events` | list | Limited diagnostic list of future scheduled events rejected by filter/status/time. |
| `error` | optional string | Permission, fetch, or unexpected Discord API failure. |

This model does not need to be persisted; it exists to improve admin feedback and logs.
