#!/usr/bin/env python3
"""Secret detection, redaction and command risk classification.

Usage:
  python security_scan.py scan [PATHS...]     scan files/dirs for secrets (values are redacted)
  python security_scan.py diff [ROOT]         scan added lines of the current git diff
  python security_scan.py classify "<cmd>"    risk class of a shell command
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import omnis_cache as oc  # noqa: E402

SECRET_PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("stripe-key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("url-credentials", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s/@]{3,}@[^\s]+", re.I)),
    # key = "literal" or KEY=literal; the value check below rejects code expressions
    ("assignment", re.compile(r"""(?i)\b[\w-]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd)[\w-]*['"]?\s*[:=]\s*(?:['"]([^'"\s]{12,})['"]|([A-Za-z0-9_+/=-]{16,})(?:\s|$))""")),
]
PLACEHOLDER = re.compile(r"(?i)^(x+|\*+|<.*>|\$\{.*\}|\{\{.*\}\}|your[_-].*|changeme|example.*|dummy|test|placeholder|process\.env.*|os\.environ.*|null|none|true|false)$")


def looks_secret(val):
    """A literal that plausibly is a credential: long, mixed letters+digits, no code syntax, not a placeholder."""
    v = val.strip()
    if PLACEHOLDER.match(v) or re.search(r"[()\[\]{}<>$]|\.\w+\(", v):
        return False
    if re.fullmatch(r"[a-z_]+|[A-Z_]+|[a-z]+(-[a-z]+)+", v):  # identifiers, kebab-case names
        return False
    return len(v) >= 12 and bool(re.search(r"\d", v)) and bool(re.search(r"[A-Za-z]", v))


def find_secrets(text):
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, rx in SECRET_PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            val = next((g for g in m.groups() if g), m.group(0)) if m.groups() else m.group(0)
            if kind == "assignment" and not looks_secret(val):
                continue
            hits.append({"line": lineno, "kind": kind, "preview": redact(line.strip())[:120]})
            break
    return hits


def redact(text):
    """Replace secret values with [REDACTED:<kind>] — safe to log or store."""
    for kind, rx in SECRET_PATTERNS:
        if kind == "assignment":
            def _sub(m):
                val = next((g for g in m.groups() if g), None)
                return m.group(0).replace(val, "[REDACTED]") if val and looks_secret(val) else m.group(0)
            text = rx.sub(_sub, text)
        else:
            text = rx.sub(f"[REDACTED:{kind}]", text)
    return text


SENSITIVE_FILES = re.compile(r"(^|/)(\.env(\..*)?|id_rsa|id_ed25519|.*\.pem|.*\.key|credentials(\.json)?|\.netrc|\.npmrc|\.pypirc|secrets?\.(json|ya?ml))$", re.I)

# (class, severity, pattern). severity: block = catastrophic, ask = needs explicit user approval
COMMAND_RULES = [
    ("destructive", "block", r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)[a-z]*\s+(/|~|\$HOME|/\*|[A-Za-z]:\\?)\s*($|;|&&|\|)"),
    ("destructive", "block", r"\bmkfs(\.\w+)?\b|\bdd\s+[^|]*of=/dev/(sd|nvme|hd|xvd)|:\(\)\s*\{\s*:\|:&\s*\};:"),
    ("destructive", "block", r"(?i)\bformat\s+[a-z]:|Remove-Item\s+.*-Recurse.*\s+(C:\\|\$env:USERPROFILE)\s*$"),
    ("remote-exec", "ask", r"(curl|wget|iwr|Invoke-WebRequest)[^|;]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|\|\s*(python3?|node|iex|Invoke-Expression)\b"),
    ("git-history", "ask", r"\bgit\s+push\b.*(--force\b|-f\b|--force-with-lease)|\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-z]*f|\bgit\s+filter-(branch|repo)\b|\bgit\s+branch\s+-D\b"),
    ("database", "ask", r"(?i)\b(drop\s+(database|schema|table)|truncate\s+table|delete\s+from\s+\w+\s*(;|$|\"|'))|\bprisma\s+migrate\s+reset\b|\bdb:drop\b|flushall|flushdb"),
    ("production", "ask", r"(?i)\b(kubectl\s+(delete|apply)|terraform\s+(apply|destroy)|vercel\s+--prod|fly\s+deploy|heroku\s+.*--app|docker\s+system\s+prune\s+-a|systemctl\s+(stop|disable)|helm\s+(uninstall|upgrade))\b"),
    ("credential", "ask", r"(^|[\s;|&])(cat|type|less|more|head|tail|Get-Content)\s+[^|;&]*(\.env\b|id_rsa|id_ed25519|\.pem\b|credentials|\.netrc)"),
    ("install", "ask", r"\b(npm|pnpm|yarn|bun)\s+(i|install|add)\s+-g\b|\bsudo\s+(apt|apt-get|yum|dnf|pacman)\s+(install|remove)|\bpip3?\s+install\s+(?!-r\b|-e\b|\.)"),
    ("permissions", "ask", r"\bchmod\s+(-R\s+)?777\b|\bchown\s+-R\b.*\s/\s*$"),
]
COMPILED_RULES = [(c, s, re.compile(p)) for c, s, p in COMMAND_RULES]


def classify(cmd):
    for cls, sev, rx in COMPILED_RULES:
        if rx.search(cmd):
            return {"class": cls, "severity": sev}
    return {"class": "normal", "severity": "allow"}


def scan_paths(paths):
    results = {}
    for p in paths:
        p = Path(p)
        files = [p] if p.is_file() else [p / f for f in oc.iter_files(p)]
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            hits = find_secrets(text)
            if hits:
                results[f.as_posix()] = hits
    return results


def scan_diff(root):
    p = subprocess.run(["git", "diff", "HEAD", "-U0"], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        p = subprocess.run(["git", "diff", "--cached", "-U0"], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    results, current = {}, None
    for line in p.stdout.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and current:
            for h in find_secrets(line[1:]):
                results.setdefault(current, []).append(h["kind"] + ": " + h["preview"])
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "classify":
        print(json.dumps(classify(" ".join(rest))))
        return 0
    res = scan_diff(rest[0] if rest else ".") if cmd == "diff" else scan_paths(rest or ["."])
    if not res:
        print("no secrets found")
        return 0
    for f, hits in res.items():
        for h in hits:
            print(f"{f}: line {h['line']} {h['kind']}: {h['preview']}" if isinstance(h, dict) else f"{f}: {h}")
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
