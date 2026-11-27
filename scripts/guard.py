#!/usr/bin/env python3
"""PreToolUse hook: enforce OMNIS command policy for Bash/PowerShell tool calls.

Catastrophic commands are denied; risky ones (force-push, DROP, curl|sh, prod deploys,
printing credential files) require the user's explicit approval. Everything else passes
through to Claude Code's normal permission system untouched.

Install via `python install.py --with-hook`. Reads the hook JSON on stdin.
Override per-project with .omnis/policies.json: {"allow": ["regex", ...]}.
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


def decide(payload):
    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return None
    cmd = (payload.get("tool_input") or {}).get("command", "")
    allow = []
    pol = Path(payload.get("cwd") or ".") / ".omnis" / "policies.json"
    try:
        allow = json.loads(pol.read_text(encoding="utf-8")).get("allow", [])
    except (OSError, ValueError):
        pass
    if any(re.search(a, cmd) for a in allow):
        return None
    r = security_scan.classify(cmd)
    if r["severity"] == "allow":
        return None
    decision = "deny" if r["severity"] == "block" else "ask"
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"OMNIS policy: '{r['class']}' command"
        + (" is blocked." if decision == "deny" else " needs your explicit approval."),
    }}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0  # never break the session on malformed input
    out = decide(payload)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
