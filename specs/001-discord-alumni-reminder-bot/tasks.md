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

- [ ] T011 Introduce a sync result object with fetched count, eligible events, ineligible event diagnostics, and optional error.
- [ ] T012 Record event eligibility rejection reasons for status, missing start time, and past start time.
- [ ] T013 Update `/event_sync` no-event output to show fetched event counts and limited ineligible event names.
- [ ] T014 Update `/event_list` to preserve current admin details while using structured sync results.
- [ ] T015 Add logging for fetched scheduled event count and matched event count.

## Phase 4: Testable Core In Place

- [ ] T016 Keep `bot.py` as the implementation file for this hardening pass.
- [ ] T017 Add tests for event eligibility and event sync diagnostics.
- [ ] T018 Add tests for agenda validation limits.
- [ ] T019 Add tests for mention neutralization and markdown-neutralized agenda rendering.
- [ ] T020 Add tests for output budgets, cooldown decisions, and quota decisions.
- [ ] T021 Add tests for reminder due-window checks and idempotency.
- [ ] T022 Reconsider module extraction only after the single-file hardening pass is stable.

## Phase 5: Reminder Hardening

- [ ] T023 Re-check event start time and active status immediately before sending a reminder.
- [ ] T024 Ensure reminder flags are marked sent only after Discord message send succeeds.
- [ ] T025 Add a maximum send budget per event and reminder type.
- [ ] T026 Fail closed and log when reminder state, database state, or Discord send state is ambiguous.
- [ ] T027 Decide and document behavior when an event is first discovered inside the 1-hour reminder window.
- [ ] T028 Add tests proving repeated reminder checks do not duplicate sends.
- [ ] T029 Add tests proving started events do not send reminders.

## Phase 6: Abuse Controls And Output Safety

- [ ] T030 Enforce a per-user `/agenda_add` cooldown before accepting another item.
- [ ] T031 Enforce a per-user agenda item quota per event.
- [ ] T032 Enforce a total active agenda item quota per event.
- [ ] T033 Add a temporary local cooldown after repeated rejected member write attempts.
- [ ] T034 Sanitize agenda item display text so user-submitted mentions and deceptive markdown cannot ping or mislead members.
- [ ] T035 Cap public reminder message length and truncate agenda content safely with guidance to run `/agenda`.
- [ ] T036 Log abuse-relevant events: rate-limit hits, cooldowns, denied permissions, agenda removals, reminder sends, and send failures.
- [ ] T037 Add `REMINDERS_ENABLED=false` as an emergency stop for reminder posts.
- [ ] T038 Add tests for agenda cooldowns, per-user quotas, per-event quotas, and rejected-write cooldowns.
- [ ] T039 Add tests proving public reminder output respects the maximum rendered size.

## Phase 7: Admin And Member Polish

- [ ] T040 Improve `/event_reset_reminders` response copy so admins understand when reminders may fire again.
- [ ] T041 Improve `/agenda_remove` autocomplete labels for long agenda items.
- [ ] T042 Add a manual Discord smoke-test section to README, including abuse safety cases.
- [ ] T043 Document an emergency stop path for public posting.
- [ ] T044 Add a release checklist for local run, test run, Discord smoke test, safety smoke test, and log review.

## Dependencies

- T003 before tests in T017-T021, T028-T029, and T038-T039.
- T006 before T007-T010.
- T011 before T012-T015.
- T017-T021 before deeper reminder hardening in T023-T029.
- T019-T020 before T030-T039.
- T027 before finalizing T028 expectations.

## MVP Completion Target

The next implementation pass should complete T001-T015 first. That addresses the observed broken state directly: the bot should respond reliably to slash commands and admins should be able to diagnose why no Discord Scheduled Events are visible or eligible.
