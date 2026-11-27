#!/usr/bin/env python3
"""OMNIS Developer-OS hooks for Claude Code. One script, one mode per hook event. All cheap, all conditional.

  os_hooks.py protect      PreToolUse  Edit|Write|MultiEdit|NotebookEdit  → ask before touching .env*/keys/lockfiles
  os_hooks.py post-edit    PostToolUse Edit|Write|MultiEdit               → secret scan of the edited file;
                                                                           prettier/eslint --fix on it if the project has them
  os_hooks.py prompt       UserPromptSubmit                               → remembers when the turn started (no output)
  os_hooks.py stop         Stop                                           → tsc --noEmit once if .ts/.tsx changed this turn;
                                                                           Windows toast if the turn took > OMNIS_TOAST_MIN (3) min
  os_hooks.py session      SessionStart                                   → after compaction: re-inject the latest checkpoint;
                                                                           new repo: one-line stack + skill hints
  os_hooks.py precompact   PreCompact                                     → auto checkpoint (task-state survives compaction)

Loop safety: Stop blocks at most once (never when stop_hook_active is set). Every failure exits 0 silently.
Disable one hook: delete its entry in ~/.claude/settings.json, or set OMNIS_HOOKS_OFF=protect,stop,... .
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PROTECTED = re.compile(r"(^|[\\/])(\.env(\.[\w.-]+)?|id_rsa|id_ed25519|[^\\/]+\.pem|[^\\/]+\.key|credentials\.json|"
                       r"package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|poetry\.lock|uv\.lock|Cargo\.lock|composer\.lock|Gemfile\.lock)$", re.I)
ENV_EXAMPLE = re.compile(r"\.env\.(example|sample|template|dist)$", re.I)
PRETTIER_CFG = [".prettierrc", ".prettierrc.json", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.mjs", ".prettierrc.yaml",
                ".prettierrc.yml", "prettier.config.js", "prettier.config.cjs", "prettier.config.mjs"]
ESLINT_CFG = ["eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts", ".eslintrc", ".eslintrc.js",
              ".eslintrc.cjs", ".eslintrc.json"]
FMT_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".css", ".scss", ".md", ".html", ".vue", ".svelte", ".yaml", ".yml"}
LINT_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue"}


def state_dir():
    d = Path(os.environ.get("OMNIS_HOME") or Path.home() / ".omnis") / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sid(p):
    return re.sub(r"[^\w-]", "", str(p.get("session_id") or "default"))[:64] or "default"


def _file(p):
    ti = p.get("tool_input") or {}
    return ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""


def _project(p, f=None):
    cwd = Path(p.get("cwd") or ".")
    if f:
        for parent in Path(f).resolve().parents:
            if (parent / "package.json").is_file() or (parent / ".git").exists():
                return parent
    return cwd


def _bin(root, name):
    for d in (root / "node_modules" / ".bin",):
        for cand in (name + ".cmd", name) if os.name == "nt" else (name,):
            if (d / cand).is_file():
                return str(d / cand)
    return None


def protect(p):
    f = _file(p)
    if not f or ENV_EXAMPLE.search(f) or not PROTECTED.search(f.replace("\\", "/")):
        return None
    kind = "lock file" if "lock" in Path(f).name.lower() else "secret/credential file"
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                   "permissionDecisionReason": f"OMNIS: {Path(f).name} is a protected {kind}. Approve only if you asked for this change."}}


def post_edit(p):
    f = _file(p)
    if not f or not Path(f).is_file():
        return None
    _note_edit(p, f)
    msgs = []
    try:
        import security_scan
        if Path(f).stat().st_size < 2_000_000 and not PROTECTED.search(f.replace("\\", "/")):
            hits = security_scan.find_secrets(Path(f).read_text(encoding="utf-8", errors="replace"))
            if hits:
                msgs.append("OMNIS secret scan: " + "; ".join(f"line {h['line']} {h['kind']}" for h in hits[:5])
                            + f" in {Path(f).name}. Move the value to an env var / secret store; never commit it.")
    except Exception:  # noqa: BLE001 — a hook must never break the session
        pass
    ext = Path(f).suffix.lower()
    root = _project(p, f)
    try:
        if ext in FMT_EXT and any((root / c).is_file() for c in PRETTIER_CFG) and _bin(root, "prettier"):
            subprocess.run([_bin(root, "prettier"), "--write", "--log-level", "warn", f], cwd=root, capture_output=True, timeout=30)
        elif ext in LINT_EXT and any((root / c).is_file() for c in ESLINT_CFG) and _bin(root, "eslint"):
            subprocess.run([_bin(root, "eslint"), "--fix", f], cwd=root, capture_output=True, timeout=45)
    except (OSError, subprocess.SubprocessError):
        pass
    if msgs:
        return {"decision": "block", "reason": " ".join(msgs)}
    return None


def _note_edit(p, f):
    s = state_dir() / f"edits-{_sid(p)}.txt"
    with s.open("a", encoding="utf-8") as fh:
        fh.write(f + "\n")


def prompt(p):
    (state_dir() / f"turn-{_sid(p)}.txt").write_text(str(time.time()), encoding="utf-8")
    return None


def toast(title, text):
    if os.name != "nt" or os.environ.get("OMNIS_NO_TOAST"):
        return False
    try:
        import toast as t
        return t.show(title, text)
    except Exception:  # noqa: BLE001
        return False


def stop(p):
    sid = _sid(p)
    edits = state_dir() / f"edits-{sid}.txt"
    changed = edits.read_text(encoding="utf-8").splitlines() if edits.is_file() else []
    if edits.is_file():
        edits.unlink()
    out = None
    ts = [f for f in changed if f.lower().endswith((".ts", ".tsx"))]
    if ts and not p.get("stop_hook_active"):
        root = _project(p, ts[0])
        tsc = _bin(root, "tsc")
        if tsc and (root / "tsconfig.json").is_file():
            try:
                r = subprocess.run([tsc, "--noEmit", "-p", str(root / "tsconfig.json")], cwd=root, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=180)
                if r.returncode != 0:
                    errs = [l for l in r.stdout.splitlines() if "error TS" in l]
                    out = {"decision": "block", "reason": f"OMNIS typecheck: {len(errs)} TypeScript error(s) after your edits:\n"
                           + "\n".join(errs[:15]) + "\nFix them (or say why not) before finishing."}
            except (OSError, subprocess.SubprocessError):
                pass
    turn = state_dir() / f"turn-{sid}.txt"
    try:
        started = float(turn.read_text(encoding="utf-8"))
        mins = (time.time() - started) / 60
        if mins >= float(os.environ.get("OMNIS_TOAST_MIN", "3")) and out is None:
            toast("Claude Code bitti", f"Uzun görev tamamlandı ({mins:.0f} dk).")
            turn.unlink()
    except (OSError, ValueError):
        pass
    return out


def session(p):
    cwd = Path(p.get("cwd") or ".")
    src = p.get("source")
    ctx = []
    if src in ("compact", "resume"):
        try:
            import checkpoint
            txt = checkpoint.render_resume(cwd)
            if txt and "no checkpoint" not in txt.lower():
                ctx.append("OMNIS task-state (latest checkpoint):\n" + txt[:3000])
        except Exception:  # noqa: BLE001
            pass
    if src == "startup":
        try:
            import project_adapt
            hint = project_adapt.session_hint(cwd)
            if hint:
                ctx.append(hint)
        except Exception:  # noqa: BLE001
            pass
    if not ctx:
        return None
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n\n".join(ctx)}}


def precompact(p):
    cwd = Path(p.get("cwd") or ".")
    if not (cwd / ".git").exists():
        return None
    try:
        import checkpoint
        checkpoint.save(cwd, "auto checkpoint before compaction", notes=f"trigger={p.get('trigger', '?')}")
    except Exception:  # noqa: BLE001
        pass
    return None


MODES = {"protect": protect, "post-edit": post_edit, "prompt": prompt, "stop": stop, "session": session, "precompact": precompact}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mode = argv[0] if argv else ""
    if mode not in MODES or mode in (os.environ.get("OMNIS_HOOKS_OFF") or "").split(","):
        return 0
    try:
        payload = json.load(sys.stdin)
        out = MODES[mode](payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001
        return 0
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
