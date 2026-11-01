"""§06 live telemetry: odometer KPIs down the left, an axonometric skyline of
the last 53 weeks of contributions on the right (flat faces: ink fronts, grey
sides, paper tops; the best day in the accent), and a segmented language ruler.

Data comes from live.py (refreshed daily by the workflow)."""

from __future__ import annotations

import datetime as dt

from core import fonts
from core.design import CSS as BASE, W, box, card, hline, patterns, strip, vline
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import document, fit, num, text
from core.theme import Theme, mix

SPLIT = 256
TOP = 40
KPI_H = 104
# skyline geometry: weeks run left to right, weekdays recede up and to the right
S, DX, DY = 8.8, 4.0, 5.6
TW, TD = .76, .76
HMAX = 104

CSS = BASE + ODO_CSS + """
.up{animation:up .7s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}
@keyframes up{from{transform:scaleY(0)}}
"""


def faces(theme: Theme) -> dict:
    if theme.dark:
        return dict(front=theme.ink, side=theme.faint, top=theme.muted, ground=theme.hair)
    return dict(front=theme.ink, side=theme.muted, top=theme.paper2, ground=theme.hair)


def skyline(calendar: list, theme: Theme, ox: float, oy: float) -> str:
    cells = [(w, d, date, count) for w, week in enumerate(calendar) for d, (date, count) in enumerate(week)]
    peak = max((c for *_, c in cells), default=0) or 1
    best = max(cells, key=lambda c: c[3]) if cells else None
    tw, dx, dy = S * TW, DX * TD, DY * TD
    f = faces(theme)
    tiles, towers, label = [], [], ""
    for w, d, date, count in sorted(cells, key=lambda c: (c[1], c[0])):  # back rows first
        px = ox + w * S + (6 - d) * DX
        py = oy - (6 - d) * DY
        if count == 0:
            tiles.append(f'<polygon points="{num(px)} {num(py)} {num(px + tw)} {num(py)} {num(px + tw + dx)} '
                         f'{num(py - dy)} {num(px + dx)} {num(py - dy)}"/>')
            continue
        h = 4 + (HMAX - 4) * (count / peak) ** .6
        hot = best and (w, d) == best[:2]
        front = theme.accent if hot else f["front"]
        side = mix(theme.accent, "#000000", .3) if hot else f["side"]
        top = mix(theme.accent, "#ffffff", .35) if hot else f["top"]
        towers.append(
            f'<g class="up" style="animation-delay:{.4 + w * .025:.2f}s">'
            f'<rect x="{num(px)}" y="{num(py - h)}" width="{num(tw)}" height="{num(h)}" fill="{front}"/>'
            f'<polygon points="{num(px + tw)} {num(py)} {num(px + tw + dx)} {num(py - dy)} {num(px + tw + dx)} '
            f'{num(py - dy - h)} {num(px + tw)} {num(py - h)}" fill="{side}"/>'
            f'<polygon points="{num(px)} {num(py - h)} {num(px + tw)} {num(py - h)} {num(px + tw + dx)} '
            f'{num(py - dy - h)} {num(px + dx)} {num(py - dy - h)}" fill="{top}"/></g>')
        if hot:
            bx, by = px + tw / 2, py - dy - h
            tag = f"BEST DAY · {count} · {dt.date.fromisoformat(date):%d %b}".upper()
            lw = fonts.width("m", tag, 9, 1) + 1 + 16
            lx = min(bx - 8, W - 8 - 24 - lw)
            label = (f'<g class="on" style="animation-delay:2.2s">'
                     f'<path d="M{num(bx)} {num(by - 4)}V{num(by - 24)}" stroke="{theme.ink}"/>'
                     f'<rect x="{num(lx + .5)}" y="{num(by - 48.5)}" width="{num(lw)}" height="24" fill="{theme.paper}" '
                     f'stroke="{theme.ink}"/>'
                     + text(lx + 8, by - 32, tag, "m", fill=theme.ink, size=9, letter_spacing="1") + "</g>")
    return f'<g fill="{f["ground"]}">{"".join(tiles)}</g>{"".join(towers)}{label}'


def months(calendar: list, theme: Theme, ox: float, oy: float) -> str:
    out = []
    for w, week in enumerate(calendar):
        first = dt.date.fromisoformat(week[0][0])
        if first.day <= 7 and w > 0:
            out.append(text(ox + w * S, oy + 16, first.strftime("%b").upper(), "m", fill=theme.muted, size=9,
                            letter_spacing="1"))
    return "".join(out)


def fold_small(langs: list[dict], minimum: float = 1.0) -> list[dict]:
    """Merge languages under `minimum` percent into "Other"."""
    keep = [lang for lang in langs if lang["pct"] >= minimum and lang["name"] != "Other"]
    rest = round(sum(lang["pct"] for lang in langs) - sum(lang["pct"] for lang in keep), 1)
    if rest > 0:
        keep.append({"name": "Other", "pct": rest})
    return keep


def ruler(langs: list[dict], theme: Theme, x0: float, y: float, width: float) -> str:
    """Segmented bar with flat fills and hard borders, labels underneath."""
    fills = [theme.ink, theme.accent, "url(#hatch)", theme.paper2, "url(#dots)", theme.paper]
    out = [text(x0, y, "LANGUAGES · BY BYTES IN PUBLIC REPOS", "m", fill=theme.muted, size=9.5, letter_spacing="1.4")]
    by = y + 16
    total = sum(lang["pct"] for lang in langs) or 1
    cx = x0
    for i, lang in enumerate(langs):
        w = width * lang["pct"] / total
        fill = fills[min(i, len(fills) - 1)]
        if fill.startswith("url"):
            out.append(f'<rect x="{num(cx)}" y="{by}" width="{num(w)}" height="16" fill="{theme.paper}"/>')
        out.append(f'<rect class="wipe" x="{num(cx)}" y="{by}" width="{num(w)}" height="16" fill="{fill}" '
                   f'style="animation-delay:{.8 + i * .1:.2f}s"/>')
        cx += w
    out.append(box(x0, by, width, 16, theme.ink))
    # legend: swatch + name + percentage, flowing left to right
    lx, ly = x0, by + 40
    for i, lang in enumerate(langs):
        pct = f"{lang['pct']:.1f}%"
        item_w = 16 + 8 + fonts.width("tm", lang["name"], 12) + 8 + fonts.width("m", pct, 10) + 24
        if lx + item_w > x0 + width + 24:
            lx, ly = x0, ly + 24
        fill = fills[min(i, len(fills) - 1)]
        if fill.startswith("url"):
            out.append(f'<rect x="{num(lx)}" y="{ly - 10}" width="16" height="12" fill="{theme.paper}"/>')
        out.append(box(lx, ly - 10, 16, 12, theme.ink, fill))
        out.append(text(lx + 24, ly, lang["name"], "tm", fill=theme.ink, size=12))
        out.append(text(lx + 24 + fonts.width("tm", lang["name"], 12) + 8, ly, pct, "m", fill=theme.muted, size=10))
        lx += item_w
    return "".join(out)


def kpis(gh: dict, lc: dict | None, theme: Theme) -> tuple[str, str]:
    s = gh["streak"]
    best = ""
    if s.get("longest_range"):
        a, b = (dt.date.fromisoformat(x) for x in s["longest_range"])
        best = f"{a:%b %d} → {b:%b %d, %Y}"
    year = dt.datetime.fromisoformat(gh["fetched_at"]).year
    items = [
        (f"{gh['contributions_last_year']:,}", "", "CONTRIBUTIONS · 12 MO", f"{gh['active_days_last_year']} active days"),
        (str(s["longest"]), " days", "LONGEST STREAK",
         f"running now: {s['current']} days" if s["current"] >= 2 else best),
        (f"{gh['commits_total']:,}", "", "COMMITS · ALL-TIME", f"{gh['commits_year']:,} in {year}"),
    ]
    if lc:
        sv = lc["solved"]
        items.append((str(sv.get("All", 0)), "", "LEETCODE SOLVED",
                      f"easy {sv.get('Easy', 0)} / medium {sv.get('Medium', 0)} / hard {sv.get('Hard', 0)}"))
    else:
        items.append((str(gh["public_repos"]), "", "PUBLIC REPOS", f"{gh['stars']} stars earned"))
    defs, body = [], []
    size = 48
    for i, (value, unit, label, sub) in enumerate(items):
        y = TOP + i * KPI_H
        base = y + 64
        delay = .2 + i * .12
        defs.append(f'<clipPath id="k{i}"><rect x="0" y="{num(base - size * .95)}" width="{SPLIT}" '
                    f'height="{num(size * 1.2)}"/></clipPath>')
        rolled, rw = odometer(value, 32, base, size, theme.ink, delay, cls="sr")
        body.append(f'<g clip-path="url(#k{i})">{rolled}</g>')
        if unit:
            body.append(f'<g class="on" style="animation-delay:{delay + 1:.2f}s">'
                        + text(32 + rw + 4, base, unit.strip(), "si", fill=theme.accent, size=24) + "</g>")
        body.append(text(32, y + 24, label, "m", fill=theme.muted, size=9.5, letter_spacing="1.4"))
        if sub:
            body.append(text(32, y + 88, sub, "t", fill=theme.muted, size=fit("t", sub, 12, SPLIT - 64)))
        if i:
            body.append(hline(0, SPLIT, y - 1, theme.ink))
    return "".join(defs), "".join(body)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    gh = (live or {}).get("github")
    sheet_w = W - 8
    if not gh or not gh.get("calendar"):
        H = TOP + 120 + 8
        body = (card(W, H, theme) + strip(0, 0, sheet_w, "§06", "Telemetry", "warming up", theme)
                + text(32, TOP + 64, "Live numbers land here after the first workflow run.", "sr",
                       fill=theme.ink, size=28))
        return document(body, W, H, title="GitHub telemetry", css=CSS, defs=patterns(theme))

    lc = (live or {}).get("leetcode")
    n_kpi = 4
    H = TOP + n_kpi * KPI_H + 8
    stamp = dt.datetime.fromisoformat(gh["fetched_at"]).strftime("%d %b %Y · %H:%M UTC").upper()
    body = [card(W, H, theme), strip(0, 0, sheet_w, "§06", f"Telemetry — github.com/{gh['login']}",
                                     f"synced {stamp}", theme)]
    kdefs, kbody = kpis(gh, lc, theme)
    body.append(kbody)
    body.append(vline(SPLIT, TOP, H - 8, theme.ink))

    # right column: skyline + months + ruler
    weeks = len(gh["calendar"])
    rx0, rw = SPLIT + 32, sheet_w - SPLIT - 64
    sky_w = (weeks - 1) * S + 6 * DX + S * TW + DX * TD
    ox = rx0 + (rw - sky_w) / 2
    oy = TOP + 32 + 48 + HMAX + 6 * DY + DY * TD
    body.append(f'<rect x="{SPLIT + 1}" y="{TOP}" width="{sheet_w - SPLIT - 2}" height="{num(oy + 32 - TOP)}" '
                f'fill="url(#dots)"/>')
    body.append(skyline(gh["calendar"], theme, ox, oy))
    body.append(months(gh["calendar"], theme, ox, oy))
    body.append(hline(SPLIT, sheet_w, oy + 31, theme.ink))
    if gh.get("languages"):
        body.append(ruler(fold_small(gh["languages"]), theme, rx0, oy + 72, rw))
    s = gh["streak"]
    desc = (f"{gh['contributions_last_year']} contributions in the last year, longest streak {s['longest']} days, "
            f"{gh['commits_total']} commits all-time. Top languages: "
            + ", ".join(f"{lang['name']} {lang['pct']}%" for lang in gh.get("languages", [])))
    return document("".join(body), W, H, title="Live GitHub telemetry", desc=desc, css=CSS,
                    defs=patterns(theme) + kdefs)
