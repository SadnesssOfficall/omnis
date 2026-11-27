# OMNIS agent orchestration

Spawn subagents only if ALL hold:
- the work splits into parts that are independent (no shared files being edited),
- each part needs substantial reading/searching whose details the main thread doesn't need,
- the user is fine with the extra token cost (each agent starts cold).

Otherwise do it inline — it is cheaper and keeps context coherent.

When you do: give each agent one clear deliverable, the files it owns, and require evidence (file:line, command output) in its report. Never let two agents edit the same file. Merge findings yourself and verify anything you act on.
