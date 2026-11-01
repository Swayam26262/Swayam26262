"""Flat palettes: paper, ink and one signal accent. No gradients anywhere.

Every card is rendered once per theme and the README picks one with
<picture> + prefers-color-scheme.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    page: str        # GitHub's own page background (previews only)
    paper: str       # card background
    paper2: str      # alternate cell fill
    ink: str         # text, hard 1px borders
    muted: str       # secondary text
    faint: str       # tertiary text, ticks
    hair: str        # secondary hairlines
    accent: str      # signal orange
    on_accent: str   # text on accent fills
    shadow: str      # solid offset block shadow

    @property
    def dark(self) -> bool:
        return self.name == "dark"


LIGHT = Theme(
    name="light", page="#ffffff", paper="#f2eee6", paper2="#e7e1d5",
    ink="#121212", muted="#57534c", faint="#8a8478", hair="#cbc4b6",
    accent="#ff4d1a", on_accent="#121212", shadow="#121212",
)

DARK = Theme(
    name="dark", page="#0d1117", paper="#121212", paper2="#1b1b1b",
    ink="#eeeae2", muted="#a8a297", faint="#716c63", hair="#35332f",
    accent="#ff5c26", on_accent="#121212", shadow="#ff5c26",
)

THEMES = (DARK, LIGHT)


def mix(a: str, b: str, t: float) -> str:
    """Linear blend of two #rrggbb colors (used to derive flat tints, never gradients)."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))
