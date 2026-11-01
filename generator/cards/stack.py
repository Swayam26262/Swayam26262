"""§04 stack as a periodic table: 39 elements on a 13 x 3 grid of hard-ruled
cells. Each group gets its own flat treatment and a marker walks the table."""

from __future__ import annotations

from core import fonts
from core.design import CSS as BASE, W, box, card, hline, patterns, strip, vline
from core.icons import icon
from core.svg import document, fit, text
from core.theme import Theme

CELL_W, CELL_H, COLS = 64, 80, 13
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
        "accent-text": dict(fill=theme.paper, sym=theme.accent, txt=theme.ink, num=theme.accent),
        "dots": dict(fill="url(#dots)", sym=theme.ink, txt=theme.ink, num=theme.muted),
    }[style]
    t["marker"] = theme.on_accent if style == "accent" else theme.accent
    return t


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    groups = profile["stack"]
    elements = [(g, item) for g in groups for item in g["items"]]
    rows = -(-len(elements) // COLS)
    sheet_w = W - 8
    legend_y = TOP + rows * CELL_H
    H = legend_y + 48 + 8
    cycle = len(elements) * STEP
    body = [card(W, H, theme)]
    body.append(strip(0, 0, sheet_w, "§04", "Stack — a periodic table",
                      f"{len(elements)} elements · {len(groups)} groups", theme))

    cells = []
    for i, (group, (symbol, name, slug)) in enumerate(elements):
        r, c = divmod(i, COLS)
        x, y = c * CELL_W, TOP + r * CELL_H
        t = treatment(group["style"], theme)
        parts = []
        if group["style"] == "dots":
            parts.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" fill="{theme.paper}"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" fill="{t["fill"]}"/>')
        parts.append(text(x + 8, y + 17, f"{i + 1:02d}", "m", fill=t["num"], size=9))
        parts.append(icon(slug, x + CELL_W - 20, y + 8, 12, t["txt"], stroke_width=1.6))
        parts.append(text(x + 8, y + 54, symbol, "sr", fill=t["sym"], size=32))
        parts.append(text(x + 8, y + 70, name, "tm", fill=t["txt"], size=fit("tm", name, 9.5, CELL_W - 16)))
        cells.append(f'<g class="on" style="animation-delay:{.2 + i * .025:.3f}s">{"".join(parts)}</g>')
        cells.append(f'<rect class="walk" x="{x + 1}" y="{y + CELL_H - 5}" width="{CELL_W - 2}" height="4" '
                     f'fill="{t["marker"]}" style="animation-duration:{cycle:.2f}s;animation-delay:{1.5 + i * STEP:.2f}s"/>')
    body.append("".join(cells))

    rules = [vline(c * CELL_W - 1, TOP, legend_y, theme.ink) for c in range(1, COLS)]
    rules += [hline(0, sheet_w, TOP + r * CELL_H - 1, theme.ink) for r in range(1, rows + 1)]
    body.append(f'<g class="rule">{"".join(rules)}</g>')

    # legend
    x = 24
    for group in groups:
        t = treatment(group["style"], theme)
        label = group["label"].upper()
        if group["style"] == "dots":
            body.append(f'<rect x="{x}" y="{legend_y + 16}" width="24" height="16" fill="{theme.paper}"/>')
        body.append(box(x, legend_y + 16, 24, 16, theme.ink, t["fill"]))
        if group["style"] == "accent-text":
            body.append(f'<rect x="{x + 8}" y="{legend_y + 20}" width="8" height="8" fill="{theme.accent}"/>')
        body.append(text(x + 32, legend_y + 28, label, "m", fill=theme.ink, size=10, letter_spacing="1.4"))
        x += 32 + fonts.width("m", label, 10, 1.4) + 1.4 + 24
    desc = "; ".join(f"{g['label']}: {', '.join(item[1] for item in g['items'])}" for g in groups)
    return document("".join(body), W, H, title="Tech stack, as a periodic table", desc=desc, css=CSS,
                    defs=patterns(theme))
