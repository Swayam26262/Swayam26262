"""Brand marks (Simple Icons / skill-icons) and generic glyphs from data/icons.json,
always drawn in a single flat color so they sit inside the palette."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .svg import num

ICONS = Path(__file__).resolve().parent.parent / "data" / "icons.json"


@lru_cache(maxsize=None)
def _all() -> dict:
    return json.loads(ICONS.read_text())


def icon(slug: str, x: float, y: float, size: float, color: str, *, stroke_width: float = 1.6) -> str:
    """Render icon `slug` with its top-left corner at (x, y), `size` px square."""
    data = _all()[slug]
    scale = size / data["viewBox"]
    parts = []
    for p in data["paths"]:
        if p.get("stroke"):
            parts.append(f'<path d="{p["d"]}" stroke="{color}" stroke-width="{num(stroke_width / scale)}" '
                         f'stroke-linecap="square" stroke-linejoin="miter" fill="none"/>')
        else:
            rule = f' fill-rule="{p["rule"]}"' if p.get("rule") else ""
            parts.append(f'<path d="{p["d"]}" fill="{color}"{rule}/>')
    return f'<g transform="translate({num(x)} {num(y)}) scale({num(scale)})">{"".join(parts)}</g>'


def title(slug: str) -> str:
    return _all()[slug]["title"]
