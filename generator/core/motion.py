"""Animation helpers that need SMIL (typing effects) plus small CSS snippets.

Typing is done by growing a clip rectangle one character at a time with
discrete SMIL keyframes. SMIL runs inside <img> SVGs in every major browser,
including inside <clipPath>, which CSS animations can't be trusted to do.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .svg import esc, num


@dataclass
class Timeline:
    """Collects (time, value) steps and renders a discrete SMIL <animate>."""
    steps: list[tuple[float, float]] = field(default_factory=list)

    def at(self, t: float, value: float) -> None:
        self.steps.append((t, value))

    def animate(self, attr: str, total: float, *, repeat: bool = True) -> str:
        steps = sorted(self.steps)
        if not steps or steps[0][0] > 0:
            steps.insert(0, (0.0, steps[0][1] if steps else 0.0))
        times, values, last = [], [], -1.0
        for t, v in steps:
            kt = round(min(t / total, 1.0), 5)
            if kt <= last:            # keyTimes must strictly increase
                values[-1] = v
                continue
            times.append(kt)
            values.append(v)
            last = kt
        key_times = ";".join(f"{t:g}" for t in times)
        vals = ";".join(num(v) for v in values)
        tail = 'repeatCount="indefinite"' if repeat else 'fill="freeze"'
        return (f'<animate attributeName="{attr}" dur="{num(total)}s" calcMode="discrete" '
                f'keyTimes="{key_times}" values="{vals}" {tail}/>')


@dataclass
class TypedLine:
    text: str
    x: float          # left edge of the text
    char_w: float     # advance width of one character (monospace)


def typing_cycle(lines: list[TypedLine], *, y: float, size: float, cls: str, fill: str,
                 cursor_fill: str, uid: str, type_dt: float = 0.055, delete_dt: float = 0.022,
                 hold: float = 2.2, gap: float = 0.35, lead: float = 0.4) -> tuple[str, str]:
    """Type, hold and delete each line in turn, forever. Returns (defs, body)."""
    t = lead
    clips, cursor = [], Timeline()
    plans = []
    for i, line in enumerate(lines):
        width = Timeline()
        width.at(0, 0)
        cursor.at(t, line.x)
        for k in range(1, len(line.text) + 1):
            t += type_dt
            width.at(t, k * line.char_w)
            cursor.at(t, line.x + k * line.char_w)
        t += hold
        for k in range(len(line.text) - 1, -1, -1):
            t += delete_dt
            width.at(t, k * line.char_w)
            cursor.at(t, line.x + k * line.char_w)
        t += gap
        plans.append((i, line, width))
    total = t
    body = []
    for i, line, width in plans:
        clips.append(
            f'<clipPath id="{uid}{i}"><rect x="{num(line.x)}" y="{num(y - size * 1.1)}" width="0" '
            f'height="{num(size * 1.6)}">{width.animate("width", total)}</rect></clipPath>'
        )
        body.append(
            f'<text x="{num(line.x)}" y="{num(y)}" class="{cls}" font-size="{num(size)}" fill="{fill}" '
            f'clip-path="url(#{uid}{i})">{esc(line.text)}</text>'
        )
    cw = lines[0].char_w
    body.append(
        f'<rect class="blink" x="{num(lines[0].x)}" y="{num(y - size * 0.82)}" width="{num(max(2.0, cw * 0.18))}" '
        f'height="{num(size * 1.02)}" rx="1" fill="{cursor_fill}">{cursor.animate("x", total)}</rect>'
    )
    return "".join(clips), "".join(body)


BLINK_CSS = ".blink{animation:blink 1.06s steps(1,end) infinite}@keyframes blink{50%{opacity:0}}"
