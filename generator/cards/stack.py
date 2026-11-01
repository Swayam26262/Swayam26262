"""§05 stack as a periodic table: 39 elements on a grid of hard-ruled cells
(13 x 3 on desktop, 5 x 8 on phones). Each group gets its own flat treatment,
applied AI sits last in teal, and a marker walks the table."""

from __future__ import annotations

from core import fonts
from core.design import CSS as BASE, box, canvas, card, hline, patterns, strip, vline
from core.icons import icon
from core.svg import document, fit, text
from core.theme import Theme

TOP = 40
STEP = .15  # seconds the walking marker spends on each cell

CSS = BASE + """
.walk{opacity:0;animation:walk steps(1,end) infinite}
@keyframes walk{0%{opacity:1}3%,100%{opacity:0}}
"""


def treatment(style: str, theme: Theme) -> dict:
    t = {
        "accent": dict(fill=theme.accent, sym=theme.on_accent, txt=theme.on_accent, num=theme.on_accent),
        "paper": dict(fill=theme.paper, sym=theme.ink, txt=theme.ink, num=theme.muted),
        "paper2": dict(fill=theme.paper2, sym=theme.ink, txt=theme.ink, num=theme.muted),
        "ink": dict(fill=theme.ink, sym=theme.paper, txt=theme.paper, num=theme.paper),
        "teal": dict(fill=theme.paper, sym=theme.teal, txt=theme.teal, num=theme.teal),
        "dots": dict(fill="url(#dots)", sym=theme.ink, txt=theme.ink, num=theme.muted),
    }[style]
    t["marker"] = theme.on_accent if style == "accent" else theme.accent
    return t


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    groups = profile["stack"]
    elements = [(g, item) for g in groups for item in g["items"]]
    W = canvas(mobile)
    sheet_w = W - 8
    cols, cell_w, cell_h = (5, 80, 80) if mobile else (13, 64, 80)
    sym_size, name_size, icon_size = (36, 10.5, 14) if mobile else (32, 9.5, 12)
    rows = -(-len(elements) // cols)
    grid_bottom = TOP + rows * cell_h
    cycle = len(elements) * STEP

    # legend flows across lines on narrow sheets
    legend, lx, ly = [], 24, grid_bottom + 16
    for group in groups:
        t = treatment(group["style"], theme)
        label = group["label"].upper()
        item_w = 32 + fonts.width("m", label, 10, 1.4) + 1.4
        if lx + item_w > sheet_w - 24:
            lx, ly = 24, ly + 32
        if group["style"] == "dots":
            legend.append(f'<rect x="{lx}" y="{ly}" width="24" height="16" fill="{theme.paper}"/>')
        legend.append(box(lx, ly, 24, 16, theme.ink, t["fill"]))
        if group["style"] == "teal":
            legend.append(f'<rect x="{lx + 8}" y="{ly + 4}" width="8" height="8" fill="{theme.teal}"/>')
        legend.append(text(lx + 32, ly + 12, label, "m", fill=theme.teal if group["style"] == "teal" else theme.ink,
                           size=10, letter_spacing="1.4"))
        lx += item_w + 24
    H = ly + 16 + 16 + 8

    body = [card(W, H, theme)]
    body.append(strip(0, 0, sheet_w, "§05", "Stack" if mobile else "Stack — a periodic table",
                      f"{len(elements)} elements", theme))
    cells = []
    for i, (group, (symbol, name, slug)) in enumerate(elements):
        r, c = divmod(i, cols)
        x, y = c * cell_w, TOP + r * cell_h
        t = treatment(group["style"], theme)
        parts = []
        if group["style"] == "dots":
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{theme.paper}"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{t["fill"]}"/>')
        parts.append(text(x + 8, y + 17, f"{i + 1:02d}", "m", fill=t["num"], size=9))
        parts.append(icon(slug, x + cell_w - 8 - icon_size, y + 8, icon_size, t["txt"], stroke_width=1.6))
        parts.append(text(x + 8, y + 54, symbol, "sr", fill=t["sym"], size=sym_size))
        parts.append(text(x + 8, y + 70, name, "tm", fill=t["txt"], size=fit("tm", name, name_size, cell_w - 16)))
        cells.append(f'<g class="on" style="animation-delay:{.2 + i * .025:.3f}s">{"".join(parts)}</g>')
        cells.append(f'<rect class="walk" x="{x + 1}" y="{y + cell_h - 5}" width="{cell_w - 2}" height="4" '
                     f'fill="{t["marker"]}" style="animation-duration:{cycle:.2f}s;animation-delay:{1.5 + i * STEP:.2f}s"/>')
    # empty slots at the end of the last row get the hatch texture
    for j in range(len(elements), rows * cols):
        r, c = divmod(j, cols)
        cells.append(f'<rect x="{c * cell_w}" y="{TOP + r * cell_h}" width="{cell_w}" height="{cell_h}" '
                     f'fill="url(#hatch)" opacity="{.5 if theme.dark else .35}"/>')
    body.append("".join(cells))

    rules = [vline(c * cell_w - 1, TOP, grid_bottom, theme.ink) for c in range(1, cols)]
    rules += [hline(0, sheet_w, TOP + r * cell_h - 1, theme.ink) for r in range(1, rows + 1)]
    body.append(f'<g class="rule">{"".join(rules)}</g>')
    body.append("".join(legend))
    desc = "; ".join(f"{g['label']}: {', '.join(item[1] for item in g['items'])}" for g in groups)
    return document("".join(body), W, H, title="Tech stack, as a periodic table", desc=desc, css=CSS,
                    defs=patterns(theme))
