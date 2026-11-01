"""§06 selected work as a bento grid: an inverted feature cell for the lead
project and five editorial cells, each with a small flat motif that loops.
Phones get the feature on top and the rest in a two-column grid. Tags with a
leading "+" (applied AI) are drawn in teal."""

from __future__ import annotations

import random
import re

from core import fonts
from core.design import CSS as BASE, box, canvas, card, patterns, secondary, strip, wrap
from core.svg import document, fit, num, text
from core.theme import Theme

TOP = 40
# (x, y, w, h) below the running header; the first cell is the feature
DESKTOP = [(0, 0, 520, 320), (520, 0, 312, 160), (520, 160, 312, 160),
           (0, 320, 312, 176), (312, 320, 208, 176), (520, 320, 312, 176)]
MOBILE = [(0, 0, 400, 304), (0, 304, 200, 168), (200, 304, 200, 168),
          (0, 472, 200, 168), (200, 472, 200, 168), (0, 640, 200, 168)]
MOBILE_FILLER = (200, 640, 200, 168)

CSS = BASE + """
.eq{animation:eq 1.2s cubic-bezier(.7,0,.3,1) infinite alternate;transform-box:fill-box;transform-origin:bottom}
@keyframes eq{from{transform:scaleY(.25)}}
.dot{animation:dot 1.2s steps(1,end) infinite}
@keyframes dot{0%{opacity:1}33%,100%{opacity:.25}}
.arc{stroke-dasharray:1;animation:arc 5s cubic-bezier(.7,0,.3,1) infinite}
@keyframes arc{0%{stroke-dashoffset:1}30%,85%{stroke-dashoffset:.1}100%{stroke-dashoffset:1}}
.bar{animation:bar 5s cubic-bezier(.7,0,.3,1) infinite;transform-box:fill-box;transform-origin:bottom}
@keyframes bar{0%{transform:scaleY(0)}25%,85%{transform:scaleY(1)}100%{transform:scaleY(0)}}
.wr{stroke-dasharray:1;animation:wr 5s steps(12,end) infinite}
@keyframes wr{0%{stroke-dashoffset:1}40%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}
.pl{animation:pl 5s steps(1,end) infinite}
@keyframes pl{0%,49%{opacity:1}50%,100%{opacity:0}}
.nt{animation:nt 5s steps(1,end) infinite}
@keyframes nt{0%,49%{opacity:0}50%,100%{opacity:1}}
"""


# ---- motifs: flat strokes and blocks in a w x h box at (x, y) ---------------

def m_wave(x, y, w, h, ink, accent):
    rnd = random.Random(3)
    n, bw = 13, 4
    step = (w - bw) / (n - 1)
    return "".join(
        f'<rect class="eq" x="{num(x + i * step)}" y="{num(y)}" width="{bw}" height="{h}" fill="{accent}" '
        f'style="animation-duration:{rnd.uniform(.5, 1.2):.2f}s;animation-delay:-{rnd.uniform(0, 1):.2f}s"/>'
        for i in range(n))


def m_chat(x, y, w, h, ink, accent):
    bw, bh = 48, 24
    bx, by = x + w - bw, y + (h - bh) / 2
    return (f'<path d="M{bx + .5} {by + .5}h{bw - 1}v{bh - 1}H{bx + 16}l-8 8v-8h-{7.5}Z" fill="none" stroke="{ink}"/>'
            + "".join(f'<rect class="dot" x="{bx + 12 + i * 10}" y="{by + 10}" width="4" height="4" fill="{accent}" '
                      f'style="animation-delay:{i * .2:.1f}s"/>' for i in range(3)))


def m_gauge(x, y, w, h, ink, accent):
    r = min(h, w / 2) - 4
    cx, cy = x + w - r - 4, y + h - 2
    arc = f"M{num(cx - r)} {num(cy)}A{num(r)} {num(r)} 0 0 1 {num(cx + r)} {num(cy)}"
    return (f'<path d="{arc}" stroke="{ink}" stroke-width="1"/>'
            f'<path class="arc" d="{arc}" pathLength="1" stroke="{accent}" stroke-width="6" stroke-linecap="butt"/>')


def m_chart(x, y, w, h, ink, accent):
    heights = [.35, .55, .4, .7, .6, .95]
    bw = 6
    gap = (w - len(heights) * bw) / (len(heights) - 1)
    return "".join(
        f'<rect class="bar" x="{num(x + i * (bw + gap))}" y="{num(y + h * (1 - f))}" width="{bw}" '
        f'height="{num(h * f)}" fill="{accent if i == len(heights) - 1 else ink}" style="animation-delay:{i * .08:.2f}s"/>'
        for i, f in enumerate(heights))


def m_write(x, y, w, h, ink, accent):
    out = []
    for i, f in enumerate((1, .7, .85)):
        yy = y + 4 + i * 10
        out.append(f'<path class="wr" d="M{num(x + w * (1 - f))} {yy}H{x + w}" pathLength="1" stroke="{ink if i else accent}" '
                   f'stroke-width="2" style="animation-delay:{i * .4:.1f}s"/>')
    return "".join(out)


def m_play(x, y, w, h, ink, accent):
    bx = x + w - 32
    return (f'<g class="pl"><rect x="{bx + .5}" y="{y + .5}" width="31" height="{h - 1}" fill="none" stroke="{ink}"/>'
            f'<path d="M{bx + 12} {y + h / 2 - 6}v12l10-6Z" fill="{accent}"/></g>'
            f'<g class="nt">' + "".join(
                f'<rect x="{bx}" y="{y + 4 + i * 9}" width="{32 - i * 8}" height="3" fill="{accent if i == 0 else ink}"/>'
                for i in range(3)) + "</g>")


MOTIFS = {"wave": m_wave, "chat": m_chat, "gauge": m_gauge, "chart": m_chart, "write": m_write, "play": m_play}


def status(project: dict) -> str:
    return f'{project.get("badge", "Code").upper()} ↗'


def tag_line(tags: list[str], x: float, y: float, fill: str, teal: str, size: float) -> str:
    spans = []
    for i, tag in enumerate(tags):
        label, extra = secondary(tag)
        if i:
            spans.append("  /  ")
        spans.append(f'<tspan fill="{teal}">{label.upper()}</tspan>' if extra else label.upper())
    return (f'<text x="{num(x)}" y="{num(y)}" class="m" font-size="{size}" letter-spacing="1.2" fill="{fill}" '
            f'xml:space="preserve">{"".join(spans)}</text>')


def feature(p: dict, x: float, y: float, w: float, h: float, theme: Theme, mobile: bool) -> str:
    bg, fg = theme.ink, theme.paper
    soft = theme.soft_inv
    pad = 24 if mobile else 32
    name_size = 48 if mobile else 64
    kind = p["kind"].upper()
    out = [f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" fill="{bg}"/>',
           text(x + pad, y + pad + 9, "01", "mb", fill=theme.accent_inv, size=10),
           text(x + pad + 24, y + pad + 9, "FEATURED", "m", fill=fg, size=10, letter_spacing="1.6"),
           text(x + w - pad, y + pad + 9, status(p), "mb", fill=theme.accent_inv, size=10, anchor="end", letter_spacing="1.6"),
           text(x + pad, y + pad + 32 + name_size * .72, p["name"], "sr", fill=fg, size=name_size)]
    kind_y = y + pad + 32 + name_size * .72 + 28
    out.append(text(x + pad, kind_y, kind, "m", fill=theme.accent_inv, size=10 if mobile else 11, letter_spacing="1.6"))
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", p["summary"])
    size, leading = (13, 20) if mobile else (15, 24)
    for i, line in enumerate(wrap(plain, "t", size, w - 2 * pad, 4)):
        out.append(text(x + pad, kind_y + 32 + i * leading, line, "t", fill=soft, size=size))
    tags_y = y + h - pad + 4
    out.append(tag_line(p["tags"], x + pad, tags_y, fg, theme.teal_inv, 9.5 if mobile else 10))
    if not mobile:  # beside the title, clear of the summary and tags
        out.append(MOTIFS[p["motif"]](x + w - pad - 112, y + pad + 48, 112, 32, fg, theme.accent_inv))
    return "".join(out)


def small(p: dict, index: int, x: float, y: float, w: float, h: float, theme: Theme, mobile: bool) -> str:
    pad = 24 if w > 240 else 16
    name_size = 28 if mobile else 32
    base = y + pad + 48
    out = [text(x + pad, y + pad + 9, f"{index:02d}", "mb", fill=theme.accent_text, size=10),
           text(x + w - pad, y + pad + 9, status(p), "mb", fill=theme.ink, size=10, anchor="end", letter_spacing="1.4"),
           text(x + pad, base, p["name"], "sr", fill=theme.ink, size=name_size)]
    kind = p["kind"].upper()
    out.append(text(x + pad, base + 20, kind, "m", fill=theme.muted, size=fit("m", kind, 9.5, w - 2 * pad, 1.4),
                    letter_spacing="1.4"))
    name_w = fonts.width("sr", p["name"], name_size)
    if not mobile and name_w + 48 + 16 <= w - 2 * pad:
        out.append(MOTIFS[p["motif"]](x + w - pad - 48, base - 24, 48, 24, theme.ink, theme.accent))
    size, leading = (12, 16) if mobile else (13, 20)
    for i, line in enumerate(wrap(p["blurb"], "t", size, w - 2 * pad, 3 if mobile else 2)):
        out.append(text(x + pad, base + 44 + i * leading, line, "t", fill=theme.muted, size=size))
    return "".join(out)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> str:
    projects = profile["projects"][:6]
    W = canvas(mobile)
    sheet_w = W - 8
    layout = MOBILE if mobile else DESKTOP
    grid_h = max(y + h for _, y, _, h in layout + ([MOBILE_FILLER] if mobile else []))
    H = TOP + grid_h + 8
    body = [card(W, H, theme),
            strip(0, 0, sheet_w, "§06", "Selected work", f"{len(projects)} projects · links below", theme)]
    rules = []
    for i, (p, (x, y, w, h)) in enumerate(zip(projects, layout)):
        y += TOP
        cell = feature(p, x, y, w, h, theme, mobile) if i == 0 else small(p, i + 1, x, y, w, h, theme, mobile)
        body.append(f'<g class="lift" style="animation-delay:{.15 + i * .1:.2f}s">{cell}</g>')
        rules.append(box(x, y, w, h, theme.ink))
    if mobile:
        fx, fy, fw, fh = MOBILE_FILLER
        fy += TOP
        body.append(f'<rect x="{fx + 1}" y="{fy + 1}" width="{fw - 2}" height="{fh - 2}" fill="url(#hatch)" '
                    f'opacity="{.5 if theme.dark else .35}"/>'
                    f'<rect x="{fx + 16.5}" y="{fy + fh - 48.5}" width="{fw - 33}" height="32" fill="{theme.paper}" '
                    f'stroke="{theme.ink}"/>'
                    + text(fx + 32, fy + fh - 28, "LINKS BELOW ↓", "m", fill=theme.ink, size=10, letter_spacing="1.6"))
        rules.append(box(fx, fy, fw, fh, theme.ink))
    body.append(f'<g class="rule">{"".join(rules)}</g>')
    desc = "; ".join(f"{p['name']}: {p['blurb']}" for p in projects)
    return document("".join(body), W, H, title="Selected work", desc=desc, css=CSS, defs=patterns(theme))
