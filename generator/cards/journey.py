"""Career timeline: a track that draws itself left to right, lighting up each
milestone as it passes. The final milestone keeps pulsing."""

from __future__ import annotations

from core import fonts
from core.icons import icon
from core.svg import balance, document, fit, num, text
from core.theme import Theme

W, H = 840, 296
TRACK_Y, X0, X1 = 150, 34, 806
BLOCK_W, BLOCK_H = 226, 86
DRAW = 2.6  # seconds for the track to reach the right edge

CSS = """
.trk{stroke-dasharray:1;animation:trk 2.6s cubic-bezier(.45,.05,.35,1) .2s both}
@keyframes trk{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
.comet{stroke-dasharray:.07 1.2;animation:comet 4.5s cubic-bezier(.5,0,.5,1) 3.2s infinite both}
@keyframes comet{0%{stroke-dashoffset:.07;opacity:1}70%{stroke-dashoffset:-1.07;opacity:1}100%{stroke-dashoffset:-1.07;opacity:0}}
.nd{animation:nd .6s cubic-bezier(.3,1.7,.5,1) both;transform-box:fill-box;transform-origin:center}
@keyframes nd{from{opacity:0;transform:scale(0)}}
.blk{animation:blk .7s cubic-bezier(.2,.8,.2,1) both}
@keyframes blk{from{opacity:0;transform:translateY(var(--dy,8px))}}
.stem{animation:stem .45s ease-out both;transform-box:fill-box}
@keyframes stem{from{transform:scaleY(0)}}
.pulse{animation:pulse 2.2s ease-out infinite both;transform-box:fill-box;transform-origin:center}
@keyframes pulse{0%{opacity:0;transform:scale(1)}1%{opacity:.8}100%{opacity:0;transform:scale(3.2)}}
"""


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    items = profile["journey"]
    n = len(items)
    margin = 64
    xs = [margin + i * (W - 2 * margin) / (n - 1) for i in range(n)]
    g = theme.grad
    defs = [
        f'<linearGradient id="tg" gradientUnits="userSpaceOnUse" x1="{X0}" x2="{X1}" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{g[0]}"/><stop offset=".55" stop-color="{g[1]}"/>'
        f'<stop offset="1" stop-color="{g[2]}"/></linearGradient>'
        f'<filter id="soft" x="-50%" y="-300%" width="200%" height="700%"><feGaussianBlur stdDeviation="3"/></filter>'
    ]
    track = f"M{X0} {TRACK_Y}H{X1}"
    body = [
        f'<path d="{track}" stroke="{theme.border2}" stroke-width="2" stroke-linecap="round" stroke-dasharray="2 6"/>',
        f'<path class="trk" d="{track}" pathLength="1" stroke="url(#tg)" stroke-width="2.5" stroke-linecap="round"/>',
        f'<path class="comet" d="{track}" pathLength="1" stroke="#fff" stroke-opacity="{.9 if theme.dark else .95}" '
        f'stroke-width="3" stroke-linecap="round" filter="url(#soft)"/>',
    ]
    for i, (item, x) in enumerate(zip(items, xs)):
        color = getattr(theme, item.get("color", "indigo"))
        t = .2 + DRAW * (x - X0) / (X1 - X0)
        above = i % 2 == 0
        top = TRACK_Y - 30 - BLOCK_H if above else TRACK_Y + 30
        cx = min(max(x, BLOCK_W / 2 + 6), W - BLOCK_W / 2 - 6)
        last = i == n - 1

        # stem from the node to its text block
        y_a, y_b = (TRACK_Y - 12, TRACK_Y - 26) if above else (TRACK_Y + 12, TRACK_Y + 26)
        origin = "bottom" if above else "top"
        body.append(f'<path class="stem" d="M{num(x)} {y_a}V{y_b}" stroke="{color}" stroke-width="1.5" '
                    f'stroke-dasharray="{"2 3" if last else "none"}" style="transform-origin:{origin};'
                    f'animation-delay:{t:.2f}s"/>')
        # node
        if last:
            body.append(f'<circle class="pulse" cx="{num(x)}" cy="{TRACK_Y}" r="7" fill="{color}" '
                        f'style="animation-delay:{t + .4:.2f}s"/>')
        body.append(f'<g class="nd" style="animation-delay:{t:.2f}s">'
                    f'<circle cx="{num(x)}" cy="{TRACK_Y}" r="8" fill="{theme.panel}" stroke="{color}" stroke-width="2.5"/>'
                    f'<circle cx="{num(x)}" cy="{TRACK_Y}" r="3.2" fill="{color}"/></g>')

        # text block, centred on the node (clamped to the canvas)
        when = item["when"].upper()
        ww = fonts.width("m", when, 10, 1.4)
        lines = balance("s", item["note"], 11.5, BLOCK_W - 6)
        title_size = fit("dm", item["title"], 15.5, BLOCK_W)
        block = [
            icon(item["icon"], cx - (ww + 17) / 2, top, 12, theme, color=color, stroke_width=2.2),
            text(cx - (ww + 17) / 2 + 17, top + 10, when, "mb", fill=color, size=10, letter_spacing="1.4"),
            text(cx, top + 32, item["title"], "dm", fill=theme.text, size=title_size, anchor="middle"),
            text(cx, top + 50, item["org"], "sm", fill=theme.muted, size=12, anchor="middle"),
        ]
        for k, line in enumerate(lines):
            block.append(text(cx, top + 69 + k * 15, line, "s", fill=theme.muted, size=11.5, anchor="middle"))
        dy = "8px" if above else "-8px"
        body.append(f'<g class="blk" style="--dy:{dy};animation-delay:{t + .12:.2f}s">{"".join(block)}</g>')

    desc = "; ".join(f"{i['when']}: {i['title']}, {i['org']}" for i in items)
    return document("".join(body), W, H, title="Journey so far", desc=desc, css=CSS, defs="".join(defs))
