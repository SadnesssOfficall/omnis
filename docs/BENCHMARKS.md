# Benchmarks (2026-11-27, Linux, Python 3.13)

Byte counts are measured. Token figures are **estimates** (bytes ÷ 4). Reproduce with `omnis.py benchmark ...`.

## Symbol lookup: `mcp` Python package (111 files)

| Query | grep -rn output | Whole files grep matched | `omnis find` output |
|---|---|---|---|
| ClientSession | 4,418 B | 7 files, 70,143 B | 175 B |
| FastMCP | 5,104 B | 19 files, 138,626 B | 164 B |
| stdio_client | 597 B | 5 files, 43,446 B | 60 B |

The fair comparison is with **grep**, which Claude normally uses first: about 10–30× less output per lookup. The output also points straight at the definition (`server/fastmcp/server.py:156 class FastMCP`), so the follow-up Read can be a narrow line range. Comparing with whole-file reads (99%+ saved) is an upper bound, not a typical session.

Index build: 0.31 s cold. A second run re-parses only changed files (tested).

## Orientation: `autofix` (36 files, JS)

README + package.json: 17,128 B. Project map: 284 B (~4.2k tokens saved per orientation, est.).

## Output filter

| Input | Raw | Filtered |
|---|---|---|
| 3,006-line file listing + Python traceback | 246,993 B | 1,065 B, 20 lines. The full traceback is kept and the full log is saved |

## Real session usage (from local transcripts)

This session, before OMNIS was installed: 1.87M tokens in 26 requests, 95% cache reads, average context 69k tokens per request.
After installation, use `omnis.py benchmark sessions --split <install date>` to compare. Tasks differ between periods, so only compare like-for-like work.

## Not measured

- No controlled A/B test (same task, same model, with vs without OMNIS) has been run yet, so no overall "% saved per session" figure is claimed.
- Windows timings.
