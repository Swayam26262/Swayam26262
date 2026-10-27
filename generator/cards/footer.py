"""Closing banner that mirrors the hero: soft aurora, a gradient sign-off and
three layers of waves rolling along the bottom edge."""

from __future__ import annotations

import math

from core import fonts
from core.svg import document, num, text
from core.theme import Theme

W, H = 840, 210

CSS = """
.wv{animation:wv linear infinite}
@keyframes wv{to{transform:translateX(-840px)}}
.au{animation:au 16s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
@keyframes au{to{transform:translate(30px,-10px) scale(1.1)}}
.fi{animation:fi 1s ease-out both}
@keyframes fi{from{opacity:0;transform:translateY(8px)}}
.hb{animation:hb 1.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes hb{0%,40%,100%{transform:scale(1)}20%{transform:scale(1.25)}}
"""


def wave(y: float, amp: float, length: float, phase: float) -> str:
    """A sine wave two canvases wide, closed down to the bottom edge."""
    pts = []
    x = -10.0
    while x <= 2 * W + 10:
        pts.append(f"{num(x)} {num(y + amp * math.sin(2 * math.pi * x / length + phase))}")
        x += 12
    return f"M{pts[0]}L{'L'.join(pts[1:])}V{H}H-10Z"


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> str:
    foot = profile["footer"]
    g = theme.grad
    bg = ("#060a18", "#0a1230") if theme.dark else ("#ffffff", "#f3f5ff")
    hw = fonts.width("d", foot["headline"], 26)
    defs = (
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg[0]}"/>'
        f'<stop offset="1" stop-color="{bg[1]}"/></linearGradient>'
        f'<linearGradient id="hg" gradientUnits="userSpaceOnUse" x1="{num((W - hw) / 2)}" x2="{num((W + hw) / 2)}" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{g[0]}"/><stop offset=".5" stop-color="{g[1]}"/><stop offset="1" stop-color="{g[2]}"/>'
        f'</linearGradient>'
        f'<radialGradient id="a"><stop offset="0" stop-color="{theme.indigo}" stop-opacity="{.45 * theme.glow}"/>'
        f'<stop offset="1" stop-color="{theme.indigo}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="p"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
    )
    layers = [  # color, baseline, amplitude, wavelength, phase, seconds per loop, opacity
        (g[0], H - 46, 7, 420, 0, 22, .22),
        (g[1], H - 34, 9, 280, 1.3, 15, .28),
        (g[2], H - 22, 6, 210, 2.1, 10, .32),
    ]
    waves = "".join(
        f'<path class="wv" d="{wave(y, a, ln, ph)}" fill="{c}" fill-opacity="{num(op * (1 if theme.dark else .8))}" '
        f'style="animation-duration:{s}s"/>' for c, y, a, ln, ph, s, op in layers
    )
    heart_x = W / 2 - fonts.width("m", foot["note"], 10, .8) / 2 - 16
    body = (
        f'<g clip-path="url(#p)"><rect width="{W}" height="{H}" fill="url(#bg)"/>'
        f'<ellipse class="au" cx="{W / 2}" cy="40" rx="320" ry="120" fill="url(#a)"/>{waves}</g>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" stroke="{theme.border}"/>'
        f'<g class="fi" style="animation-delay:.2s">'
        + text(W / 2, 64, foot["headline"], "d", fill="url(#hg)", size=26, anchor="middle")
        + "</g>"
        + f'<g class="fi" style="animation-delay:.5s">'
        + text(W / 2, 94, foot["line"], "s", fill=theme.muted, size=14, anchor="middle")
        + "</g>"
        + f'<g class="fi" style="animation-delay:.8s">'
        + f'<path class="hb" d="M{num(heart_x)} {H - 77}c-2-3-7-2.5-7 1.5 0 3 4 5.5 7 8 3-2.5 7-5 7-8 0-4-5-4.5-7-1.5Z" '
          f'fill="{theme.pink}"/>'
        + text(W / 2 + 8, H - 70, foot["note"], "m", fill=theme.faint if theme.dark else theme.muted, size=10,
               anchor="middle", letter_spacing=".8")
        + "</g>"
    )
    return document(body, W, H, title=foot["headline"], desc=f"{foot['line']} {foot['note']}", css=CSS, defs=defs)
