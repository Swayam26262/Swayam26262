"""Tiny helpers for writing SVG by hand and wrapping it into a final document."""

from __future__ import annotations

import html
import re
from pathlib import Path

from . import fonts

BASE_CSS = (
    "text{font-kerning:normal}"
    # Respect reduced-motion users: CSS animations snap to their final frame.
    "@media (prefers-reduced-motion:reduce){*{animation-duration:0s!important;"
    "animation-delay:0s!important;animation-iteration-count:1!important}}"
)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def num(v: float) -> str:
    """Compact number formatting for attributes."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def attrs(**kw) -> str:
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        k = k.rstrip("_").replace("_", "-")
        out.append(f'{k}="{esc(num(v) if isinstance(v, float) else v)}"')
    return " ".join(out)


def text(x, y, content, cls, *, fill=None, size=None, anchor=None, extra="", raw=False, **kw) -> str:
    """A <text> element. `cls` must include one font class (see fonts.SPECS)."""
    body = content if raw else esc(content)
    a = attrs(x=float(x), y=float(y), class_=cls, fill=fill, font_size=size, text_anchor=anchor, **kw)
    return f"<text {a}{' ' + extra if extra else ''}>{body}</text>"


def fit(cls: str, content: str, size: float, max_width: float, tracking: float = 0.0, floor: float = 7.0) -> float:
    """Largest font size <= `size` at which `content` fits in `max_width`."""
    while size > floor and fonts.width(cls, content, size, tracking) > max_width:
        size -= .25
    return size


def wrap(cls: str, content: str, size: float, max_width: float) -> list[str]:
    """Greedy word wrap using real glyph advances."""
    lines, line = [], ""
    for word in content.split():
        trial = f"{line} {word}".strip()
        if line and fonts.width(cls, trial, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def balance(cls: str, content: str, size: float, max_width: float) -> list[str]:
    """One line if it fits, otherwise two lines of similar length (no lonely last word)."""
    if fonts.width(cls, content, size) <= max_width:
        return [content]
    words = content.split()
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        widest = max(fonts.width(cls, a, size), fonts.width(cls, b, size))
        if best is None or widest < best[0]:
            best = (widest, [a, b])
    return best[1] if best else [content]


_TEXT_RE = re.compile(r">([^<>]+)<")
_CLASS_RE = re.compile(r'class="([^"]+)"')


def used_text(markup: str) -> str:
    return "".join(html.unescape(t) for t in _TEXT_RE.findall(markup))


def used_font_classes(markup: str) -> list[str]:
    found = set()
    for cls in _CLASS_RE.findall(markup):
        found.update(c for c in cls.split() if c in fonts.SPECS)
    return sorted(found)


def document(body: str, width: float, height: float, *, title: str, desc: str = "", css: str = "",
             defs: str = "") -> str:
    """Wrap `body` into a standalone SVG with embedded font subsets."""
    chars = "".join(sorted(set(used_text(body))))
    faces = "".join(fonts.font_face_css(c, chars) for c in used_font_classes(body))
    w, h = num(width), num(height)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="svg-title svg-desc" fill="none">'
        f'<title id="svg-title">{esc(title)}</title><desc id="svg-desc">{esc(desc or title)}</desc>'
        f"<style>{faces}{BASE_CSS}{css}</style>"
        f"{f'<defs>{defs}</defs>' if defs else ''}"
        f"{body}</svg>\n"
    )


_FONT_DATA = re.compile(r"base64,[A-Za-z0-9+/=]+")


def write(path: Path, svg: str) -> bool:
    """Write only when content changed. Returns True if the file was updated.

    Embedded WOFF2 bytes differ between brotli builds even for identical glyphs,
    so font payloads are ignored when deciding whether anything changed (the
    glyph set itself is derived from the visible text, which is compared).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and _FONT_DATA.sub("", path.read_text()) == _FONT_DATA.sub("", svg):
        return False
    path.write_text(svg)
    return True
