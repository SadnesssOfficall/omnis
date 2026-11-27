#!/usr/bin/env python3
"""Usage & session intelligence from Claude Code's local transcripts (~/.claude/projects/**/*.jsonl).

Token counts come from the `usage` field Claude Code records for each API response —
these are real numbers, not estimates. What is NOT available locally: your plan's limit
and the server's exact reset time. The 5-hour window shown here is a heuristic (window
opens at the hour of the first message after a 5h gap); if you know your reset times,
set them with `setup`.

Usage:
  python usage_monitor.py [status]            current window, today, this session
  python usage_monitor.py report [--days 7]   per-day / per-model / per-project + efficiency hints
  python usage_monitor.py setup --reset "HH:MM,HH:MM" [--tz Europe/Istanbul]
  python usage_monitor.py limits              limit/rate messages found in transcripts
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

WINDOW = timedelta(hours=5)
LIMIT_RX = re.compile(r"(usage limit|limit reached|rate limit|resets? (at|in)|5-hour limit|weekly limit|out of extra usage)", re.I)


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def config_path():
    p = claude_home() / "omnis"
    p.mkdir(parents=True, exist_ok=True)
    return p / "usage.json"


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def load_events(home=None, since=None):
    """One event per API response (deduplicated by message id + request id)."""
    base = Path(home) if home else claude_home() / "projects"
    seen, events, limits = set(), [], []
    for f in base.glob("**/*.jsonl"):
        try:
            if since and datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < since:
                continue
            lines = f.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with lines:
            for line in lines:
                if '"usage"' not in line and "limit" not in line.lower():
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                ts = parse_ts(d.get("timestamp"))
                if not ts or (since and ts < since):
                    continue
                msg = d.get("message") or {}
                text = _text(msg)
                if d.get("type") == "assistant" and (d.get("isApiErrorMessage") or msg.get("model") == "<synthetic>") and LIMIT_RX.search(text):
                    limits.append({"time": ts, "text": text[:200], "session": d.get("sessionId")})
                u = msg.get("usage")
                if d.get("type") != "assistant" or not u or msg.get("model") == "<synthetic>":
                    continue
                key = (msg.get("id"), d.get("requestId"))
                if key in seen:
                    continue
                seen.add(key)
                events.append({
                    "time": ts, "model": msg.get("model", "?"), "session": d.get("sessionId"),
                    "project": d.get("cwd") or f.parent.name, "sidechain": bool(d.get("isSidechain")),
                    "input": u.get("input_tokens", 0) or 0, "output": u.get("output_tokens", 0) or 0,
                    "cache_write": u.get("cache_creation_input_tokens", 0) or 0,
                    "cache_read": u.get("cache_read_input_tokens", 0) or 0,
                })
    events.sort(key=lambda e: e["time"])
    limits.sort(key=lambda e: e["time"])
    return events, limits


def _text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def total(evs):
    t = defaultdict(int)
    for e in evs:
        for k in ("input", "output", "cache_write", "cache_read"):
            t[k] += e[k]
    t["requests"] = len(evs)
    t["all"] = t["input"] + t["output"] + t["cache_write"] + t["cache_read"]
    return dict(t)


def windows(events):
    """Heuristic 5h windows: start at the floored hour of the first event after the previous window closed."""
    out = []
    for e in events:
        if not out or e["time"] >= out[-1]["end"]:
            start = e["time"].replace(minute=0, second=0, microsecond=0)
            out.append({"start": start, "end": start + WINDOW, "events": []})
        out[-1]["events"].append(e)
    return out


def configured_next_reset(now):
    try:
        cfg = json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    tzname = cfg.get("tz")
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tzname) if tzname else now.astimezone().tzinfo
    except Exception:
        tz = now.astimezone().tzinfo
    local = now.astimezone(tz)
    cands = []
    for hm in cfg.get("reset_times", []):
        h, m = map(int, hm.split(":"))
        t = local.replace(hour=h, minute=m, second=0, microsecond=0)
        cands.append(t if t > local else t + timedelta(days=1))
    return min(cands) if cands else None


def fmt(n):
    return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.1f}k" if n >= 1e3 else str(n)


def fmt_tot(t):
    return (f"{fmt(t.get('all', 0))} total (in {fmt(t.get('input', 0))}, out {fmt(t.get('output', 0))}, "
            f"cache write {fmt(t.get('cache_write', 0))}, cache read {fmt(t.get('cache_read', 0))}) in {t.get('requests', 0)} requests")


def status(now=None, home=None):
    now = now or datetime.now(timezone.utc)
    events, limits = load_events(home, since=now - timedelta(days=2))
    out = []
    ws = windows(events)
    cur = ws[-1] if ws and ws[-1]["end"] > now else None
    if cur:
        left = cur["end"] - now
        out.append(f"Current 5h window (heuristic): {cur['start'].astimezone():%H:%M} → {cur['end'].astimezone():%H:%M}, "
                   f"{int(left.total_seconds() // 3600)}h{int(left.total_seconds() % 3600 // 60):02d}m left")
        out.append("  " + fmt_tot(total(cur["events"])))
        if len(ws) > 1:
            prev = [total(w["events"])["all"] for w in ws[:-1]]
            out.append(f"  previous windows (last 2 days): avg {fmt(sum(prev) // len(prev))}, max {fmt(max(prev))}")
    else:
        out.append("No active 5h window (no requests in the last 5 hours).")
    nr = configured_next_reset(now)
    if nr:
        out.append(f"Next reset (your configured schedule): {nr:%Y-%m-%d %H:%M %Z}")
    local_today = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    out.append("Today: " + fmt_tot(total([e for e in events if e["time"] >= local_today])))
    if events:
        sess = events[-1]["session"]
        se = [e for e in events if e["session"] == sess]
        dur = se[-1]["time"] - se[0]["time"]
        out.append(f"Latest session {str(sess)[:8]}: started {se[0]['time'].astimezone():%H:%M}, {int(dur.total_seconds() // 60)} min, " + fmt_tot(total(se)))
    recent_limits = [l for l in limits if l["time"] > now - timedelta(hours=12)]
    if recent_limits:
        l = recent_limits[-1]
        out.append(f"⚠ Limit message seen at {l['time'].astimezone():%H:%M}: {l['text'][:120]}")
    out.append("Plan limits and exact server reset times are not available locally; use /usage (or /status) in Claude Code for those.")
    return "\n".join(out)


def report(days=7, home=None):
    now = datetime.now(timezone.utc)
    events, _ = load_events(home, since=now - timedelta(days=days))
    if not events:
        return f"no usage recorded in the last {days} days"
    by_day, by_model, by_proj = defaultdict(list), defaultdict(list), defaultdict(list)
    for e in events:
        by_day[e["time"].astimezone().strftime("%Y-%m-%d")].append(e)
        by_model[e["model"]].append(e)
        by_proj[e["project"]].append(e)
    out = [f"Usage, last {days} days: " + fmt_tot(total(events)), "", "Per day:"]
    out += [f"  {d}  {fmt_tot(total(v))}" for d, v in sorted(by_day.items())]
    out += ["", "Per model:"] + [f"  {m:<22} {fmt(total(v)['all'])}" for m, v in sorted(by_model.items(), key=lambda x: -total(x[1])["all"])]
    out += ["", "Top projects:"] + [f"  {fmt(total(v)['all']):>8}  {p}" for p, v in sorted(by_proj.items(), key=lambda x: -total(x[1])["all"])[:8]]
    out += ["", "Efficiency hints (heuristic):"] + hints(events)
    return "\n".join(out)


def hints(events):
    t = total(events)
    h = []
    ctx = t["input"] + t["cache_write"] + t["cache_read"]
    if ctx:
        hit = t["cache_read"] / ctx
        h.append(f"  cache read share {hit:.0%} of input context" + (" — low; long gaps between messages or frequent context changes break the cache" if hit < 0.7 else ""))
    per_req = ctx / max(1, t["requests"])
    h.append(f"  avg context per request {fmt(int(per_req))}" + (" — high; consider /compact, /clear between unrelated tasks, and OMNIS map/find/filter instead of full reads" if per_req > 120_000 else ""))
    side = [e for e in events if e["sidechain"]]
    if side:
        st = total(side)
        h.append(f"  subagents used {fmt(st['all'])} ({st['all'] / max(1, t['all']):.0%} of total)")
    return h


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="status", choices=["status", "report", "setup", "limits"])
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--reset", help="comma-separated local reset times, e.g. 04:00,09:00")
    ap.add_argument("--tz")
    ap.add_argument("--home", help="transcripts dir (testing)")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print(status(home=a.home))
    elif a.cmd == "report":
        print(report(a.days, a.home))
    elif a.cmd == "limits":
        _, limits = load_events(a.home, since=datetime.now(timezone.utc) - timedelta(days=a.days))
        print("\n".join(f"{l['time'].astimezone():%Y-%m-%d %H:%M}  {l['text'][:150]}" for l in limits) or "no limit messages found")
    else:
        if not a.reset or not all(re.fullmatch(r"\d{1,2}:\d{2}", x.strip()) for x in a.reset.split(",")):
            ap.error("--reset HH:MM[,HH:MM...] is required")
        cfg = {"reset_times": [x.strip() for x in a.reset.split(",")], "tz": a.tz}
        config_path().write_text(json.dumps(cfg, indent=1), encoding="utf-8")
        print(f"saved {config_path()}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
