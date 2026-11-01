"""§04 currently: a small human section. What's being built, learned, practised
and explored this month, as a ledger beside (desktop) or under (phones) a
serif heading. {leetcode} in an item becomes the live solved count."""

from __future__ import annotations

import datetime as dt

from core.design import (CSS as BASE, canvas, card, hline, patterns, secondary, serif_heading, snap, stamp_block, strip,
                         vline, wrap)
from core.svg import document, text
from core.theme import Theme

SPLIT = 280
TOP = 40


def items(profile: dict, live: dict) -> list[tuple[str, str, bool]]:
    solved = live.get("leetcode", {}).get("solved", {}).get("All")
    out = []
    for label, value in profile["currently"]["items"]:
        label, extra = secondary(label)
        value = value.replace("{leetcode}", str(solved)) if solved else value.replace("{leetcode} ", "")
        out.append((label, value, extra))
    return out


def render(profile: dict, theme: Theme, live: dict | None = None, today: dt.date | None = None,
           mobile: bool = False) -> str:
    live = live or {}
    today = today or dt.datetime.now(dt.timezone.utc).date()
    W = canvas(mobile)
    sheet_w = W - 8
    rows = items(profile, live)
    head = strip(0, 0, sheet_w, "§04", "Currently", f"updated {today:%b %Y}", theme)
    if mobile:
        heading, end = serif_heading(profile["currently"]["heading"], 24, TOP + 32, sheet_w - 48, theme)
        x0, w, y = 0, sheet_w, snap(end + 32)
        label_x, text_x, text_w, size = 24, 24, sheet_w - 48, 14
    else:
        heading, end = serif_heading(profile["currently"]["heading"], 32, TOP + 32, SPLIT - 64, theme)
        x0, w, y = SPLIT, sheet_w - SPLIT, TOP
        label_x, text_x, text_w, size = SPLIT + 24, SPLIT + 160, sheet_w - SPLIT - 184, 15
    out = []
    for i, (label, value, extra) in enumerate(rows):
        lines = wrap(value, "t", size, text_w, 2)
        if mobile:
            row_h = 40 + 24 * len(lines) + 8
            first = y + 32
            label_y, text_top = first, first + 24
        else:
            row_h = 24 * len(lines) + 40
            label_y, text_top = y + 32, y + 32
        if i:
            out.append(hline(x0, x0 + w, y - 1, theme.ink))
        parts = [text(label_x, label_y, label.upper(), "mb", fill=theme.teal if extra else theme.accent_text, size=10,
                      letter_spacing="1.6")]
        for k, line in enumerate(lines):
            parts.append(text(text_x, text_top + k * 24, line, "t", fill=theme.teal if extra else theme.ink, size=size))
        out.append(f'<g class="slide" style="animation-delay:{.3 + i * .1:.2f}s">{"".join(parts)}</g>')
        y += snap(row_h)
    H = y + 8
    body = [card(W, H, theme), head, f'<g class="lift" style="animation-delay:.15s">{heading}</g>']
    if mobile:
        body.append(hline(0, sheet_w, snap(end + 32) - 1, theme.ink))
    else:
        body.append(vline(SPLIT, TOP, H - 8, theme.ink))
        hatch_top = snap(end + 40)
        if H - 8 - hatch_top >= 96:
            body.append(stamp_block(0, hatch_top, SPLIT, H - 8 - hatch_top, f"AS OF {today:%b %Y}".upper(), theme))
    body.extend(out)
    desc = "; ".join(f"{label}: {value}" for label, value, _ in rows)
    return document("".join(body), W, H, title="Currently", desc=desc, css=BASE, defs=patterns(theme))
