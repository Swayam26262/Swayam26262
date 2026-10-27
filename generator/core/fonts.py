"""Font loading, text measurement, per-SVG subsetting and text-to-path.

An SVG rendered through <img> (which is how GitHub shows README images) can't
load web fonts, so every SVG carries its own base64 WOFF2 subset containing
exactly the glyphs it uses.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"


@dataclass(frozen=True)
class FontSpec:
    css_class: str
    file: str
    family: str
    weight: int
    fallback: str


MONO_FALLBACK = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS_FALLBACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# CSS class -> font. Classes are short because they repeat a lot in the markup.
SPECS = {
    "m": FontSpec("m", "JetBrainsMono-Regular.ttf", "spm", 400, MONO_FALLBACK),
    "mb": FontSpec("mb", "JetBrainsMono-Bold.ttf", "spm", 700, MONO_FALLBACK),
    "d": FontSpec("d", "SpaceGrotesk-Bold.ttf", "spd", 700, SANS_FALLBACK),
    "dm": FontSpec("dm", "SpaceGrotesk-Medium.ttf", "spd", 500, SANS_FALLBACK),
    "s": FontSpec("s", "Inter-Regular.ttf", "sps", 400, SANS_FALLBACK),
    "sm": FontSpec("sm", "Inter-Medium.ttf", "sps", 500, SANS_FALLBACK),
    "sb": FontSpec("sb", "Inter-SemiBold.ttf", "sps", 600, SANS_FALLBACK),
    "u": FontSpec("u", "Unbounded-ExtraBold.ttf", "spu", 800, SANS_FALLBACK),
}


class Font:
    def __init__(self, spec: FontSpec):
        self.spec = spec
        self.tt = TTFont(FONT_DIR / spec.file)
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.metrics = self.tt["hmtx"].metrics
        self.glyphs = self.tt.getGlyphSet()

    def advance(self, ch: str) -> int:
        name = self.cmap.get(ord(ch))
        return self.metrics[name][0] if name else self.upm // 2

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Advance width in px. Kerning is ignored: good to a pixel or two."""
        if not text:
            return 0.0
        return sum(self.advance(c) for c in text) * size / self.upm + tracking * (len(text) - 1)

    def path(self, text: str, x: float, y: float, size: float, tracking: float = 0.0) -> str:
        """Outline `text` as an SVG path with its baseline starting at (x, y)."""
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        cx = x
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name is None:
                continue
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
            cx += self.metrics[name][0] * scale + tracking
        return pen.getCommands()

    def woff2_base64(self, text: str) -> str:
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "tnum"]
        opts.name_IDs = []
        opts.notdef_outline = True
        opts.hinting = False
        font = TTFont(FONT_DIR / self.spec.file)
        sub = subset.Subsetter(opts)
        sub.populate(text=text + " ")
        sub.subset(font)
        font.flavor = "woff2"
        buf = io.BytesIO()
        font.save(buf)
        return base64.b64encode(buf.getvalue()).decode("ascii")


@lru_cache(maxsize=None)
def font(css_class: str) -> Font:
    return Font(SPECS[css_class])


def width(css_class: str, text: str, size: float, tracking: float = 0.0) -> float:
    return font(css_class).width(text, size, tracking)


def font_face_css(css_class: str, text: str) -> str:
    spec = SPECS[css_class]
    data = font(css_class).woff2_base64(text)
    return (
        f"@font-face{{font-family:{spec.family}{css_class};font-weight:{spec.weight};"
        f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
        f".{css_class}{{font-family:{spec.family}{css_class},{spec.fallback};font-weight:{spec.weight}}}"
    )
