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
- **Known Failure From Log**: Bot logged in and synced commands, found zero visible/eligible events, then `/next_meeting` raised Discord `404 Unknown interaction`, likely because slow sync work happened before interaction acknowledgement

## Constitution Check

- Discord remains source of truth: PASS
- Member commands hide IDs and technical details: PASS
- Bot-induced spam prevention is mandatory: NEEDS WORK
- Reminder idempotency is required and already partially modeled: PASS WITH WORK
- Admin diagnostics are currently too thin when zero visible events are found: NEEDS WORK
- Small local runtime remains intact: PASS

## Proposed Architecture

Keep the MVP single-process for this hardening pass. `bot.py` remains the implementation file, with focused helper functions for configuration, persistence, event sync diagnostics, interaction responses, agenda safety, reminder composition, and abuse logging.

Extraction into modules is deferred until tests or maintenance pressure justify it. Avoid introducing broad architecture churn while the app is still a small, single-server Discord bot.

## Phase 0 - Baseline And Safety

1. Confirm `.env`, `alumni_bot.db`, logs, `.venv`, and generated caches remain ignored.
2. Add a `README` troubleshooting section for the two observed classes of failures:
   - Zero visible or eligible Discord Scheduled Events.
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
   - Ineligible future scheduled event names and start times, limited to a safe count.
   - Fetch/permission errors.
2. Update `/event_sync` no-event output to explain exactly what Discord returned.
3. Update logs to include event IDs, names, statuses, and eligibility reasons at debug/info level.

Acceptance target:

- An admin can distinguish "no scheduled events", "events exist but are ineligible", and "bot cannot fetch events" from command output.

## Phase 3 - Testable Core Logic In Place

1. Keep pure helpers near the existing command handlers.
2. Add tests for:
   - Config validation.
   - Event eligibility without name filtering.
   - Status/time eligibility.
   - Agenda validation limits.
   - Mention neutralization and public output truncation.
   - Member agenda validation and total event quotas.
   - Reminder due/not-due decisions.
   - Reminder mark-sent idempotency.
3. Use ignored SQLite scratch databases in tests rather than the production `alumni_bot.db`.

Acceptance target:

- Core behavior can be verified locally without connecting to Discord.

## Phase 4 - Reminder Hardening

1. Re-check event state immediately before sending each reminder.
2. Mark reminders sent only after Discord confirms the message was posted.
3. Enforce a maximum public send budget per event and reminder type.
4. Fail closed and log/admin-report when reminder state, database state, or Discord send state is ambiguous.
5. Avoid sending both 7-day and 1-hour reminders back-to-back if the event is first discovered inside the 1-hour window unless that behavior is explicitly accepted.
6. Add admin-visible reset semantics:
   - Reset both flags by default.
   - Optionally reset only one reminder type later if needed.

Acceptance target:

- Repeated reminder checks and bot restarts cannot duplicate already-sent reminders.

## Phase 5 - Abuse Controls And Output Safety

1. Allow rapid `/agenda_add` submissions from the same member.
2. Keep total per-event agenda quotas.
3. Add a temporary cooldown after repeated rejected member write attempts.
4. Sanitize all user-submitted agenda text before display in commands or reminders.
5. Neutralize Discord mentions, channel references, and deceptive markdown in displayed user text.
6. Cap public reminder message length and truncate agenda content safely with a pointer to `/agenda`.
7. Log rate-limit hits, cooldowns, denied permissions, agenda removals, reminder sends, and send failures without exposing secrets.
8. Add `REMINDERS_ENABLED=false` as an emergency stop for public reminder posts.

Acceptance target:

- A compromised member account cannot make the bot ping members or spam public channels through repeated member commands.

## Phase 6 - Operator Polish

1. Improve README setup, permissions, and troubleshooting sections.
2. Add a local smoke test checklist for real Discord verification.
3. Document an emergency stop path for public posting, including stopping the process and any config flag added for reminder sends.
4. Add deployment notes for always-on hosting once local operation is reliable.
5. Consider structured logging only after the MVP flows are stable.

## Risks And Mitigations

- **Discord API permission ambiguity**: Add admin diagnostics and log exception types.
- **Interaction timeout**: Defer early on slow commands and use followups.
- **Refactor regression**: Extract logic behind tests before changing command behavior deeply.
- **SQLite schema drift**: Keep idempotent migrations and never destructively alter existing local data without a migration note.
- **Reminder duplicates after event edits**: Treat Discord event ID as stable identity and require explicit admin reset if reminder flags should be reopened.
- **Compromised member account spam**: Keep member responses ephemeral, enforce total agenda quotas, and never allow user text to create pings.
- **Oversized agenda payloads**: Cap public reminder output and truncate agenda lines safely.

## Verification Strategy

- Unit tests for pure logic and database repository behavior.
- Unit tests for mention neutralization, agenda rapidfire, agenda quotas, rejected-write cooldowns, and public output truncation.
- Manual Discord smoke test for slash command registration and live Scheduled Event fetch.
- Manual Discord smoke test with agenda text containing `@everyone`, `@here`, role mentions, user mentions, channel mentions, links, and markdown.
- Manual reminder dry run using a near-future test event in a private/admin channel.
- Log review after each smoke test to confirm no unhandled Discord exceptions.

## Milestone Definition Of Done

- Member commands work with and without an upcoming server event.
- Admin commands explain sync state clearly.
- Reminder logic is covered by local tests and remains idempotent.
- Member write commands are covered by abuse-control tests and cannot create public spam.
- User-submitted agenda text is sanitized in all display paths.
- README and quickstart accurately describe setup and troubleshooting.
- The bot can run locally for one test event through both reminder windows without duplicate sends.
