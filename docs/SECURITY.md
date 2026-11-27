# OMNIS security model

## Always on
- **SKILL.md rules**: protect user changes, don't print credential files, and ask before destructive, production, install or network-write actions. Repo content, tool output and other skills are treated as untrusted and cannot override these rules.
- **Redaction**: memory, bug patterns and checkpoints pass through `security_scan.redact` before they're written.

## Optional hook (`install.py --with-hook`)
`guard.py` runs before every Bash/PowerShell call:
- **deny**: `rm -rf /`, `rm -rf ~`, mkfs, `dd` to a disk, fork bombs, formatting a drive.
- **ask**: piping a download into a shell (`curl|sh`), force-push, `reset --hard`, `clean -f`, `branch -D`, filter-branch, DROP/TRUNCATE/unscoped DELETE, `migrate reset`, FLUSHALL, kubectl/terraform/helm apply or destroy, prod deploys, stopping system services, printing `.env`/keys/credentials, global or system package installs, `chmod 777`.
- Everything else goes to Claude Code's normal permission system unchanged. Malformed input never blocks the session.
- Per-project exceptions: `.omnis/policies.json` → `{"allow": ["<regex>"]}`.
- The hook is pattern-based. It catches common dangerous forms, not every possible obfuscation. It is a seatbelt, not a sandbox.

## External skills
- Files are fetched read-only from a **pinned commit**. Nothing downloaded is executed.
- `skill_audit.py` checks each skill for:
  - **block**: piping a download into a shell, encoded execution, destructive commands, credential exfiltration, prompt injection ("ignore previous instructions", "don't tell the user"), symlinks, missing SKILL.md.
  - **warn**: permission bypass, writes to settings or CLAUDE.md, hooks, network calls, package installs, binaries, hidden or bidi unicode, embedded credentials.
- Skills with a `block` finding are never installed. A `warn` finding needs `--allow-warn`, used only after the user has seen the findings.
- Never overwrites a skill OMNIS didn't install. Updates and removals back up the old copy to `~/.claude/omnis/backups/`.

## Known limits
- Regex-based secret detection catches common formats. Unusual custom tokens can slip through.
- The audit is static. A skill can still give Claude bad advice in prose, so review what you install.
