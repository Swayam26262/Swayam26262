"""Brand icons (Simple Icons / skill-icons) and generic glyphs from data/icons.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .svg import num
from .theme import Theme, readable

ICONS = Path(__file__).resolve().parent.parent / "data" / "icons.json"


@lru_cache(maxsize=None)
def _all() -> dict:
    return json.loads(ICONS.read_text())


def brand_color(slug: str, theme: Theme, bg: str | None = None) -> str:
    icon = _all()[slug]
    if not icon.get("hex"):
        return theme.text
    return readable("#" + icon["hex"], bg or theme.panel, theme.text)


def icon(slug: str, x: float, y: float, size: float, theme: Theme, *, color: str | None = None,
         bg: str | None = None, stroke_width: float = 1.8, extra: str = "") -> str:
    """Render icon `slug` with its top-left corner at (x, y), `size` px square."""
    data = _all()[slug]
    scale = size / data["viewBox"]
    tint = color or brand_color(slug, theme, bg)
    parts = []
    for p in data["paths"]:
        if p.get("stroke"):
            parts.append(
                f'<path d="{p["d"]}" stroke="{tint}" stroke-width="{num(stroke_width / scale)}" '
                f'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            )
            continue
        fill = p["fill"]
        if fill == "brand":
            fill = tint
        elif fill == "text":
            fill = color or theme.text
        rule = f' fill-rule="{p["rule"]}"' if p.get("rule") else ""
        parts.append(f'<path d="{p["d"]}" fill="{fill}"{rule}/>')
    return (f'<g transform="translate({num(x)} {num(y)}) scale({num(scale)})"{" " + extra if extra else ""}>'
            f'{"".join(parts)}</g>')


def title(slug: str) -> str:
    return _all()[slug]["title"]
