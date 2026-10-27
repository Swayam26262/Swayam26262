"""Numbers whose digits roll into place like an odometer (pure CSS)."""

from __future__ import annotations

from . import fonts
from .svg import num, text

CSS = """
.odo{animation:odo 2.2s cubic-bezier(.12,.9,.22,1) both}
@keyframes odo{from{transform:translateY(0)}}
"""


def odometer(digits: str, x: float, base: float, size: float, color: str, delay: float,
             cls: str = "u") -> tuple[str, float]:
    """Digit columns starting at x on baseline `base`. Returns (markup, width).

    Wrap the result in a clip path covering one line box (about 1.25 * size tall)
    so only the landing digit stays visible.
    """
    face = fonts.font(cls)
    lh = size * 1.25
    out, cx = [], x
    for i, ch in enumerate(digits):
        if not ch.isdigit():  # separators like "," or "." don't roll
            out.append(text(cx, base, ch, cls, fill=color, size=size))
            cx += face.width(ch, size)
            continue
        col_w = face.width(ch, size)  # sized to the digit it lands on, so "12" isn't gappy
        spins = 10 + int(ch)
        strip = "".join(f'<tspan x="{num(cx + col_w / 2)}" y="{num(base + k * lh)}">{k % 10}</tspan>'
                        for k in range(spins + 1))
        out.append(
            f'<g class="odo" style="transform:translateY(-{num(spins * lh)}px);animation-delay:{delay + i * .12:.2f}s">'
            f'<text class="{cls}" font-size="{num(size)}" fill="{color}" text-anchor="middle">{strip}</text></g>'
        )
        cx += col_w
    return "".join(out), cx - x
