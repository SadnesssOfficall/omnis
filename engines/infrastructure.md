# OMNIS infrastructure engine

1. `omnis.py doctor` first (tools, disk, runtimes).
2. **Read before acting**: service status, logs (through `omnis.py filter`), config files. Identify whether the target is production.
3. **Any change to production, DNS, firewalls, deploys, or running services needs explicit approval**; state the rollback before acting. Back up config files before editing (`cp file file.bak-YYYYMMDD`).
4. **Containers**: `docker ps`, `docker logs --tail 200 <c>` via filter; never `system prune -a` or remove volumes without approval.
5. **Verify** after a change: service health endpoint / status, logs clean, and the user-visible behavior.
