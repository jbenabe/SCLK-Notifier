# Implementation Plan: Discord Alumni Reminder Bot

**Spec**: `specs/001-discord-alumni-reminder-bot/spec.md`  
**Created**: 2026-06-27  
**Goal**: Turn the integrated prototype into a reliable single-server Discord alumni reminder bot with clear diagnostics and testable behavior.

## Technical Context

- **Language/Runtime**: Python 3.11+ recommended
- **Primary Dependencies**: `discord.py`, `python-dotenv`, `tzdata`
- **Storage**: Local SQLite database `alumni_bot.db`
- **External System**: Discord Gateway, Slash Commands, Scheduled Events API
- **Current Shape**: One large `bot.py` file with config, persistence, Discord client, command handlers, and reminder logic together
- **Known Failure From Log**: Bot logged in and synced commands, found zero matching events, then `/next_meeting` raised Discord `404 Unknown interaction`, likely because slow sync work happened before interaction acknowledgement

## Constitution Check

- Discord remains source of truth: PASS
- Member commands hide IDs and technical details: PASS
- Reminder idempotency is required and already partially modeled: PASS WITH WORK
- Admin diagnostics are currently too thin when zero events match: NEEDS WORK
- Small local runtime remains intact: PASS

## Proposed Architecture

Keep the MVP single-process, but separate responsibilities so behavior can be tested without a live Discord connection:

- `config.py`: Environment loading and validation.
- `db.py`: SQLite connection, schema, migrations, and repository functions.
- `events.py`: Event eligibility, event link creation, event row formatting, sync result modeling.
- `agenda.py`: Agenda validation and agenda item operations.
- `reminders.py`: Reminder window decisions, message composition, idempotent mark-sent flow.
- `discord_bot.py`: Discord client, loops, commands, interaction acknowledgement, Discord API calls.
- `bot.py`: Minimal entrypoint that initializes DB, loads config, and runs the bot.
- `tests/`: Unit tests for config, event matching, agenda validation, reminder idempotency, and command-safe response decisions where practical.

This decomposition is not required all at once; implement it in slices that preserve working behavior after each step.

## Phase 0 - Baseline And Safety

1. Confirm `.env`, `alumni_bot.db`, logs, `.venv`, and generated caches remain ignored.
2. Add a `README` troubleshooting section for the two observed classes of failures:
   - Zero matching Discord Scheduled Events.
   - Discord `Unknown interaction` caused by missed response windows.
3. Add a small local test harness or unit test setup before refactoring business logic.

## Phase 1 - Interaction Reliability

1. Defer slash command responses before any path that may fetch Discord APIs or perform sync work.
2. Use follow-up responses consistently after deferral.
3. Add a helper for safe ephemeral command responses to reduce duplicate interaction handling code.
4. Add error handling for late/unknown interactions that logs context without crashing command execution.

Acceptance target:

- `/next_meeting`, `/agenda`, `/agenda_add`, `/event_sync`, and `/event_list` do not raise `Unknown interaction` even when Discord fetches are slow.

## Phase 2 - Event Sync Diagnostics

1. Return a structured sync result containing:
   - Discord events fetched count.
   - Matching events count.
   - Matching event summaries.
   - Non-matching future scheduled event names and start times, limited to a safe count.
   - Fetch/permission errors.
2. Update `/event_sync` no-match output to explain exactly what filter was used and what Discord returned.
3. Update logs to include event IDs, names, statuses, and eligibility reasons at debug/info level.

Acceptance target:

- An admin can distinguish "no scheduled events", "events exist but filter mismatch", and "bot cannot fetch events" from command output.

## Phase 3 - Testable Core Logic

1. Move pure functions and database operations out of Discord command handlers.
2. Add tests for:
   - Config validation.
   - Case-insensitive event name matching.
   - Status/time eligibility.
   - Agenda validation limits.
   - Reminder due/not-due decisions.
   - Reminder mark-sent idempotency.
3. Use temporary SQLite databases in tests rather than the production `alumni_bot.db`.

Acceptance target:

- Core behavior can be verified locally without connecting to Discord.

## Phase 4 - Reminder Hardening

1. Re-check event state immediately before sending each reminder.
2. Mark reminders sent only after Discord confirms the message was posted.
3. Avoid sending both 7-day and 1-hour reminders back-to-back if the event is first discovered inside the 1-hour window unless that behavior is explicitly accepted.
4. Add admin-visible reset semantics:
   - Reset both flags by default.
   - Optionally reset only one reminder type later if needed.

Acceptance target:

- Repeated reminder checks and bot restarts cannot duplicate already-sent reminders.

## Phase 5 - Operator Polish

1. Improve README setup, permissions, and troubleshooting sections.
2. Add a local smoke test checklist for real Discord verification.
3. Add deployment notes for always-on hosting once local operation is reliable.
4. Consider structured logging only after the MVP flows are stable.

## Risks And Mitigations

- **Discord API permission ambiguity**: Add admin diagnostics and log exception types.
- **Interaction timeout**: Defer early on slow commands and use followups.
- **Refactor regression**: Extract logic behind tests before changing command behavior deeply.
- **SQLite schema drift**: Keep idempotent migrations and never destructively alter existing local data without a migration note.
- **Reminder duplicates after event edits**: Treat Discord event ID as stable identity and require explicit admin reset if reminder flags should be reopened.

## Verification Strategy

- Unit tests for pure logic and database repository behavior.
- Manual Discord smoke test for slash command registration and live Scheduled Event fetch.
- Manual reminder dry run using a near-future test event in a private/admin channel.
- Log review after each smoke test to confirm no unhandled Discord exceptions.

## Milestone Definition Of Done

- Member commands work with and without a matching event.
- Admin commands explain sync state clearly.
- Reminder logic is covered by local tests and remains idempotent.
- README and quickstart accurately describe setup and troubleshooting.
- The bot can run locally for one test event through both reminder windows without duplicate sends.
