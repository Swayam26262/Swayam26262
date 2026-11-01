"""§07 live telemetry: odometer KPIs, an axonometric skyline of the last 53
weeks of contributions (flat faces: ink fronts, grey sides, paper tops; the
best day in the accent), and a segmented language ruler. KPIs run down the left
on desktop and sit in a 2 x 2 grid above the skyline on phones.

Data comes from live.py (refreshed daily by the workflow)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from core import fonts
from core.design import CSS as BASE, box, canvas, card, hline, patterns, strip, vline
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import document, fit, num, text
from core.theme import Theme, mix

TOP = 40

CSS = BASE + ODO_CSS + """
.up{animation:up .7s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}
@keyframes up{from{transform:scaleY(0)}}
"""


@dataclass(frozen=True)
class Sky:
    """Skyline geometry: weeks run left to right, weekdays recede up and to the right."""
    s: float      # week pitch
    dx: float     # per-row depth offset
    dy: float
    hmax: float
    tw: float = .76
    td: float = .76

    def width(self, weeks: int) -> float:
        return (weeks - 1) * self.s + 6 * self.dx + self.s * self.tw + self.dx * self.td

    def depth(self) -> float:
        return 6 * self.dy + self.dy * self.td


DESKTOP_SKY = Sky(8.8, 4.0, 5.6, 104)
MOBILE_SKY = Sky(6.0, 2.8, 4.0, 80)


def faces(theme: Theme) -> dict:
    if theme.dark:
        return dict(front=theme.ink, side=theme.faint, top=theme.muted, ground=theme.hair)
    return dict(front=theme.ink, side=theme.muted, top=theme.paper2, ground=theme.hair)


def skyline(calendar: list, theme: Theme, ox: float, oy: float, g: Sky, right: float) -> str:
    cells = [(w, d, date, count) for w, week in enumerate(calendar) for d, (date, count) in enumerate(week)]
    peak = max((c for *_, c in cells), default=0) or 1
    best = max(cells, key=lambda c: c[3]) if cells else None
    tw, dx, dy = g.s * g.tw, g.dx * g.td, g.dy * g.td
    f = faces(theme)
    tiles, towers, label = [], [], ""
    for w, d, date, count in sorted(cells, key=lambda c: (c[1], c[0])):  # back rows first
        px = ox + w * g.s + (6 - d) * g.dx
        py = oy - (6 - d) * g.dy
        if count == 0:
            tiles.append(f'<polygon points="{num(px)} {num(py)} {num(px + tw)} {num(py)} {num(px + tw + dx)} '
                         f'{num(py - dy)} {num(px + dx)} {num(py - dy)}"/>')
            continue
        h = 4 + (g.hmax - 4) * (count / peak) ** .6
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
            lx = min(bx - 8, right - lw)
            label = (f'<g class="on" style="animation-delay:2.2s">'
                     f'<path d="M{num(bx)} {num(by - 4)}V{num(by - 24)}" stroke="{theme.ink}"/>'
                     f'<rect x="{num(lx + .5)}" y="{num(by - 48.5)}" width="{num(lw)}" height="24" fill="{theme.paper}" '
                     f'stroke="{theme.ink}"/>'
                     + text(lx + 8, by - 32, tag, "m", fill=theme.ink, size=9, letter_spacing="1") + "</g>")
    return f'<g fill="{f["ground"]}">{"".join(tiles)}</g>{"".join(towers)}{label}'


def months(calendar: list, theme: Theme, ox: float, oy: float, g: Sky, every: int) -> str:
    out, n = [], 0
    for w, week in enumerate(calendar):
        first = dt.date.fromisoformat(week[0][0])
        if first.day <= 7 and w > 0:
            if n % every == 0:
                out.append(text(ox + w * g.s, oy + 16, first.strftime("%b").upper(), "m", fill=theme.muted, size=9,
                                letter_spacing="1"))
            n += 1
    return "".join(out)


def fold_small(langs: list[dict], minimum: float = 1.0) -> list[dict]:
    """Merge languages under `minimum` percent into "Other"."""
    keep = [lang for lang in langs if lang["pct"] >= minimum and lang["name"] != "Other"]
    rest = round(sum(lang["pct"] for lang in langs) - sum(lang["pct"] for lang in keep), 1)
    if rest > 0:
        keep.append({"name": "Other", "pct": rest})
    return keep


def ruler(langs: list[dict], theme: Theme, x0: float, y: float, width: float) -> tuple[str, float]:
    """Segmented bar with flat fills and hard borders, legend underneath. Returns (markup, bottom)."""
    fills = [theme.ink, theme.accent, "url(#hatch)", theme.paper2, "url(#dots)", theme.paper]
    out = [text(x0, y, "LANGUAGES · BY BYTES", "m", fill=theme.muted, size=9.5, letter_spacing="1.4")]
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
    return "".join(out), ly


def kpi_items(gh: dict, lc: dict | None) -> list[tuple[str, str, str, str]]:
    s = gh["streak"]
    best = ""
    if s.get("longest_range"):
        a, b = (dt.date.fromisoformat(x) for x in s["longest_range"])
        best = f"{a:%b %d} → {b:%b %d, %Y}"
    year = dt.datetime.fromisoformat(gh["fetched_at"]).year
    items = [
        (f"{gh['contributions_last_year']:,}", "", "CONTRIBUTIONS · 12 MO", f"{gh['active_days_last_year']} active days"),
        (str(s["longest"]), "days", "LONGEST STREAK", f"running now: {s['current']} days" if s["current"] >= 2 else best),
        (f"{gh['commits_total']:,}", "", "COMMITS · ALL-TIME", f"{gh['commits_year']:,} in {year}"),
    ]
    if lc:
        sv = lc["solved"]
        items.append((str(sv.get("All", 0)), "", "LEETCODE SOLVED",
                      f"easy {sv.get('Easy', 0)} / medium {sv.get('Medium', 0)} / hard {sv.get('Hard', 0)}"))
    else:
        items.append((str(gh["public_repos"]), "", "PUBLIC REPOS", f"{gh['stars']} stars earned"))
    return items


def kpi(item: tuple, i: int, x: float, y: float, w: float, size: float, theme: Theme) -> tuple[str, str]:
    value, unit, label, sub = item
    base = y + 24 + size * 1.05
    delay = .2 + i * .12
    defs = (f'<clipPath id="k{i}"><rect x="{num(x)}" y="{num(base - size * .95)}" width="{num(w)}" '
            f'height="{num(size * 1.2)}"/></clipPath>')
    rolled, rw = odometer(value, x + 24, base, size, theme.ink, delay, cls="sr")
    out = [text(x + 24, y + 24, label, "m", fill=theme.muted, size=fit("m", label, 9.5, w - 48, 1.4), letter_spacing="1.4"),
           f'<g clip-path="url(#k{i})">{rolled}</g>']
    if unit:
        out.append(f'<g class="on" style="animation-delay:{delay + 1:.2f}s">'
                   + text(x + 24 + rw + 4, base, unit, "si", fill=theme.accent, size=size / 2) + "</g>")
    if sub:
        out.append(text(x + 24, base + 22, sub, "t", fill=theme.muted, size=fit("t", sub, 12, w - 48)))
    return defs, "".join(out)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    gh = (live or {}).get("github")
    W = canvas(mobile)
    sheet_w = W - 8
    if not gh or not gh.get("calendar"):
        H = TOP + 120 + 8
        body = (card(W, H, theme) + strip(0, 0, sheet_w, "§07", "Telemetry", "warming up", theme)
                + text(24, TOP + 64, "Live numbers land here after the first run.", "sr", fill=theme.ink,
                       size=fit("sr", "Live numbers land here after the first run.", 28, sheet_w - 48)))
        return document(body, W, H, title="GitHub telemetry", css=CSS, defs=patterns(theme))

    items = kpi_items(gh, (live or {}).get("leetcode"))
    stamp = dt.datetime.fromisoformat(gh["fetched_at"])
    title = "Telemetry" if mobile else f"Telemetry — github.com/{gh['login']}"
    right = f"synced {stamp:%d %b}" if mobile else f"synced {stamp:%d %b %Y · %H:%M UTC}"
    defs, body = [patterns(theme)], [strip(0, 0, sheet_w, "§07", title, right, theme)]
    if mobile:
        g, kpi_w, kpi_h = MOBILE_SKY, sheet_w / 2, 112
        for i, item in enumerate(items):
            r, c = divmod(i, 2)
            d, b = kpi(item, i, c * kpi_w, TOP + r * kpi_h, kpi_w, 40, theme)
            defs.append(d)
            body.append(b)
            body.append(box(c * kpi_w, TOP + r * kpi_h, kpi_w, kpi_h, theme.ink))
        sky_top = TOP + 2 * kpi_h
        rx0, rw = 24, sheet_w - 48
        every = 2
    else:
        g, split, kpi_h = DESKTOP_SKY, 256, 104
        for i, item in enumerate(items):
            d, b = kpi(item, i, 0, TOP + i * kpi_h, split, 48, theme)
            defs.append(d)
            body.append(b)
            if i:
                body.append(hline(0, split, TOP + i * kpi_h - 1, theme.ink))
        body.append(vline(split, TOP, TOP + len(items) * kpi_h, theme.ink))
        sky_top = TOP
        rx0, rw = split + 32, sheet_w - split - 64
        every = 1
    weeks = len(gh["calendar"])
    ox = rx0 + (rw - g.width(weeks)) / 2
    oy = sky_top + 32 + 48 + g.hmax + g.depth()
    left = 1 if mobile else 257
    body.append(f'<rect x="{left}" y="{sky_top}" width="{sheet_w - left - 1}" height="{num(oy + 32 - sky_top)}" '
                f'fill="url(#dots)"/>')
    body.append(skyline(gh["calendar"], theme, ox, oy, g, sheet_w - 24))
    body.append(months(gh["calendar"], theme, ox, oy, g, every))
    body.append(hline(left - 1, sheet_w, oy + 31, theme.ink))
    bottom = oy + 32
    if gh.get("languages"):
        rule, ly = ruler(fold_small(gh["languages"]), theme, rx0, oy + 72, rw)
        body.append(rule)
        bottom = ly + 24
    H = max(bottom, TOP + len(items) * 104 if not mobile else 0) + 8
    H += -H % 8
    body.insert(0, card(W, H, theme))
    s = gh["streak"]
    desc = (f"{gh['contributions_last_year']} contributions in the last year, longest streak {s['longest']} days, "
            f"{gh['commits_total']} commits all-time. Top languages: "
            + ", ".join(f"{lang['name']} {lang['pct']}%" for lang in gh.get("languages", [])))
    return document("".join(body), W, H, title="Live GitHub telemetry", desc=desc, css=CSS, defs="".join(defs))
