# TODO

This is the shared backlog for SCLK Notifier. Prefer small pull requests that complete one focused item.

## P0 - Needed Before Confident Use

- [ ] Run a live Discord smoke test from `docs/LOCAL_DEPLOY.md`.
- [ ] Confirm `/event_sync` diagnostics are helpful when no upcoming visible event is found.
- [ ] Confirm `/test_notify` posts a production-shaped notification that mentions only the command caller.
- [ ] Investigate notification behavior once expected-vs-actual details or screenshots are available; latest smoke test showed Discord `403 Missing Access` when sending to the announcement channel.
- [ ] Point `ANNOUNCEMENT_CHANNEL_ID` at `meeting` or `alumni-announcements`, then confirm the bot has View Channel and Send Messages access.
- [ ] Require the new Alumni Board role (`1520613667513569384`) for elevated bot commands instead of broad Manage Server permission.
- [ ] Confirm mention-heavy agenda text does not ping anyone.
- [ ] Confirm `REMINDERS_ENABLED=false` prevents public reminder posts.
- [ ] Validate local redeploy instructions on the actual bot machine.

## P1 - Reliability And Hosting

- [ ] Choose an always-on hosting target: Railway, Render, Fly.io, VPS, or another service.
- [ ] Add provider-specific deploy docs after the hosting target is chosen.
- [ ] Keep deployment docs portable for Windows and Linux hosts without personal machine paths.
- [ ] Add stronger tests for reminder idempotency and event sync diagnostics.
- [ ] Improve command error handling for Discord API failures.
- [ ] Add a simple health/check command for admins.

## P2 - Maintainability And Admin Tools

- [ ] Split `bot.py` into modules only after the current behavior is covered by tests.
- [ ] Make safety limits configurable through environment variables.
- [ ] Add admin command to view recent abuse/safety audit events.
- [ ] Add admin command to show current config health without exposing secrets.
- [ ] Add startup/config validation for `ALUMNI_BOARD_ROLE_ID` and announcement-channel access.
- [ ] Add tests for agenda removal and reminder reset behavior.
- [ ] Add slash-command agenda management for admins to carry over, close, delegate, or mark topics for committee follow-up.
- [ ] Consider an admin-only agenda moderation channel after the slash-command MVP is stable.

## P3 - Nice-To-Have Ideas

- [ ] Enable GitHub `main` branch protection requiring pull requests before merge.
- [ ] Add richer release notes from merged pull requests.
- [ ] Add issue templates for bug reports and feature requests.
- [ ] Consider a tiny web dashboard only if Discord commands become awkward.
- [ ] Consider Docker after a hosted deployment target is selected.
