# OMNIS database engine

1. **Find the schema source of truth**: ORM schema (prisma/schema.prisma, models.py, drizzle schema, entities) or migrations folder. `omnis.py find <Model>` locates models.
2. **Before any migration**: what tables/columns change, is it additive (safe) or destructive (drop/rename/type change = data loss risk), how many rows are affected (ask or query a non-prod DB), is there a rollback (down migration / backup).
3. **Destructive or production operations require explicit approval** — the OMNIS hook will ask for DROP/TRUNCATE/unscoped DELETE/migrate reset.
4. **Query review checklist**: N+1 (queries inside loops, lazy relations in lists), missing indexes on filtered/joined columns, unbounded SELECTs, transactions around multi-step writes, parameterized queries only.
5. **Verify**: run migrations against a local/test database, run the related tests, and report what was not run against real data.
