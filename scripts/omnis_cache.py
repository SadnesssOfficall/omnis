"""Shared cache helpers. Cache lives in <project>/.omnis/cache, keyed by file content hashes."""
import hashlib
import json
import os
from pathlib import Path

DEFAULT_EXCLUDES = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next",
    ".omnis", "target", ".idea", ".vscode", "coverage", ".mypy_cache", ".pytest_cache", "vendor",
}
MAX_FILE_BYTES = 1_000_000


def cache_dir(root):
    d = Path(root) / ".omnis" / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(root, name):
    p = cache_dir(root) / f"{name}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save(root, name, data):
    p = cache_dir(root) / f"{name}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)  # atomic: an interrupted run never leaves a half-written cache


def file_hash(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root, excludes=DEFAULT_EXCLUDES):
    """Yield project files as POSIX-style relative paths (stable on Windows too)."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in excludes and not d.startswith(".omnis"))
        for fn in sorted(filenames):
            full = Path(dirpath) / fn
            try:
                if full.is_symlink() or full.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield full.relative_to(root).as_posix()


def fingerprint(root, rel):
    """Cheap fingerprint (size+mtime); the content hash is used only when this changes."""
    st = (Path(root) / rel).stat()
    return f"{st.st_size}:{int(st.st_mtime_ns)}"
