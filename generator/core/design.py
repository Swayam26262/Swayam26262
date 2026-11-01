"""Shared building blocks for the editorial look.

Rules of the system:
  * 8pt grid: every box, padding and gap is a multiple of 8.
  * Flat fills only. Depth comes from hard 1px rules and solid offset blocks.
  * Display type is Instrument Serif, text is Instrument Sans, utilities are mono.
"""

from __future__ import annotations

from .svg import num, text
from .theme import Theme

G = 8            # the grid unit
SHADOW = 8       # offset of the solid block shadow
W = 105 * G      # 840: canvas width of a full-width spread


def u(n: float) -> float:
    """n grid units in px."""
    return n * G


def hline(x1: float, x2: float, y: float, color: str, width: float = 1) -> str:
    return f'<path d="M{num(x1)} {num(y + .5)}H{num(x2)}" stroke="{color}" stroke-width="{width}"/>'


def vline(x: float, y1: float, y2: float, color: str, width: float = 1) -> str:
    return f'<path d="M{num(x + .5)} {num(y1)}V{num(y2)}" stroke="{color}" stroke-width="{width}"/>'


def box(x: float, y: float, w: float, h: float, color: str, fill: str = "none") -> str:
    """A rectangle whose 1px outline lands on whole pixels."""
    return (f'<rect x="{num(x + .5)}" y="{num(y + .5)}" width="{num(w - 1)}" height="{num(h - 1)}" '
            f'fill="{fill}" stroke="{color}"/>')


def card(w: float, h: float, theme: Theme, *, fill: str | None = None, shadow: str | None = None) -> str:
    """A sheet of paper with a hard border and a solid offset block behind it.

    The canvas is w x h; the sheet itself is (w - SHADOW) x (h - SHADOW).
    """
    sw, sh = w - SHADOW, h - SHADOW
    return (f'<rect x="{SHADOW}" y="{SHADOW}" width="{num(sw)}" height="{num(sh)}" fill="{shadow or theme.shadow}"/>'
            + box(0, 0, sw, sh, theme.ink, fill or theme.paper))


def strip(x: float, y: float, w: float, index: str, title: str, right: str, theme: Theme) -> str:
    """Running header: '§02  TITLE ............ RIGHT' over a hard rule. 40px tall."""
    base = y + 25
    return (text(x + 24, base, index, "mb", fill=theme.accent, size=10, letter_spacing="1")
            + text(x + 64, base, title.upper(), "m", fill=theme.ink, size=10, letter_spacing="1.6")
            + text(x + w - 24, base, right.upper(), "m", fill=theme.muted, size=10, anchor="end", letter_spacing="1.6")
            + hline(x, x + w, y + 39, theme.ink))


def patterns(theme: Theme) -> str:
    """Raw geometric textures: 45 degree hatching and an 8px dot grid."""
    return (
        f'<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0V8" stroke="{theme.ink}" stroke-width="1"/></pattern>'
        f'<pattern id="hatch-a" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0V8" stroke="{theme.accent}" stroke-width="2"/></pattern>'
        f'<pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse">'
        f'<rect x="3.5" y="3.5" width="1" height="1" fill="{theme.faint}"/></pattern>'
    )


def stamp_block(x: float, y: float, w: float, h: float, label: str, theme: Theme) -> str:
    """Hatched texture block with a hard rule on top and a mono label in a paper box."""
    from . import fonts  # local import keeps design.py free of font loading at import time
    lw = fonts.width("m", label, 10, 1.6) + 1.6 + 32
    return (f'<rect x="{num(x + 1)}" y="{num(y)}" width="{num(w - 1)}" height="{num(h - 1)}" fill="url(#hatch)" '
            f'opacity="{.5 if theme.dark else .35}"/>'
            + hline(x, x + w, y, theme.ink)
            + f'<rect x="{num(x + 32.5)}" y="{num(y + h - 64.5)}" width="{num(lw)}" height="32" fill="{theme.paper}" '
              f'stroke="{theme.ink}"/>'
            + text(x + 48, y + h - 44, label, "m", fill=theme.ink, size=10, letter_spacing="1.6"))


def corner_marks(x: float, y: float, w: float, h: float, color: str, size: float = 8) -> str:
    """Print registration ticks in the four corners of a region."""
    out = []
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        out.append(f'<path d="M{num(cx)} {num(cy + dy * size)}V{num(cy)}H{num(cx + dx * size)}" stroke="{color}"/>')
    return "".join(out)


# Motion vocabulary: mechanical, no fades-from-glow. Everything ends on a crisp frame.
CSS = """
.rule{shape-rendering:crispEdges}
.rise{animation:rise .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box}
@keyframes rise{from{transform:translateY(105%)}}
.slide{animation:slide .6s cubic-bezier(.2,.8,.2,1) both}
@keyframes slide{from{opacity:0;transform:translateX(16px)}}
.lift{animation:lift .6s cubic-bezier(.2,.8,.2,1) both}
@keyframes lift{from{opacity:0;transform:translateY(8px)}}
.on{animation:on .1s steps(1,start) both}
@keyframes on{from{opacity:0}}
.wipe{animation:wipe .7s cubic-bezier(.7,0,.3,1) both;transform-box:fill-box;transform-origin:left}
@keyframes wipe{from{transform:scaleX(0)}}
.blip{animation:blip 1s steps(1,end) infinite}
@keyframes blip{50%{opacity:0}}
"""
