"""§08 sign-off: a flat accent sheet with a serif headline on the left, a
contact ledger on the right and a mono colophon strip along the bottom."""

from __future__ import annotations

import datetime as dt

from core.design import CSS as BASE, W, card, hline, strip, vline
from core.motion import BLINK_CSS
from core.svg import document, fit, text
from core.theme import Theme

SPLIT = 520
TOP = 40
ROW = 48


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    foot = profile["footer"]
    today = today or dt.datetime.now(dt.timezone.utc).date()
    ink = theme.on_accent
    sheet_w = W - 8
    rows = foot["contact"]
    body_h = max(len(rows) * ROW, 192)
    H = TOP + body_h + 40 + 8
    out = [card(W, H, theme, fill=theme.accent, shadow=theme.ink)]
    # the running header sits on the accent sheet, so draw it entirely in the on-accent ink
    strip_theme = Theme(**{**theme.__dict__, "accent": ink, "ink": ink, "muted": ink})
    out.append(strip(0, 0, sheet_w, "§08", "Contact", f"{profile['person']['location']}", strip_theme))

    # headline
    lines = foot["headline"]
    size = min(fit("sr", line.strip("*"), 64, SPLIT - 64) for line in lines)
    y = TOP + 32 + size * .72
    head = []
    for line in lines:
        italic = line.startswith("*")
        head.append(text(32, y, line.strip("*"), "si" if italic else "sr", fill=ink, size=size))
        last_end = y
        y += size * .95
    out.append(f'<g class="lift" style="animation-delay:.15s">{"".join(head)}</g>')
    out.append(f'<rect class="blink" x="{32 + 4 + _width_of(lines[-1], size)}" y="{last_end - size * .62}" '
               f'width="{size * .08:.1f}" height="{size * .66:.1f}" fill="{ink}"/>')

    # contact ledger
    out.append(vline(SPLIT, TOP, TOP + body_h, ink))
    for i, (label, value) in enumerate(rows):
        ry = TOP + i * ROW
        out.append(f'<g class="slide" style="animation-delay:{.3 + i * .08:.2f}s">'
                   + text(SPLIT + 24, ry + 29, label.upper(), "m", fill=ink, size=10, letter_spacing="1.6")
                   + text(SPLIT + 112, ry + 29, value, "tm", fill=ink, size=fit("tm", value, 14, sheet_w - SPLIT - 136))
                   + "</g>")
        out.append(hline(SPLIT, sheet_w, ry + ROW - 1, ink))

    # colophon
    cy = TOP + body_h
    out.append(hline(0, sheet_w, cy, ink))
    colophon = foot["colophon"].upper()
    out.append(text(24, cy + 25, colophon, "m", fill=ink, size=fit("m", colophon, 9.5, sheet_w - 160, 1.2),
                    letter_spacing="1.2"))
    out.append(text(sheet_w - 24, cy + 25, f"REV. {today:%Y.%m}", "mb", fill=ink, size=10, anchor="end",
                    letter_spacing="1.2"))
    return document("".join(out), W, H, title=" ".join(line.strip("*") for line in lines),
                    desc="; ".join(f"{k}: {v}" for k, v in rows), css=BASE + BLINK_CSS)


def _width_of(line: str, size: float) -> float:
    from core import fonts
    return fonts.width("si" if line.startswith("*") else "sr", line.strip("*"), size)
