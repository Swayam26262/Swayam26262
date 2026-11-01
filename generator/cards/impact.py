"""§02 impact as a bento grid: one feature cell, an accent cell, a hatched
statement cell and small cells, sharing hard 1px rules. Serif numerals roll
into place like an odometer. Stats marked kind = "ai" are drawn in teal."""

from __future__ import annotations

import re

from core import fonts
from core.design import CSS as BASE, box, canvas, card, patterns, strip, wrap
from core.odometer import CSS as ODO_CSS, odometer
from core.svg import balance, document, fit, num, text
from core.theme import Theme

TOP = 40
# (impact index, x, y, w, h, numeral size, style); y is below the running header
DESKTOP = [(0, 0, 0, 416, 224, 120, "feature"), (1, 416, 0, 208, 112, 56, "plain"), (2, 624, 0, 208, 112, 56, "plain"),
           (3, 416, 112, 416, 112, 56, "accent"), (4, 0, 224, 208, 112, 56, "plain"), (5, 208, 224, 208, 112, 56, "plain")]
DESKTOP_NOTE = (416, 224, 416, 112)
MOBILE = [(0, 0, 0, 400, 208, 80, "feature"), (1, 0, 208, 200, 112, 48, "plain"), (2, 200, 208, 200, 112, 48, "plain"),
          (3, 0, 320, 400, 112, 48, "accent"), (4, 0, 432, 200, 112, 48, "plain"), (5, 200, 432, 200, 112, 48, "plain")]
MOBILE_NOTE = (0, 544, 400, 104)

CSS = BASE + ODO_CSS


def split_value(value: str) -> tuple[str, str, str]:
    m = re.match(r"^(\D*)([\d,.]+)(.*)$", value)
    return (m.group(1), m.group(2), m.group(3)) if m else ("", "", value)


def cell(item: dict, idx: int, x: float, y: float, w: float, h: float, size: float, style: str,
         theme: Theme, delay: float) -> tuple[str, str]:
    ai = item.get("kind") == "ai"
    accent_cell = style == "accent"
    ink = theme.on_accent if accent_cell else theme.ink
    sub = theme.on_accent if accent_cell else theme.muted
    mark = theme.on_accent if accent_cell else (theme.teal if ai else theme.accent_text)
    tint = theme.on_accent if accent_cell else (theme.teal if ai else theme.accent)
    out = []
    if accent_cell:
        out.append(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 1}" height="{h - 1}" fill="{theme.accent}"/>')
    pad = 24 if style == "feature" else 16
    context = item["context"].upper()
    out.append(text(x + pad, y + pad + 9, f"{idx + 1:02d}", "mb", fill=mark, size=10))
    out.append(text(x + pad + 24, y + pad + 9, context, "m", fill=theme.teal if ai and not accent_cell else sub,
                    size=fit("m", context, 10, w - 2 * pad - 24, 1.2), letter_spacing="1.2"))
    prefix, digits, suffix = split_value(item["value"])
    label_y = y + h - pad
    lines = [item["label"]]
    if style == "feature":  # two balanced lines when they fit, otherwise up to three
        lines = balance("tm", item["label"], 16, w - 2 * pad)
        if any(fonts.width("tm", line, 16) > w - 2 * pad for line in lines):
            lines = wrap(item["label"], "tm", 16, w - 2 * pad, 3)
    base = label_y - (24 * len(lines) + 16 if style == "feature" else 24)
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
                         + text(cx, base, suffix, "si", fill=tint, size=size * .5) + "</g>")
    out.append("".join(num_parts))
    if style == "feature":
        for i, line in enumerate(lines[::-1]):
            out.append(text(x + pad, label_y - i * 24, line, "tm", fill=ink, size=16))
    else:
        out.append(text(x + pad, label_y, item["label"], "t", fill=ink, size=fit("t", item["label"], 14, w - 2 * pad)))
    return defs, f'<g class="lift" style="animation-delay:{delay - .1:.2f}s">{"".join(out)}</g>'


def note(copy: dict, rect: tuple, theme: Theme) -> str:
    x, y, w, h = rect
    y += TOP
    statement = copy["impact_note"]
    size = fit("si", statement, 28, w - 64)
    label_w = fonts.width("si", statement, size) + 32
    sources = copy["impact_sources"].upper()
    return (f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" fill="url(#hatch)" '
            f'opacity="{.45 if theme.dark else .3}"/>'
            f'<g class="lift" style="animation-delay:1s"><rect x="{x + 16.5}" y="{y + 16.5}" '
            f'width="{num(label_w)}" height="48" fill="{theme.paper}" stroke="{theme.ink}"/>'
            + text(x + 32, y + 48, statement, "si", fill=theme.ink, size=size)
            + text(x + 16, y + h - 16, sources, "m", fill=theme.ink, size=fit("m", sources, 9.5, w - 32, 1.2),
                   letter_spacing="1.2") + "</g>")


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    items = profile["impact"]
    W = canvas(mobile)
    sheet_w = W - 8
    layout, note_rect = (MOBILE, MOBILE_NOTE) if mobile else (DESKTOP, DESKTOP_NOTE)
    grid_h = max(y + h for _, _, y, _, h, _, _ in layout + [(0, *note_rect, 0, "")])
    H = TOP + grid_h + 8
    defs, body = [patterns(theme)], [card(W, H, theme)]
    body.append(strip(0, 0, sheet_w, "§02", "Impact", "Measured in production", theme))
    body.append(note(profile["copy"], note_rect, theme))
    rules = []
    for n, (i, x, y, w, h, size, style) in enumerate(layout):
        d, b = cell(items[i], i, x, TOP + y, w, h, size, style, theme, .25 + n * .12)
        defs.append(d)
        body.append(b)
        rules.append(box(x, TOP + y, w, h, theme.ink))
    nx, ny, nw, nh = note_rect
    rules.append(box(nx, TOP + ny, nw, nh, theme.ink))
    body.append(f'<g class="rule">{"".join(rules)}</g>')
    desc = "; ".join(f"{i['value']} {i['label']} ({i['context']})" for i in items)
    return document("".join(body), W, H, title="Impact, by the numbers", desc=desc, css=CSS, defs="".join(defs))
