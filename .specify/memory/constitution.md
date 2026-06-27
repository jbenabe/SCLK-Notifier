# SCLK Notifier Constitution

## Core Principles

### I. Discord Is The System Of Record
Native Discord Scheduled Events are the source of truth for meeting name, time, status, location, RSVP flow, and event links. The application may cache event state locally for reminders and agenda association, but it must not become a competing calendar system.

### II. Member Commands Stay Simple
Members should never need server IDs, channel IDs, role IDs, event IDs, database IDs, or implementation details. Member-facing flows must orient around the next upcoming matching meeting and use short slash commands with clear ephemeral responses.

### III. Bot-Induced Spam Prevention
The bot must assume member accounts can be compromised and must never amplify spam. Member-triggered responses must be ephemeral by default, public messages must be limited to scheduled reminders or explicit admin-approved workflows, and user-submitted content must never create role, everyone, here, user, or channel mentions.

### IV. Reminders Must Be Reliable And Idempotent
Reminder delivery must be safe across restarts, downtime, event edits, and repeated syncs. A reminder may be sent late if the bot was offline, but it must not be sent after a meeting starts and must not duplicate once marked sent.

### V. Admin Workflows Must Be Diagnosable
Admin commands must make configuration and event matching problems obvious. When no event is found, the bot must explain what it searched for, what Discord returned when available, and which admin action is needed next.

### VI. Small Local Runtime First
The MVP remains a single-server Python Discord bot with SQLite persistence and no Docker requirement. Changes should keep local setup approachable while leaving a clean path to always-on hosting later.

## Technical Guardrails

- Slash command handlers that may fetch Discord APIs or touch disk must acknowledge interactions within Discord's response window by deferring early when needed.
- Environment validation must fail fast on missing or malformed values before connecting to Discord.
- SQLite writes must preserve agenda history by soft-deleting agenda items and retaining event/reminder audit fields.
- Public sends must be deny-by-default: only scheduled reminders and explicitly admin-approved workflows may post to public channels.
- Member-triggered command responses must be ephemeral unless a future spec documents an explicit admin-approved public workflow.
- Role mentions must be constrained with `AllowedMentions` so only the configured alumni role can be pinged, and user-submitted content must be displayed with all Discord mentions neutralized.
- User-submitted text must be sanitized before display to prevent broad pings, targeted pings, channel pings, deceptive markdown, and oversized public payloads.
- Member write commands must have local abuse controls, including per-user cooldowns, per-user/per-event quotas, and temporary cooldowns after repeated rejected submissions.
- Public reminder messages must have a maximum rendered size and must truncate agenda content safely when needed.
- Reminder sends must be protected by persisted idempotency flags and a maximum send budget per event/reminder type.
- If reminder state, database state, or Discord send state is ambiguous, the bot must fail closed by skipping public sends and logging or admin-reporting the issue.
- Admin-only commands must require the Discord Manage Server permission.
- Abuse-relevant events must be logged without leaking tokens or private configuration: rate-limit hits, cooldowns, permission denials, agenda removals, reminder sends, and send failures.
- The application must document an emergency stop path for public posting, such as disabling reminder sends through configuration or stopping the process.

## Product Boundaries

In scope:

- Read scheduled and active Discord Scheduled Events from one configured guild.
- Match alumni meetings by a configurable, case-insensitive event name filter.
- Send 7-day and 1-hour reminders to one configured announcement channel.
- Maintain agenda items for the next upcoming matching meeting.
- Provide admin diagnostics, sync, listing, and reminder reset commands.
- Enforce local safety controls that prevent compromised member accounts from causing public spam through the bot.

Out of scope for this phase:

- Creating or editing Discord Scheduled Events.
- Managing RSVPs outside Discord's native event UI.
- Google Calendar or external calendar sync.
- Multi-guild support.
- Web dashboard.
- Docker-only deployment.

## Governance

Every feature spec and task plan must preserve the core principles. If implementation pressure creates a conflict, the spec must document the tradeoff and the smallest acceptable exception before code changes are made.

Specs should be written in user outcomes first, technical choices second. Plans must include acceptance criteria for Discord interaction timing, event matching diagnostics, reminder idempotency, local restart behavior, mention neutralization, command abuse limits, public output budgets, and fail-closed behavior.
