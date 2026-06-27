# Feature Specification: Discord Alumni Reminder Bot

**Feature Branch**: `001-discord-alumni-reminder-bot`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: Existing README, `bot.py`, and runtime log from the integrated but not fully working Discord bot.

## User Scenarios And Testing

### User Story 1 - Member sees the next meeting (Priority: P1)

As an alumni member, I can run `/next_meeting` and immediately see the next matching Discord Scheduled Event, its Discord event link, meeting time, and agenda count.

**Why this priority**: If members cannot discover the next meeting, reminder and agenda features are hard to trust.

**Independent Test**: With one future Discord Scheduled Event whose name contains the configured filter, run `/next_meeting`; the bot responds ephemerally within Discord's interaction window and includes the event link.

**Acceptance Scenarios**:

1. Given a matching future scheduled event exists, when a member runs `/next_meeting`, then the bot returns the event name, Discord timestamp, event link, and agenda item count.
2. Given no matching future event exists, when a member runs `/next_meeting`, then the bot returns a helpful ephemeral message and does not raise `Unknown interaction`.
3. Given event sync requires a Discord API fetch, when `/next_meeting` is invoked, then the bot acknowledges or defers before the Discord interaction expires.

---

### User Story 2 - Member contributes agenda items (Priority: P1)

As an alumni member, I can add an agenda item without knowing any event or database IDs, and I can view the current agenda for the next meeting.

**Why this priority**: Agenda collection is a core purpose of the bot and must feel lightweight for members without letting compromised accounts create spam or pings.

**Independent Test**: Run `/agenda_add item:"Discuss fundraiser planning"` and then `/agenda`; the item appears under the next upcoming matching event.

**Acceptance Scenarios**:

1. Given a future matching event exists, when a member runs `/agenda_add` with non-empty text of 500 characters or fewer, then the item is attached to the next event and confirmed ephemerally.
2. Given no future matching event exists, when a member runs `/agenda_add`, then the bot explains that an admin must verify the Discord event and sync.
3. Given an item is empty or too long, when a member runs `/agenda_add`, then the bot rejects it with a clear ephemeral validation message.
4. Given agenda items exist, when a member runs `/agenda`, then the bot lists active items in creation order with submitter display names.
5. Given a member repeatedly submits agenda items, when they exceed configured cooldown or quota limits, then the bot rejects the write ephemerally, logs the safety event, and does not create public output.
6. Given an agenda item contains Discord mentions or markdown, when the bot displays it in any command or reminder, then the content is neutralized and cannot ping anyone.

---

### User Story 3 - Admin can diagnose event matching (Priority: P1)

As a server admin, I can sync and list Discord Scheduled Events so I know whether the bot sees the meeting and why a match was or was not tracked.

**Why this priority**: The last observed run authenticated successfully but found zero matching events. Admin diagnostics must make that situation actionable.

**Independent Test**: Run `/event_sync` with no matching events and verify the response shows the active filter, count of Discord events inspected when available, and concrete next checks.

**Acceptance Scenarios**:

1. Given matching events exist, when an admin runs `/event_sync`, then matching events are tracked locally and summarized.
2. Given scheduled events exist but none match the filter, when an admin runs `/event_sync`, then the bot reports the filter and lists nearby scheduled event names or explains that none were returned.
3. Given Discord permissions prevent fetching scheduled events, when an admin runs `/event_sync`, then the bot reports a permission or fetch failure without crashing.
4. Given tracked events exist, when an admin runs `/event_list`, then the bot shows event time, status, reminder flags, agenda count, event link, and technical IDs.

---

### User Story 4 - Bot sends reliable reminders (Priority: P1)

As an alumni organizer, I want the bot to send 7-day and 1-hour reminders exactly once per event, including the native Discord event link and current agenda.

**Why this priority**: The bot's main value is dependable reminder delivery.

**Independent Test**: Seed a tracked event within the 7-day window and run the reminder check twice; the first run sends and marks the reminder, the second run does not send again.

**Acceptance Scenarios**:

1. Given a future tracked event enters the 7-day reminder window, when the reminder loop runs, then the bot posts a role mention, meeting time, event link, agenda summary, and RSVP prompt.
2. Given a future tracked event enters the 1-hour reminder window, when the reminder loop runs, then the bot posts a shorter reminder with the agenda.
3. Given a reminder was already sent, when the bot restarts and the loop runs again, then it does not resend that reminder.
4. Given the meeting has started, when the reminder loop runs, then no new reminder is sent.
5. Given agenda content would make a public reminder too long, when the reminder is composed, then the agenda is truncated safely and the reminder points members to `/agenda`.
6. Given reminder send state is ambiguous, when the reminder loop runs, then the bot skips public posting, logs the ambiguity, and does not risk duplicate spam.

---

### User Story 5 - Admin controls agenda and reminder state (Priority: P2)

As a server admin, I can remove agenda items and reset reminder flags when an event changes.

**Why this priority**: These workflows support real meeting maintenance after the core member and reminder flows work.

**Independent Test**: Add an agenda item, remove it with `/agenda_remove`, confirm `/agenda` no longer shows it; reset reminder flags with `/event_reset_reminders`.

**Acceptance Scenarios**:

1. Given agenda items exist for the next meeting, when an admin runs `/agenda_remove`, then autocomplete offers active items and the chosen item is soft-deleted.
2. Given a tracked event exists, when an admin runs `/event_reset_reminders`, then both reminder flags are reset for that event.
3. Given a non-admin invokes either command, then the bot denies the command ephemerally.

## Functional Requirements

- **FR-001**: The bot MUST load configuration from environment variables: `DISCORD_TOKEN`, `GUILD_ID`, `ANNOUNCEMENT_CHANNEL_ID`, `ALUMNI_ROLE_ID`, `TIMEZONE`, `EVENT_NAME_FILTER`, and optional `REMINDERS_ENABLED`.
- **FR-002**: The bot MUST fail startup with a readable error when required configuration is missing or malformed.
- **FR-003**: The bot MUST sync guild-specific slash commands for fast availability.
- **FR-004**: The bot MUST fetch Discord Scheduled Events from exactly one configured guild.
- **FR-005**: The bot MUST track only scheduled or active future events whose names contain `EVENT_NAME_FILTER`, case-insensitively.
- **FR-006**: The bot MUST persist tracked event metadata, agenda items, active flags, and reminder flags in SQLite.
- **FR-007**: The bot MUST deactivate cached events that are no longer returned, no longer eligible, or already started.
- **FR-008**: The bot MUST expose member commands `/next_meeting`, `/agenda`, and `/agenda_add`.
- **FR-009**: The bot MUST expose admin commands `/event_sync`, `/event_list`, `/event_reset_reminders`, and `/agenda_remove`.
- **FR-010**: Admin commands MUST require Manage Server permission.
- **FR-011**: Commands that may exceed Discord's immediate response window MUST defer or otherwise acknowledge the interaction before slow work.
- **FR-012**: Reminder messages MUST mention only the configured alumni role and must disable broader user/everyone mentions.
- **FR-013**: Reminder checks MUST be idempotent across process restarts by reading and writing SQLite reminder flags.
- **FR-014**: Agenda item text MUST be trimmed, non-empty, and 500 characters or fewer.
- **FR-015**: The bot MUST preserve removed agenda items as inactive records rather than deleting rows.
- **FR-016**: The bot MUST provide actionable no-event diagnostics that mention the current event name filter.
- **FR-017**: The bot MUST log Discord API failures, sync outcomes, reminder sends, and permission denials.
- **FR-018**: Member-triggered command responses MUST be ephemeral by default and MUST NOT post to public channels.
- **FR-019**: The bot MUST sanitize displayed user-submitted text so `@everyone`, `@here`, role mentions, user mentions, channel mentions, and deceptive markdown cannot ping or mislead members.
- **FR-020**: `/agenda_add` MUST enforce a per-user cooldown before accepting another agenda item.
- **FR-021**: `/agenda_add` MUST enforce a per-user agenda item quota per event.
- **FR-022**: `/agenda_add` MUST enforce a total agenda item quota per event.
- **FR-023**: Repeated rejected member write attempts MUST trigger a temporary local cooldown.
- **FR-024**: Public reminder messages MUST enforce a maximum rendered size and truncate agenda content safely when needed.
- **FR-025**: Reminder sends MUST have a maximum send budget per event and reminder type.
- **FR-026**: If database state, reminder state, or Discord send state is ambiguous, the bot MUST fail closed by skipping public sends and logging the issue.
- **FR-027**: Abuse-relevant events MUST be logged, including rate-limit hits, cooldowns, denied permissions, agenda removals, reminder sends, and send failures.
- **FR-028**: Admin diagnostics MUST NOT expose tokens, secrets, or private configuration values beyond safe operational labels such as the event name filter.
- **FR-029**: The project MUST document an emergency stop path for public posting.
- **FR-030**: When `REMINDERS_ENABLED=false`, the bot MUST skip public reminder posts while continuing to log that reminders were skipped.

## Key Entities

- **Configured Guild**: The single Discord server the bot serves.
- **Discord Scheduled Event**: The native Discord event used as the meeting source of truth.
- **Tracked Event**: A local SQLite cache row keyed by Discord event ID with reminder flags and sync metadata.
- **Agenda Item**: A member-submitted discussion item attached to a tracked event.
- **Reminder**: A scheduled notification type, currently 7-day or 1-hour, whose sent state is persisted.

## Success Criteria

- **SC-001**: `/next_meeting` responds successfully within Discord's interaction window in both matching-event and no-event cases.
- **SC-002**: Admins can identify a bad `EVENT_NAME_FILTER` or missing Discord event from `/event_sync` output without reading logs.
- **SC-003**: A seeded reminder check sends each reminder type no more than once per event across repeated runs.
- **SC-004**: Agenda add/list/remove behavior can be verified locally against SQLite without connecting to Discord.
- **SC-005**: A fresh developer can configure and run the bot from README and quickstart instructions in under 20 minutes, assuming Discord app credentials are available.
- **SC-006**: A compromised member account cannot cause public channel spam by repeatedly invoking member commands.
- **SC-007**: User text containing `@everyone`, `@here`, role mentions, user mentions, channel mentions, links, or markdown is displayed without pinging anyone.
- **SC-008**: Oversized agenda content in reminders is truncated safely while preserving the reminder's meeting time and event link.

## Assumptions

- The alumni association uses one Discord server for this phase.
- Admins will continue creating and editing meetings through Discord's Event UI.
- The bot process must be running for reminders to be sent.
- SQLite is acceptable for local and small hosted deployments.
- Safety posture is strict: server safety wins over member convenience when the two conflict.

## Out Of Scope

- Creating recurring events.
- RSVP management outside Discord.
- Cross-posting to other platforms.
- Multi-server tenant support.
- Web administration UI.
