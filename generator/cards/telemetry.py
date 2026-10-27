"""Live GitHub telemetry: odometer KPIs, a 3D skyline of the last 53 weeks of
contributions that rises on load, and a top-languages bar.

Data comes from live.py (refreshed daily by the workflow)."""

from __future__ import annotations

import datetime as dt

from core import fonts
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import document, num, text
from core.theme import Theme, mix

W = 840
PAD = 28

# skyline geometry (oblique projection: weeks run left->right, weekdays recede up-right)
S, DX, DY = 13.4, 5.0, 6.8      # week pitch, per-row depth offset
TW, TD = .78, .78               # tower footprint as a fraction of the pitch
HMAX = 74

CSS = ODO_CSS + """
.rise{animation:rise .9s cubic-bezier(.2,.9,.25,1.15) both;transform-box:fill-box;transform-origin:bottom}
@keyframes rise{from{transform:scaleY(0)}}
.seg{animation:seg 1.1s cubic-bezier(.3,.8,.2,1) both;transform-box:fill-box;transform-origin:left}
@keyframes seg{from{transform:scaleX(0)}}
.fi{animation:fi .8s ease-out both}
@keyframes fi{from{opacity:0}}
.ring{animation:ring 2s ease-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ring{from{opacity:.7;transform:scale(1)}to{opacity:0;transform:scale(3)}}
.best{animation:best 2.4s ease-in-out infinite}
@keyframes best{50%{transform:translateY(-3px)}}
"""


def grad_at(t: float, stops: tuple[str, str, str]) -> str:
    return mix(stops[0], stops[1], t * 2) if t < .5 else mix(stops[1], stops[2], (t - .5) * 2)


def skyline(calendar: list, theme: Theme, ox: float, oy: float) -> tuple[str, float, float]:
    """Returns (markup, left x, top y) of the 3D contribution skyline."""
    cells = [(w, d, date, count) for w, week in enumerate(calendar) for d, (date, count) in enumerate(week)]
    peak = max((c for *_, c in cells), default=0) or 1
    tw, dx, dy = S * TW, DX * TD, DY * TD
    ground = theme.border if theme.dark else "#e3e8f4"
    tiles, towers = [], []
    best = max(cells, key=lambda c: c[3]) if cells else None
    best_xy = None
    weeks = max(len(calendar) - 1, 1)
    # painter's order: back rows (Sunday) first, then left to right
    for w, d, date, count in sorted(cells, key=lambda c: (c[1], c[0])):
        px = ox + w * S + (6 - d) * DX
        py = oy - (6 - d) * DY
        top = f"{num(px)} {num(py)} {num(px + tw)} {num(py)} {num(px + tw + dx)} {num(py - dy)} {num(px + dx)} {num(py - dy)}"
        if count == 0:
            tiles.append(f'<polygon points="{top}"/>')
            continue
        level = (count / peak) ** .55
        h = 3 + (HMAX - 3) * level
        base = grad_at(w / weeks, theme.grad)
        color = mix(theme.panel2, base, .45 + .55 * level)
        front = color
        side = mix(color, "#000000", .32)
        lid = mix(color, "#ffffff", .22 if theme.dark else .35)
        delay = .35 + w * .028 + (6 - d) * .03
        towers.append(
            f'<g class="rise" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{num(px)}" y="{num(py - h)}" width="{num(tw)}" height="{num(h)}" fill="{front}"/>'
            f'<polygon points="{num(px + tw)} {num(py)} {num(px + tw + dx)} {num(py - dy)} {num(px + tw + dx)} '
            f'{num(py - dy - h)} {num(px + tw)} {num(py - h)}" fill="{side}"/>'
            f'<polygon points="{num(px)} {num(py - h)} {num(px + tw)} {num(py - h)} {num(px + tw + dx)} '
            f'{num(py - dy - h)} {num(px + dx)} {num(py - dy - h)}" fill="{lid}"/></g>'
        )
        if best and (w, d) == best[:2]:
            best_xy = (px + tw / 2 + dx / 2, py - dy - h)
    out = f'<g fill="{ground}" fill-opacity="{.7 if theme.dark else 1}">{"".join(tiles)}</g>{"".join(towers)}'
    if best and best_xy:
        bx, by = best_xy
        label = f"best day · {best[3]} on {dt.date.fromisoformat(best[2]).strftime('%b %d')}"
        lw = fonts.width("m", label, 9.5) + 16
        lx = min(max(bx - lw / 2, PAD), W - PAD - lw)
        out += (f'<g class="fi" style="animation-delay:2.4s"><g class="best">'
                f'<path d="M{num(bx)} {num(by - 4)}V{num(by - 16)}" stroke="{theme.text}" stroke-opacity=".5" stroke-dasharray="2 2"/>'
                f'<rect x="{num(lx)}" y="{num(by - 36)}" width="{num(lw)}" height="20" rx="10" fill="{theme.panel2}" '
                f'stroke="{theme.border2}"/>'
                + text(lx + 8, by - 22.5, label, "m", fill=theme.text, size=9.5)
                + f'<circle cx="{num(bx)}" cy="{num(by - 3)}" r="2.5" fill="{theme.text}"/></g></g>')
    return out, ox, oy - 6 * DY - dy - HMAX


def months(calendar: list, theme: Theme, x0: float, oy: float) -> str:
    """Month names under the front row, at the first week that starts in each month."""
    out = []
    for w, week in enumerate(calendar):
        first = dt.date.fromisoformat(week[0][0])
        if first.day <= 7 and w > 0:
            out.append(text(x0 + w * S, oy + 16, first.strftime("%b").upper(), "m", fill=theme.faint, size=9,
                            letter_spacing="1"))
    return "".join(out)


def kpis(gh: dict, lc: dict | None, theme: Theme, y: float) -> tuple[str, str]:
    s = gh["streak"]
    best = ""
    if s.get("longest_range"):
        a, b = (dt.date.fromisoformat(x) for x in s["longest_range"])
        best = f"{a:%b %d} → {b:%b %d, %Y}"
    year = dt.datetime.fromisoformat(gh["fetched_at"]).year
    streak_sub = f"running now: {s['current']} days" if s["current"] >= 2 else best
    items = [
        (f"{gh['contributions_last_year']:,}", "", "CONTRIBUTIONS · 12 MO", f"{gh['active_days_last_year']} active days", theme.cyan),
        (str(s["longest"]), " days" if s["longest"] != 1 else " day", "LONGEST STREAK", streak_sub, theme.amber),
        (f"{gh['commits_total']:,}", "", "COMMITS · ALL-TIME", f"{gh['commits_year']:,} in {year}", theme.pink),
    ]
    if lc:
        sv = lc["solved"]
        items.append((str(sv.get("All", 0)), "", "LEETCODE SOLVED",
                      f"E {sv.get('Easy', 0)} · M {sv.get('Medium', 0)} · H {sv.get('Hard', 0)}", theme.green))
    else:
        items.append((str(gh["public_repos"]), "", "PUBLIC REPOS", f"{gh['stars']} stars earned", theme.green))
    col = (W - 2 * PAD) / len(items)
    defs, body = [], []
    size = 26
    for i, (value, unit, label, sub, color) in enumerate(items):
        x = PAD + i * col
        delay = .2 + i * .12
        defs.append(f'<clipPath id="k{i}"><rect x="{num(x)}" y="{num(y - size * 1.02)}" width="{num(col)}" '
                    f'height="{num(size * 1.25)}"/></clipPath>')
        rolled, rw = odometer(value, x, y, size, theme.text, delay)
        body.append(f'<rect x="{num(x)}" y="{num(y - 38)}" width="22" height="2" rx="1" fill="{color}"/>')
        body.append(f'<g clip-path="url(#k{i})">{rolled}</g>')
        if unit:
            body.append(f'<g class="fi" style="animation-delay:{delay + 1:.2f}s">'
                        + text(x + rw + 2, y, unit, "sm", fill=theme.muted, size=13) + "</g>")
        body.append(text(x, y + 20, label, "m", fill=theme.muted, size=9.5, letter_spacing="1.2"))
        if sub:
            body.append(text(x, y + 36, sub, "s", fill=theme.faint if theme.dark else theme.muted, size=11))
        if i:
            body.append(f'<path d="M{num(x - 14)} {num(y - 36)}v76" stroke="{theme.border}"/>')
    return "".join(defs), "".join(body)


def fold_small(langs: list[dict], minimum: float = 1.0) -> list[dict]:
    """Merge languages under `minimum` percent into "Other"."""
    keep = [lang for lang in langs if lang["pct"] >= minimum and lang["name"] != "Other"]
    rest = round(sum(lang["pct"] for lang in langs) - sum(lang["pct"] for lang in keep), 1)
    if rest > 0:
        keep.append({"name": "Other", "color": "#8b949e", "pct": rest})
    return keep


def languages(langs: list[dict], theme: Theme, y: float) -> tuple[str, float]:
    langs = fold_small(langs)
    x0, width = PAD, W - 2 * PAD
    out = [text(PAD, y, "TOP LANGUAGES", "m", fill=theme.muted, size=9.5, letter_spacing="1.2"),
           text(W - PAD, y, "by bytes across public repos", "s", fill=theme.faint if theme.dark else theme.muted,
                size=11, anchor="end")]
    by = y + 12
    out.append(f'<rect x="{x0}" y="{num(by)}" width="{num(width)}" height="10" rx="5" fill="{theme.panel2}"/>')
    out.append(f'<clipPath id="lb"><rect x="{x0}" y="{num(by)}" width="{num(width)}" height="10" rx="5"/></clipPath>')
    segs, cx = [], x0
    total = sum(lang["pct"] for lang in langs) or 1
    for i, lang in enumerate(langs):
        w = width * lang["pct"] / total
        segs.append(f'<rect class="seg" x="{num(cx)}" y="{num(by)}" width="{num(w + .5)}" height="10" fill="{lang["color"]}" '
                    f'style="animation-delay:{.6 + i * .12:.2f}s"/>')
        cx += w
    out.append(f'<g clip-path="url(#lb)">{"".join(segs)}</g>')
    # legend, wrapping if needed
    lx, ly = x0, by + 34
    for lang in langs:
        pct = f"{lang['pct']:.1f}%"
        iw = 14 + fonts.width("sm", lang["name"], 12) + 6 + fonts.width("m", pct, 11) + 22
        if lx + iw > W - PAD:
            lx, ly = x0, ly + 20
        out.append(f'<circle cx="{num(lx + 4)}" cy="{num(ly - 4)}" r="4" fill="{lang["color"]}"/>')
        out.append(text(lx + 14, ly, lang["name"], "sm", fill=theme.text, size=12))
        out.append(text(lx + 14 + fonts.width("sm", lang["name"], 12) + 6, ly, pct, "m", fill=theme.muted, size=11))
        lx += iw
    return "".join(out), ly


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    gh = (live or {}).get("github")
    th = theme
    header = []
    if not gh or not gh.get("calendar"):
        H = 120
        body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{th.panel}" stroke="{th.border}"/>'
                + text(W / 2, 56, "Telemetry is warming up", "d", fill=th.text, size=18, anchor="middle")
                + text(W / 2, 80, "The first run of the profile workflow fills this card with live GitHub data.",
                       "s", fill=th.muted, size=12.5, anchor="middle"))
        return document(body, W, H, title="GitHub telemetry", css=CSS)

    # header
    header.append(f'<circle class="ring" cx="{PAD + 4}" cy="30" r="3.5" fill="{th.green}"/>'
                  f'<circle cx="{PAD + 4}" cy="30" r="3.5" fill="{th.green}"/>')
    header.append(text(PAD + 16, 33.5, f"LIVE TELEMETRY · GITHUB.COM/{gh['login'].upper()}", "mb", fill=th.text,
                       size=10, letter_spacing="1.4"))
    stamp = dt.datetime.fromisoformat(gh["fetched_at"]).strftime("%d %b %Y · %H:%M UTC").upper()
    header.append(text(W - PAD, 33.5, f"SYNCED {stamp}", "m", fill=th.faint, size=9.5, anchor="end", letter_spacing="1"))
    header.append(f'<path d="M{PAD} 52H{W - PAD}" stroke="{th.border}"/>')

    kdefs, kbody = kpis(gh, (live or {}).get("leetcode"), th, 112)

    weeks = len(gh["calendar"])
    sky_w = (weeks - 1) * S + 6 * DX + S * TW + DX * TD
    ox = (W - sky_w) / 2
    oy = 206 + 6 * DY + DY * TD + HMAX
    sky, _, _ = skyline(gh["calendar"], th, ox, oy)
    sky += months(gh["calendar"], th, ox, oy)

    ldy = oy + 52
    lang_body, bottom = languages(gh["languages"], th, ldy) if gh.get("languages") else ("", ldy)
    H = round(bottom + 26)

    panel = f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{th.panel}" stroke="{th.border}"/>'
    glow = (f'<radialGradient id="sg" cx=".5" cy="1" r=".6"><stop offset="0" stop-color="{th.indigo}" '
            f'stop-opacity="{.16 * th.glow}"/><stop offset="1" stop-color="{th.indigo}" stop-opacity="0"/></radialGradient>')
    body = (panel + f'<rect x="1" y="180" width="{W - 2}" height="{num(oy - 160)}" fill="url(#sg)"/>'
            + "".join(header) + kbody + sky + lang_body)
    s = gh["streak"]
    desc = (f"{gh['contributions_last_year']} contributions in the last year, current streak {s['current']} days, "
            f"longest streak {s['longest']} days, {gh['commits_total']} commits all-time. Top languages: "
            + ", ".join(f"{lang['name']} {lang['pct']}%" for lang in gh.get("languages", [])))
    return document(body, W, H, title="Live GitHub telemetry", desc=desc, css=CSS, defs=glow + kdefs)
