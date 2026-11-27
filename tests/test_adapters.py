"""MCP server, multi-tool installer targets, guard formats and the gateway filter."""
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import gateway_filter  # noqa: E402
import guard  # noqa: E402
import install  # noqa: E402
import mcp_server  # noqa: E402

RM_ROOT = "rm -rf " + "/"


class TestMcpStdio(unittest.TestCase):
    def rpc(self, msgs, root):
        lines = "\n".join(json.dumps(m) for m in msgs) + "\n"
        p = subprocess.run([sys.executable, str(SCRIPTS / "mcp_server.py"), "--root", str(root)], input=lines.encode(),
                           capture_output=True, timeout=120)
        return [json.loads(l) for l in p.stdout.decode("utf-8").splitlines() if l.strip()]

    def test_initialize_list_call(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "app.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
            out = self.rpc([
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "find", "arguments": {"name": "hello"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "nope"},
            ], d)
        self.assertEqual([r["id"] for r in out], [1, 2, 3, 4])  # notification got no reply
        self.assertEqual(out[0]["result"]["protocolVersion"], "2025-03-26")
        names = {t["name"] for t in out[1]["result"]["tools"]}
        self.assertTrue({"map", "find", "outline", "deps", "filter", "verify", "doctor", "security_scan",
                         "memory_get", "memory_add", "checkpoint_save", "checkpoint_resume", "usage"} <= names)
        self.assertIn("app.py", out[2]["result"]["content"][0]["text"])
        self.assertEqual(out[3]["error"]["code"], -32601)

    def test_filter_refuses_risky_and_output_is_redacted(self):
        s = mcp_server.Server(".")
        r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "filter", "arguments": {"command": RM_ROOT}}})
        self.assertTrue(r["result"]["isError"])
        self.assertIn("refused", r["result"]["content"][0]["text"])
        r = s.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                      "params": {"name": "filter", "arguments": {"command": f'"{sys.executable}" -c "print(\'sk-ant-' + "a" * 30 + '\')"'}}})
        self.assertNotIn("a" * 30, r["result"]["content"][0]["text"])
        self.assertEqual(s.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "zzz"}})["error"]["code"], -32602)

    def test_memory_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            s = mcp_server.Server(d)
            s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "memory_add", "arguments": {"type": "decision", "text": "use sqlite for cache"}}})
            r = s.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "memory_get", "arguments": {"query": "sqlite"}}})
            self.assertIn("sqlite", r["result"]["content"][0]["text"])


class TestMcpHttp(unittest.TestCase):
    def test_token_origin_and_no_exec(self):
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as d:
            srv = mcp_server.Server(d, allow_exec=False, locked_root=d)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), mcp_server.make_http_handler(srv, "tok123"))
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            url = f"http://127.0.0.1:{httpd.server_address[1]}/mcp"

            def post(body, headers):
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
                try:
                    with urllib.request.urlopen(req, timeout=30) as r:
                        return r.status, json.loads(r.read() or b"null")
                except urllib.error.HTTPError as e:
                    return e.code, None
            lst = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            self.assertEqual(post(lst, {})[0], 401)
            self.assertEqual(post(lst, {"Authorization": "Bearer tok123", "Origin": "https://evil.example"})[0], 403)
            code, body = post(lst, {"Authorization": "Bearer tok123"})
            self.assertEqual(code, 200)
            self.assertNotIn("filter", {t["name"] for t in body["result"]["tools"]})
            code, body = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "map", "arguments": {"root": str(Path(d).parent)}}},
                              {"Authorization": "Bearer tok123"})
            self.assertTrue(body["result"]["isError"])  # outside locked root
            self.assertEqual(post({"jsonrpc": "2.0", "method": "notifications/initialized"}, {"Authorization": "Bearer tok123"})[0], 202)
            httpd.shutdown()

    def test_refuses_public_bind(self):
        with self.assertRaises(SystemExit):
            mcp_server.main(["--http", "--host", "0.0.0.0"])


class TestGuardFormats(unittest.TestCase):
    def test_formats(self):
        bash = {"tool_name": "Bash", "tool_input": {"command": RM_ROOT}}
        self.assertEqual(guard.decide(bash)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(guard.decide(bash, "codex")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(guard.decide({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}}, "codex"))
        g = guard.decide({"tool_name": "run_shell_command", "tool_input": {"command": RM_ROOT}}, "gemini")
        self.assertEqual(g["decision"], "deny")
        self.assertIsNone(guard.decide({"tool_name": "run_shell_command", "tool_input": {"command": "ls"}}, "gemini"))
        self.assertEqual(guard.decide({"command": "git push --force", "cwd": "."}, "cursor")["permission"], "ask")
        self.assertEqual(guard.decide({"command": "ls"}, "cursor")["permission"], "allow")


class TestInstallTargets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "ev"
        for d in (".codex", ".gemini/antigravity", ".cursor", ".codeium/windsurf", ".config/opencode", ".continue"):
            (self.home / d).mkdir(parents=True)
        (self.home / ".codex" / "config.toml").write_text('model = "x"\n', encoding="utf-8")
        (self.home / ".gemini" / "settings.json").write_text('{"theme": "dark"}', encoding="utf-8")
        (self.home / ".cursor" / "mcp.json").write_text('{\n  // my servers\n  "mcpServers": {"other": {"command": "x"}},\n}\n', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_install(self, *argv):
        ns = type("A", (), {"project": None, "with_hook": False, "uninstall": False, "verify": False, "yes": False, "target": None})()
        args = list(argv)
        ns.yes = "--yes" in args
        ns.uninstall = "--uninstall" in args
        ns.target = args[args.index("--target") + 1]
        if "--project" in args:
            ns.project = args[args.index("--project") + 1]
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = install.targets_main(ns, home=self.home)
        return rc, buf.getvalue()

    def test_dry_run_writes_nothing(self):
        before = sorted(str(p) for p in self.home.rglob("*"))
        rc, out = self.run_install("--target", "codex,gemini,cursor")
        self.assertEqual(rc, 0)
        self.assertIn("dry run", out)
        self.assertEqual(before, sorted(str(p) for p in self.home.rglob("*")))

    def test_install_idempotent_uninstall(self):
        names = "codex,gemini,antigravity,cursor,vscode,windsurf,opencode,continue"
        self.run_install("--target", names, "--yes")
        cfg = (self.home / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('model = "x"', cfg)
        self.assertEqual(cfg.count("[mcp_servers.omnis]"), 1)
        self.assertTrue((self.home / ".codex" / "rules" / "omnis.rules").is_file())
        hooks = json.loads((self.home / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("guard.py", hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"])
        gem = json.loads((self.home / ".gemini" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(gem["theme"], "dark")
        self.assertIn("omnis", gem["mcpServers"])
        self.assertIn("BeforeTool", gem["hooks"])
        cur = json.loads((self.home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(set(cur["mcpServers"]), {"other", "omnis"})  # JSONC preserved semantically
        self.assertTrue((self.home / ".omnis" / "app" / "scripts" / "mcp_server.py").is_file())
        self.assertTrue(any((self.home / ".omnis" / "backups").rglob("mcp.json")))
        # second run: nothing changes
        _, out = self.run_install("--target", names.replace("vscode,", ""), "--yes")
        self.assertNotRegex(out, r"\n  [+~] (?!.*\.omnis)")
        self.assertEqual((self.home / ".codex" / "config.toml").read_text(encoding="utf-8").count("[mcp_servers.omnis]"), 1)
        # uninstall
        self.run_install("--target", names, "--uninstall", "--yes")
        self.assertNotIn("omnis", (self.home / ".codex" / "config.toml").read_text(encoding="utf-8"))
        self.assertFalse((self.home / ".codex" / "rules" / "omnis.rules").exists())
        self.assertFalse((self.home / ".codex" / "AGENTS.md").exists())
        gem = json.loads((self.home / ".gemini" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(gem, {"theme": "dark"})
        self.assertEqual(set(json.loads((self.home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]), {"other"})

    def test_agents_md_project_block(self):
        proj = Path(self.tmp.name) / "repo"
        proj.mkdir()
        (proj / "AGENTS.md").write_text("# Mine\nkeep me\n", encoding="utf-8")
        self.run_install("--target", "agents", "--project", str(proj), "--yes")
        self.run_install("--target", "agents", "--project", str(proj), "--yes")
        t = (proj / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(t.count(install.MD_BEGIN), 1)
        self.assertIn("keep me", t)
        self.run_install("--target", "agents", "--project", str(proj), "--uninstall", "--yes")
        self.assertEqual((proj / "AGENTS.md").read_text(encoding="utf-8"), "# Mine\nkeep me\n")

    def test_unknown_target(self):
        rc, out = self.run_install("--target", "nosuch")
        self.assertEqual(rc, 2)

    def test_foreign_codex_entry_left_alone(self):
        (self.home / ".codex" / "config.toml").write_text('[mcp_servers.omnis]\ncommand = "mine"\n', encoding="utf-8")
        _, out = self.run_install("--target", "codex", "--yes")
        self.assertIn("not managed by OMNIS", out)
        self.assertEqual((self.home / ".codex" / "config.toml").read_text(encoding="utf-8"), '[mcp_servers.omnis]\ncommand = "mine"\n')


class TestGatewayFilter(unittest.TestCase):
    def test_masks_and_injects_once(self):
        secret = "sk-ant-" + "b" * 30
        body, n = gateway_filter.transform({"messages": [{"role": "user", "content": [{"type": "text", "text": f"key {secret}"}]}]}, inject=True)
        self.assertEqual(n, 1)
        self.assertNotIn(secret, json.dumps(body))
        self.assertEqual(body["messages"][0]["role"], "system")
        again, _ = gateway_filter.transform(body, inject=True)
        self.assertEqual(len(again["messages"]), 2)
        anth, _ = gateway_filter.transform({"system": "x", "messages": []}, inject=True, anthropic=True)
        self.assertTrue(anth["system"].startswith("[OMNIS]"))
        plain, n = gateway_filter.transform({"messages": [{"role": "user", "content": "hello"}]})
        self.assertEqual((plain["messages"], n), ([{"role": "user", "content": "hello"}], 0))


if __name__ == "__main__":
    unittest.main()
