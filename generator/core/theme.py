"""Flat palettes: paper, ink, a signal orange and a quiet teal. No gradients.

Every card is rendered once per theme and the README picks one with
<picture> + prefers-color-scheme. All text colors clear WCAG AA (4.5:1) on the
surface they are used on; the bright `accent` is kept for large type and
graphics, `accent_text` for small orange text.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    page: str         # GitHub's own page background (previews only)
    paper: str        # sheet background
    paper2: str       # alternate cell fill
    ink: str          # text, hard 1px borders
    muted: str        # secondary text
    faint: str        # tertiary text
    hair: str         # secondary hairlines
    accent: str       # signal orange: large type, fills, graphics
    on_accent: str    # text on accent fills
    shadow: str       # solid offset block shadow
    accent_text: str  # small orange text on paper
    accent_inv: str   # small orange text on ink-filled surfaces
    teal: str         # secondary accent (applied AI, secondary categories) on paper
    teal_inv: str     # teal on ink-filled surfaces
    soft_inv: str     # secondary text on ink-filled surfaces

    @property
    def dark(self) -> bool:
        return self.name == "dark"


LIGHT = Theme(
    name="light", page="#ffffff", paper="#f2eee6", paper2="#e7e1d5",
    ink="#121212", muted="#46423c", faint="#615c54", hair="#cbc4b6",
    accent="#ec4511", on_accent="#121212", shadow="#121212",
    accent_text="#b0350a", accent_inv="#ec4511", teal="#1d6f63", teal_inv="#67c1b2", soft_inv="#b9b3a8",
)

DARK = Theme(
    name="dark", page="#0d1117", paper="#121212", paper2="#1b1b1b",
    ink="#eeeae2", muted="#c4beb3", faint="#9b9589", hair="#35332f",
    accent="#ff5c26", on_accent="#121212", shadow="#ff5c26",
    accent_text="#ff5c26", accent_inv="#b0350a", teal="#67c1b2", teal_inv="#1d6f63", soft_inv="#4a463f",
)

THEMES = (DARK, LIGHT)


def mix(a: str, b: str, t: float) -> str:
    """Linear blend of two #rrggbb colors (used to derive flat tints, never gradients)."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))
