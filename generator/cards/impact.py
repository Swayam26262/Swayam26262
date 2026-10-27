"""'By the numbers' tiles whose digits roll into place like an odometer."""

from __future__ import annotations

import re

from core import fonts
from core.icons import icon
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import document, esc, fit, num, text
from core.theme import Theme

W, COLS, GAP, TILE_H = 840, 3, 12, 122
SIZE = 36
NUM = "u"   # Unbounded, same face as the name in the hero

CSS = ODO_CSS + """
.fx{animation:fx .7s ease-out both}
@keyframes fx{from{opacity:0;transform:translateY(6px)}}
.tile{animation:tile .7s cubic-bezier(.2,.8,.2,1) both}
@keyframes tile{from{opacity:0;transform:translateY(14px)}}
.bar{animation:bar 1.4s cubic-bezier(.3,.8,.2,1) both;transform-box:fill-box;transform-origin:left}
@keyframes bar{from{transform:scaleX(0)}}
"""


def split_value(value: str) -> tuple[str, str, str]:
    m = re.match(r"^(\D*)([\d,.]+)(.*)$", value)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", "", value)


def tile(item: dict, x: float, y: float, w: float, theme: Theme, idx: int) -> tuple[str, str]:
    color = getattr(theme, item.get("color", "indigo"))
    delay = .15 + idx * .1
    tid = f"t{idx}"
    defs = (
        f'<radialGradient id="g{tid}" cx="1" cy="0" r="1"><stop offset="0" stop-color="{color}" '
        f'stop-opacity="{.22 * theme.glow + .04}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="l{tid}" x1="0" x2="1"><stop offset="0" stop-color="{color}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="c{tid}"><rect x="{num(x)}" y="{num(y + 38)}" width="{num(w)}" height="{num(SIZE * 1.25)}"/></clipPath>'
    )
    pad = 20
    base = y + 38 + SIZE * 1.02
    prefix, digits, suffix = split_value(item["value"])
    small = SIZE * .56
    cx = x + pad
    num_parts = []
    if prefix:
        num_parts.append(f'<text class="{NUM} fx" x="{num(cx)}" y="{num(base)}" font-size="{num(small)}" '
                         f'fill="{color}" style="animation-delay:{delay + .5:.2f}s">{esc(prefix)}</text>')
        cx += fonts.width(NUM, prefix, small) + 3
    rolled, rw = odometer(digits, cx, base, SIZE, theme.text, delay + .1, cls=NUM)
    num_parts.append(f'<g clip-path="url(#c{tid})">{rolled}</g>')
    cx += rw + 3
    if suffix:
        num_parts.append(f'<text class="{NUM} fx" x="{num(cx)}" y="{num(base)}" font-size="{num(small)}" '
                         f'fill="{color}" style="animation-delay:{delay + 1.2:.2f}s">{esc(suffix)}</text>')
    body = (
        f'<g class="tile" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="{TILE_H - 1}" rx="14" '
        f'fill="{theme.panel}" stroke="{theme.border}"/>'
        f'<rect x="{num(x + 1)}" y="{num(y + 1)}" width="{num(w - 2)}" height="{TILE_H - 2}" rx="13.5" fill="url(#g{tid})"/>'
        f'<rect class="bar" x="{num(x + 18)}" y="{num(y)}" width="{num(w * .55)}" height="2" rx="1" fill="url(#l{tid})" '
        f'style="animation-delay:{delay + .3:.2f}s"/>'
        + icon(item["icon"], x + pad, y + 17, 13, theme, color=color, stroke_width=2)
        + text(x + pad + 20, y + 28, item["context"].upper(), "m", fill=theme.muted,
               size=fit("m", item["context"].upper(), 9.5, w - pad * 2 - 20, 1.1), letter_spacing="1.1")
        + "".join(num_parts)
        + text(x + pad, y + TILE_H - 18, item["label"], "s", fill=theme.muted,
               size=fit("s", item["label"], 13, w - pad * 2))
        + "</g>"
    )
    return defs, body


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    items = profile["impact"]
    rows = (len(items) + COLS - 1) // COLS
    tw = (W - GAP * (COLS - 1)) / COLS
    H = rows * TILE_H + (rows - 1) * GAP
    defs, body = [], []
    for i, item in enumerate(items):
        r, c = divmod(i, COLS)
        d, b = tile(item, c * (tw + GAP), r * (TILE_H + GAP), tw, theme, i)
        defs.append(d)
        body.append(b)
    desc = "; ".join(f"{i['value']} {i['label']} ({i['context']})" for i in items)
    return document("".join(body), W, H, title="Impact, by the numbers", desc=desc, css=CSS, defs="".join(defs))
