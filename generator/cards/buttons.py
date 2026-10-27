"""Contact buttons. Same width so the row lines up; a glint runs across them
one after another."""

from __future__ import annotations

from core import fonts
from core.icons import brand_color, icon
from core.svg import document, num, text
from core.theme import Theme

H, ICON, FS = 44, 18, 13.5

CSS = """
.gl{animation:gl 7s cubic-bezier(.5,0,.5,1) infinite}
@keyframes gl{0%{transform:translateX(0)}22%,100%{transform:translateX(260px)}}
"""


def button(spec: dict, theme: Theme, width: float, index: int) -> str:
    fill = theme.panel2 if theme.dark else "#ffffff"
    color = getattr(theme, spec["color"]) if spec.get("color") else brand_color(spec["icon"], theme, fill)
    label_w = fonts.width("sb", spec["label"], FS)
    content_w = ICON + 9 + label_w
    x = (width - content_w) / 2 - 6
    defs = (
        f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity="{.18 if theme.dark else .8}"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="u" x1="0" x2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="c"><rect width="{num(width)}" height="{H}" rx="12"/></clipPath>'
    )
    body = (
        f'<rect x=".5" y=".5" width="{num(width - 1)}" height="{H - 1}" rx="11.5" fill="{fill}" stroke="{theme.border2}"/>'
        f'<rect x="{num(width * .2)}" y="{H - 2}" width="{num(width * .6)}" height="1.5" fill="url(#u)"/>'
        + icon(spec["icon"], x, (H - ICON) / 2, ICON, theme, color=color, bg=fill, stroke_width=1.9)
        + text(x + ICON + 9, H / 2 + 4.7, spec["label"], "sb", fill=theme.text, size=FS)
        + icon("glyph:arrow", width - 22, H / 2 - 5, 10, theme, color=theme.faint, stroke_width=2.4)
        + f'<g clip-path="url(#c)"><g transform="skewX(-20)"><rect class="gl" x="-90" y="0" width="60" height="{H}" '
          f'fill="url(#g)" style="animation-delay:{1.5 + index * .35:.2f}s"/></g></g>'
    )
    return document(body, width, H, title=spec["label"], desc=f"{spec['label']}: {spec['url']}", css=CSS, defs=defs)


def render(profile: dict, theme: Theme, live: dict | None = None, today=None) -> dict[str, str]:
    specs = profile["buttons"]
    width = max(ICON + 9 + fonts.width("sb", b["label"], FS) for b in specs) + 56
    return {f"btn-{b['slug']}": button(b, theme, width, i) for i, b in enumerate(specs)}
