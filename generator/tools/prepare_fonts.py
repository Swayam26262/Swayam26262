"""Build the static, pre-subset font files committed under generator/fonts/.

The generator embeds fonts into every SVG (an SVG loaded through <img> cannot
fetch web fonts), so we keep small static instances here and subset them again
per SVG at build time.

Sources (all SIL Open Font License 1.1):
  JetBrains Mono  https://github.com/JetBrains/JetBrainsMono   fonts/ttf/*.ttf
  Space Grotesk   https://github.com/google/fonts             ofl/spacegrotesk/SpaceGrotesk[wght].ttf
  Inter           https://github.com/google/fonts             ofl/inter/Inter[opsz,wght].ttf
  Unbounded       https://github.com/google/fonts             ofl/unbounded/Unbounded[wght].ttf

Usage: python generator/tools/prepare_fonts.py <dir-with-downloaded-sources>
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

OUT = Path(__file__).resolve().parent.parent / "fonts"

LATIN = [
    (0x20, 0x7E),      # Basic Latin
    (0xA0, 0xFF),      # Latin-1 Supplement
    (0x2010, 0x2027),  # dashes, quotes, bullets, ellipsis
    (0x2030, 0x203A),
    (0x2190, 0x21FF),  # arrows
    (0x2212, 0x2212), (0x2248, 0x2248), (0x2260, 0x2265), (0x221E, 0x221E),
    (0x2713, 0x2717),  # check marks
    (0x2605, 0x2606),  # stars
]
MONO_EXTRA = [
    (0x2500, 0x259F),  # box drawing + block elements
    (0x25A0, 0x25FF),  # geometric shapes
    (0x2318, 0x2318), (0x23CE, 0x23CE),  # command, return
    (0x26A1, 0x26A1),  # high voltage
    (0x2770, 0x2777),  # heavy angle brackets (❯)
    (0x03BB, 0x03BB),  # lambda
    (0xE0A0, 0xE0B3),  # powerline
]

# (output name, source file, variable axes or None, extra ranges)
FONTS = [
    ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Regular.ttf", None, MONO_EXTRA),
    ("JetBrainsMono-Bold.ttf", "JetBrainsMono-Bold.ttf", None, MONO_EXTRA),
    ("SpaceGrotesk-Medium.ttf", "SpaceGrotesk-VF.ttf", {"wght": 500}, []),
    ("SpaceGrotesk-Bold.ttf", "SpaceGrotesk-VF.ttf", {"wght": 700}, []),
    ("Inter-Regular.ttf", "Inter-VF.ttf", {"wght": 400, "opsz": 14}, []),
    ("Inter-Medium.ttf", "Inter-VF.ttf", {"wght": 500, "opsz": 14}, []),
    ("Inter-SemiBold.ttf", "Inter-VF.ttf", {"wght": 600, "opsz": 14}, []),
    ("Unbounded-ExtraBold.ttf", "Unbounded-VF.ttf", {"wght": 800}, []),
]

LICENSES = {
    "OFL-JetBrainsMono.txt": "JetBrainsMono-OFL.txt",
    "OFL-SpaceGrotesk.txt": "SpaceGrotesk-OFL.txt",
    "OFL-Inter.txt": "Inter-OFL.txt",
    "OFL-Unbounded.txt": "Unbounded-OFL.txt",
}


def unicodes(ranges):
    return sorted({cp for lo, hi in ranges for cp in range(lo, hi + 1)})


def build(src: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for out_name, src_name, axes, extra in FONTS:
        font = TTFont(src / src_name)
        if axes and "fvar" in font:
            pinned = {a.axisTag: axes.get(a.axisTag, a.defaultValue) for a in font["fvar"].axes}
            font = instancer.instantiateVariableFont(font, pinned, updateFontNames=False)
        opts = subset.Options()
        opts.layout_features = ["kern", "liga", "calt", "tnum"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = False
        opts.hinting = False
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=unicodes(LATIN + extra))
        sub.subset(font)
        font.flavor = None
        font.save(OUT / out_name)
        print(f"{out_name:28} {len(font.getGlyphOrder()):5} glyphs  {(OUT / out_name).stat().st_size / 1024:6.1f} KB")
    for out_name, src_name in LICENSES.items():
        (OUT / out_name).write_text((src / src_name).read_text())


if __name__ == "__main__":
    build(Path(sys.argv[1]))
