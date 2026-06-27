# Research Notes: Discord Alumni Reminder Bot

## Current Behavior Observed

- The README defines Discord Scheduled Events as the source of truth.
- The current implementation already supports:
  - Guild-specific slash command sync.
  - Scheduled event fetch and local tracking.
  - Agenda add/list/remove.
  - 7-day and 1-hour reminder flags.
  - SQLite persistence.
- The runtime log shows:
  - Bot authenticated successfully.
  - Seven slash commands synced to the configured guild.
  - Event sync found zero visible events.
  - `/next_meeting` later failed with Discord `404 Unknown interaction`.

## Key Decisions

### Decision: Keep Discord Scheduled Events As Source Of Truth

Reasoning: This matches the README and keeps the bot focused. Discord's native event UI already handles recurrence-like admin workflows, RSVP prompts, links, and event visibility.

Alternatives considered:

- Bot-created events: rejected for this phase because it increases permissions and duplicates Discord UI.
- Google Calendar sync: rejected for this phase because the README explicitly excludes it.

### Decision: Add Early Interaction Acknowledgement

Reasoning: Discord interactions expire if not acknowledged quickly. Commands that fetch scheduled events can miss that window. Deferring before slow work is the most direct fix.

Alternatives considered:

- Only optimize sync speed: insufficient because Discord/network latency is outside the bot's control.
- Avoid sync during member commands: worsens no-event behavior and stale data.

### Decision: Improve Sync Diagnostics Before Adding More Features

Reasoning: The observed zero-match state is likely a configuration, event-name, permissions, or Discord API visibility issue. Admin commands should expose this directly.

Alternatives considered:

- More reminders or agenda features: rejected until the bot can clearly prove it sees events.

### Decision: Refactor To Testable Modules Gradually

Reasoning: The existing one-file script works as a prototype, but reminder decisions, event eligibility, and agenda validation should be tested without Discord. A staged refactor reduces risk.

Alternatives considered:

- Full rewrite: too risky for an already integrated bot.
- Leave as one file: makes durable testing and diagnostics harder.

## Open Questions

- Should event matching require exact phrase containment, or should admins be able to configure multiple aliases?
- If the bot first discovers an event inside the 1-hour window, should it send both the missed 7-day reminder and the 1-hour reminder, or only the most relevant reminder?
- Should agenda submissions close at meeting start only, or a configurable period before start?
- Should reminder messages include the full agenda every time, or only counts plus `/agenda` guidance for long agendas?
