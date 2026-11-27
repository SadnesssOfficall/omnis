import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import omnis_cache  # noqa: E402
import output_filter  # noqa: E402
import project_scan  # noqa: E402
import symbol_index  # noqa: E402
import verify_plan  # noqa: E402


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # spaces and unicode in the path on purpose
        self.root = Path(self.tmp.name) / "proje klasörü"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()


class TestProjectScan(Fixture):
    def test_detects_node_project(self):
        write(self.root, "package.json", json.dumps({
            "dependencies": {"next": "14", "react": "18"}, "devDependencies": {"vitest": "1"},
            "scripts": {"dev": "next dev", "test": "vitest", "build": "next build"}}))
        write(self.root, "pnpm-lock.yaml", "")
        write(self.root, "src/app/page.tsx", "export default function Page() {}")
        write(self.root, "src/utils.test.ts", "")
        write(self.root, "node_modules/huge/index.js", "x")
        m = project_scan.scan(self.root)
        self.assertIn("Next.js", m["frameworks"])
        self.assertIn("pnpm", m["package_managers"])
        self.assertEqual(m["commands"]["test"], "pnpm test")
        self.assertEqual(m["tests"]["count"], 1)
        self.assertNotIn("node_modules", m["top_dirs"])

    def test_nested_package_json(self):
        write(self.root, "app/package.json", json.dumps({"dependencies": {"express": "4"}, "scripts": {"test": "node --test"}}))
        m = project_scan.scan(self.root)
        self.assertIn("Express", m["frameworks"])
        self.assertEqual(m["commands"]["test"], "(cd app) npm run test")

    def test_broken_package_json_does_not_crash(self):
        write(self.root, "package.json", "{not json")
        m = project_scan.scan(self.root)
        self.assertIn("(package.json unparseable)", m["frameworks"])

    def test_env_file_listed_but_not_read(self):
        write(self.root, ".env", "SECRET=supersecretvalue")
        m = project_scan.scan_cached(self.root)
        self.assertIn(".env", m["config_files"])
        self.assertNotIn("supersecretvalue", json.dumps(m))

    def test_cache_hit_then_invalidation(self):
        write(self.root, "main.py", "print(1)")
        self.assertEqual(project_scan.scan_cached(self.root)["_cache"], "miss")
        self.assertEqual(project_scan.scan_cached(self.root)["_cache"], "hit")
        write(self.root, "requirements.txt", "fastapi\n")
        m = project_scan.scan_cached(self.root)
        self.assertEqual(m["_cache"], "miss")
        self.assertIn("FastAPI", m["frameworks"])

    def test_corrupt_cache_is_ignored(self):
        write(self.root, "a.py", "")
        (omnis_cache.cache_dir(self.root) / "project_map.json").write_text("garbage{", encoding="utf-8")
        self.assertEqual(project_scan.scan_cached(self.root)["_cache"], "miss")


class TestSymbolIndex(Fixture):
    def test_python_ast_and_incremental(self):
        write(self.root, "pkg/__init__.py", "")
        write(self.root, "pkg/core.py", "import os\n\nclass Engine:\n    def run(self):\n        pass\n\ndef helper():\n    pass\n")
        write(self.root, "pkg/cli.py", "from .core import Engine\n")
        idx, st = symbol_index.build(self.root)
        self.assertEqual(st["reparsed"], 3)
        syms = {s[0]: s for s in idx["files"]["pkg/core.py"]["symbols"]}
        self.assertEqual(syms["Engine"][2], 3)
        self.assertEqual(idx["files"]["pkg/core.py"]["confidence"], "high")
        _, st2 = symbol_index.build(self.root)
        self.assertEqual((st2["reparsed"], st2["reused"]), (0, 3))
        time.sleep(0.01)
        write(self.root, "pkg/core.py", "def only():\n    pass\n")
        idx, st3 = symbol_index.build(self.root)
        self.assertEqual(st3["reparsed"], 1)
        self.assertEqual([s[0] for s in idx["files"]["pkg/core.py"]["symbols"]], ["only"])

    def test_deps_python_relative(self):
        write(self.root, "pkg/__init__.py", "")
        write(self.root, "pkg/core.py", "def f(): pass\n")
        write(self.root, "pkg/cli.py", "from .core import f\n")
        idx, _ = symbol_index.build(self.root)
        out, inc = symbol_index.deps(idx, "pkg/core.py")
        self.assertEqual(inc, ["pkg/cli.py"])

    def test_typescript_regex_and_deps(self):
        write(self.root, "src/api.ts", "export async function fetchUser(id: string) {}\nexport const save = async (x) => {}\nexport interface User {}\n")
        write(self.root, "src/page.tsx", "import { fetchUser } from './api'\nexport default function Page() {}\n")
        idx, _ = symbol_index.build(self.root)
        names = [s[0] for s in idx["files"]["src/api.ts"]["symbols"]]
        self.assertEqual(names, ["fetchUser", "save", "User"])
        self.assertEqual(symbol_index.deps(idx, "src/api.ts")[1], ["src/page.tsx"])
        exact, _ = symbol_index.find(idx, "fetchUser")
        self.assertTrue(exact[0].startswith("src/api.ts:1"))

    def test_syntax_error_and_removed_files(self):
        write(self.root, "bad.py", "def (:\n")
        p = write(self.root, "gone.py", "def x(): pass\n")
        idx, _ = symbol_index.build(self.root)
        self.assertEqual(idx["files"]["bad.py"]["confidence"], "none")
        p.unlink()
        idx, st = symbol_index.build(self.root)
        self.assertNotIn("gone.py", idx["files"])
        self.assertEqual(st["removed"], 1)

    def test_huge_file_skipped(self):
        write(self.root, "big.py", "x = 1\n" * 300_000)
        idx, _ = symbol_index.build(self.root)
        self.assertNotIn("big.py", idx["files"])


class TestOutputFilter(unittest.TestCase):
    def test_short_output_untouched(self):
        out, st = output_filter.filter_text("a\nb\nc")
        self.assertEqual(out, "a\nb\nc")
        self.assertEqual(st["dropped"], 0)

    def test_keeps_error_drops_noise(self):
        lines = [f"\x1b[32mcompiling module {i}\x1b[0m" for i in range(2000)]
        lines += ["  45% |█████████████        |\r 100% |████████████████████|"] * 50
        lines.insert(1000, "src/app.ts:42:7 - error TS2322: Type 'string' is not assignable to type 'number'.")
        lines += ["Tests: 3 failed, 120 passed"]
        out, st = output_filter.filter_text("\n".join(lines), max_lines=60)
        self.assertIn("error TS2322", out)
        self.assertIn("src/app.ts:42:7", out)
        self.assertIn("3 failed", out)
        self.assertNotIn("\x1b[", out)
        self.assertNotIn("█", out)
        self.assertLessEqual(len(out.splitlines()), 61)
        self.assertGreater(st["dropped"], 1900)

    def test_python_traceback_preserved(self):
        noise = [f"INFO request {i} ok" for i in range(500)]
        tb = ["Traceback (most recent call last):", '  File "app/views.py", line 88, in handler',
              "    total = price / qty", "ZeroDivisionError: division by zero"]
        out, _ = output_filter.filter_text("\n".join(noise[:250] + tb + noise[250:]))
        for l in tb:
            self.assertIn(l, out)

    def test_paths_named_error_are_not_errors(self):
        paths = [f"/usr/lib/python3/pkg{i}/errors.py" for i in range(3000)]
        tb = ["Traceback (most recent call last):", '  File "x.py", line 1, in <module>', "ZeroDivisionError: division by zero"]
        out, _ = output_filter.filter_text("\n".join(paths + tb), max_lines=60)
        for l in tb:
            self.assertIn(l, out)

    def test_repeated_warnings_deduped(self):
        lines = ["warning: deprecated API foo used at line %d" % i for i in range(300)] + ["x"] * 10
        out, _ = output_filter.filter_text("\n".join(lines), max_lines=50)
        self.assertLessEqual(out.count("deprecated API"), 5)

    def test_cli_saves_full_log(self):
        with tempfile.TemporaryDirectory() as d:
            text = "\n".join(f"line {i}" for i in range(500))
            p = subprocess.run([sys.executable, str(SCRIPTS / "output_filter.py"), "--save", d],
                               input=text.encode(), capture_output=True)
            self.assertEqual(p.returncode, 0)
            logs = list(Path(d).glob("*.log"))
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].read_text(encoding="utf-8"), text)

    def test_run_propagates_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = f'"{sys.executable}" -c "import sys; print(\'boom error\'); sys.exit(3)"'
            p = subprocess.run([sys.executable, str(SCRIPTS / "output_filter.py"), "--run", cmd, "--save", d], capture_output=True)
            self.assertEqual(p.returncode, 3)
            self.assertIn(b"boom error", p.stdout)


class TestVerifyPlan(Fixture):
    def git(self, *a):
        subprocess.run(["git", *a], cwd=self.root, check=True, capture_output=True)

    def test_not_a_repo(self):
        self.assertIsNone(verify_plan.changed_files(self.root))

    def test_changed_and_related_tests(self):
        self.git("init", "-q")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")
        write(self.root, "src/cart.py", "def total(): pass\n")
        write(self.root, "tests/test_cart.py", "")
        write(self.root, ".env.local", "X=1")
        p = verify_plan.plan(self.root)
        self.assertIn("src/cart.py", p["changed"])
        self.assertIn("tests/test_cart.py", p["related_tests"])
        self.assertIn(".env.local", p["secret_like_files"])


class TestWindowsPaths(unittest.TestCase):
    def test_relative_paths_are_posix(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "a b/ç ö.py", "def f(): pass\n")
            files = list(omnis_cache.iter_files(d))
            self.assertEqual(files, ["a b/ç ö.py"])
            self.assertNotIn("\\", files[0])


if __name__ == "__main__":
    unittest.main()
