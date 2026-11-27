# OMNIS deep workflow (complex or high-risk changes)

1. **Baseline** — `git status` (note existing user changes), `project_scan.py .`, `symbol_index.py .`.
2. **Scope** — for each file you expect to touch, run `symbol_index.py --deps <file>` to list consumers. Note which consumers are covered by tests.
3. **Unknowns** — if the change depends on a library/API version you're unsure of, check the installed version (lockfile) and its official docs before coding.
4. **Plan** — write a short numbered plan (files, order, how each step is verified). For more than ~5 steps, keep it in the task list and update it as you go so work can resume after an interruption.
5. **Risk check** — auth, payments, data migrations, infra, and public APIs: identify rollback and ask before destructive or irreversible steps.
6. **Implement in small steps**, running the relevant check after each.
7. **Agents** — only split into subagents when parts are truly independent and each needs heavy reading; never have two agents edit the same file.
8. **Review the diff** — `git diff`: unintended changes, debug leftovers, secrets, scope creep.
9. **Verify** — `verify_plan.py --run` plus any targeted checks; UI changes need a real browser check if tools exist, otherwise list as NOT VERIFIED.
10. **Report** with the VERIFIED / NOT VERIFIED / RISKS block.
