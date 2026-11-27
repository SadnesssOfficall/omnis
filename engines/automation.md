# OMNIS usage & reminder automation

**Usage**: `omnis.py usage` (current heuristic 5h window, today, session), `omnis.py usage report --days 7`, `omnis.py usage limits`. Exact plan limits/reset times come only from Claude Code's own /usage or /status — say so. If the user knows their reset times: `omnis.py usage setup --reset 04:00,09:00 --tz Europe/Istanbul`.

**When a limit message appears**: save a checkpoint immediately (`omnis.py checkpoint save --task ... --done ... --next ...`), report the reset time only if known, offer a reminder. Never try to bypass limits.

**Creating a recurring reminder** (default 5h):
1. `omnis.py reminder add --every 5h --purpose usage-check [--quiet 23:00-08:00] [--max N] [--until DATE] [--tz ...]` → returns an ID. Purposes: usage-check, checkpoint, resume, review, break.
2. Pick the scheduler and tell the user its limits:
   - **In-session** (default): `omnis.py reminder cron ID` prints `cron` + `prompt`; create it with the CronCreate tool (or `/loop`). Fires only while this Claude Code session is open.
   - **Cloud** (`/schedule` skill): runs without the machine; needs claude.ai account access.
   - **OS** (works with Claude closed; desktop notification + log): `omnis.py reminder os-install ID` shows the cron/schtasks entry; run again with `--yes` only after the user agrees.
3. Only report success after the scheduler confirms (CronCreate returns a job id / crontab -l shows the line).
4. Manage: `reminder list|pause|resume|set|remove ID`; removing also requires deleting the CronCreate job / `os-remove ID --yes`.
