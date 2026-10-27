"""Render every README artwork into assets/.

  python generator/build.py              # render everything from cached live data
  python generator/build.py --live       # refresh GitHub/LeetCode data first (GITHUB_TOKEN for GitHub)
  python generator/build.py hero stack   # just these cards
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import live as live_data  # noqa: E402
from cards import buttons, footer, hero, impact, journey, projects, stack, telemetry, terminal  # noqa: E402
from core.svg import write  # noqa: E402
from core.theme import THEMES  # noqa: E402

ROOT = HERE.parent
ASSETS = ROOT / "assets"

CARDS = {
    "hero": hero.render,
    "terminal": terminal.render,
    "telemetry": telemetry.render,
    "impact": impact.render,
    "journey": journey.render,
    "stack": stack.render,
    "projects": projects.render,
    "buttons": buttons.render,
    "footer": footer.render,
}


def load_profile() -> dict:
    return tomllib.loads((HERE / "profile.toml").read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", nargs="*", help="only build these cards")
    ap.add_argument("--live", action="store_true", help="refresh live GitHub/LeetCode data before rendering")
    ap.add_argument("--data", type=Path, help="render from this live-data JSON instead of the cache")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="pretend today is this date (previews/tests)")
    args = ap.parse_args(argv)

    profile = load_profile()
    if args.data:
        data = json.loads(args.data.read_text())
    elif args.live:
        data = live_data.refresh(profile)
    else:
        data = live_data.load()
    today = args.today or dt.datetime.now(dt.timezone.utc).date()

    unknown = set(args.cards) - set(CARDS)
    if unknown:
        ap.error(f"unknown card(s): {', '.join(sorted(unknown))}")
    changed = 0
    for name, render in CARDS.items():
        if args.cards and name not in args.cards:
            continue
        for theme in THEMES:
            result = render(profile, theme, data, today)
            # a card renders one SVG, or a {file stem: svg} dict for families like project cards
            outputs = result if isinstance(result, dict) else {name: result}
            for stem, svg in outputs.items():
                out = ASSETS / f"{stem}-{theme.name}.svg"
                if write(out, svg):
                    changed += 1
                    print(f"updated {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.1f} KB)")
    print(f"{changed} file(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
