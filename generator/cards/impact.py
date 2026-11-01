"""§02 impact as a bento grid: one feature cell, an accent cell, a hatched
statement cell and small cells, sharing hard 1px rules. Serif numerals roll
into place like an odometer."""

from __future__ import annotations

import re

from core import fonts
from core.design import CSS as BASE, W, card, hline, patterns, strip, vline
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import balance, document, fit, num, text
from core.theme import Theme

COL, ROW = 104, 112          # 8 columns x 3 rows on the 8pt grid
TOP = 40
# (impact index, col, row, col span, row span, numeral size, style)
LAYOUT = [
    (0, 0, 0, 4, 2, 120, "feature"),
    (1, 4, 0, 2, 1, 56, "plain"),
    (2, 6, 0, 2, 1, 56, "plain"),
    (3, 4, 1, 4, 1, 64, "accent"),
    (4, 0, 2, 2, 1, 56, "plain"),
    (5, 2, 2, 2, 1, 56, "plain"),
]
NOTE = (4, 2, 4, 1)          # the hatched statement cell

CSS = BASE + ODO_CSS


def split_value(value: str) -> tuple[str, str, str]:
    m = re.match(r"^(\D*)([\d,.]+)(.*)$", value)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", "", value)


def cell(item: dict, idx: int, x: float, y: float, w: float, h: float, size: float, style: str,
         theme: Theme, delay: float) -> tuple[str, str]:
    ink = theme.on_accent if style == "accent" else theme.ink
    sub = theme.on_accent if style == "accent" else theme.muted
    out = []
    if style == "accent":
        out.append(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 1}" height="{h - 1}" fill="{theme.accent}"/>')
    pad = 24 if style == "feature" else 16
    context = item["context"].upper()
    out.append(text(x + pad, y + pad + 9, f"{idx + 1:02d}", "mb", fill=ink if style == "accent" else theme.accent,
                    size=10))
    out.append(text(x + pad + 24, y + pad + 9, context, "m", fill=sub,
                    size=fit("m", context, 10, w - 2 * pad - 24, 1.2), letter_spacing="1.2"))
    prefix, digits, suffix = split_value(item["value"])
    label_y = y + h - pad
    lines = balance("tm", item["label"], 16, w - 2 * pad) if style == "feature" else [item["label"]]
    base = label_y - (24 * len(lines) + 16 if style == "feature" else 24)
    small = size * .5
    cx = x + pad
    num_parts = []
    if prefix:
        num_parts.append(text(cx, base, prefix, "si", fill=ink, size=size))
        cx += fonts.width("si", prefix, size) + 2
    rolled, rw = odometer(digits, cx, base, size, ink, delay, cls="sr")
    clip_id = f"o{idx}"
    defs = (f'<clipPath id="{clip_id}"><rect x="{num(x)}" y="{num(base - size * .95)}" width="{num(w)}" '
            f'height="{num(size * 1.2)}"/></clipPath>')
    num_parts.append(f'<g clip-path="url(#{clip_id})">{rolled}</g>')
    cx += rw + 4
    if suffix:
        num_parts.append(f'<g class="on" style="animation-delay:{delay + 1.2:.2f}s">'
                         + text(cx, base, suffix, "si", fill=ink if style == "accent" else theme.accent, size=small)
                         + "</g>")
    out.append("".join(num_parts))
    if style == "feature":
        for i, line in enumerate(lines[::-1]):
            out.append(text(x + pad, label_y - i * 24, line, "tm", fill=ink, size=16))
    else:
        out.append(text(x + pad, label_y, item["label"], "t", fill=ink,
                        size=fit("t", item["label"], 14, w - 2 * pad)))
    return defs, f'<g class="lift" style="animation-delay:{delay - .1:.2f}s">{"".join(out)}</g>'


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    items = profile["impact"]
    sheet_w = W - 8
    H = TOP + 3 * ROW + 8
    defs, body = [patterns(theme)], [card(W, H, theme)]
    body.append(strip(0, 0, sheet_w, "§02", "Impact", "Measured in production", theme))

    # hatched statement cell (drawn first so the grid rules sit on top)
    c, r, cs, rs = NOTE
    nx, ny, nw, nh = c * COL, TOP + r * ROW, cs * COL, rs * ROW
    body.append(f'<rect x="{nx + 1}" y="{ny + 1}" width="{nw - 2}" height="{nh - 2}" fill="url(#hatch)" '
                f'opacity="{.45 if theme.dark else .3}"/>')
    note = profile["copy"]["impact_note"]
    label_w = fonts.width("si", note, 28) + 32
    body.append(f'<g class="lift" style="animation-delay:1s"><rect x="{nx + 16.5}" y="{ny + 24.5}" '
                f'width="{num(label_w)}" height="48" fill="{theme.paper}" stroke="{theme.ink}"/>'
                + text(nx + 32, ny + 56, note, "si", fill=theme.ink, size=28)
                + text(nx + 16, ny + nh - 16, "SOURCES: GOPARKEASY · AI RECEPTIONIST · FIXMYRESUME · INFOSYS", "m",
                       fill=theme.muted, size=fit("m", "SOURCES: GOPARKEASY · AI RECEPTIONIST · FIXMYRESUME · INFOSYS",
                                                  9, nw - 32, 1.2), letter_spacing="1.2")
                + "</g>")

    for n, (i, col, row, cspan, rspan, size, style) in enumerate(LAYOUT):
        x, y = col * COL, TOP + row * ROW
        d, b = cell(items[i], i, x, y, cspan * COL, rspan * ROW, size, style, theme, .25 + n * .12)
        defs.append(d)
        body.append(b)

    # the grid: hard rules between cells
    rules = [hline(0, sheet_w, TOP + ROW * 2 - 1, theme.ink), hline(4 * COL, sheet_w, TOP + ROW - 1, theme.ink),
             vline(4 * COL - 1, TOP, TOP + 3 * ROW, theme.ink), vline(6 * COL - 1, TOP, TOP + ROW, theme.ink),
             vline(2 * COL - 1, TOP + 2 * ROW, TOP + 3 * ROW, theme.ink)]
    body.append(f'<g class="rule">{"".join(rules)}</g>')
    desc = "; ".join(f"{i['value']} {i['label']} ({i['context']})" for i in items)
    return document("".join(body), W, H, title="Impact, by the numbers", desc=desc, css=CSS, defs="".join(defs))
