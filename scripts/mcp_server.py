#!/usr/bin/env python3
"""OMNIS MCP server: the OMNIS tools for any MCP client (Codex, Gemini CLI, Cursor, Copilot, ...).

  python mcp_server.py                         stdio transport (what every local client uses)
  python mcp_server.py --http [--port 8765]    streamable-HTTP transport on 127.0.0.1 with a bearer token

Stdlib only: a minimal JSON-RPC 2.0 implementation of the MCP tool surface
(initialize, ping, tools/list, tools/call). Every tool shells out to omnis.py, so behaviour
matches the CLI exactly. All tool output goes through the secret redactor.

HTTP mode is for local bridges only. It binds to loopback, needs a token
(--token, $OMNIS_MCP_TOKEN, or one generated into ~/.omnis/mcp-token), rejects
non-local Origin headers, and keeps the command-running `filter` tool off unless --allow-exec.
It refuses a non-loopback --host unless --allow-remote is given. Do not expose it to the internet.
"""
import argparse
import hmac
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import security_scan  # noqa: E402

VERSION = "1.1.0"
PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]
MAX_OUT = 20000

S = lambda **p: {"type": "string", **p}  # noqa: E731
ROOT = {"root": S(description="Project directory (default: server working directory)")}


def _tool(name, desc, props=None, required=None):
    return {"name": name, "description": desc,
            "inputSchema": {"type": "object", "properties": {**ROOT, **(props or {})}, "required": required or []}}


TOOLS = [
    _tool("map", "Cached project map: languages, frameworks, run/build/test commands, entry points. Call once per session instead of reading many files.",
          {"refresh": {"type": "boolean"}}),
    _tool("find", "Where is a symbol defined (incremental index).", {"name": S()}, ["name"]),
    _tool("outline", "Symbols and line numbers of a file; read only the lines you need afterwards.", {"file": S()}, ["file"]),
    _tool("deps", "Who imports this file / blast radius.", {"file": S()}, ["file"]),
    _tool("filter", "Run a shell command and return only errors, traces and the summary (full log saved, exit code kept). Risky commands are refused; run those in your own shell with user approval.",
          {"command": S()}, ["command"]),
    _tool("verify", "Checks for the current git changes; run=true executes them and reports VERIFIED/FAILED.", {"run": {"type": "boolean"}}),
    _tool("doctor", "Environment diagnosis (OS, shell, tools, disk; env var names only)."),
    _tool("security_scan", "Secret scan with redaction. mode=diff scans added lines of the git diff (do this before committing); mode=scan scans paths.",
          {"mode": S(enum=["diff", "scan"]), "paths": {"type": "array", "items": S()}}),
    _tool("security_classify", "Risk class of a shell command under the OMNIS guard policy (allow / ask / block).", {"command": S()}, ["command"]),
    _tool("memory_get", "Search project memory (decisions, conventions, gotchas) or, with error, known bug patterns.",
          {"query": S(), "error": S(description="error line to match against the bug store")}),
    _tool("memory_add", "Store a one-line durable project fact (type decision|convention|architecture|gotcha) or a bug pattern (type bug + cause + fix).",
          {"type": S(), "text": S(), "source": S(), "cause": S(), "fix": S(), "files": S()}, ["type", "text"]),
    _tool("checkpoint_save", "Save progress of a long task.", {"task": S(), "done": S(description="items separated by ;"), "next": S(), "notes": S()}, ["task"]),
    _tool("checkpoint_resume", "Resume the latest checkpoint, including git changes since."),
    _tool("usage", "Claude Code token usage from local transcripts (status|report|limits). Other tools have no local transcript data.",
          {"cmd": S(enum=["status", "report", "limits"])}),
]


class Server:
    def __init__(self, default_root=".", allow_exec=True, locked_root=None):
        self.default_root = Path(default_root).resolve()
        self.allow_exec = allow_exec
        self.locked_root = Path(locked_root).resolve() if locked_root else None

    def tools(self):
        return [t for t in TOOLS if self.allow_exec or t["name"] != "filter"]

    def _root(self, args):
        root = Path(args.get("root") or self.default_root).expanduser().resolve()
        if self.locked_root and self.locked_root != root and self.locked_root not in root.parents:
            raise ValueError(f"root must be inside {self.locked_root}")
        if not root.is_dir():
            raise ValueError(f"not a directory: {root}")
        return root

    def _omnis(self, root, argv, timeout=600):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, str(HERE / "omnis.py"), *argv], cwd=str(root), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr.strip() else "")
        return p.returncode, out

    def call(self, name, args):
        if name not in {t["name"] for t in self.tools()}:
            raise KeyError(name)
        root = self._root(args)
        argv = None
        if name == "map":
            argv = ["map", "."] + (["--refresh"] if args.get("refresh") else [])
        elif name in ("find", "outline", "deps"):
            argv = [name, args.get("name") or args.get("file") or ""]
        elif name == "filter":
            cmd = args.get("command", "")
            risk = security_scan.classify(cmd)
            if risk["severity"] != "allow":
                return 1, f"refused by OMNIS policy ('{risk['class']}', {risk['severity']}). Ask the user and run it in your own shell if they approve."
            argv = ["filter", cmd]
        elif name == "verify":
            argv = ["verify"] + (["--run"] if args.get("run") else [])
        elif name == "doctor":
            argv = ["doctor"]
        elif name == "security_scan":
            argv = ["security", "diff", "."] if args.get("mode", "diff") == "diff" else ["security", "scan", *(args.get("paths") or ["."])]
        elif name == "security_classify":
            return 0, json.dumps(security_scan.classify(args.get("command", "")))
        elif name == "memory_get":
            argv = ["memory", "bug", "match", args["error"]] if args.get("error") else (
                ["memory", "search", args["query"]] if args.get("query") else ["memory", "inspect"])
        elif name == "memory_add":
            if args["type"] == "bug":
                argv = ["memory", "bug", "add", "--signature", args["text"], "--cause", args.get("cause", "?"),
                        "--fix", args.get("fix", "?"), "--files", args.get("files", "")]
            else:
                argv = ["memory", "add", args["type"], args["text"]] + (["--source", args["source"]] if args.get("source") else [])
        elif name == "checkpoint_save":
            argv = ["checkpoint", "save", "--task", args["task"], "--done", args.get("done", ""),
                    "--next", args.get("next", ""), "--notes", args.get("notes", "")]
        elif name == "checkpoint_resume":
            argv = ["checkpoint", "resume"]
        elif name == "usage":
            argv = ["usage", args.get("cmd", "status")]
        return self._omnis(root, argv)

    def handle(self, msg):
        """One JSON-RPC message in, response dict (or None for notifications) out."""
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "method" not in msg:
            return _err(msg.get("id") if isinstance(msg, dict) else None, -32600, "invalid request")
        mid, method, params = msg.get("id"), msg["method"], msg.get("params") or {}
        if "id" not in msg:
            return None  # notification (notifications/initialized, cancelled, ...)
        if method == "initialize":
            want = params.get("protocolVersion")
            return _ok(mid, {"protocolVersion": want if want in PROTOCOLS else PROTOCOLS[0],
                             "capabilities": {"tools": {"listChanged": False}},
                             "serverInfo": {"name": "omnis", "version": VERSION},
                             "instructions": "OMNIS: use map once, find/outline instead of whole-file reads, filter for long command output, "
                                             "security_scan before commits. Never print secrets."})
        if method == "ping":
            return _ok(mid, {})
        if method == "tools/list":
            return _ok(mid, {"tools": self.tools()})
        if method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            if name not in {t["name"] for t in self.tools()}:
                return _err(mid, -32602, f"unknown tool: {name}")
            try:
                code, out = self.call(name, args)
            except (ValueError, KeyError, subprocess.TimeoutExpired) as e:
                return _ok(mid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
            out = security_scan.redact(out)
            if len(out) > MAX_OUT:
                out = out[:MAX_OUT] + f"\n… truncated ({len(out)} chars)"
            return _ok(mid, {"content": [{"type": "text", "text": out or "(no output)"}], "isError": code not in (0, None)})
        return _err(mid, -32601, f"method not found: {method}")


def _ok(mid, result):
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid, code, message):
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def dispatch(server, payload):
    if isinstance(payload, list):
        out = [r for r in (server.handle(m) for m in payload) if r]
        return out or None
    return server.handle(payload)


def serve_stdio(server):
    stdin = sys.stdin.buffer if hasattr(sys.stdin, "buffer") else sys.stdin
    for raw in stdin:
        line = raw.decode("utf-8", "replace").strip() if isinstance(raw, bytes) else raw.strip()
        if not line:
            continue
        try:
            resp = dispatch(server, json.loads(line))
        except ValueError:
            resp = _err(None, -32700, "parse error")
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def token_file():
    return Path(os.environ.get("OMNIS_HOME") or Path.home() / ".omnis") / "mcp-token"


def load_token(explicit=None):
    tok = explicit or os.environ.get("OMNIS_MCP_TOKEN")
    if tok:
        return tok
    f = token_file()
    if f.is_file():
        return f.read_text(encoding="utf-8").strip()
    f.parent.mkdir(parents=True, exist_ok=True)
    tok = secrets.token_urlsafe(32)
    f.write_text(tok, encoding="utf-8")
    try:
        os.chmod(f, 0o600)
    except OSError:
        pass
    return tok


LOCAL_ORIGINS = ("http://localhost", "http://127.0.0.1", "https://localhost", "https://127.0.0.1", "http://[::1]")


def make_http_handler(server, token):
    from http.server import BaseHTTPRequestHandler

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _send(self, code, body=None, ctype="application/json"):
            data = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
            self.send_response(code)
            if data:
                self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self):
            origin = self.headers.get("Origin")
            if origin and not origin.startswith(LOCAL_ORIGINS):
                self._send(403, {"error": "origin not allowed"})
                return False
            auth = self.headers.get("Authorization", "")
            if not hmac.compare_digest(auth.encode(), f"Bearer {token}".encode()):
                self._send(401, {"error": "missing or wrong bearer token"})
                return False
            return True

        def do_GET(self):
            if self.path.rstrip("/") == "/health":
                return self._send(200, {"ok": True, "name": "omnis", "version": VERSION})
            self._send(405, {"error": "use POST /mcp"})

        def do_DELETE(self):
            self._send(405)

        def do_POST(self):
            if self.path.split("?")[0].rstrip("/") != "/mcp":
                return self._send(404, {"error": "not found"})
            if not self._authorized():
                return
            n = int(self.headers.get("Content-Length") or 0)
            if n > 1_000_000:
                return self._send(413)
            try:
                resp = dispatch(server, json.loads(self.rfile.read(n).decode("utf-8")))
            except ValueError:
                resp = _err(None, -32700, "parse error")
            if resp is None:
                return self._send(202)
            self._send(200, resp)

    return H


def serve_http(server, host, port, token):
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer((host, port), make_http_handler(server, token))
    print(f"OMNIS MCP (streamable HTTP) on http://{host}:{port}/mcp — token in {token_file()} or $OMNIS_MCP_TOKEN", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return httpd


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="default project dir (stdio) / allowed root (http)")
    ap.add_argument("--http", action="store_true")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token")
    ap.add_argument("--allow-exec", action="store_true", help="http: enable the command-running filter tool")
    ap.add_argument("--allow-remote", action="store_true", help="http: allow a non-loopback --host (put TLS + auth in front!)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not a.http:
        serve_stdio(Server(a.root))
        return 0
    if a.host not in ("127.0.0.1", "localhost", "::1") and not a.allow_remote:
        sys.exit("refusing to bind a non-loopback host without --allow-remote")
    serve_http(Server(a.root, allow_exec=a.allow_exec, locked_root=a.root), a.host, a.port, load_token(a.token))
    return 0


if __name__ == "__main__":
    sys.exit(main())
