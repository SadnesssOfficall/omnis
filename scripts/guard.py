#!/usr/bin/env python3
"""Shell-command safety hook: enforce the OMNIS command policy in any AI tool that has a hook.

Catastrophic commands are denied; risky ones (force-push, DROP, curl|sh, prod deploys,
printing credential files) need the user's explicit approval where the tool can ask.
Everything else passes through to the tool's normal permission system untouched.

  python guard.py                    Claude Code PreToolUse (default)
  python guard.py --format codex     Codex CLI PreToolUse hook (same JSON shape; "ask" is not
                                     supported there, so risky commands fall back to Codex approvals)
  python guard.py --format gemini    Gemini CLI BeforeTool hook (allow/deny only)
  python guard.py --format cursor    Cursor beforeShellExecution hook (allow/deny/ask)

Reads the hook JSON on stdin. Per-project override: .omnis/policies.json {"allow": ["regex", ...]}.
Malformed input never breaks the session (exit 0, no output).
"""
import json
import re
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security_scan  # noqa: E402

SHELL_TOOLS = {"Bash", "PowerShell", "shell", "local_shell", "exec_command", "run_shell_command"}


def _command(payload):
    if "command" in payload and isinstance(payload.get("command"), str):  # cursor
        return payload["command"]
    if payload.get("tool_name") not in SHELL_TOOLS:
        return None
    ti = payload.get("tool_input") or {}
    cmd = ti.get("command", "")
    if isinstance(cmd, list):  # codex may pass argv
        cmd = " ".join(str(c) for c in cmd)
    return cmd if isinstance(cmd, str) else None


def evaluate(payload):
    """Return (decision, reason) with decision in allow|ask|deny."""
    cmd = _command(payload)
    if cmd is None:
        return "allow", ""
    pol = Path(payload.get("cwd") or ".") / ".omnis" / "policies.json"
    try:
        allow = json.loads(pol.read_text(encoding="utf-8")).get("allow", [])
    except (OSError, ValueError):
        allow = []
    if any(re.search(a, cmd) for a in allow):
        return "allow", ""
    r = security_scan.classify(cmd)
    if r["severity"] == "allow":
        return "allow", ""
    decision = "deny" if r["severity"] == "block" else "ask"
    reason = f"OMNIS policy: '{r['class']}' command" + (" is blocked." if decision == "deny" else " needs your explicit approval.")
    return decision, reason


def render(fmt, decision, reason):
    """Tool-specific hook output, or None for 'say nothing' (normal permission flow)."""
    if fmt == "cursor":
        return {"permission": decision, "userMessage": reason, "agentMessage": reason} if decision != "allow" else {"permission": "allow"}
    if decision == "allow":
        return None
    if fmt == "gemini":
        return {"decision": "deny", "reason": reason} if decision == "deny" else None
    if fmt == "codex" and decision == "ask":
        return None  # Codex has no "ask" from hooks; its own approval policy + omnis.rules handle it
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": reason}}


def decide(payload, fmt="claude"):
    d, reason = evaluate(payload)
    return render(fmt, d, reason)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    fmt = argv[argv.index("--format") + 1] if "--format" in argv and argv.index("--format") + 1 < len(argv) else "claude"
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    out = decide(payload, fmt)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
