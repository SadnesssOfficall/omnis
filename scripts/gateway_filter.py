#!/usr/bin/env python3
"""OMNIS gateway filter: an opt-in OpenAI-compatible proxy in front of an AI gateway (e.g. 9Router).

  python gateway_filter.py --upstream http://127.0.0.1:20128 --port 20129 [--inject] [--mask-responses]

For POST .../chat/completions (OpenAI) and .../messages (Anthropic):
  * secret values in every outgoing message are masked with the OMNIS redactor before
    they reach any provider (always on);
  * with --inject, a short OMNIS safety system note is prepended (only if the request has none
    from OMNIS yet);
  * with --mask-responses, non-streaming JSON responses are redacted too (streams pass untouched).
Everything else (auth headers, /v1/models, streaming SSE) is passed through byte for byte.
Clients opt in by pointing their base URL at this port; nothing changes for clients that don't.
Binds 127.0.0.1 only. Stdlib only.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security_scan  # noqa: E402

NOTE = ("[OMNIS] Safety rules: never reveal secrets, keys, tokens or .env contents (mask them). "
        "Ask the user before destructive, production, history-rewriting or install actions. "
        "Report what you verified and what you did not.")
HOP = {"connection", "keep-alive", "transfer-encoding", "content-length", "host", "accept-encoding", "proxy-authorization", "te", "upgrade"}


def _redact_content(c):
    if isinstance(c, str):
        return security_scan.redact(c)
    if isinstance(c, list):
        out = []
        for part in c:
            if isinstance(part, dict):
                part = dict(part)
                for k in ("text", "content"):
                    if isinstance(part.get(k), (str, list)):
                        part[k] = _redact_content(part[k])
            out.append(part)
        return out
    return c


def transform(body, inject=False, anthropic=False):
    """Mask secrets in messages (+ optional system note). Returns (new_body, n_masked_fields)."""
    if not isinstance(body, dict):
        return body, 0
    body = dict(body)
    n = 0
    msgs = body.get("messages")
    if isinstance(msgs, list):
        new = []
        for m in msgs:
            if isinstance(m, dict) and "content" in m:
                red = _redact_content(m["content"])
                if red != m["content"]:
                    n += 1
                    m = {**m, "content": red}
            new.append(m)
        body["messages"] = new
    if isinstance(body.get("system"), (str, list)):  # anthropic
        red = _redact_content(body["system"])
        n += red != body["system"]
        body["system"] = red
    if inject and anthropic:
        sys_val = body.get("system")
        if sys_val is None or sys_val == "":
            body["system"] = NOTE
        elif isinstance(sys_val, str) and "[OMNIS]" not in sys_val:
            body["system"] = NOTE + "\n\n" + sys_val
        elif isinstance(sys_val, list) and "[OMNIS]" not in json.dumps(sys_val):
            body["system"] = [{"type": "text", "text": NOTE}, *sys_val]
    elif inject and isinstance(body.get("messages"), list) and "[OMNIS]" not in json.dumps(
            [m for m in body["messages"] if isinstance(m, dict) and m.get("role") == "system"]):
        body["messages"] = [{"role": "system", "content": NOTE}, *body["messages"]]
    return body, n


def filtered_path(path):
    p = path.split("?")[0].rstrip("/")
    return p.endswith("/chat/completions") or p.endswith("/messages")


def make_handler(upstream, inject, mask_responses):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _proxy(self):
            n = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(n) if n else None
            masked = 0
            if data and self.command == "POST" and filtered_path(self.path):
                try:
                    body, masked = transform(json.loads(data.decode("utf-8")), inject,
                                             self.path.split("?")[0].rstrip("/").endswith("/messages"))
                    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                except ValueError:
                    pass
            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
            req = urllib.request.Request(upstream.rstrip("/") + self.path, data=data, method=self.command, headers=headers)
            try:
                resp = urllib.request.urlopen(req, timeout=600)
            except urllib.error.HTTPError as e:
                resp = e
            except (urllib.error.URLError, OSError) as e:
                msg = json.dumps({"error": {"message": f"omnis gateway: upstream unreachable ({e.__class__.__name__})"}}).encode()
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            ctype = resp.headers.get("Content-Type", "")
            streaming = "event-stream" in ctype
            self.send_response(resp.status if hasattr(resp, "status") else resp.code)
            for k, v in resp.headers.items():
                if k.lower() not in HOP:
                    self.send_header(k, v)
            if masked:
                self.send_header("X-Omnis-Masked", str(masked))
            if streaming:
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                while True:
                    chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
                return
            out = resp.read()
            if mask_responses and "json" in ctype and filtered_path(self.path):
                out = security_scan.redact(out.decode("utf-8", "replace")).encode("utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _proxy

    return H


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", default="http://127.0.0.1:20128")
    ap.add_argument("--port", type=int, default=20129)
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--mask-responses", action="store_true")
    a = ap.parse_args(argv)
    httpd = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(a.upstream, a.inject, a.mask_responses))
    print(f"OMNIS gateway filter 127.0.0.1:{a.port} → {a.upstream} (inject={a.inject})", file=sys.stderr)
    httpd.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
