"""Hero sheet: the name set huge in Instrument Serif rising out of its slot,
an identicon pixel matrix on a flat orange block, a spec table, a typing line
and a ticker band running along the bottom."""

from __future__ import annotations

import math

from core import fonts
from core.design import CSS as BASE, W, box, card, hline, patterns, strip, vline
from core.motion import BLINK_CSS, TypedLine, typing_cycle
from core.svg import document, num, text
from core.theme import Theme

H = 472                  # canvas (sheet is 464 + 8px block shadow)
SHEET_W, SHEET_H = W - 8, H - 8
SPLIT = 544              # left column width
TICKER_Y, TICKER_H = 424, 40
IDENTICON = ["11011", "11111", "00100", "01110", "11111"]

CSS = BASE + BLINK_CSS + """
.tick{animation:tick linear infinite}
@keyframes tick{to{transform:translateX(var(--shift))}}
"""


def _name(person: dict, theme: Theme) -> tuple[str, str]:
    first, last = person["name"].split(" ", 1)
    roman, italic = fonts.font("sr"), fonts.font("si")
    max_w = SPLIT - 64
    size = min(152, max_w / (roman.width(first, 1)), max_w / (italic.width(last + ".", 1)))
    cap = .7 * size
    base1 = 112 + cap
    base2 = base1 + .84 * size
    defs, body = [], []
    k = 0
    for line, (word, face, color, base) in enumerate(((first, roman, theme.ink, base1),
                                                     (last + ".", italic, theme.accent, base2))):
        top = base - size * .92
        defs.append(f'<clipPath id="n{line}"><rect x="0" y="{num(top)}" width="{SPLIT}" '
                    f'height="{num(size * 1.2)}"/></clipPath>')
        x = 32.0
        glyphs = []
        for ch in word:
            d = face.path(ch, x, base, size)
            glyphs.append(f'<g class="rise" style="animation-delay:{.15 + k * .05:.2f}s"><path d="{d}" fill="{color}"/></g>')
            x += face.width(ch, size)
            k += 1
        body.append(f'<g clip-path="url(#n{line})">{"".join(glyphs)}</g>')
    return "".join(defs), "".join(body)


def _emblem(theme: Theme) -> str:
    """Identicon from the GitHub avatar as a 5x5 matrix of flat bars on the orange block."""
    x0, y0, cw, ch, gap = SPLIT + 8, 40 + 16, 48, 24, 8
    out = [f'<rect x="{SPLIT + 1}" y="40" width="{SHEET_W - SPLIT - 2}" height="184" fill="{theme.accent}"/>']
    order = 0
    for r, row in enumerate(IDENTICON):
        for c, on in enumerate(row):
            x, y = x0 + c * (cw + gap), y0 + r * (ch + gap)
            if on == "1":
                out.append(f'<rect class="on" x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{theme.on_accent}" '
                           f'style="animation-delay:{.3 + order * .045:.2f}s"/>')
            else:
                out.append(box(x, y, cw, ch, theme.on_accent))
            order += 1
    return "".join(out)


def _spec(rows: list[list[str]], theme: Theme) -> str:
    out = []
    y = 224
    for i, (label, value) in enumerate(rows):
        live = label.lower() == "status"
        row = (text(SPLIT + 16, y + 25, label.upper(), "m", fill=theme.muted, size=10, letter_spacing="1.6")
               + text(SPLIT + 96 + (16 if live else 0), y + 25, value, "tm", fill=theme.ink, size=14))
        if live:
            row += f'<rect class="blip" x="{SPLIT + 96}" y="{y + 15}" width="8" height="8" fill="{theme.accent}"/>'
        out.append(f'<g class="slide" style="animation-delay:{.55 + i * .08:.2f}s">{row}</g>')
        if i:
            out.append(hline(SPLIT, SHEET_W, y - 1, theme.ink))
        y += 40
    return "".join(out)


def _ticker(items: list[str], theme: Theme) -> tuple[str, str]:
    size, ls = 11, 1.6
    unit = "".join(f"{item.upper()}  ■  " for item in items)
    face = fonts.font("m")
    width = sum(face.advance(c) for c in unit) * size / face.upm + ls * len(unit)
    copies = math.ceil((SHEET_W + width) / width) + 1
    base = TICKER_Y + 25
    runs = []
    for k in range(copies):
        spans = []
        for item in items:
            spans.append(f'{item.upper()}  <tspan fill="{theme.accent}">■</tspan>  ')
        runs.append(f'<text x="{num(k * width)}" y="{base}" class="m" font-size="{size}" letter-spacing="{ls}" '
                    f'fill="{theme.paper}" xml:space="preserve">{"".join(spans)}</text>')
    defs = f'<clipPath id="tk"><rect x="1" y="{TICKER_Y}" width="{SHEET_W - 2}" height="{TICKER_H - 1}"/></clipPath>'
    body = (f'<rect x="1" y="{TICKER_Y}" width="{SHEET_W - 2}" height="{TICKER_H - 1}" fill="{theme.ink}"/>'
            f'<g clip-path="url(#tk)"><g class="tick" style="--shift:-{num(width)}px;animation-duration:{width / 38:.1f}s">'
            f'{"".join(runs)}</g></g>')
    return defs, body


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    person = profile["person"]
    defs = [patterns(theme)]
    body = [card(W, H, theme)]
    body.append(strip(0, 0, SHEET_W, "§00", f"Profile sheet — {person['name']}",
                      f"{person['coords']}", theme))
    body.append(vline(SPLIT, 40, TICKER_Y, theme.ink))

    # left column: kicker, name, typing line
    body.append('<g class="on" style="animation-delay:.1s">'
                + text(32, 80, person["role"].upper(), "mb", fill=theme.accent, size=11, letter_spacing="2")
                + "</g>")
    name_defs, name = _name(person, theme)
    defs.append(name_defs)
    body.append(name)
    body.append(text(32, 392, "→", "m", fill=theme.accent, size=13))
    cw = fonts.width("m", "M", 13)
    lines = [TypedLine(t, 56, cw) for t in person["taglines"]]
    tdefs, typed = typing_cycle(lines, y=392, size=13, cls="m", fill=theme.ink, cursor_fill=theme.accent,
                                uid="ty", lead=1.6)
    defs.append(tdefs)
    body.append(typed)

    # right column: emblem + spec table
    body.append(_emblem(theme))
    body.append(hline(SPLIT, SHEET_W, 223, theme.ink))
    body.append(_spec(person["spec"], theme))

    tick_defs, tick = _ticker(person["ticker"], theme)
    defs.append(tick_defs)
    body.append(hline(0, SHEET_W, TICKER_Y - 1, theme.ink))
    body.append(tick)

    return document("".join(body), W, H, title=f"{person['name']} — {person['role']}",
                    desc=" · ".join(person["taglines"]), css=CSS, defs="".join(defs))
