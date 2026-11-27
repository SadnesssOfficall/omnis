# OMNIS debug workflow (evidence first)

1. **Capture the failure** — run the failing command through `output_filter.py --run`. Keep the exact error line and the first project-owned stack frame.
2. **Reproduce** — get a single command that fails reliably. If you cannot reproduce, say so and collect more evidence instead of guessing.
3. **Locate** — `symbol_index.py --find <function from the stack>` and `--file` for an outline; read only the relevant line range.
4. **Recent changes** — `git log --oneline -10 -- <file>` and `git diff HEAD -- <file>`; regressions usually live there.
5. **Hypotheses** — list 1–3 causes, each with the evidence for it. No invented probabilities.
6. **Test the top hypothesis** cheaply (a print, a narrower test, a REPL check) before editing.
7. **Fix minimally** — the smallest change that addresses the root cause, not the symptom.
8. **Regression test** — add a test that failed before the fix when the project has a test suite.
9. **Verify** — re-run the original failing command, then `verify_plan.py --run`.
10. **Similar patterns** — `symbol_index.py --find` / grep for the same mistake elsewhere; report, don't silently fix unrelated code.

Report:
```
ROOT CAUSE: <one sentence, with file:line>
EVIDENCE: <what proved it>
FIX: <what changed>
VERIFIED: ... / NOT VERIFIED: ...
```
