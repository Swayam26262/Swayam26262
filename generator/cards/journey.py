"""§03 trajectory: a serif heading on the left and a ledger of roles on the
right, newest first, one row per milestone with hard rules between rows."""

from __future__ import annotations

from core import fonts
from core.design import CSS as BASE, W, card, hline, patterns, stamp_block, strip, vline
from core.svg import document, fit, text
from core.theme import Theme

SPLIT = 280
ROW = 72
TOP = 40


def _heading(profile: dict, theme: Theme) -> tuple[str, float]:
    copy = profile["copy"]
    width = SPLIT - 64
    lines = copy["journey_heading"]
    size = min(fit("sr", line.strip("*"), 40, width) for line in lines)
    out, y = [], TOP + 32 + size * .72
    for line in lines:
        italic = line.startswith("*")
        out.append(text(32, y, line.strip("*"), "si" if italic else "sr",
                        fill=theme.accent if italic else theme.ink, size=size))
        y += size * .95
    words, para, cur = copy["journey_text"].split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if cur and fonts.width("t", trial, 14) > width:
            para.append(cur)
            cur = word
        else:
            cur = trial
    para.append(cur)
    y += 16
    for line in para:
        y += 24
        out.append(text(32, y, line, "t", fill=theme.muted, size=14))
    return f'<g class="lift" style="animation-delay:.15s">{"".join(out)}</g>', y


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    items = list(reversed(profile["journey"]))   # newest first
    sheet_w = W - 8
    H = TOP + ROW * len(items) + 8
    body = [card(W, H, theme)]
    body.append(strip(0, 0, sheet_w, "§03", "Trajectory", f"{len(items)} milestones", theme))
    body.append(vline(SPLIT, TOP, H - 8, theme.ink))
    heading, text_end = _heading(profile, theme)
    body.append(heading)
    hatch_top = int(text_end + 40) + (-int(text_end + 40) % 8)
    if H - 8 - hatch_top >= 96:
        first = profile["journey"][0]["when"].upper()
        body.append(stamp_block(0, hatch_top, SPLIT, H - 8 - hatch_top, f"{first} → NOW", theme))

    x0 = SPLIT
    rows = []
    for i, item in enumerate(items):
        y = TOP + i * ROW
        now = item["when"].lower() == "now"
        when = item["when"].upper()
        row = []
        if now:
            row.append(f'<rect x="{x0 + 1}" y="{y + 1}" width="{sheet_w - x0 - 2}" height="{ROW - 2}" fill="{theme.paper2}"/>')
            row.append(f'<rect class="blip" x="{x0 + 24}" y="{y + 24}" width="8" height="8" fill="{theme.accent}"/>')
            row.append(text(x0 + 40, y + 32, when, "mb", fill=theme.accent, size=11, letter_spacing="1.6"))
        else:
            row.append(text(x0 + 24, y + 32, when, "mb", fill=theme.ink, size=11, letter_spacing="1.6"))
        tx = x0 + 128
        row.append(text(tx, y + 32, item["title"], "tb", fill=theme.ink,
                        size=fit("tb", item["title"], 16, 248)))
        row.append(text(sheet_w - 24, y + 32, item["org"].upper(), "m", fill=theme.muted,
                        size=fit("m", item["org"].upper(), 10, 160, 1.2), anchor="end", letter_spacing="1.2"))
        row.append(text(tx, y + 54, item["note"], "t", fill=theme.muted,
                        size=fit("t", item["note"], 14, sheet_w - 24 - tx)))
        rows.append(f'<g class="slide" style="animation-delay:{.3 + i * .1:.2f}s">{"".join(row)}</g>')
        if i:
            rows.append(hline(x0, sheet_w, y - 1, theme.ink))
    body.append("".join(rows))
    # a hard spine through the date column
    body.append(vline(x0 + 104, TOP, H - 8, theme.hair))
    desc = "; ".join(f"{i['when']}: {i['title']}, {i['org']}" for i in profile["journey"])
    return document("".join(body), W, H, title="Trajectory", desc=desc, css=BASE, defs=patterns(theme))
