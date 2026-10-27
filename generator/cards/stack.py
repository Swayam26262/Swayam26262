"""Tech stack: one row per category, chips with brand marks that pop in and
catch a passing glint every few seconds."""

from __future__ import annotations

from core import fonts
from core.icons import icon, title
from core.svg import document, num, text
from core.theme import Theme

W, PAD = 840, 22
LABEL_W = 132
CHIP_H, CHIP_GAP, ICON = 30, 8, 15
FS = 12.5

CSS = """
.chip{animation:chip .55s cubic-bezier(.2,.9,.3,1.25) both}
@keyframes chip{from{opacity:0;transform:translateY(9px)}}
.lbl{animation:lbl .6s ease-out both}
@keyframes lbl{from{opacity:0;transform:translateX(-8px)}}
.glint{animation:glint 9s cubic-bezier(.5,0,.5,1) 2.5s infinite}
@keyframes glint{0%{transform:translateX(0)}28%,100%{transform:translateX(1100px)}}
"""


def parse(item: str) -> tuple[str, str]:
    if "=" in item:
        label, slug = item.split("=", 1)
        return label, slug
    return title(item), item


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    rows = profile["stack"]
    x_min, x_max = PAD + LABEL_W, W - PAD
    accents = [theme.cyan, theme.blue, theme.indigo, theme.violet, theme.pink, theme.amber, theme.green]
    chip_fill = theme.panel2 if theme.dark else "#ffffff"

    body, clips = [], []
    y = PAD
    order = 0
    for r, row in enumerate(rows):
        # flow the chips, wrapping inside the row
        placed, cx, cy = [], x_min, y + 12
        for item in row["items"]:
            label, slug = parse(item)
            w = 10 + ICON + 7 + fonts.width("sm", label, FS) + 12
            if cx + w > x_max and cx > x_min:
                cx, cy = x_min, cy + CHIP_H + CHIP_GAP
            placed.append((label, slug, cx, cy, w))
            cx += w + CHIP_GAP
        row_h = (cy + CHIP_H + 12) - y
        accent = accents[r % len(accents)]
        mid = y + row_h / 2
        body.append(
            f'<g class="lbl" style="animation-delay:{r * .12:.2f}s">'
            + text(PAD + 4, mid + 4, f"{r + 1:02d}", "mb", fill=accent, size=10.5, letter_spacing="1")
            + text(PAD + 28, mid + 4, row["label"].upper(), "m", fill=theme.muted, size=10, letter_spacing="1.5")
            + "</g>"
        )
        for label, slug, x0, y0, w in placed:
            delay = .15 + r * .12 + order * .025
            order += 1
            body.append(
                f'<g class="chip" style="animation-delay:{delay:.2f}s">'
                f'<rect x="{num(x0 + .5)}" y="{num(y0 + .5)}" width="{num(w - 1)}" height="{CHIP_H - 1}" rx="9" '
                f'fill="{chip_fill}" stroke="{theme.border}"/>'
                + icon(slug, x0 + 10, y0 + (CHIP_H - ICON) / 2, ICON, theme, bg=chip_fill,
                       color=None if not slug.startswith("glyph:") else accent, stroke_width=2)
                + text(x0 + 10 + ICON + 7, y0 + CHIP_H / 2 + 4.3, label, "sm", fill=theme.text, size=FS)
                + "</g>"
            )
            clips.append(f'<rect x="{num(x0)}" y="{num(y0)}" width="{num(w)}" height="{CHIP_H}" rx="9"/>')
        if r < len(rows) - 1:
            body.append(f'<path d="M{PAD} {num(y + row_h)}H{W - PAD}" stroke="{theme.border}" stroke-dasharray="3 5"/>')
        y += row_h
    H = y + PAD

    defs = (
        f'<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{.16 if theme.dark else .7}"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="chips">{"".join(clips)}</clipPath>'
    )
    panel = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{theme.panel}" '
             f'stroke="{theme.border}"/>')
    glint = (f'<g clip-path="url(#chips)"><g transform="skewX(-20)"><rect class="glint" x="-160" y="0" width="120" '
             f'height="{H}" fill="url(#gl)"/></g></g>')
    desc = "; ".join(f"{row['label']}: {', '.join(parse(i)[0] for i in row['items'])}" for row in rows)
    return document(panel + "".join(body) + glint, W, H, title="Tech stack", desc=desc, css=CSS, defs=defs)
