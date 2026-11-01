"""§03 trajectory: a serif heading and a ledger of roles, newest first, one row
per milestone with hard rules between rows. Heading beside the ledger on
desktop, above it on phones. Rows marked kind = "ai" date in teal."""

from __future__ import annotations

from core.design import (CSS as BASE, canvas, card, hline, paragraph, patterns, serif_heading, snap, stamp_block,
                         strip, vline, wrap)
from core.svg import document, fit, text
from core.theme import Theme

SPLIT = 280
TOP = 40


def row(item: dict, x0: float, y: float, w: float, theme: Theme, mobile: bool) -> str:
    now = item["when"].lower() == "now"
    ai = item.get("kind") == "ai"
    when = item["when"].upper()
    date_color = theme.accent_text if now else (theme.teal if ai else theme.ink)
    out = []
    if now:
        out.append(f'<rect class="blip" x="{x0 + 24}" y="{y + 24}" width="8" height="8" fill="{theme.accent}"/>')
    date_x = x0 + (40 if now else 24)
    org = item["org"].upper()
    if mobile:
        out.append(text(date_x, y + 32, when, "mb", fill=date_color, size=11, letter_spacing="1.6"))
        out.append(text(x0 + w - 24, y + 32, org, "m", fill=theme.muted, size=fit("m", org, 9.5, w - 160, 1.2),
                        anchor="end", letter_spacing="1.2"))
        out.append(text(x0 + 24, y + 58, item["title"], "tb", fill=theme.ink, size=fit("tb", item["title"], 16, w - 48)))
        for i, line in enumerate(wrap(item["note"], "t", 13, w - 48, 2)):
            out.append(text(x0 + 24, y + 80 + i * 20, line, "t", fill=theme.muted, size=13))
    else:
        out.append(text(date_x, y + 32, when, "mb", fill=date_color, size=11, letter_spacing="1.6"))
        tx = x0 + 128
        out.append(text(tx, y + 32, item["title"], "tb", fill=theme.ink, size=fit("tb", item["title"], 16, 248)))
        out.append(text(x0 + w - 24, y + 32, org, "m", fill=theme.muted, size=fit("m", org, 10, 160, 1.2),
                        anchor="end", letter_spacing="1.2"))
        out.append(text(tx, y + 54, item["note"], "t", fill=theme.muted,
                        size=fit("t", item["note"], 14, x0 + w - 24 - tx)))
    return "".join(out)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    items = list(reversed(profile["journey"]))   # newest first
    copy = profile["copy"]
    W = canvas(mobile)
    sheet_w = W - 8
    head = strip(0, 0, sheet_w, "§03", "Trajectory", f"{len(items)} milestones", theme)
    row_h = 112 if mobile else 72

    if mobile:
        heading, end = serif_heading(copy["journey_heading"], 24, TOP + 32, sheet_w - 48, theme)
        para, end = paragraph(copy["journey_text"], 24, end + 8, sheet_w - 48, theme.muted)
        x0, w, y0 = 0, sheet_w, snap(end + 32)
    else:
        heading, end = serif_heading(copy["journey_heading"], 32, TOP + 32, SPLIT - 64, theme)
        para, end = paragraph(copy["journey_text"], 32, end + 16, SPLIT - 64, theme.muted)
        x0, w, y0 = SPLIT, sheet_w - SPLIT, TOP
    H = y0 + row_h * len(items) + 8
    body = [card(W, H, theme), head, f'<g class="lift" style="animation-delay:.15s">{heading}{para}</g>']
    if mobile:
        body.append(hline(0, sheet_w, y0 - 1, theme.ink))
    else:
        body.append(vline(SPLIT, TOP, H - 8, theme.ink))
        hatch_top = snap(end + 40)
        if H - 8 - hatch_top >= 96:
            first = profile["journey"][0]["when"].upper()
            body.append(stamp_block(0, hatch_top, SPLIT, H - 8 - hatch_top, f"{first} → NOW", theme))
        body.append(vline(x0 + 104, TOP, H - 8, theme.hair))
    for i, item in enumerate(items):
        y = y0 + i * row_h
        if item["when"].lower() == "now":
            body.append(f'<rect x="{x0 + 1}" y="{y + 1}" width="{w - 2}" height="{row_h - 2}" fill="{theme.paper2}"/>')
        body.append(f'<g class="slide" style="animation-delay:{.3 + i * .1:.2f}s">{row(item, x0, y, w, theme, mobile)}</g>')
        if i:
            body.append(hline(x0, x0 + w, y - 1, theme.ink))
    desc = "; ".join(f"{i['when']}: {i['title']}, {i['org']}" for i in profile["journey"])
    return document("".join(body), W, H, title="Trajectory", desc=desc, css=BASE, defs=patterns(theme))
