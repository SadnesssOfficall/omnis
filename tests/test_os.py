"""Developer OS: setup/rollback in an isolated CLAUDE_CONFIG_DIR, hooks, registry, adaptation, automation."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import automation  # noqa: E402
import os_hooks  # noqa: E402
import os_setup  # noqa: E402
import project_adapt  # noqa: E402


class Isolated(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.env = {"CLAUDE_CONFIG_DIR": str(t / "claude"), "OMNIS_HOME": str(t / "omnis"),
                    "OMNIS_NO_CLAUDE_CLI": "1", "OMNIS_NO_SCHED": "1", "OMNIS_NO_TOAST": "1"}
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        self.home = t / "claude"
        self.home.mkdir()
        (self.home / "CLAUDE.md").write_text("# Benim kurallarım\nSorvia kuralı: dokunma.\n", encoding="utf-8")
        (self.home / "settings.json").write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "python guard.py"}]}]}}), encoding="utf-8")
        (self.home / "agents").mkdir()
        (self.home / "agents" / "qa.md").write_text("---\nname: qa\ndescription: mine\n---\nuser agent\n", encoding="utf-8")

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def quiet(self, fn, *a):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = fn(*a)
        return rc, buf.getvalue()


class TestSetupRollback(Isolated):
    def test_dry_run_changes_nothing(self):
        before = {p: p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        self.quiet(os_setup.setup, True)
        self.assertEqual(before, {p: p.read_bytes() for p in self.home.rglob("*") if p.is_file()})

    def test_setup_idempotent_and_rollback(self):
        rc, out = self.quiet(os_setup.setup, False)
        self.assertEqual(rc, 0, out)
        md = (self.home / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith("# Benim kurallarım\nSorvia kuralı: dokunma.\n"))
        self.assertEqual(md.count(os_setup.MD_BEGIN), 1)
        self.assertEqual((self.home / "agents" / "qa.md").read_text(encoding="utf-8").splitlines()[-1], "user agent")  # not overwritten
        self.assertTrue((self.home / "agents" / "architect.md").is_file())
        self.assertFalse((self.home / "commands" / "review.md").exists())  # built-in name never created
        self.assertTrue((self.home / "commands" / "omnis-review.md").is_file())
        s = json.loads((self.home / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("python guard.py", json.dumps(s))  # existing guard kept
        for ev in ("PostToolUse", "Stop", "SessionStart", "PreCompact", "UserPromptSubmit"):
            self.assertIn(ev, s["hooks"])
        self.assertNotIn("✗", out.split("## OMNIS durum")[1].split("Geri")[0].replace("✗ claude --version", ""))
        # second run: no duplicates
        self.quiet(os_setup.setup, False)
        s2 = json.loads((self.home / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(s2["hooks"]["Stop"]), 1)
        self.assertEqual((self.home / "CLAUDE.md").read_text(encoding="utf-8").count(os_setup.MD_BEGIN), 1)
        # rollback both runs
        self.quiet(os_setup.rollback, None)
        self.quiet(os_setup.rollback, None)
        self.assertEqual((self.home / "CLAUDE.md").read_text(encoding="utf-8"), "# Benim kurallarım\nSorvia kuralı: dokunma.\n")
        self.assertFalse((self.home / "agents" / "architect.md").exists())
        self.assertTrue((self.home / "agents" / "qa.md").exists())
        self.assertNotIn("os_hooks.py", (self.home / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(automation.load(), {})


class TestHooks(Isolated):
    def test_protect(self):
        self.assertEqual(os_hooks.protect({"tool_input": {"file_path": "a/.env.local"}})["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertIsNotNone(os_hooks.protect({"tool_input": {"file_path": "C:\\p\\package-lock.json"}}))
        self.assertIsNone(os_hooks.protect({"tool_input": {"file_path": "a/.env.example"}}))
        self.assertIsNone(os_hooks.protect({"tool_input": {"file_path": "src/env.ts"}}))

    def test_stop_typecheck_blocks_once(self):
        d = Path(self.tmp.name) / "p"
        d.mkdir()
        (d / "tsconfig.json").write_text("{}", encoding="utf-8")
        f = d / "a.ts"
        f.write_text("x", encoding="utf-8")
        os_hooks._note_edit({"session_id": "s1"}, str(f))
        # no local tsc → silent; and with stop_hook_active it must never block
        self.assertIsNone(os_hooks.stop({"session_id": "s1", "cwd": str(d)}))
        os_hooks._note_edit({"session_id": "s1"}, str(f))
        self.assertIsNone(os_hooks.stop({"session_id": "s1", "cwd": str(d), "stop_hook_active": True}))

    def test_session_resume_injects_checkpoint(self):
        import checkpoint
        d = Path(self.tmp.name) / "r"
        d.mkdir()
        subprocess.run(["git", "init", "-q", str(d)], check=True)
        checkpoint.save(d, "port the guard", nxt=["write tests"])
        out = os_hooks.session({"cwd": str(d), "source": "compact"})
        self.assertIn("port the guard", out["hookSpecificOutput"]["additionalContext"])

    def test_bad_input_is_silent(self):
        p = subprocess.run([sys.executable, str(SCRIPTS / "os_hooks.py"), "stop"], input=b"nope", capture_output=True)
        self.assertEqual((p.returncode, p.stdout), (0, b""))


class TestAdaptAutomation(Isolated):
    def test_detect_stacks(self):
        d = Path(self.tmp.name) / "s"
        (d / "mc" / "src" / "main" / "resources").mkdir(parents=True)
        (d / "mc" / "src" / "main" / "resources" / "plugin.yml").write_text("name: X", encoding="utf-8")
        self.assertIn("minecraft-plugin", project_adapt.detect(d / "mc"))
        (d / "fx").mkdir()
        (d / "fx" / "fxmanifest.lua").write_text("fx_version 'cerulean'", encoding="utf-8")
        self.assertEqual(project_adapt.detect(d / "fx")[0], "fivem")
        (d / "bot").mkdir()
        (d / "bot" / "package.json").write_text(json.dumps({"dependencies": {"discord.js": "14"}}), encoding="utf-8")
        self.assertIn("discord-bot", project_adapt.detect(d / "bot"))

    def test_automation_lifecycle(self):
        self.assertEqual(automation.parse_every("5h"), 300)
        self.assertEqual(automation.schedule_args(1440), ["/SC", "DAILY", "/MO", "1"])
        self.assertEqual(automation.schedule_args(180), ["/SC", "HOURLY", "/MO", "3"])
        with self.assertRaises(ValueError):
            automation.parse_every("5x")
        repo = Path(self.tmp.name) / "g"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        self.quiet(automation.main, ["add", "repo-health", "--every", "8h", "--repo", str(repo), "--no-schedule"])
        tid = next(iter(automation.load()))
        rc, out = self.quiet(automation.main, ["run", tid, "--no-notify"])
        self.assertEqual(rc, 0)
        self.assertIn("repo-health", out)
        self.quiet(automation.main, ["pause", tid, "--no-schedule"])
        self.assertTrue(automation.load()[tid]["paused"])
        self.quiet(automation.main, ["remove", tid, "--no-schedule"])
        self.assertEqual(automation.load(), {})


if __name__ == "__main__":
    unittest.main()
