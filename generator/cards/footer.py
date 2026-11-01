"""§09 sign-off: a flat accent sheet with a serif headline, a contact ledger
and a mono colophon strip. Headline beside the ledger on desktop, above it on
phones. Every channel in the ledger is also a real link right under the sheet
in the README."""

from __future__ import annotations

import datetime as dt

from core import fonts
from core.design import CSS as BASE, canvas, card, hline, snap, strip, vline, wrap
from core.motion import BLINK_CSS
from core.svg import document, fit, text
from core.theme import Theme

TOP = 40
ROW = 48


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    foot = profile["footer"]
    today = today or dt.datetime.now(dt.timezone.utc).date()
    ink = theme.on_accent
    W = canvas(mobile)
    sheet_w = W - 8
    rows = foot["contact"]
    # the running header sits on the accent sheet, so draw it entirely in the on-accent ink
    strip_theme = Theme(**{**theme.__dict__, "accent_text": ink, "ink": ink, "muted": ink})
    head = strip(0, 0, sheet_w, "§09", "Contact", profile["person"]["location"], strip_theme, index_color=ink)

    lines = foot["headline"]
    if mobile:
        width, x, max_size = sheet_w - 48, 24, 48
    else:
        split = 520
        width, x, max_size = split - 64, 32, 64
    size = min(fit("sr", line.strip("*"), max_size, width) for line in lines)
    y = TOP + 32 + size * .72
    headline = []
    for i, line in enumerate(lines):
        if i:
            y += size * .95
        italic = line.startswith("*")
        headline.append(text(x, y, line.strip("*"), "si" if italic else "sr", fill=ink, size=size))
    last = lines[-1]
    cursor_x = x + 4 + fonts.width("si" if last.startswith("*") else "sr", last.strip("*"), size)
    cursor = (f'<rect class="blink" x="{cursor_x:.1f}" y="{y - size * .62:.1f}" width="{size * .08:.1f}" '
              f'height="{size * .66:.1f}" fill="{ink}"/>')

    if mobile:
        ledger_x, ledger_w, ledger_y = 0, sheet_w, snap(y + size * .3 + 32)
        body_bottom = ledger_y + len(rows) * ROW
    else:
        ledger_x, ledger_w, ledger_y = split, sheet_w - split, TOP
        body_bottom = TOP + max(len(rows) * ROW, snap(y + size * .3 + 32) - TOP)
    ledger = []
    if mobile:
        ledger.append(hline(0, sheet_w, ledger_y - 1, ink))
    else:
        ledger.append(vline(split, TOP, body_bottom, ink))
    for i, (label, value) in enumerate(rows):
        ry = ledger_y + i * ROW
        vx = ledger_x + (104 if mobile else 112)
        ledger.append(f'<g class="slide" style="animation-delay:{.3 + i * .08:.2f}s">'
                      + text(ledger_x + 24, ry + 29, label.upper(), "m", fill=ink, size=10, letter_spacing="1.6")
                      + text(vx, ry + 29, value, "tm", fill=ink, size=fit("tm", value, 14, ledger_x + ledger_w - 24 - vx))
                      + "</g>")
        if i < len(rows) - 1 or mobile:
            ledger.append(hline(ledger_x, ledger_x + ledger_w, ry + ROW - 1, ink))

    # colophon: one line on desktop, wrapped on phones
    colophon = foot["colophon"].upper()
    rev = f"REV. {today:%Y.%m}"
    if mobile:
        col_lines = wrap(colophon, "m", 9, sheet_w - 112)  # leaves room for the letter-spacing
        col_h = 16 + 16 * len(col_lines) + 24 + 16
    else:
        col_lines = [colophon]
        col_h = 40
    H = body_bottom + col_h + 8
    out = [card(W, H, theme, fill=theme.accent, shadow=theme.ink), head,
           f'<g class="lift" style="animation-delay:.15s">{"".join(headline)}</g>', cursor, "".join(ledger)]
    out.append(hline(0, sheet_w, body_bottom, ink))
    if mobile:
        for i, line in enumerate(col_lines):
            out.append(text(24, body_bottom + 28 + i * 16, line, "m", fill=ink, size=9, letter_spacing="1.2"))
        out.append(text(24, body_bottom + 28 + len(col_lines) * 16 + 8, rev, "mb", fill=ink, size=10, letter_spacing="1.2"))
    else:
        out.append(text(24, body_bottom + 25, colophon, "m", fill=ink, size=fit("m", colophon, 9.5, sheet_w - 160, 1.2),
                        letter_spacing="1.2"))
        out.append(text(sheet_w - 24, body_bottom + 25, rev, "mb", fill=ink, size=10, anchor="end", letter_spacing="1.2"))
    return document("".join(out), W, H, title=" ".join(line.strip("*") for line in lines),
                    desc="; ".join(f"{k}: {v}" for k, v in rows), css=BASE + BLINK_CSS)
