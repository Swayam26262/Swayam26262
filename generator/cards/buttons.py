"""Rectangular contact buttons: hard 1px border, solid offset block, mono label.
The first button is the primary action and is filled with the accent."""

from __future__ import annotations

import math

from core import fonts
from core.design import CSS as BASE, SHADOW, box
from core.svg import document, text
from core.theme import Theme

H = 40 + SHADOW
SIZE, LS = 11, 1.6
MOBILE = False  # small enough to reuse on phones

CSS = BASE + """
.nudge{animation:nudge 2.4s cubic-bezier(.7,0,.3,1) infinite}
@keyframes nudge{0%,60%,100%{transform:translate(0,0)}70%,90%{transform:translate(2px,-2px)}}
"""


def button(spec: dict, theme: Theme, primary: bool) -> str:
    label = spec["label"].upper()
    label_w = fonts.width("mb", label, SIZE, LS) + LS
    arrow_w = fonts.width("m", "↗", SIZE + 2)
    inner = 16 + label_w + 8 + arrow_w + 16
    w = math.ceil(inner / 8) * 8
    fill = theme.accent if primary else theme.paper
    ink = theme.on_accent if primary else theme.ink
    shadow = theme.ink if primary or not theme.dark else theme.accent
    body = (
        f'<rect x="{SHADOW}" y="{SHADOW}" width="{w}" height="40" fill="{shadow}"/>'
        + box(0, 0, w, 40, theme.ink, fill)
        + text(16, 25, label, "mb", fill=ink, size=SIZE, letter_spacing=LS)
        + f'<g class="nudge">{text(w - 16, 26, "↗", "m", fill=ink, size=SIZE + 2, anchor="end")}</g>'
    )
    return document(body, w + SHADOW, H, title=spec["label"], desc=f"{spec['label']}: {spec['url']}", css=CSS)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None, mobile: bool = False) -> dict[str, str]:
    return {f"btn-{b['slug']}": button(b, theme, i == 0) for i, b in enumerate(profile["buttons"])}
