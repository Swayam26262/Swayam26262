"""Hero banner: aurora glow, a neural mesh with travelling pulses, the name
drawn stroke-by-stroke, and a typing line that cycles through taglines."""

from __future__ import annotations

import math
import random

from core import fonts
from core.icons import icon
from core.motion import BLINK_CSS, TypedLine, typing_cycle
from core.svg import document, num, text
from core.theme import Theme

W, H = 840, 320

CSS = BLINK_CSS + """
.au{animation:drift 18s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(38px,14px) scale(1.12)}100%{transform:translate(-26px,22px) scale(.94)}}
.tw{animation:tw 4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.12}50%{opacity:.95}}
.pl{stroke-dasharray:.09 1.2;animation:pl 3s linear infinite}
@keyframes pl{0%{stroke-dashoffset:.09}55%,100%{stroke-dashoffset:-1.05}}
.ltr{stroke-dasharray:1;animation:draw 1.5s cubic-bezier(.65,0,.25,1) both,fillin .9s ease-out both}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes fillin{from{fill-opacity:0}to{fill-opacity:1}}
.glow{animation:fade 1.6s ease-out 1.6s both,breathe 5s ease-in-out 3.2s infinite}
@keyframes fade{from{opacity:0}}
@keyframes breathe{50%{opacity:.55}}
.shine{animation:shine 7s cubic-bezier(.45,0,.2,1) 3s infinite}
@keyframes shine{0%{transform:translateX(0)}32%,100%{transform:translateX(1180px)}}
.up{animation:up .9s cubic-bezier(.2,.8,.2,1) both}
@keyframes up{from{opacity:0;transform:translateY(10px)}}
.ring{animation:ring 2s ease-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ring{from{opacity:.7;transform:scale(1)}to{opacity:0;transform:scale(2.8)}}
"""


def _mesh(rnd: random.Random, theme: Theme) -> str:
    nodes = [(rnd.uniform(18, W - 18), rnd.uniform(16, H - 16)) for _ in range(30)]
    edges = set()
    for i, (x, y) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.dist((x, y), nodes[j]))[1:3]
        for j in near:
            if math.dist(nodes[i], nodes[j]) < 210:
                edges.add(tuple(sorted((i, j))))
    edges = sorted(edges)
    d = "".join(f"M{num(nodes[a][0])} {num(nodes[a][1])}L{num(nodes[b][0])} {num(nodes[b][1])}" for a, b in edges)
    out = [f'<path d="{d}" stroke="{theme.indigo}" stroke-opacity="{.26 if theme.dark else .22}" stroke-width=".8"/>']
    for x, y in nodes:
        out.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="1.7" fill="{theme.indigo}" fill-opacity=".6"/>')
    for a, b in rnd.sample(edges, min(12, len(edges))):
        if rnd.random() < .5:
            a, b = b, a
        dur, delay = rnd.uniform(2.6, 4.2), rnd.uniform(0, 4)
        out.append(
            f'<path class="pl" d="M{num(nodes[a][0])} {num(nodes[a][1])}L{num(nodes[b][0])} {num(nodes[b][1])}" '
            f'pathLength="1" stroke="{theme.cyan}" stroke-width="1.8" stroke-linecap="round" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>'
        )
    return "".join(out)


def _stars(rnd: random.Random, theme: Theme) -> str:
    color = "#ffffff" if theme.dark else theme.indigo
    out = []
    for _ in range(54):
        x, y = rnd.uniform(10, W - 10), rnd.uniform(8, H - 8)
        r = rnd.choice((.5, .7, .8, 1, 1.2, 1.5))
        out.append(
            f'<circle class="tw" cx="{num(x)}" cy="{num(y)}" r="{r}" fill="{color}" '
            f'style="animation-duration:{rnd.uniform(2.4, 6):.2f}s;animation-delay:-{rnd.uniform(0, 6):.2f}s"/>'
        )
    return "".join(out)


def _aurora(theme: Theme) -> tuple[str, str]:
    blobs = [  # color, cx, cy, rx, ry, strength, delay
        (theme.cyan, 140, 50, 270, 170, .55, 0),
        (theme.indigo, 440, 10, 320, 170, .5, -6),
        (theme.violet, 640, 120, 200, 140, .35, -3),
        (theme.pink, 740, 300, 280, 170, .5, -9),
    ]
    defs, body = [], []
    for i, (c, cx, cy, rx, ry, k, delay) in enumerate(blobs):
        defs.append(
            f'<radialGradient id="a{i}"><stop offset="0" stop-color="{c}" stop-opacity="{num(k * theme.glow)}"/>'
            f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        )
        body.append(
            f'<ellipse class="au" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#a{i})" '
            f'style="animation-delay:{delay}s"/>'
        )
    return "".join(defs), "".join(body)


def _hud_row(items: list[tuple[str, str, str]], y: float, theme: Theme) -> str:
    size, isz, gap, sep = 13, 14, 7, 30
    widths = [isz + gap + fonts.width("sm", label, size) for _, label, _ in items]
    total = sum(widths) + sep * (len(items) - 1)
    x = (W - total) / 2
    out = []
    for i, ((slug, label, color), w) in enumerate(zip(items, widths)):
        if i:
            out.append(f'<path d="M{num(x - sep / 2)} {num(y - 11)}v13" stroke="{theme.border2}"/>')
        out.append(icon(slug, x, y - isz + 2, isz, theme, color=color, stroke_width=2))
        out.append(text(x + isz + gap, y, label, "sm", fill=theme.muted, size=size))
        x += w + sep
    return "".join(out)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    rnd = random.Random(26262)
    person = profile["person"]
    defs, body = [], []

    bg = ("#060a18", "#0a1230", "#0d0b26") if theme.dark else ("#ffffff", "#f3f5ff", "#fff3fa")
    defs.append(
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg[0]}"/>'
        f'<stop offset=".55" stop-color="{bg[1]}"/><stop offset="1" stop-color="{bg[2]}"/></linearGradient>'
        f'<clipPath id="panel"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
        # Fade the mesh and stars behind the name so the text stays crisp.
        f'<radialGradient id="hole"><stop offset="0" stop-color="#2a2a2a"/><stop offset=".6" stop-color="#555"/>'
        f'<stop offset="1" stop-color="#fff"/></radialGradient>'
        f'<mask id="fade"><rect width="{W}" height="{H}" fill="#fff"/>'
        f'<ellipse cx="{W / 2}" cy="170" rx="360" ry="130" fill="url(#hole)"/></mask>'
    )
    aurora_defs, aurora = _aurora(theme)
    defs.append(aurora_defs)

    body.append(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="url(#bg)"/>{aurora}')
    body.append(f'<g mask="url(#fade)">{_mesh(rnd, theme)}{_stars(rnd, theme)}</g></g>')
    body.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" stroke="{theme.border}"/>')

    # viewfinder corners + tiny HUD labels
    c, L = theme.faint, 14
    for x, y, dx, dy in ((16, 16, 1, 1), (W - 16, 16, -1, 1), (16, H - 16, 1, -1), (W - 16, H - 16, -1, -1)):
        body.append(f'<path d="M{x} {y + dy * L}V{y}H{x + dx * L}" stroke="{c}" stroke-width="1.3" stroke-opacity=".8"/>')
    lab = dict(size=9.5, fill=theme.faint, letter_spacing="1.4")
    body.append(text(38, 30, "~/swayam/readme", "m", **lab))
    body.append(text(W - 38, 30, person["coords"].upper(), "m", anchor="end", **lab))
    body.append(f'<circle cx="41" cy="{H - 25.5}" r="2.2" fill="{theme.green}"/>')
    body.append(text(49, H - 22, "ALL SYSTEMS NOMINAL", "m", **lab))
    body.append(text(W - 38, H - 22, f"GITHUB.COM/{person['github'].upper()}", "m", anchor="end", **lab))

    # status pill
    status = person["status"].upper()
    tw = fonts.width("m", status, 10.5, 1.5) + 1.5
    pw = 30 + tw + 16
    px, py = (W - pw) / 2, 46
    body.append(
        f'<g class="up" style="animation-delay:.15s"><rect x="{num(px)}" y="{py}" width="{num(pw)}" height="26" rx="13" '
        f'fill="{theme.panel2}" fill-opacity=".75" stroke="{theme.border2}"/>'
        f'<circle class="ring" cx="{num(px + 17)}" cy="{py + 13}" r="3.6" fill="{theme.green}"/>'
        f'<circle cx="{num(px + 17)}" cy="{py + 13}" r="3.6" fill="{theme.green}"/>'
        + text(px + 30, py + 17, status, "m", fill=theme.text, size=10.5, letter_spacing="1.5")
        + "</g>"
    )

    # the name, outlined glyph by glyph
    name, size, tracking, base = person["name"].upper(), 60, 3, 160
    face = fonts.font("u")
    nw = face.width(name, size, tracking)
    x0, cx = (W - nw) / 2, (W - nw) / 2
    g0, g1, g2 = theme.grad
    defs.append(
        f'<linearGradient id="ng" gradientUnits="userSpaceOnUse" x1="{num(x0)}" y1="0" x2="{num(x0 + nw)}" y2="0">'
        f'<stop offset="0" stop-color="{g0}"/><stop offset=".5" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/></linearGradient>'
        f'<linearGradient id="shinegrad" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{.6 if theme.dark else .75}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<filter id="blur" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="14"/></filter>'
    )
    letters, uses, clip_uses = [], [], []
    k = 0
    for ch in name:
        if ch != " ":
            d = face.path(ch, cx, base, size)
            defs.append(f'<path id="L{k}" d="{d}" pathLength="1"/>')
            delay = .2 + k * .07
            uses.append(f'<use href="#L{k}" class="ltr" style="animation-delay:{delay:.2f}s,{delay + .95:.2f}s"/>')
            clip_uses.append(f'<use href="#L{k}"/>')
            letters.append(f'<use href="#L{k}"/>')
            k += 1
        cx += face.width(ch, size) + tracking
    defs.append(f'<clipPath id="nc">{"".join(clip_uses)}</clipPath>')
    body.append(f'<g class="glow" fill="url(#ng)" opacity="{.75 if theme.dark else .35}" filter="url(#blur)">{"".join(letters)}</g>')
    body.append(f'<g fill="url(#ng)" stroke="url(#ng)" stroke-width="1.3" stroke-linejoin="round">{"".join(uses)}</g>')
    body.append(
        f'<g clip-path="url(#nc)"><g transform="skewX(-18)"><rect class="shine" x="-200" y="0" width="150" '
        f'height="{H}" fill="url(#shinegrad)"/></g></g>'
    )

    # typing taglines
    tsize = 17
    cw = fonts.width("m", "M", tsize)
    lines = [TypedLine(t, (W - len(t) * cw) / 2, cw) for t in person["taglines"]]
    tdefs, typed = typing_cycle(lines, y=216, size=tsize, cls="m", fill=theme.text, cursor_fill=theme.cyan,
                                uid="ty", lead=2.1)
    defs.append(tdefs)
    body.append(typed)

    # location / focus / education
    hud = [
        ("glyph:pin", person["location"], theme.cyan),
        ("glyph:bolt", "  ·  ".join(person["focus"]), theme.indigo),
        ("glyph:cap", person["education"], theme.pink),
    ]
    body.append(f'<g class="up" style="animation-delay:2.2s">{_hud_row(hud, 266, theme)}</g>')

    return document("".join(body), W, H, title=f"{person['name']} — {person['role']}",
                    desc=" · ".join(person["taglines"]), css=CSS, defs="".join(defs))
