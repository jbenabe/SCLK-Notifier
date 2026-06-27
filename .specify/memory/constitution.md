# SCLK Notifier Constitution

## Core Principles

### I. Discord Is The System Of Record
Native Discord Scheduled Events are the source of truth for meeting name, time, status, location, RSVP flow, and event links. The application may cache event state locally for reminders and agenda association, but it must not become a competing calendar system.

### II. Member Commands Stay Simple
Members should never need server IDs, channel IDs, role IDs, event IDs, database IDs, or implementation details. Member-facing flows must orient around the next upcoming matching meeting and use short slash commands with clear ephemeral responses.

### III. Reminders Must Be Reliable And Idempotent
Reminder delivery must be safe across restarts, downtime, event edits, and repeated syncs. A reminder may be sent late if the bot was offline, but it must not be sent after a meeting starts and must not duplicate once marked sent.

### IV. Admin Workflows Must Be Diagnosable
Admin commands must make configuration and event matching problems obvious. When no event is found, the bot must explain what it searched for, what Discord returned when available, and which admin action is needed next.

### V. Small Local Runtime First
The MVP remains a single-server Python Discord bot with SQLite persistence and no Docker requirement. Changes should keep local setup approachable while leaving a clean path to always-on hosting later.

## Technical Guardrails

- Slash command handlers that may fetch Discord APIs or touch disk must acknowledge interactions within Discord's response window by deferring early when needed.
- Environment validation must fail fast on missing or malformed values before connecting to Discord.
- SQLite writes must preserve agenda history by soft-deleting agenda items and retaining event/reminder audit fields.
- Role mentions must be constrained with `AllowedMentions` so only the configured alumni role can be pinged.
- Admin-only commands must require the Discord Manage Server permission.

## Product Boundaries

In scope:

- Read scheduled and active Discord Scheduled Events from one configured guild.
- Match alumni meetings by a configurable, case-insensitive event name filter.
- Send 7-day and 1-hour reminders to one configured announcement channel.
- Maintain agenda items for the next upcoming matching meeting.
- Provide admin diagnostics, sync, listing, and reminder reset commands.

Out of scope for this phase:

- Creating or editing Discord Scheduled Events.
- Managing RSVPs outside Discord's native event UI.
- Google Calendar or external calendar sync.
- Multi-guild support.
- Web dashboard.
- Docker-only deployment.

## Governance

Every feature spec and task plan must preserve the five core principles. If implementation pressure creates a conflict, the spec must document the tradeoff and the smallest acceptable exception before code changes are made.

Specs should be written in user outcomes first, technical choices second. Plans must include acceptance criteria for Discord interaction timing, event matching diagnostics, reminder idempotency, and local restart behavior.
