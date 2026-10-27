"""Featured project cards. Each card is its own SVG (so each can link to its
project) with a light beam running around the border and a small looping
motif that hints at what the project does."""

from __future__ import annotations

import random
import re

from core import fonts
from core.icons import icon
from core.svg import document, esc, num, text
from core.theme import Theme, mix

W, H = 410, 214
PAD = 22
BOX = (W - PAD - 100, PAD + 2, 100, 44)   # motif box: x, y, w, h

CSS = """
.beam{stroke-dasharray:.14 .86;animation:beam 7s linear infinite}
@keyframes beam{to{stroke-dashoffset:-1}}
.in{animation:in .7s cubic-bezier(.2,.8,.2,1) both}
@keyframes in{from{opacity:0;transform:translateY(8px)}}
.eq{animation:eq 1.1s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
@keyframes eq{from{transform:scaleY(.22)}to{transform:scaleY(1)}}
.dot{animation:dot 1.3s ease-in-out infinite}
@keyframes dot{0%,60%,100%{transform:translateY(0);opacity:.45}30%{transform:translateY(-5px);opacity:1}}
.gauge{stroke-dasharray:1;animation:gauge 6s cubic-bezier(.3,.7,.2,1) infinite}
@keyframes gauge{0%{stroke-dashoffset:1}30%,85%{stroke-dashoffset:.08}100%{stroke-dashoffset:1}}
.score{animation:score 6s ease infinite}
@keyframes score{0%,22%{opacity:0}32%,85%{opacity:1}95%,100%{opacity:0}}
.bar{animation:bar 6s cubic-bezier(.3,.8,.2,1) infinite;transform-box:fill-box;transform-origin:bottom}
@keyframes bar{0%{transform:scaleY(0)}25%,85%{transform:scaleY(1)}100%{transform:scaleY(0)}}
.ln{stroke-dasharray:1;animation:ln 6s ease-in-out infinite}
@keyframes ln{0%,20%{stroke-dashoffset:1}50%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}
.wr{stroke-dasharray:1;animation:wr 6s linear infinite}
@keyframes wr{0%{stroke-dashoffset:1}30%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:1}}
.vid{animation:vid 6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes vid{0%,100%{transform:scale(1)}12%{transform:scale(1.08)}24%{transform:scale(1)}}
.arr{animation:arr 6s ease-in-out infinite}
@keyframes arr{0%,20%{transform:translateX(-4px);opacity:0}32%,85%{transform:translateX(0);opacity:1}100%{opacity:0}}
.nt{animation:nt 6s ease-out infinite}
@keyframes nt{0%,30%{opacity:0;transform:translateX(-4px)}42%,88%{opacity:1;transform:translateX(0)}100%{opacity:0}}
"""


def rounded_path(x: float, y: float, w: float, h: float, r: float) -> str:
    return (f"M{num(x + r)} {num(y)}H{num(x + w - r)}A{r} {r} 0 0 1 {num(x + w)} {num(y + r)}"
            f"V{num(y + h - r)}A{r} {r} 0 0 1 {num(x + w - r)} {num(y + h)}H{num(x + r)}"
            f"A{r} {r} 0 0 1 {num(x)} {num(y + h - r)}V{num(y + r)}A{r} {r} 0 0 1 {num(x + r)} {num(y)}Z")


def rich_lines(src: str, size: float, max_w: float, theme: Theme, limit: int = 4) -> list[str]:
    """Word-wrap text with **bold** spans; returns tspans markup per line.

    Words are (text, bold) runs; punctuation right after a bold span (", served")
    is glued to it so it never gets a stray space or wraps on its own.
    """
    words: list[list[tuple[str, bool]]] = []
    prev_space = True
    for part in re.split(r"(\*\*.+?\*\*)", src):
        if not part:
            continue
        bold = part.startswith("**")
        text_ = part[2:-2] if bold else part
        for i, w in enumerate(text_.split()):
            if i == 0 and words and not prev_space and not text_[0].isspace():
                words[-1].append((w, bold))
            else:
                words.append([(w, bold)])
        prev_space = text_[-1].isspace()
    space = fonts.width("s", " ", size)

    def width(word):
        return sum(fonts.width("sb" if b else "s", t, size) for t, b in word)

    lines, cur, cur_w = [], [], 0.0
    for word in words:
        ww = width(word)
        if cur and cur_w + space + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur_w += (space if cur else 0) + ww
        cur.append(word)
    if cur:
        lines.append(cur)
    if len(lines) > limit:
        lines = lines[:limit]
        lines[-1] = lines[-1] + [[("…", False)]]
    out = []
    for line in lines:
        spans = []
        for i, word in enumerate(line):
            if i:
                spans.append(" ")
            for t, bold in word:
                spans.append(f'<tspan class="sb" fill="{theme.text}">{esc(t)}</tspan>' if bold else esc(t))
        out.append("".join(spans))
    return out


# ---- motifs ---------------------------------------------------------------

def motif_wave(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    rnd = random.Random(3)
    n, bw = 13, 4
    step = (w - bw) / (n - 1)
    out = []
    for i in range(n):
        bh = h * rnd.uniform(.45, 1)
        out.append(f'<rect class="eq" x="{num(x + i * step)}" y="{num(y + (h - bh) / 2)}" width="{bw}" '
                   f'height="{num(bh)}" rx="2" fill="url(#mg)" style="animation-duration:{rnd.uniform(.7, 1.4):.2f}s;'
                   f'animation-delay:-{rnd.uniform(0, 1.4):.2f}s"/>')
    return "".join(out)


def motif_chat(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    bx, by, bw_, bh = x + 30, y + 6, 70, 32
    bubble = (f'<path d="M{bx + 10} {by}H{bx + bw_ - 10}a10 10 0 0 1 10 10v{bh - 20}a10 10 0 0 1-10 10H{bx + 18}'
              f'l-9 7v-7.5A10 10 0 0 1 {bx} {by + bh - 10}V{by + 10}a10 10 0 0 1 10-10Z" '
              f'fill="{theme.panel2}" stroke="{color}" stroke-opacity=".7"/>')
    dots = "".join(f'<circle class="dot" cx="{bx + 22 + i * 13}" cy="{by + bh / 2}" r="3.6" fill="{color}" '
                   f'style="animation-delay:{i * .18:.2f}s"/>' for i in range(3))
    small = (f'<rect x="{x}" y="{y + 2}" width="22" height="14" rx="7" fill="{mix(color, theme.panel, .55)}"/>'
             f'<rect x="{x + 6}" y="{y + 20}" width="16" height="10" rx="5" fill="{mix(color, theme.panel, .7)}"/>')
    return small + bubble + dots


def motif_gauge(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    cx, cy, r = x + w / 2 + 8, y + h - 2, 34
    arc = f"M{num(cx - r)} {num(cy)}A{r} {r} 0 0 1 {num(cx + r)} {num(cy)}"
    return (f'<path d="{arc}" stroke="{theme.border2}" stroke-width="7" stroke-linecap="round"/>'
            f'<path class="gauge" d="{arc}" pathLength="1" stroke="url(#mg)" stroke-width="7" stroke-linecap="round"/>'
            f'<g class="score">' + text(cx, cy - 6, "92", "d", fill=theme.text, size=17, anchor="middle")
            + text(cx, cy + 9, "ATS", "mb", fill=color, size=8, anchor="middle", letter_spacing="1.5") + "</g>")


def motif_chart(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    heights = [.35, .55, .42, .7, .6, .92]
    bw, gap = 11, 6.6
    x0 = x + w - len(heights) * bw - (len(heights) - 1) * gap
    bars, pts = [], []
    for i, f in enumerate(heights):
        bx = x0 + i * (bw + gap)
        bh = h * f
        bars.append(f'<rect class="bar" x="{num(bx)}" y="{num(y + h - bh)}" width="{bw}" height="{num(bh)}" rx="3" '
                    f'fill="url(#mg)" fill-opacity=".85" style="animation-delay:{i * .08:.2f}s"/>')
        pts.append(f"{num(bx + bw / 2)} {num(y + h - bh - 6)}")
    line = (f'<path class="ln" d="M{"L".join(pts)}" pathLength="1" stroke="{theme.text}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(bars) + line


def motif_write(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    out = []
    for i, f in enumerate((1, .78, .9, .55)):
        yy = y + 6 + i * 11
        out.append(f'<path d="M{x} {yy}h{num(w * f)}" stroke="{theme.border2}" stroke-width="4" stroke-linecap="round"/>')
        out.append(f'<path class="wr" d="M{x} {yy}h{num(w * f)}" pathLength="1" stroke="url(#mg)" stroke-width="4" '
                   f'stroke-linecap="round" style="animation-delay:{i * .35:.2f}s"/>')
    return "".join(out)


def motif_play(color: str, theme: Theme) -> str:
    x, y, w, h = BOX
    vid = (f'<g class="vid"><rect x="{x}" y="{y + 7}" width="40" height="30" rx="8" fill="{color}"/>'
           f'<path d="M{x + 16} {y + 15}v14l11-7Z" fill="#fff"/></g>')
    arrow = (f'<path class="arr" d="M{x + 47} {y + 22}h11m-4-4 4 4-4 4" stroke="{theme.muted}" stroke-width="1.8" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    notes = "".join(
        f'<g class="nt" style="animation-delay:{i * .25:.2f}s"><circle cx="{x + 66}" cy="{y + 9 + i * 13}" r="2.2" '
        f'fill="{color}"/><path d="M{x + 72} {y + 9 + i * 13}h{24 - i * 5}" stroke="{theme.text}" '
        f'stroke-opacity=".75" stroke-width="3" stroke-linecap="round"/></g>' for i in range(3))
    return vid + arrow + notes


MOTIFS = {"wave": motif_wave, "chat": motif_chat, "gauge": motif_gauge, "chart": motif_chart,
          "write": motif_write, "play": motif_play}


def card(project: dict, theme: Theme) -> str:
    color = getattr(theme, project.get("color", "indigo"))
    deep = mix(color, "#000000", .35)
    defs = (
        f'<radialGradient id="cg" cx="0" cy="0" r="1"><stop offset="0" stop-color="{color}" '
        f'stop-opacity="{.2 if theme.dark else .1}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="eg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
        f'<stop offset="1" stop-color="{deep}"/></linearGradient>'
        f'<linearGradient id="mg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
        f'<stop offset="1" stop-color="{mix(color, theme.violet, .5)}"/></linearGradient>'
        f'<filter id="bb" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.5"/></filter>'
    )
    border = rounded_path(.75, .75, W - 1.5, H - 1.5, 15.5)
    out = [
        f'<path d="{border}" fill="{theme.panel}" stroke="{theme.border}"/>',
        f'<rect x="1" y="1" width="{W * .9}" height="{H * .9}" rx="15" fill="url(#cg)"/>',
        f'<path class="beam" d="{border}" pathLength="1" stroke="{color}" stroke-width="3" filter="url(#bb)" '
        f'stroke-opacity=".8"/>',
        f'<path class="beam" d="{border}" pathLength="1" stroke="{color}" stroke-width="1.4"/>',
        # emblem
        f'<rect x="{PAD}" y="{PAD}" width="44" height="44" rx="12" fill="url(#eg)"/>',
        icon(project["icon"], PAD + 11, PAD + 11, 22, theme, color="#ffffff", stroke_width=2.1),
    ]
    title_size = 19 if fonts.width("d", project["name"], 19) < W - 2 * PAD - 160 else 17
    out.append(f'<g class="in" style="animation-delay:.1s">'
               + text(PAD + 58, PAD + 20, project["name"], "d", fill=theme.text, size=title_size)
               + text(PAD + 58, PAD + 39, project["kind"].upper(), "m", fill=color, size=9.5, letter_spacing="1.3")
               + "</g>")
    out.append(f'<g class="in" style="animation-delay:.25s">{MOTIFS[project["motif"]](color, theme)}</g>')

    lines = rich_lines(project["summary"], 12.5, W - 2 * PAD, theme)
    body = "".join(f'<text x="{PAD}" y="{num(PAD + 74 + i * 18.5)}" class="s" font-size="12.5" fill="{theme.muted}">'
                   f'{ln}</text>' for i, ln in enumerate(lines))
    out.append(f'<g class="in" style="animation-delay:.35s">{body}</g>')

    # tags + badge
    ty = H - PAD - 22
    badge = project.get("badge", "Code").upper()
    live = badge == "LIVE"
    bw = fonts.width("mb", badge, 10, 1.2) + 40
    bx = W - PAD - bw
    tx = PAD
    tags = []
    for tag in project["tags"]:
        tw = fonts.width("m", tag, 10.5) + 16
        if tx + tw > bx - 8:  # never run into the badge; later tags just drop
            break
        tags.append(f'<rect x="{num(tx)}" y="{ty}" width="{num(tw)}" height="22" rx="6" fill="{theme.panel2}" '
                    f'stroke="{theme.border}"/>' + text(tx + 8, ty + 14.8, tag, "m", fill=theme.muted, size=10.5))
        tx += tw + 6
    badge_color = theme.green if live else theme.indigo
    tags.append(
        f'<rect x="{num(bx)}" y="{ty}" width="{num(bw)}" height="22" rx="11" fill="{mix(badge_color, theme.panel, .82)}" '
        f'stroke="{badge_color}" stroke-opacity=".55"/>'
        + (f'<circle cx="{num(bx + 12)}" cy="{ty + 11}" r="3" fill="{badge_color}"/>' if live else
           icon("glyph:code", bx + 7, ty + 5, 12, theme, color=badge_color, stroke_width=2.2))
        + text(bx + 22, ty + 15, badge, "mb", fill=badge_color, size=10, letter_spacing="1.2")
        + icon("glyph:arrow", bx + bw - 17, ty + 6, 10, theme, color=badge_color, stroke_width=2.4)
    )
    out.append(f'<g class="in" style="animation-delay:.45s">{"".join(tags)}</g>')
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", project["summary"])
    return document("".join(out), W, H, title=f"{project['name']} — {project['kind']}",
                    desc=f"{plain} Built with {', '.join(project['tags'])}.", css=CSS, defs=defs)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> dict[str, str]:
    return {f"project-{p['slug']}": card(p, theme) for p in profile["projects"]}
