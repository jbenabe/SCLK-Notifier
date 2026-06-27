# Contributing

Thanks for helping with SCLK Notifier. The goal is to keep this bot small, reliable, and safe for the Discord server.

## Ground Rules

- Never commit `.env`, Discord tokens, logs, local databases, or screenshots that expose secrets.
- Keep member-facing behavior simple.
- Keep public Discord posting conservative.
- Prefer small pull requests that can be reviewed quickly.
- Run tests before opening a pull request.

## Local Setup

```powershell
git clone https://github.com/award73/SCLK-Notifier.git
cd SCLK-Notifier\discord-alumni-reminder-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `.env` with your own Discord test server values. Do not use production credentials in a shared branch.

## Test Commands

From the repository root:

```powershell
.\discord-alumni-reminder-bot\.venv\Scripts\python.exe -m py_compile discord-alumni-reminder-bot\bot.py
.\discord-alumni-reminder-bot\.venv\Scripts\python.exe -m unittest discover -s discord-alumni-reminder-bot\tests
```

From inside `discord-alumni-reminder-bot/` with the venv activated:

```powershell
python -m py_compile bot.py
python -m unittest discover -s tests
```

## Branches

Use short descriptive branch names:

```text
codex/fix-event-sync-diagnostics
codex/add-reminder-tests
codex/docs-local-deploy
```

## Pull Requests

Each PR should include:

- What changed.
- How it was tested.
- Any Discord manual smoke-test results, if relevant.
- Any new environment variables.

CI must pass before merging.

## Release Tags

Only tag releases from `main` after CI passes:

```powershell
git switch main
git pull
git tag v0.1.0
git push origin v0.1.0
```

The release workflow creates the GitHub Release. Deployment is still manual until an always-on host is chosen.
