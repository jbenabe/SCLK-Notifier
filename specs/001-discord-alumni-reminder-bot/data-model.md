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
- Agenda text may be stored as submitted for audit, but every display path must render a sanitized version that cannot create Discord mentions or deceptive formatting.
- Agenda writes are subject to item validation, rejected-write cooldowns, and total per-event quotas.

## abuse_events

Optional local audit table for safety-relevant events. This may be introduced when abuse controls move from specification to implementation.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | integer | yes | Local SQLite primary key. |
| `event_type` | text | yes | Example: `rate_limit_hit`, `cooldown_started`, `permission_denied`, `send_failure`. |
| `discord_user_id` | text | no | User associated with the event, when applicable. |
| `discord_event_id` | text | no | Scheduled event associated with the event, when applicable. |
| `details` | text | no | Sanitized operational detail; never tokens or secrets. |
| `created_at_utc` | text | yes | ISO 8601 UTC timestamp. |

### Invariants

- Safety logs must not store Discord tokens, `.env` values, or private configuration secrets.
- Abuse events are operational diagnostics and must not trigger public Discord messages by themselves.

## Sync Result

Structured in-memory result returned by event sync.

| Field | Type | Notes |
| --- | --- | --- |
| `fetched_count` | integer | Number of Discord events returned by API. |
| `matched_count` | integer | Number of events accepted by eligibility rules. |
| `matched_events` | list | Event ID, name, status, and start time summaries. |
| `ineligible_events` | list | Limited diagnostic list of scheduled events rejected by status/time. |
| `error` | optional string | Permission, fetch, or unexpected Discord API failure. |

This model does not need to be persisted; it exists to improve admin feedback and logs.

## Safety Policy

Structured in-memory policy used by agenda and reminder flows.

| Field | Type | Notes |
| --- | --- | --- |
| `agenda_event_quota` | integer | Maximum active agenda items allowed for one event. |
| `rejected_write_cooldown_seconds` | integer | Temporary cooldown after repeated rejected writes. |
| `public_message_max_chars` | integer | Maximum rendered public reminder length before truncation. |

These values may start as constants and later become configuration if admins need tuning.
