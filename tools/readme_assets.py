"""Builds the animated SVGs used by the README files (assets/readme/).

Run:  python tools/readme_assets.py
Same family as the SadnesssOfficall profile README (ivy ruins, amber lights,
spaced serif caps). Everything is self-contained: no external fonts, images or
links inside the SVGs, because GitHub serves them through camo as <img>.
Text inside the SVGs is English so every README translation shares them.
"""
import math
import os
import random
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "readme")
os.makedirs(OUT, exist_ok=True)

SERIF = "'Cormorant Garamond','Cormorant','Didot','Bodoni 72',Georgia,'Times New Roman',serif"
SANS = "'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'Cascadia Mono','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": dict(bg="#0b0c0a", panel="#11130f", panel2="#171a14", border="#262a22", stone="#14161200",
                 text="#e4ddcc", muted="#8f8a7e", amber="#f5c27a", amber2="#e0a456", glow="#ffd89a",
                 leaf="#1e3a20", leaf2="#2f5a31", vein="#4f8048", vine="#3a5a33", ok="#7fb069", bad="#e07a5f"),
    "light": dict(bg="#f5f1e8", panel="#fbf8f2", panel2="#efe9dc", border="#d8cfbd", stone="#e9e2d3",
                  text="#1c1e19", muted="#6d675a", amber="#b07a2a", amber2="#c9903e", glow="#e8b25e",
                  leaf="#3f6b3c", leaf2="#58864f", vein="#8db47a", vine="#5d7f52", ok="#4b7a3a", bad="#b0452c"),
}

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)


def leaf_path(s=1.0):
    p = [(0, 0), (-7, -6), (-19, -2), (-17, 10), (-15, 20), (-5, 25), (0, 34),
         (5, 25), (15, 20), (17, 10), (19, -2), (7, -6)]
    a = [(x * s, y * s) for x, y in p]
    return ("M{:.1f},{:.1f} C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} "
            "C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} C{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}Z").format(
        *a[0], *a[1], *a[2], *a[3], *a[4], *a[5], *a[6], *a[7], *a[8], *a[9], *a[10], *a[11], *a[0])


def leaf(x, y, s, rot, fill, vein, cls="", style=""):
    c = f' class="{cls}"' if cls else ""
    st = f' style="{style}"' if style else ""
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})"><g{c}{st}>'
            f'<path d="{leaf_path(s)}" fill="{fill}"/>'
            f'<path d="M0,{2*s:.1f} L0,{30*s:.1f} M0,{12*s:.1f} L{-8*s:.1f},{6*s:.1f} M0,{12*s:.1f} L{8*s:.1f},{6*s:.1f}" '
            f'stroke="{vein}" stroke-width="{0.9*s:.2f}" fill="none" stroke-linecap="round" opacity=".7"/></g></g>')


def hanging_vine(x0, length, seed, stem, fill, vein, scale=1.0):
    r = random.Random(seed)
    x, y = x0, 0
    d = f"M{x0},-4"
    leaves = []
    for k in range(int(length / 26)):
        nx = x + r.uniform(-9, 9)
        d += f" Q{x + r.uniform(-14, 14):.1f},{y + 13:.1f} {nx:.1f},{y + 26:.1f}"
        x, y = nx, y + 26
        side = -1 if k % 2 else 1
        leaves.append((x + side * 4, y - 6, r.uniform(.75, 1.15) * scale, side * r.uniform(25, 55)))
    g = [f'<path d="{d}" stroke="{stem}" stroke-width="2.2" fill="none"/>']
    for lx, ly, s, rot in leaves:
        g.append(leaf(lx, ly, s, rot, fill, vein, "fl",
                      f"animation-duration:{r.uniform(2.4, 4.2):.1f}s;animation-delay:{-r.uniform(0, 4):.1f}s"))
    return f'<g class="sw" style="animation-duration:{r.uniform(5, 8):.1f}s">{"".join(g)}</g>'


# ---------------------------------------------------------------- hero
def hero(theme):
    t = THEMES[theme]
    W, H = 1360, 440
    cx, cy = 680, 170
    rnd = random.Random(42)
    css = [
        "@keyframes flick{0%,100%{opacity:.35}20%{opacity:1}45%{opacity:.55}60%{opacity:.95}80%{opacity:.5}}",
        "@keyframes drift{0%{transform:translate(0,0);opacity:0}12%{opacity:.9}100%{transform:translate(26px,-150px);opacity:0}}",
        "@keyframes sway{0%{transform:rotate(-2.2deg)}100%{transform:rotate(2.4deg)}}",
        "@keyframes flut{0%{transform:rotate(-6deg)}100%{transform:rotate(7deg)}}",
        "@keyframes spin{to{transform:rotate(360deg)}}",
        "@keyframes spinr{to{transform:rotate(-360deg)}}",
        "@keyframes look{0%,18%{transform:translate(0,0)}24%,40%{transform:translate(-9px,1px)}46%,62%{transform:translate(9px,-1px)}68%,100%{transform:translate(0,0)}}",
        "@keyframes blinkl{0%,86%,100%{transform:scaleY(1)}90%{transform:scaleY(.08)}}",
        "@keyframes in{0%{opacity:0;transform:translateY(8px)}100%{opacity:1;transform:none}}",
        "@keyframes halo{0%,100%{opacity:.45}50%{opacity:.85}}",
        ".f{animation:flick 4s ease-in-out infinite}",
        ".p{animation:drift 9s linear infinite;opacity:0}",
        ".sw{transform-box:fill-box;transform-origin:50% 0;animation:sway 6s ease-in-out infinite alternate}",
        ".fl{transform-box:fill-box;transform-origin:50% 0;animation:flut 3.2s ease-in-out infinite alternate}",
        f".r1{{transform-origin:{cx}px {cy}px;animation:spin 60s linear infinite}}",
        f".r2{{transform-origin:{cx}px {cy}px;animation:spinr 90s linear infinite}}",
        ".pu{animation:look 9s ease-in-out infinite}",
        f".lid{{transform-origin:{cx}px {cy}px;animation:blinkl 6s ease-in-out infinite}}",
        ".in{animation:in 1.4s ease-out both}",
        ".halo{animation:halo 5s ease-in-out infinite}",
    ]
    p = [f'<rect width="{W}" height="{H}" fill="url(#bgg)"/>']
    # stone blocks of a ruined wall
    for row in range(0, H, 44):
        off = (row // 44 % 2) * 60
        for x in range(-off, W, 120):
            w = 120 - rnd.randint(2, 6)
            p.append(f'<rect x="{x + 2}" y="{row + 2}" width="{w}" height="40" rx="3" fill="{t["panel2"]}" '
                     f'opacity="{rnd.uniform(.25, .6):.2f}" stroke="{t["border"]}" stroke-opacity=".35"/>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    p.append(f'<circle class="halo" cx="{cx}" cy="{cy}" r="190" fill="url(#glow)"/>')
    # sigil: rune ring + eye
    runes = []
    for i in range(36):
        a = math.radians(i * 10)
        r1, r2 = 112, (124 if i % 3 == 0 else 118)
        runes.append(f'<path d="M{cx + r1*math.cos(a):.1f},{cy + r1*math.sin(a):.1f} L{cx + r2*math.cos(a):.1f},{cy + r2*math.sin(a):.1f}" '
                     f'stroke="{t["amber"]}" stroke-width="1.4" opacity=".8"/>')
    p.append(f'<g class="r1"><circle cx="{cx}" cy="{cy}" r="128" fill="none" stroke="{t["amber"]}" stroke-opacity=".35"/>'
             f'<circle cx="{cx}" cy="{cy}" r="108" fill="none" stroke="{t["amber"]}" stroke-opacity=".55" stroke-dasharray="2 6"/>'
             f'{"".join(runes)}</g>')
    tri = " ".join(f"{cx + 96*math.cos(math.radians(a - 90)):.1f},{cy + 96*math.sin(math.radians(a - 90)):.1f}" for a in (0, 120, 240))
    tri2 = " ".join(f"{cx + 96*math.cos(math.radians(a + 90)):.1f},{cy + 96*math.sin(math.radians(a + 90)):.1f}" for a in (0, 120, 240))
    p.append(f'<g class="r2"><polygon points="{tri}" fill="none" stroke="{t["vine"]}" stroke-width="1.2" opacity=".8"/>'
             f'<polygon points="{tri2}" fill="none" stroke="{t["vine"]}" stroke-width="1.2" opacity=".8"/></g>')
    eye = f"M{cx - 62},{cy} Q{cx},{cy - 46} {cx + 62},{cy} Q{cx},{cy + 46} {cx - 62},{cy}Z"
    p.append(f'<clipPath id="eyec"><path d="{eye}"/></clipPath>')
    p.append(f'<g class="lid"><path d="{eye}" fill="{t["bg"]}" stroke="{t["amber"]}" stroke-width="2"/>'
             f'<g clip-path="url(#eyec)"><g class="pu"><circle cx="{cx}" cy="{cy}" r="22" fill="url(#iris)"/>'
             f'<circle cx="{cx}" cy="{cy}" r="8" fill="{t["bg"]}"/><circle cx="{cx + 6}" cy="{cy - 7}" r="3" fill="#fff1d6"/></g></g></g>')
    # fairy-light string
    d = "M0,26"
    pts = []
    for i in range(0, W + 1, 85):
        d += f" Q{i + 42},{58 if (i // 85) % 2 else 46} {i + 85},26"
        pts.append((i + 42, 46 if (i // 85) % 2 else 40))
    p.append(f'<path d="{d}" stroke="{t["vine"]}" stroke-width="1.2" fill="none" opacity=".8"/>')
    for x, y in pts:
        p.append(f'<g class="f" style="animation-duration:{2.6 + rnd.random()*3.4:.2f}s;animation-delay:{-rnd.random()*5:.2f}s">'
                 f'<circle cx="{x}" cy="{y}" r="16" fill="url(#bulb)"/><circle cx="{x}" cy="{y}" r="3" fill="#fff1d6"/></g>')
    for _ in range(24):
        p.append(f'<circle class="p" cx="{rnd.uniform(40, W - 40):.0f}" cy="{rnd.uniform(220, H - 10):.0f}" r="{rnd.uniform(.8, 2.2):.1f}" '
                 f'fill="{t["amber"]}" style="animation-duration:{rnd.uniform(7, 14):.1f}s;animation-delay:{-rnd.uniform(0, 14):.1f}s"/>')
    stem = "#1a2a17" if theme == "dark" else "#4a6a42"
    lf = "#0f1a0e" if theme == "dark" else t["leaf"]
    for x0, ln, seed, sc in [(60, 170, 3, 1.05), (112, 100, 5, .9), (1300, 150, 11, 1.1), (1250, 80, 9, .85)]:
        p.append(hanging_vine(x0, ln, seed, stem, lf, t["vein"], sc))
    p.append(f'<g class="in"><text x="{cx}" y="352" text-anchor="middle" font-family="{SERIF}" font-size="64" '
             f'letter-spacing="30" fill="{t["text"]}">OMNIS</text>'
             f'<rect x="{cx - 170}" y="372" width="120" height="1" fill="{t["amber"]}" opacity=".7"/>'
             f'<rect x="{cx + 50}" y="372" width="120" height="1" fill="{t["amber"]}" opacity=".7"/>'
             f'<circle cx="{cx}" cy="372" r="2.6" fill="{t["amber"]}"/>'
             f'<text x="{cx}" y="402" text-anchor="middle" font-family="{SANS}" font-size="14" letter-spacing="5" '
             f'fill="{t["muted"]}">ONE CONTEXT-EFFICIENT, SAFE ENGINEERING LAYER</text>'
             f'<text x="{cx}" y="424" text-anchor="middle" font-family="{SANS}" font-size="14" letter-spacing="5" '
             f'fill="{t["amber"]}">FOR EVERY AI CODING TOOL</text></g>')
    defs = (f'<defs><linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["panel"]}"/>'
            f'<stop offset="1" stop-color="{t["bg"]}"/></linearGradient>'
            f'<radialGradient id="vig" cx=".5" cy=".42" r=".75"><stop offset=".35" stop-color="{t["bg"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["bg"]}" stop-opacity=".95"/></radialGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{t["glow"]}" stop-opacity=".28"/>'
            f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="bulb"><stop offset="0" stop-color="#ffd89a" stop-opacity=".9"/>'
            f'<stop offset=".4" stop-color="#f5c27a" stop-opacity=".35"/><stop offset="1" stop-color="#f5c27a" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="iris"><stop offset="0" stop-color="#ffe2b0"/><stop offset=".55" stop-color="{t["amber2"]}"/>'
            f'<stop offset="1" stop-color="{t["leaf2"]}"/></radialGradient></defs>')
    save(f"hero-{theme}.svg",
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="OMNIS - one context-efficient, safe engineering layer for every AI coding tool">'
         f'<title>OMNIS</title><style>{"".join(css)}{REDUCED}</style>{defs}{"".join(p)}</svg>')


# ---------------------------------------------------------------- divider
def divider(theme):
    t = THEMES[theme]
    W, H, cy = 900, 64, 32
    r = random.Random(21)
    d, x = f"M60,{cy}", 60
    while x < 840:
        d += f" Q{x + 20},{cy + (7 if (x // 40) % 2 else -7)} {x + 40},{cy}"
        x += 40
    css = ["@keyframes grow{0%{stroke-dashoffset:900}35%,100%{stroke-dashoffset:0}}",
           "@keyframes pulse{0%,100%{opacity:.45;transform:scale(.8)}50%{opacity:1;transform:scale(1.15)}}",
           "@keyframes flut{0%{transform:rotate(-8deg)}100%{transform:rotate(8deg)}}",
           ".vine{stroke-dasharray:900;animation:grow 9s ease-out infinite}",
           ".dot{transform-box:fill-box;transform-origin:center;animation:pulse 3.2s ease-in-out infinite}",
           ".fl{transform-box:fill-box;transform-origin:50% 0;animation:flut 3s ease-in-out infinite alternate}"]
    leaves = []
    for i, lx in enumerate(range(100, 820, 52)):
        if 380 < lx < 520:
            continue
        frac = (lx - 60) / 780 * 35
        css.append(f"@keyframes lp{i}{{0%,{frac:.1f}%{{transform:scale(0)}}{frac + 4:.1f}%,100%{{transform:scale(1)}}}}")
        css.append(f".lp{i}{{transform-box:fill-box;transform-origin:50% 0;animation:lp{i} 9s ease-out infinite}}")
        side = 1 if i % 2 else -1
        leaves.append(f'<g class="lp{i}">' + leaf(lx, cy + side * 2, r.uniform(.42, .6), (180 if side < 0 else 0) + r.uniform(-30, 30),
                                                  t["leaf2"], t["vein"], "fl", f"animation-delay:{-r.uniform(0, 3):.1f}s") + "</g>")
    # small eye in the centre instead of the profile's plain dot
    center = (f'<g class="dot"><circle cx="450" cy="{cy}" r="11" fill="{t["amber"]}" opacity=".16"/>'
              f'<path d="M439,{cy} Q450,{cy - 8} 461,{cy} Q450,{cy + 8} 439,{cy}Z" fill="none" stroke="{t["amber"]}" stroke-width="1.2"/>'
              f'<circle cx="450" cy="{cy}" r="2.4" fill="{t["amber"]}"/></g>'
              f'<path d="M416,{cy} L432,{cy} M468,{cy} L484,{cy}" stroke="{t["amber"]}" stroke-width="1" opacity=".6"/>')
    save(f"divider-{theme}.svg",
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="divider">'
         f'<style>{"".join(css)}{REDUCED}</style><path d="M20,{cy} L880,{cy}" stroke="{t["border"]}"/>'
         f'<path class="vine" d="{d}" stroke="{t["vine"]}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
         f'{"".join(leaves)}{center}</svg>')


# ---------------------------------------------------------------- section titles
TITLES = [
    ("what", "WHAT", "THE LAYER, IN ONE BREATH"),
    ("features", "FEATURES", "WHAT LIVES INSIDE"),
    ("demo", "DEMO", "REAL OUTPUT, NOTHING STAGED"),
    ("tools", "TOOLS", "ONE ENGINE, MANY CLIENTS"),
    ("start", "START", "ONE COMMAND PER TOOL"),
    ("commands", "COMMANDS", "THE FULL REFERENCE"),
    ("numbers", "NUMBERS", "MEASURED, NOT PROMISED"),
    ("safety", "SAFETY", "SEATBELTS, NOT SANDBOXES"),
    ("faq", "FAQ", "HONEST ANSWERS"),
]


def title(theme, key, text, sub):
    t = THEMES[theme]
    W, H = 900, 92
    css = ("@keyframes in{0%{opacity:0;transform:translateY(6px)}100%{opacity:1;transform:none}}"
           "@keyframes line{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}"
           ".in{animation:in 1.2s ease-out both}.ln{transform-box:fill-box;transform-origin:center;animation:line 1.6s .3s ease-out both}")
    save(f"title-{key}-{theme}.svg",
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{text}">'
         f'<style>{css}{REDUCED}</style>'
         f'<g class="in"><text x="450" y="46" text-anchor="middle" font-family="{SERIF}" font-size="30" letter-spacing="14" '
         f'fill="{t["text"]}">{text}</text>'
         f'<text x="450" y="78" text-anchor="middle" font-family="{SANS}" font-size="12" letter-spacing="4" fill="{t["muted"]}">{sub}</text></g>'
         f'<rect class="ln" x="250" y="62" width="140" height="1" fill="{t["amber"]}" opacity=".7"/>'
         f'<rect class="ln" x="510" y="62" width="140" height="1" fill="{t["amber"]}" opacity=".7"/></svg>')


# ---------------------------------------------------------------- feature cards
# (key, name, tag, two description lines, footer, glyph)
FEATURES = [
    ("map", "MAP · FIND", "CONTEXT", ["Project map, symbol index, outline,", "import graph. Cached, incremental."], "map  find  outline  deps", "eye"),
    ("filter", "FILTER", "OUTPUT", ["Runs a command, keeps errors and", "summaries, saves the full log."], "filter \"<cmd>\"", "funnel"),
    ("memory", "MEMORY", "CONTINUITY", ["Project facts with expiry and a", "\"seen this error before?\" store."], "memory  memory bug", "book"),
    ("checkpoint", "CHECKPOINTS", "CONTINUITY", ["Save a task, resume it in a new", "session with git changes since."], "checkpoint save | resume", "flag"),
    ("usage", "USAGE", "LIMITS", ["Token use from local transcripts,", "recurring reminders, quiet hours."], "usage  reminder", "hourglass"),
    ("security", "GUARD", "SAFETY", ["Secret scan with redaction and a", "hook that blocks or asks first."], "security  guard.py", "shield"),
    ("skills", "SKILLS", "REGISTRY", ["Pinned, audited skill installer,", "lock file, conflicts, rollback."], "skills  audit  registry", "leaf"),
    ("mcp", "MCP SERVER", "PROTOCOL", ["Stdlib JSON-RPC over stdio, or", "loopback HTTP with a token."], "scripts/mcp_server.py", "plug"),
    ("install", "INSTALLER", "MULTI-TOOL", ["One installer for 12 targets:", "dry run, backups, uninstall."], "install.py --target", "stack"),
    ("os", "DEVELOPER OS", "CLAUDE CODE", ["14 agents, 30 commands, hooks,", "automation, one-step rollback."], "/omnis setup · geri-al", "rune"),
    ("gateway", "GATEWAY", "9ROUTER", ["Opt-in proxy that masks secrets", "before requests leave the machine."], "gateway_filter.py", "gate"),
    ("verify", "VERIFY", "HONESTY", ["Changed files to related tests;", "reports VERIFIED or FAILED."], "verify --run", "check"),
]


def glyph(kind, x, y, c, c2):
    s = f'stroke="{c}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    g = {
        "eye": f'<path d="M{x-16},{y} Q{x},{y-13} {x+16},{y} Q{x},{y+13} {x-16},{y}Z" {s}/><circle cx="{x}" cy="{y}" r="4.5" fill="{c}"/>',
        "funnel": f'<path d="M{x-16},{y-12} L{x+16},{y-12} L{x+4},{y+2} L{x+4},{y+13} L{x-4},{y+9} L{x-4},{y+2}Z" {s}/>',
        "book": f'<path d="M{x},{y-9} Q{x-9},{y-14} {x-17},{y-11} L{x-17},{y+11} Q{x-9},{y+8} {x},{y+13} Q{x+9},{y+8} {x+17},{y+11} L{x+17},{y-11} Q{x+9},{y-14} {x},{y-9}Z M{x},{y-9} L{x},{y+13}" {s}/>',
        "flag": f'<path d="M{x-10},{y+14} L{x-10},{y-14} L{x+12},{y-9} L{x-10},{y-2}" {s}/>',
        "hourglass": f'<path d="M{x-11},{y-14} L{x+11},{y-14} L{x-11},{y+14} L{x+11},{y+14}Z" {s}/><circle cx="{x}" cy="{y+9}" r="2.4" fill="{c}"/>',
        "shield": f'<path d="M{x},{y-15} L{x+14},{y-9} Q{x+14},{y+8} {x},{y+15} Q{x-14},{y+8} {x-14},{y-9}Z M{x-6},{y} L{x-1},{y+5} L{x+7},{y-5}" {s}/>',
        "leaf": f'<g transform="translate({x},{y-15})"><path d="{leaf_path(.8)}" fill="{c2}"/></g>',
        "plug": f'<path d="M{x-6},{y-15} L{x-6},{y-7} M{x+6},{y-15} L{x+6},{y-7} M{x-11},{y-7} L{x+11},{y-7} L{x+11},{y+1} Q{x},{y+12} {x-11},{y+1}Z M{x},{y+7} L{x},{y+15}" {s}/>',
        "stack": f'<path d="M{x},{y-13} L{x+15},{y-6} L{x},{y+1} L{x-15},{y-6}Z M{x-15},{y} L{x},{y+7} L{x+15},{y} M{x-15},{y+6} L{x},{y+13} L{x+15},{y+6}" {s}/>',
        "rune": f'<circle cx="{x}" cy="{y}" r="14" {s}/><path d="M{x},{y-14} L{x},{y+14} M{x-10},{y-6} L{x+10},{y+6} M{x+10},{y-6} L{x-10},{y+6}" {s}/>',
        "gate": f'<path d="M{x-14},{y+14} L{x-14},{y-4} Q{x},{y-20} {x+14},{y-4} L{x+14},{y+14} M{x-7},{y+14} L{x-7},{y-2} M{x+7},{y+14} L{x+7},{y-2}" {s}/>',
        "check": f'<circle cx="{x}" cy="{y}" r="14" {s}/><path d="M{x-7},{y} L{x-2},{y+6} L{x+8},{y-6}" {s}/>',
    }
    return g[kind]


def card(theme, f):
    key, name, tag, desc, foot, gl = f
    t = THEMES[theme]
    W, H = 440, 176
    r = random.Random(sum(map(ord, key)))
    css = ("@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}"
           "@keyframes sheen{0%{transform:translateX(-520px)}60%,100%{transform:translateX(520px)}}"
           "@keyframes flut{0%{transform:rotate(-7deg)}100%{transform:rotate(7deg)}}"
           "@keyframes gl{0%,100%{opacity:.75}50%{opacity:1}}"
           ".pl{animation:pulse 2.4s ease-in-out infinite}.gl{animation:gl 3.6s ease-in-out infinite}"
           f".sh{{animation:sheen 7s ease-in-out infinite;animation-delay:{-r.uniform(0, 7):.1f}s}}"
           ".fl{transform-box:fill-box;transform-origin:50% 0;animation:flut 3.4s ease-in-out infinite alternate}")
    leaves = [leaf(lx, ly, s, rot, t["leaf2"] if i % 2 else t["leaf"], t["vein"], "fl",
                   f"animation-delay:{-r.uniform(0, 3):.1f}s;animation-duration:{r.uniform(2.6, 4):.1f}s")
              for i, (lx, ly, s, rot) in enumerate([(W - 62, 6, .55, -40), (W - 44, 16, .62, -20), (W - 26, 30, .5, 10), (W - 16, 46, .4, 30)])]
    vd = f"M{W - 70},-2 Q{W - 40},18 {W - 14},40"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(name)}">'
           f'<style>{css}{REDUCED}</style><defs>'
           f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["panel2"]}"/><stop offset="1" stop-color="{t["panel"]}"/></linearGradient>'
           f'<linearGradient id="sg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["amber"]}" stop-opacity="0"/>'
           f'<stop offset=".5" stop-color="{t["amber"]}" stop-opacity=".10"/><stop offset="1" stop-color="{t["amber"]}" stop-opacity="0"/></linearGradient>'
           f'<clipPath id="cp"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath></defs>'
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="url(#bg)" stroke="{t["border"]}"/>'
           f'<g clip-path="url(#cp)"><rect class="sh" x="0" y="0" width="160" height="{H}" fill="url(#sg)" transform="skewX(-20)"/>'
           f'<path d="{vd}" stroke="{t["vine"]}" stroke-width="1.4" fill="none"/>{"".join(leaves)}</g>'
           f'<g class="gl">{glyph(gl, W - 110, 52, t["amber"], t["leaf2"])}</g>'
           f'<text x="28" y="40" font-family="{SANS}" font-size="10.5" letter-spacing="3" fill="{t["amber"]}">{tag}</text>'
           f'<text x="28" y="76" font-family="{SERIF}" font-size="26" letter-spacing="7" fill="{t["text"]}">{escape(name)}</text>'
           f'<text x="28" y="106" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{escape(desc[0])}</text>'
           f'<text x="28" y="124" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{escape(desc[1])}</text>'
           f'<path d="M28,142 L{W - 28},142" stroke="{t["border"]}"/>'
           f'<circle class="pl" cx="34" cy="158" r="3.2" fill="{t["amber"]}"/>'
           f'<text x="46" y="162" font-family="{MONO}" font-size="11.5" fill="{t["text"]}">{escape(foot)}</text>'
           f'<text x="{W - 28}" y="162" text-anchor="end" font-family="{SANS}" font-size="12" letter-spacing="2" fill="{t["amber"]}">DOCS →</text>'
           f'</svg>')
    save(f"card-{key}-{theme}.svg", svg)


# ---------------------------------------------------------------- terminal demo
# Real output of OMNIS on a small Next.js sample project (paths redacted).
DEMO = [
    ("$", "python scripts/omnis.py map"),
    ("o", "# Project map: ~/shop  (5 files, cache miss)"),
    ("o", "- Languages: TypeScript (3)"),
    ("o", "- Package managers: npm, pnpm"),
    ("o", "- Frameworks/libs: Next.js, React, Vitest"),
    ("o", "- Commands: dev → `pnpm dev`; build → `pnpm build`; test → `pnpm test`"),
    ("o", "- Tests: 1 files (e.g. tests/cart.test.ts)"),
    ("$", "python scripts/omnis.py find calcTotal"),
    ("o", "src/cart.ts:1  function calcTotal  [medium]"),
    ("$", "python scripts/omnis.py deps src/cart.ts"),
    ("o", "imported by:"),
    ("o", "  src/checkout.ts"),
    ("$", "python scripts/omnis.py filter \"python -c ...3000 lines, then fail\""),
    ("e", "boom: config missing"),
    ("m", "[omnis-filter] 3/3002 lines shown; full output: .omnis/logs/20261127-230038-4c7f3757.log"),
    ("m", "[omnis-filter] exit code: 1"),
    ("$", "python scripts/omnis.py security classify \"rm -rf /\""),
    ("e", "{\"class\": \"destructive\", \"severity\": \"block\"}"),
]


def terminal(theme):
    t = THEMES[theme]
    W = 900
    lh = 21
    top = 54
    H = top + lh * len(DEMO) + 30
    cycle = 22.0
    css = ["@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
           "@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}",
           ".cur{animation:blink 1s step-end infinite}.pl{animation:pulse 2.4s ease-in-out infinite}"]
    rows = []
    tcur = 0.4
    for i, (kind, txt) in enumerate(DEMO):
        y = top + 16 + i * lh
        dur = 1.1 if kind == "$" else 0.18
        s0 = tcur / cycle * 100
        s1 = (tcur + dur) / cycle * 100
        tcur += dur + (0.35 if kind == "$" else 0.12)
        if kind == "$":
            n = max(len(txt), 1)
            w = 8.0 * n
            css.append(f"@keyframes t{i}{{0%,{s0:.2f}%{{transform:scaleX(0);animation-timing-function:steps({n},end)}}"
                       f"{s1:.2f}%,95%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}")
            css.append(f".t{i}{{transform-box:fill-box;transform-origin:0 0;animation:t{i} {cycle}s infinite}}")
            rows.append(f'<clipPath id="c{i}"><rect class="t{i}" x="44" y="{y - 15}" width="{w + 4:.0f}" height="20"/></clipPath>')
            rows.append(f'<text x="26" y="{y}" font-family="{MONO}" font-size="13" fill="{t["amber"]}" class="r{i}">$</text>')
            rows.append(f'<text clip-path="url(#c{i})" x="44" y="{y}" font-family="{MONO}" font-size="13" fill="{t["text"]}">{escape(txt)}</text>')
            css.append(f"@keyframes r{i}{{0%,{s0:.2f}%{{opacity:0}}{s0 + .01:.2f}%,95%{{opacity:1}}100%{{opacity:0}}}}")
            css.append(f".r{i}{{animation:r{i} {cycle}s infinite}}")
        else:
            col = {"o": t["muted"], "e": t["bad"], "m": t["ok"]}[kind]
            css.append(f"@keyframes r{i}{{0%,{s0:.2f}%{{opacity:0}}{s1:.2f}%,95%{{opacity:1}}100%{{opacity:0}}}}")
            css.append(f".r{i}{{animation:r{i} {cycle}s infinite}}")
            rows.append(f'<text class="r{i}" x="44" y="{y}" font-family="{MONO}" font-size="12.5" fill="{col}" xml:space="preserve">{escape(txt)}</text>')
    yc = top + 16 + len(DEMO) * lh
    rows.append(f'<rect class="cur" x="26" y="{yc - 13}" width="8" height="15" fill="{t["amber"]}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="Terminal demo: omnis map, find, deps, filter and security classify on a sample project">'
           f'<style>{"".join(css)}{REDUCED}</style>'
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{t["panel"]}" stroke="{t["border"]}"/>'
           f'<path d="M1,15 Q1,1 15,1 L{W - 15},1 Q{W - 1},1 {W - 1},15 L{W - 1},38 L1,38Z" fill="{t["panel2"]}"/>'
           f'<path d="M1,38 L{W - 1},38" stroke="{t["border"]}"/>'
           f'<circle cx="24" cy="20" r="5" fill="{t["bad"]}" opacity=".8"/><circle cx="42" cy="20" r="5" fill="{t["amber"]}" opacity=".8"/>'
           f'<circle cx="60" cy="20" r="5" fill="{t["ok"]}" opacity=".8"/>'
           f'<text x="{W / 2}" y="24" text-anchor="middle" font-family="{SANS}" font-size="11" letter-spacing="3" fill="{t["muted"]}">OMNIS · SAMPLE PROJECT</text>'
           f'<circle class="pl" cx="{W - 30}" cy="20" r="3.2" fill="{t["amber"]}"/>'
           f'{"".join(rows)}</svg>')
    save(f"demo-{theme}.svg", svg)


if __name__ == "__main__":
    for th in THEMES:
        hero(th)
        divider(th)
        for k, txt, sub in TITLES:
            title(th, k, txt, sub)
        for f in FEATURES:
            card(th, f)
        terminal(th)
    print("ok", len(os.listdir(OUT)), "files in", OUT)
