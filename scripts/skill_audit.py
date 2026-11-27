#!/usr/bin/env python3
"""Static audit of a skill directory before installation. Treats all content as untrusted.

Usage: python skill_audit.py PATH [PATH...] [--json]

Verdicts: pass | warn (needs explicit approval) | block (never installed).
Score = 100 - sum(finding weights), shown with every finding so it is transparent.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from security_scan import find_secrets  # noqa: E402

# (id, severity, weight, regex, explanation). Scanned across every text file.
RULES = [
    ("remote-pipe-exec", "block", 60, r"(curl|wget|iwr|Invoke-WebRequest)[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b|\|\s*iex\b|Invoke-Expression\s*\(\s*(New-Object|iwr|Invoke-WebRequest)", "downloads and executes remote code"),
    ("encoded-exec", "block", 60, r"base64\s+(-d|--decode)[^\n]*\|\s*(ba)?sh|eval\s*\(\s*(atob|Buffer\.from)\(|exec\s*\(\s*(base64\.b64decode|codecs\.decode)|powershell[^\n]*-enc(odedcommand)?\s", "executes obfuscated/encoded payload"),
    ("destructive", "block", 60, r"\brm\s+-rf\s+(/|~|\$HOME)(\s|$)|\bmkfs\b|del\s+/s\s+/q\s+[a-z]:\\", "destructive filesystem command"),
    ("credential-exfil", "block", 60, r"(\.ssh/id_|\.aws/credentials|\.claude/\.credentials|\.netrc|\.git-credentials)[^\n]*(curl|wget|fetch|requests\.|http)|(curl|wget|fetch|requests\.post)[^\n]*(\.ssh/id_|\.aws/credentials|\.netrc)", "reads credentials and sends them over the network"),
    ("prompt-injection", "block", 50, r"(?i)ignore (all |any )?(previous|prior|above|other) (instructions|rules)|disregard (the )?(system|safety|previous)|you are no longer claude|do not (tell|inform) the user|without (asking|telling) the user", "tries to override instructions or hide actions from the user"),
    ("permission-bypass", "warn", 25, r"(?i)--dangerously-skip-permissions|bypassPermissions|\"defaultMode\"\s*:\s*\"bypass|permissionDecision\"\s*:\s*\"allow", "disables or bypasses Claude Code permission prompts"),
    ("settings-write", "warn", 20, r"(?i)(settings(\.local)?\.json|CLAUDE\.md)[^\n]*(write|>>|>\s|open\([^)]*['\"]w)", "modifies Claude Code settings or memory files"),
    ("hooks", "warn", 15, r"(?i)\"hooks\"\s*:|PreToolUse|PostToolUse|SessionStart|UserPromptSubmit", "registers lifecycle hooks (runs code automatically)"),
    ("network", "warn", 8, r"(?i)\b(curl|wget|requests\.(get|post)|urllib\.request|fetch\(|axios|http\.client|Invoke-WebRequest)\b", "makes network requests"),
    ("package-install", "warn", 8, r"(?i)\b(npm|pnpm|yarn)\s+(i|install|add)\b|\bpip3?\s+install\b|\bapt(-get)?\s+install\b|\bbrew\s+install\b", "installs packages"),
    ("subprocess", "info", 3, r"\bsubprocess\.|child_process|os\.system\(|\bexec(Sync)?\(", "runs shell commands"),
]
COMPILED = [(i, s, w, re.compile(p), e) for i, s, w, p, e in RULES]
BINARY_EXT = {".exe", ".dll", ".so", ".dylib", ".bin", ".jar", ".pyc", ".node", ".wasm"}
TEXT_LIMIT = 2_000_000


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


def audit(path):
    path = Path(path)
    findings, files, total_bytes = [], [], 0
    skill_md = path / "SKILL.md"
    fm = None
    if not skill_md.is_file():
        findings.append(("no-skill-md", "block", 100, "SKILL.md", "not a skill: SKILL.md missing"))
    else:
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        if not fm or not fm.get("name") or not fm.get("description"):
            findings.append(("bad-frontmatter", "warn", 20, "SKILL.md", "frontmatter missing name/description"))
    for f in sorted(path.rglob("*")):
        rel = f.relative_to(path).as_posix()
        if f.is_symlink():
            findings.append(("symlink", "block", 60, rel, "symlink inside skill (could point outside)"))
            continue
        if not f.is_file():
            continue
        files.append(rel)
        size = f.stat().st_size
        total_bytes += size
        if f.suffix.lower() in BINARY_EXT:
            findings.append(("binary", "warn", 20, rel, "ships a compiled binary that cannot be reviewed"))
            continue
        if size > TEXT_LIMIT:
            findings.append(("huge-file", "warn", 10, rel, f"{size} bytes — not scanned"))
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if re.search(r"[​-‏‪-‮⁦-⁩]", text):
            findings.append(("hidden-unicode", "warn", 25, rel, "invisible/bidi unicode characters (can hide instructions)"))
        for rid, sev, w, rx, expl in COMPILED:
            m = rx.search(text)
            if m:
                line = text[:m.start()].count("\n") + 1
                findings.append((rid, sev, w, f"{rel}:{line}", expl))
        if find_secrets(text):
            findings.append(("embedded-secret", "warn", 20, rel, "contains something that looks like a credential"))
    # de-duplicate same rule in many files: keep first, count the rest
    seen, uniq = {}, []
    for fnd in findings:
        if fnd[0] in seen:
            seen[fnd[0]] += 1
            continue
        seen[fnd[0]] = 1
        uniq.append(fnd)
    score = max(0, 100 - sum(f[2] for f in uniq))
    sev = {f[1] for f in uniq}
    verdict = "block" if "block" in sev else "warn" if "warn" in sev else "pass"
    desc = (fm or {}).get("description", "")
    return {
        "path": path.as_posix(), "name": (fm or {}).get("name") or path.name, "verdict": verdict, "score": score,
        "findings": [{"rule": r, "severity": s, "weight": w, "where": loc, "why": e, "occurrences": seen[r]} for r, s, w, loc, e in uniq],
        "files": len(files), "bytes": total_bytes,
        # always-loaded cost is the frontmatter description; the body loads only when the skill is used
        "context_overhead": {"always_tokens_est": len(desc) // 4 + 10,
                             "on_use_tokens_est": (skill_md.stat().st_size // 4) if skill_md.is_file() else 0},
        "description": desc[:200],
    }


def render(r):
    out = [f"{r['name']}: {r['verdict'].upper()} (score {r['score']}/100) — {r['files']} files, {r['bytes']} B, "
           f"context ~{r['context_overhead']['always_tokens_est']} tok always / ~{r['context_overhead']['on_use_tokens_est']} tok when used (est.)"]
    for f in r["findings"]:
        out.append(f"   [{f['severity']}] -{f['weight']} {f['rule']} at {f['where']}" + (f" (+{f['occurrences'] - 1} more)" if f["occurrences"] > 1 else "") + f": {f['why']}")
    return "\n".join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    as_json = "--json" in argv
    paths = [a for a in argv if a != "--json"]
    if not paths:
        print(__doc__)
        return 2
    results = [audit(p) for p in paths]
    print(json.dumps(results, indent=1) if as_json else "\n".join(render(r) for r in results))
    return 1 if any(r["verdict"] == "block" for r in results) else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
