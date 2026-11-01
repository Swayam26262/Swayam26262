"""Hero sheet: the name set huge in Instrument Serif rising out of its slot,
an identicon pixel matrix on a flat orange block, a spec table, a typing line
and a ticker band running along the bottom.

Desktop puts the name and the spec table side by side; phones stack them."""

from __future__ import annotations

import math

from core import fonts
from core.design import CSS as BASE, box, canvas, card, hline, patterns, secondary, snap, strip, vline
from core.motion import BLINK_CSS, TypedLine, typing_cycle
from core.svg import document, fit, num, text
from core.theme import Theme

IDENTICON = ["11011", "11111", "00100", "01110", "11111"]
SPEC_ROW = 40
TICKER_H = 40

CSS = BASE + BLINK_CSS + """
.tick{animation:tick linear infinite}
@keyframes tick{to{transform:translateX(var(--shift))}}
"""


def name_block(person: dict, theme: Theme, x: float, top: float, width: float, max_size: float):
    """Two lines, first name roman, last name in orange italic, each glyph rising out of a slot."""
    first, last = person["name"].split(" ", 1)
    roman, italic = fonts.font("sr"), fonts.font("si")
    size = min(max_size, width / roman.width(first, 1), width / italic.width(last + ".", 1))
    base1 = top + .7 * size
    base2 = base1 + .84 * size
    defs, body = [], []
    k = 0
    for line, (word, face, color, base) in enumerate(((first, roman, theme.ink, base1),
                                                     (last + ".", italic, theme.accent, base2))):
        defs.append(f'<clipPath id="n{line}"><rect x="0" y="{num(base - size * .92)}" width="{num(x + width + 8)}" '
                    f'height="{num(size * 1.2)}"/></clipPath>')
        cx = x
        glyphs = []
        for ch in word:
            d = face.path(ch, cx, base, size)
            glyphs.append(f'<g class="rise" style="animation-delay:{.15 + k * .05:.2f}s"><path d="{d}" fill="{color}"/></g>')
            cx += face.width(ch, size)
            k += 1
        body.append(f'<g clip-path="url(#n{line})">{"".join(glyphs)}</g>')
    return "".join(defs), "".join(body), base2 + .3 * size


def emblem(theme: Theme, x: float, y: float, w: float, cell_w: float) -> tuple[str, float]:
    """Identicon from the GitHub avatar as a 5x5 matrix of flat bars on the orange block."""
    cell_h, gap, pad = (16 if cell_w > 56 else 24), 8, 16
    height = pad * 2 + 5 * cell_h + 4 * gap
    x0 = x + (w - (5 * cell_w + 4 * gap)) / 2
    out = [f'<rect x="{num(x + 1)}" y="{num(y)}" width="{num(w - 2)}" height="{num(height)}" fill="{theme.accent}"/>']
    order = 0
    for r, row in enumerate(IDENTICON):
        for c, on in enumerate(row):
            cx, cy = x0 + c * (cell_w + gap), y + pad + r * (cell_h + gap)
            if on == "1":
                out.append(f'<rect class="on" x="{num(cx)}" y="{num(cy)}" width="{cell_w}" height="{cell_h}" '
                           f'fill="{theme.on_accent}" style="animation-delay:{.3 + order * .045:.2f}s"/>')
            else:
                out.append(box(cx, cy, cell_w, cell_h, theme.on_accent))
            order += 1
    return "".join(out), height


def spec_table(rows: list[list[str]], theme: Theme, x: float, y: float, w: float) -> str:
    out = []
    value_x = x + 96
    for i, (label, value) in enumerate(rows):
        label, extra = secondary(label)
        live = label.lower() == "status"
        color = theme.teal if extra else theme.ink
        label_color = theme.teal if extra else theme.muted
        vx = value_x + (16 if live else 0)
        row = (text(x + 16, y + 25, label.upper(), "m", fill=label_color, size=10, letter_spacing="1.6")
               + text(vx, y + 25, value, "tm", fill=color, size=fit("tm", value, 14, x + w - 16 - vx)))
        if live:
            row += f'<rect class="blip" x="{value_x}" y="{y + 15}" width="8" height="8" fill="{theme.accent}"/>'
        out.append(f'<g class="slide" style="animation-delay:{.55 + i * .08:.2f}s">{row}</g>')
        if i:
            out.append(hline(x, x + w, y - 1, theme.ink))
        y += SPEC_ROW
    return "".join(out)


def ticker(items: list[str], theme: Theme, y: float, width: float) -> tuple[str, str]:
    size, ls = 11, 1.6
    face = fonts.font("m")
    unit = "".join(f"{secondary(item)[0].upper()}  ■  " for item in items)
    run_w = sum(face.advance(c) for c in unit) * size / face.upm + ls * len(unit)
    copies = math.ceil((width + run_w) / run_w) + 1
    spans = []
    for item in items:
        label, extra = secondary(item)
        fill = f' fill="{theme.teal_inv}"' if extra else ""
        spans.append(f'<tspan{fill}>{label.upper()}</tspan>  <tspan fill="{theme.accent}">■</tspan>  ')
    runs = "".join(f'<text x="{num(k * run_w)}" y="{y + 25}" class="m" font-size="{size}" letter-spacing="{ls}" '
                   f'fill="{theme.paper}" xml:space="preserve">{"".join(spans)}</text>' for k in range(copies))
    defs = f'<clipPath id="tk"><rect x="1" y="{y}" width="{num(width - 2)}" height="{TICKER_H - 1}"/></clipPath>'
    body = (hline(0, width, y - 1, theme.ink)
            + f'<rect x="1" y="{y}" width="{num(width - 2)}" height="{TICKER_H - 1}" fill="{theme.ink}"/>'
            + f'<g clip-path="url(#tk)"><g class="tick" style="--shift:-{num(run_w)}px;'
              f'animation-duration:{run_w / 38:.1f}s">{runs}</g></g>')
    return defs, body


def typing(person: dict, theme: Theme, x: float, y: float, size: float) -> tuple[str, str]:
    cw = fonts.width("m", "M", size)
    lines = [TypedLine(t, x + 24, cw) for t in person["taglines"]]
    defs, body = typing_cycle(lines, y=y, size=size, cls="m", fill=theme.ink, cursor_fill=theme.accent,
                              uid="ty", lead=1.6)
    return defs, text(x, y, "→", "m", fill=theme.accent_text, size=size) + body


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    person = profile["person"]
    W = canvas(mobile)
    sheet_w = W - 8
    defs, body = [patterns(theme)], []
    right = person["location"] if mobile else person["coords"]
    head = strip(0, 0, sheet_w, "§00", "Profile sheet" if mobile else f"Profile sheet — {person['name']}", right, theme)
    kicker = ('<g class="on" style="animation-delay:.1s">'
              + text(24 if mobile else 32, 80, person["role"].upper(), "mb", fill=theme.accent_text, size=11,
                     letter_spacing="2") + "</g>")

    if mobile:
        name_defs, name, name_end = name_block(person, theme, 24, 104, sheet_w - 48, 120)
        type_y = snap(name_end + 16)
        tdefs, typed = typing(person, theme, 24, type_y, 11)
        emblem_top = snap(type_y + 24)
        mark, mark_h = emblem(theme, 0, emblem_top, sheet_w, 64)
        spec_top = emblem_top + mark_h
        ticker_y = spec_top + SPEC_ROW * len(person["spec"])
        H = ticker_y + TICKER_H + 8
        parts = [head, kicker, name, typed, hline(0, sheet_w, emblem_top - 1, theme.ink), mark,
                 hline(0, sheet_w, spec_top - 1, theme.ink), spec_table(person["spec"], theme, 0, spec_top, sheet_w)]
    else:
        split = 544
        name_defs, name, _ = name_block(person, theme, 32, 112, split - 64, 152)
        ticker_y = 424
        H = ticker_y + TICKER_H + 8
        tdefs, typed = typing(person, theme, 32, 392, 13)
        mark, mark_h = emblem(theme, split, 40, sheet_w - split, 48)
        parts = [head, vline(split, 40, ticker_y, theme.ink), kicker, name, typed, mark,
                 hline(split, sheet_w, 40 + mark_h - 1, theme.ink),
                 spec_table(person["spec"], theme, split, 40 + mark_h, sheet_w - split)]
    tick_defs, tick = ticker(person["ticker"], theme, ticker_y, sheet_w)
    defs += [name_defs, tdefs, tick_defs]
    body = [card(W, H, theme)] + parts + [tick]
    return document("".join(body), W, H, title=f"{person['name']} — {person['role']}",
                    desc=" · ".join(person["taglines"]), css=CSS, defs="".join(defs))
