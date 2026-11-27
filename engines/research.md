# OMNIS research engine

1. **Pin the version** you're researching (lockfile / `pip show` / `npm ls <pkg>`); answers differ across major versions.
2. **Check memory first**: `omnis.py memory search "<topic>" --type research`. Trust a hit only if it's not expired and matches the version.
3. **Sources in order**: official docs → changelog/release notes → the library's GitHub issues → source code. Blog posts last.
4. **Validate** examples by running them when practical.
5. **Record** a concise finding with a source and expiry: `omnis.py memory add research "<lib> <ver>: <finding> (src: <url>)" --ttl 90`.
6. For broad multi-source research, use the deep-research skill if installed; otherwise search in parallel and synthesize.
