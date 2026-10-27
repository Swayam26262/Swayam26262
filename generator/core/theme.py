"""Dark and light palettes. Every card is rendered once per theme and the
README picks one with <picture> + prefers-color-scheme."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    page: str        # GitHub's own page background (for previews only)
    panel: str       # card background
    panel2: str      # raised surfaces inside cards
    border: str
    border2: str
    text: str
    muted: str
    faint: str
    cyan: str
    indigo: str
    violet: str
    pink: str
    green: str
    amber: str
    red: str
    blue: str
    glow: float      # opacity multiplier for glows/auroras
    shadow: bool     # light cards get a soft drop shadow

    @property
    def grad(self) -> tuple[str, str, str]:
        return (self.cyan, self.indigo, self.pink)

    @property
    def dark(self) -> bool:
        return self.name == "dark"


DARK = Theme(
    name="dark", page="#0d1117", panel="#0a1020", panel2="#111a30",
    border="#1c2846", border2="#2b3b63", text="#e6edf3", muted="#94a3c0", faint="#5d6d8f",
    cyan="#22d3ee", indigo="#818cf8", violet="#a78bfa", pink="#f472b6",
    green="#34d399", amber="#fbbf24", red="#f87171", blue="#60a5fa",
    glow=1.0, shadow=False,
)

LIGHT = Theme(
    name="light", page="#ffffff", panel="#fbfcff", panel2="#f1f4fd",
    border="#dfe5f2", border2="#c7d2fe", text="#0f172a", muted="#475569", faint="#94a3b8",
    cyan="#0891b2", indigo="#4f46e5", violet="#7c3aed", pink="#db2777",
    green="#059669", amber="#d97706", red="#dc2626", blue="#2563eb",
    glow=0.55, shadow=True,
)

THEMES = (DARK, LIGHT)


def mix(a: str, b: str, t: float) -> str:
    """Linear blend of two #rrggbb colors."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def luminance(c: str) -> float:
    def ch(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable(color: str, bg: str, fallback: str, minimum: float = 2.6) -> str:
    """Nudge a brand color towards the fallback until it stands out on `bg`.

    Keeps the hue where possible (Supabase green just gets deeper on white),
    and ends at the fallback for colors like Next.js black on a dark panel.
    """
    for step in range(11):
        candidate = mix(color, fallback, step / 10)
        if contrast(candidate, bg) >= minimum:
            return candidate
    return fallback
