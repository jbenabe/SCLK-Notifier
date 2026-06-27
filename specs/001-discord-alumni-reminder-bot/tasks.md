# Tasks: Discord Alumni Reminder Bot

**Input**: Documents in `specs/001-discord-alumni-reminder-bot/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`

## Phase 1: Setup And Baseline

- [ ] T001 Confirm ignored local artifacts remain untracked: `.env`, `alumni_bot.db`, `*.log`, `__pycache__/`, `.venv/`.
- [ ] T002 Add a lightweight test dependency decision to `requirements-dev.txt` or equivalent.
- [ ] T003 Create a temporary-database test fixture so tests do not touch `alumni_bot.db`.
- [ ] T004 Add a README troubleshooting section based on the quickstart checklist.

## Phase 2: Interaction Reliability

- [ ] T005 Identify every command path that can call `sync_events()` or Discord fetch APIs.
- [ ] T006 Add an interaction response helper that defers ephemerally before slow work and sends followups consistently.
- [ ] T007 Update `/next_meeting` to defer before syncing and to avoid `Unknown interaction` on no-event responses.
- [ ] T008 Update `/agenda` and `/agenda_add` to use the same safe acknowledgement pattern.
- [ ] T009 Update `/event_sync` and `/event_list` to use the same safe acknowledgement pattern.
- [ ] T010 Log late interaction failures with command name and user ID, without crashing the bot loop.

## Phase 3: Event Sync Diagnostics

- [ ] T011 Introduce a sync result object with fetched count, matched events, non-matching event diagnostics, and optional error.
- [ ] T012 Record event eligibility rejection reasons for status, missing start time, past start time, and filter mismatch.
- [ ] T013 Update `/event_sync` no-match output to show the configured filter and limited non-matching event names.
- [ ] T014 Update `/event_list` to preserve current admin details while using structured sync results.
- [ ] T015 Add logging for fetched scheduled event count and matched event count.

## Phase 4: Testable Core Extraction

- [ ] T016 Move configuration loading into `config.py` with tests for missing and malformed values.
- [ ] T017 Move SQLite schema and repository functions into `db.py`.
- [ ] T018 Move event eligibility and event link formatting into `events.py` with unit tests.
- [ ] T019 Move agenda validation and formatting into `agenda.py` with unit tests.
- [ ] T020 Move reminder due-window checks and message composition into `reminders.py` with unit tests.
- [ ] T021 Keep `bot.py` as the minimal process entrypoint after extraction.

## Phase 5: Reminder Hardening

- [ ] T022 Re-check event start time and active status immediately before sending a reminder.
- [ ] T023 Ensure reminder flags are marked sent only after Discord message send succeeds.
- [ ] T024 Decide and document behavior when an event is first discovered inside the 1-hour reminder window.
- [ ] T025 Add tests proving repeated reminder checks do not duplicate sends.
- [ ] T026 Add tests proving started events do not send reminders.

## Phase 6: Admin And Member Polish

- [ ] T027 Improve `/event_reset_reminders` response copy so admins understand when reminders may fire again.
- [ ] T028 Improve `/agenda_remove` autocomplete labels for long agenda items.
- [ ] T029 Add a manual Discord smoke-test section to README.
- [ ] T030 Add a release checklist for local run, test run, Discord smoke test, and log review.

## Dependencies

- T003 before tests in T016-T020 and T025-T026.
- T006 before T007-T010.
- T011 before T012-T015.
- T016-T020 before deeper reminder hardening in T022-T026.
- T024 before finalizing T025 expectations.

## MVP Completion Target

The next implementation pass should complete T001-T015 first. That addresses the observed broken state directly: the bot should respond reliably to slash commands and admins should be able to diagnose why no Discord Scheduled Events are matching.
