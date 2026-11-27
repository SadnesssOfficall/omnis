#!/usr/bin/env python3
"""Environment diagnosis: OS, shell, runtimes, tools, disk. Never prints secret values.

Usage: python env_doctor.py [--json]
"""
import json
import os
import platform
import shutil
import subprocess
import sys

TOOLS = {
    "git": ["git", "--version"], "python": [sys.executable, "--version"], "node": ["node", "--version"],
    "npm": ["npm", "--version"], "pnpm": ["pnpm", "--version"], "yarn": ["yarn", "--version"],
    "bun": ["bun", "--version"], "uv": ["uv", "--version"], "go": ["go", "version"],
    "cargo": ["cargo", "--version"], "docker": ["docker", "--version"], "gh": ["gh", "--version"],
    "rg": ["rg", "--version"], "psql": ["psql", "--version"], "mysql": ["mysql", "--version"],
    "redis-cli": ["redis-cli", "--version"], "sqlite3": ["sqlite3", "--version"],
    "playwright": ["npx", "--no-install", "playwright", "--version"],
}
SENSITIVE_ENV = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "CREDENTIAL", "AUTH")


def version(cmd):
    exe = shutil.which(cmd[0]) if not os.path.isabs(cmd[0]) else cmd[0]
    if not exe:
        return None
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=8, errors="replace")
        if p.returncode != 0:  # e.g. `npx --no-install playwright` when playwright isn't installed
            return None
        return (p.stdout or p.stderr).strip().splitlines()[0][:80] if (p.stdout or p.stderr).strip() else "present"
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return "present (version check failed)"


def diagnose():
    shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or "unknown"
    if os.environ.get("PSModulePath") and os.name == "nt":
        shell += " (PowerShell available)"
    du = shutil.disk_usage(os.getcwd())
    tools = {k: version(v) for k, v in TOOLS.items()}
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "shell": shell,
        "cwd": os.getcwd(),
        "tools": {k: v for k, v in tools.items() if v},
        "missing": sorted(k for k, v in tools.items() if not v),
        "disk_free_gb": round(du.free / 1e9, 1),
        "disk_used_pct": round(100 * du.used / du.total, 1),
        # names only, never values
        "sensitive_env_vars_present": sorted(k for k in os.environ if any(s in k.upper() for s in SENSITIVE_ENV)),
    }


def main(argv=None):
    d = diagnose()
    if argv and "--json" in argv or "--json" in sys.argv[1:]:
        print(json.dumps(d, indent=1))
        return 0
    print(f"OS: {d['os']} | shell: {d['shell']}")
    print("tools: " + ", ".join(f"{k} {v}" for k, v in d["tools"].items()))
    print("missing: " + (", ".join(d["missing"]) or "none"))
    warn = " ⚠ low disk" if d["disk_free_gb"] < 2 or d["disk_used_pct"] > 92 else ""
    print(f"disk: {d['disk_free_gb']} GB free ({d['disk_used_pct']}% used){warn}")
    if d["sensitive_env_vars_present"]:
        print("sensitive env var names present (values hidden): " + ", ".join(d["sensitive_env_vars_present"]))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
