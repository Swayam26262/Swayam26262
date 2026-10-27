"""Collect the brand icons used by the generator into generator/data/icons.json.

Brand marks come from Simple Icons (CC0-1.0, https://simpleicons.org). A few
brands Simple Icons no longer ships (LinkedIn, AWS) come from skill-icons
(MIT, https://github.com/tandpfun/skill-icons). Generic glyphs (database,
sparkle, ...) are drawn here.

Usage:
  npm pack simple-icons && tar xzf simple-icons-*.tgz        # -> ./package
  curl -O https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/LinkedIn.svg
  curl -O https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/AWS-Dark.svg
  python generator/tools/extract_icons.py ./package ./dir-with-skill-icons
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "icons.json"

SIMPLE_ICONS = [
    "typescript", "javascript", "python", "html5", "css",
    "react", "nextdotjs", "tailwindcss", "vite",
    "nodedotjs", "express", "django", "fastapi", "socketdotio", "jsonwebtokens",
    "mongodb", "postgresql", "redis", "supabase",
    "googlegemini", "pytorch", "tensorflow", "opencv", "scikitlearn", "streamlit",
    "docker", "nginx", "vercel", "githubactions", "git", "jest", "puppeteer",
    "sonarqubeserver", "postman",
    "github", "gmail", "leetcode", "googledrive",
]

# Generic glyphs on a 24x24 grid, drawn as strokes (rendered with stroke=currentColor).
GLYPHS = {
    "database": "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3Zm0 0v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
    "sparkle": "M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Zm6 11 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z",
    "queue": "M4 5h16M4 10h16M4 15h10M4 20h6M18 15l3 3-3 3",
    "mic": "M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Zm-7 9a7 7 0 0 0 14 0M12 19v3M8 22h8",
    "vector": "M5 6a2 2 0 1 0 0-.01M19 6a2 2 0 1 0 0-.01M12 19a2 2 0 1 0 0-.01M6.7 7.2l4.2 9.8M17.3 7.2l-4.2 9.8M7 6h10",
    "browser": "M3 5h18v14H3zM3 9h18M6 7h.01M8.5 7h.01M9 14l2 2 4-4",
    "globe": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-9 9h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3Z",
    "file": "M14 3H6v18h12V7l-4-4Zm0 0v4h4M9 13h6M9 17h6M9 9h2",
    "eye": "M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
    "pin": "M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Zm0-14a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z",
    "briefcase": "M4 8h16v11H4zM9 8V5h6v3M4 13h16",
    "cap": "M2 9l10-5 10 5-10 5L2 9Zm4 2.5V16c0 1.5 2.7 3 6 3s6-1.5 6-3v-4.5M22 9v5",
    "bolt": "M13 2 4 14h7l-1 8 9-12h-7l1-8Z",
    "code": "M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16",
    "game": "M6 9h4M8 7v4M15 10h.01M18 8h.01M7 5h10a5 5 0 0 1 4.6 7l-1.4 3.4a2.8 2.8 0 0 1-4.7.6L14 14h-4l-1.5 2a2.8 2.8 0 0 1-4.7-.6L2.4 12A5 5 0 0 1 7 5Z",
    "chart": "M4 20V10M10 20V4M16 20v-7M22 20H2",
    "rocket": "M5 15c-1.5 1.3-2 5-2 5s3.7-.5 5-2M9 12a22 22 0 0 1 9-9c2 0 3 1 3 3a22 22 0 0 1-9 9M9 12l3 3M9 12H5l2-4h5M12 15v4l4-2v-5",
    "heart": "M12 20s-8-4.6-8-10.5A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 8 2.5C20 15.4 12 20 12 20Z",
    "mail": "M3 5h18v14H3zM3 6l9 7 9-7",
    "terminal": "M4 17l6-5-6-5M12 19h8",
    "chat": "M4 5h16v11H9l-5 4V5Zm4 5h.01M12 10h.01M16 10h.01",
    "pen": "M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4Zm9-13 4 4",
    "play": "M4 5h16v14H4zM10 9v6l5-3-5-3Z",
    "film": "M4 4h16v16H4zM8 4v16M16 4v16M4 8h4M4 12h4M4 16h4M16 8h4M16 12h4M16 16h4",
    "link": "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
    "arrow": "M7 17 17 7M9 7h8v8",
}

# Skill-icons files: keep the logo paths, drop the rounded background tile.
SKILL_ICONS = {
    "linkedin": ("LinkedIn.svg", "LinkedIn", "0A66C2", "brand"),
    "aws": ("AWS-Dark.svg", "AWS", "FF9900", "text"),
}


def simple_icon(pkg: Path, slug: str, meta: dict) -> dict:
    svg = (pkg / "icons" / f"{slug}.svg").read_text()
    d = re.search(r'<path d="([^"]+)"', svg).group(1)
    info = meta[slug]
    return {"title": info["title"], "hex": info["hex"], "viewBox": 24,
            "paths": [{"d": d, "fill": "brand"}], "source": "simple-icons"}


def skill_icon(path: Path, title: str, hex_: str, default_fill: str) -> dict:
    svg = path.read_text()
    paths = []
    for attrs in re.findall(r"<path([^>]*)/>", svg):
        d = re.search(r'\sd="([^"]+)"', attrs).group(1)
        fill = re.search(r'fill="([^"]+)"', attrs)
        fill = fill.group(1) if fill else "#fff"
        rule = re.search(r'fill-rule="([^"]+)"', attrs)
        # white parts of the mark follow the theme ("text"); colored parts keep their hex
        if fill.lower() in ("#fff", "#ffffff", "white"):
            fill = default_fill
        entry = {"d": d, "fill": fill}
        if rule:
            entry["rule"] = rule.group(1)
        paths.append(entry)
    return {"title": title, "hex": hex_, "viewBox": 256, "paths": paths, "source": "skill-icons"}


def main(pkg: Path, skill_dir: Path) -> None:
    meta = {i["slug"]: i for i in json.loads((pkg / "data" / "simple-icons.json").read_text())}
    icons = {slug: simple_icon(pkg, slug, meta) for slug in SIMPLE_ICONS}
    for slug, (fname, title, hex_, fill) in SKILL_ICONS.items():
        icons[slug] = skill_icon(skill_dir / fname, title, hex_, fill)
    for slug, d in GLYPHS.items():
        icons[f"glyph:{slug}"] = {"title": slug, "hex": None, "viewBox": 24,
                                  "paths": [{"d": d, "stroke": True}], "source": "generator"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(icons, indent=1, sort_keys=True) + "\n")
    print(f"wrote {len(icons)} icons to {OUT}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
