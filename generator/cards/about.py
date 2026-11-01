"""§01 about: a serif statement and short bio on the left, a flat console on
the right that types `neofetch` (with live GitHub/LeetCode numbers) and
`cat now.md`, then idles on a blinking block cursor."""

from __future__ import annotations

import calendar
import datetime as dt
import random
import re

from core import fonts
from core.design import CSS as BASE, W, card, patterns, stamp_block, strip, vline
from core.motion import BLINK_CSS, Timeline
from core.svg import document, esc, fit, num, text
from core.theme import Theme

SPLIT = 280               # left column width
FS, LH = 12, 24           # console type size and line height
CW = fonts.width("m", "M", FS)
IDENTICON = ["11011", "11111", "00100", "01110", "11111"]
MARKUP = re.compile(r"(\*\*.+?\*\*|`.+?`)")

CSS = BASE + BLINK_CSS


def uptime(since: dt.date, today: dt.date) -> str:
    months = (today.year - since.year) * 12 + today.month - since.month - (today.day < since.day)
    year, month = divmod(since.month - 1 + months, 12)
    year += since.year
    anchor = dt.date(year, month + 1, min(since.day, calendar.monthrange(year, month + 1)[1]))
    days = (today - anchor).days
    y, m = divmod(months, 12)
    parts = [f"{y} year{'s' * (y != 1)}"] if y else []
    parts.append(f"{m} month{'s' * (m != 1)}")
    parts.append(f"{days} day{'s' * (days != 1)}")
    return ", ".join(parts)


def neofetch_rows(profile: dict, live: dict, today: dt.date) -> list[tuple[str, str]]:
    rows = [tuple(r) for r in profile["about"]["neofetch"]]
    joined = dt.date.fromisoformat(profile["person"]["github_joined"])
    rows.append(("Uptime", f"{uptime(joined, today)} on GitHub"))
    gh = live.get("github")
    if gh:
        rows.append(("Repos", f"**{gh['public_repos']}** public / **{gh['stars']}** stars earned"))
        rows.append(("Commits", f"**{gh['commits_total']:,}** all-time / **{gh['commits_year']:,}** in {today.year}"))
        s = gh["streak"]
        if s["current"] >= 2:
            rows.append(("Streak", f"**{s['current']}** days running / best **{s['longest']}**"))
        else:
            rows.append(("Streak", f"best **{s['longest']}** days in a row"))
    lc = live.get("leetcode")
    if lc:
        sv = lc["solved"]
        rows.append(("LeetCode", f"**{sv.get('All', 0)}** solved / E {sv.get('Easy', 0)} M {sv.get('Medium', 0)} "
                                 f"H {sv.get('Hard', 0)}"))
    return rows


def rich(line: str, base: str, accent: str, strong: str) -> str:
    out = []
    for part in MARKUP.split(line):
        if not part:
            continue
        if part.startswith("**"):
            out.append(f'<tspan class="mb" fill="{strong}">{esc(part[2:-2])}</tspan>')
        elif part.startswith("`"):
            out.append(f'<tspan fill="{accent}">{esc(part[1:-1])}</tspan>')
        else:
            out.append(f'<tspan fill="{base}">{esc(part)}</tspan>')
    return "".join(out)


def plain(line: str) -> str:
    return MARKUP.sub(lambda m: m.group(0).strip("*`"), line)


class Console:
    """Lays out console lines top to bottom and schedules when each appears."""

    def __init__(self, x: float, y: float, colors: dict):
        self.x, self.y, self.c = x, y, colors
        self.t = .6
        self.body: list[str] = []
        self.cursor_x, self.cursor_y = Timeline(), Timeline()
        self.clips: list[tuple[float, float, Timeline]] = []
        self.rnd = random.Random(7)

    def show(self, markup: str, delay: float | None = None) -> None:
        self.body.append(f'<g class="on" style="animation-delay:{self.t if delay is None else delay:.2f}s">{markup}</g>')

    def prompt(self) -> float:
        self.show(text(self.x, self.y, "swayam@gpe:~$", "mb", fill=self.c["accent"], size=FS))
        return self.x + 14 * CW

    def type(self, command: str) -> None:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - FS * .82)
        self.t += .4
        width = Timeline()
        width.at(0, 0)
        for k in range(1, len(command) + 1):
            self.t += .06 + self.rnd.uniform(0, .05)
            width.at(self.t, k * CW)
            self.cursor_x.at(self.t, x + k * CW)
        self.clips.append((x, self.y, width))
        self.body.append(text(x, self.y, command, "m", fill=self.c["text"], size=FS,
                              clip_path=f"url(#c{len(self.clips) - 1})"))
        self.t += .3
        self.y += LH

    def line(self, markup: str, *, x: float | None = None, gap: float = .05) -> None:
        self.show(f'<text x="{num(self.x if x is None else x)}" y="{num(self.y)}" class="m" font-size="{FS}">{markup}</text>')
        self.t += gap
        self.y += LH

    def finish(self) -> tuple[str, str]:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - FS * .82)
        total = self.t + .1
        defs = "".join(
            f'<clipPath id="c{i}"><rect x="{num(x)}" y="{num(y - 16)}" width="0" height="24">'
            f'{width.animate("width", total, repeat=False)}</rect></clipPath>'
            for i, (x, y, width) in enumerate(self.clips))
        cursor = (f'<rect class="blink" width="{num(CW)}" height="{num(FS * 1.1)}" fill="{self.c["accent"]}">'
                  f'{self.cursor_x.animate("x", total, repeat=False)}{self.cursor_y.animate("y", total, repeat=False)}'
                  f'</rect>')
        return defs, "".join(self.body) + cursor


def _left(profile: dict, theme: Theme, top: float) -> tuple[str, float]:
    about = profile["about"]
    width = SPLIT - 64
    size = min(fit("sr", plain(line).strip("*"), 40, width) for line in about["heading"])
    out, y = [], top + 32 + size * .72
    for line in about["heading"]:
        italic = line.startswith("*")
        out.append(text(32, y, line.strip("*"), "si" if italic else "sr", fill=theme.accent if italic else theme.ink,
                        size=size))
        y += size * .95
    y += 16
    words, lines, cur = about["bio"].split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if cur and fonts.width("t", trial, 14) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    for line in lines:
        y += 24
        out.append(text(32, y, line, "t", fill=theme.muted, size=14))
    return f'<g class="lift" style="animation-delay:.2s">{"".join(out)}</g>', y


def render(profile: dict, theme: Theme, live: dict | None = None, today: dt.date | None = None) -> str:
    live = live or {}
    today = today or dt.datetime.now(dt.timezone.utc).date()
    dark = theme.dark
    colors = {
        "bg": "#0a0a0a" if dark else theme.ink,
        "text": theme.ink if dark else theme.paper,
        "muted": theme.muted if dark else "#a8a297",
        "accent": theme.accent,
        "strong": "#ffffff" if dark else "#ffffff",
    }
    top = 40
    cx = SPLIT + 24
    con = Console(cx, top + 24 + 17, colors)

    con.type("neofetch")
    block_top = con.y - 16
    cell, gap = 16, 8
    logo = []
    for r, row in enumerate(IDENTICON):
        for c, on in enumerate(row):
            x, y = cx + c * (cell + gap), block_top + r * (cell + gap)
            if on == "1":
                logo.append(f'<rect class="on" x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{colors["accent"]}" '
                            f'style="animation-delay:{con.t + (r * 5 + c) * .03:.2f}s"/>')
            else:
                logo.append(f'<rect x="{x + .5}" y="{y + .5}" width="{cell - 1}" height="{cell - 1}" fill="none" '
                            f'stroke="{colors["muted"]}" stroke-opacity=".5"/>')
    con.body.append("".join(logo))
    ix = cx + 5 * cell + 4 * gap + 24
    rows = neofetch_rows(profile, live, today)
    key_w = 10 * CW
    con.line(f'<tspan class="mb" fill="{colors["text"]}">swayam</tspan><tspan fill="{colors["muted"]}">@</tspan>'
             f'<tspan class="mb" fill="{colors["accent"]}">github</tspan>', x=ix)
    con.line(f'<tspan fill="{colors["muted"]}">{"-" * 13}</tspan>', x=ix)
    for key, value in rows:
        con.show(text(ix, con.y, key.lower(), "m", fill=colors["muted"], size=FS))
        con.line(rich(value, colors["text"], colors["accent"], colors["strong"]), x=ix + key_w)
    con.y += LH
    con.t += .4

    con.type("cat now.md")
    for item in profile["about"]["now"]:
        con.line(f'<tspan fill="{colors["accent"]}">→ </tspan>'
                 + rich(item, colors["text"], colors["accent"], colors["strong"]), gap=.12)
    con.y += LH
    con.t += .3
    cdefs, console = con.finish()

    H = int(con.y + 24 + 8)
    H += -H % 8
    sheet_h = H - 8
    body = [card(W, H, theme)]
    body.append(strip(0, 0, W - 8, "§01", "Whoami", "Live data · refreshed daily", theme))
    body.append(f'<rect x="{SPLIT + 1}" y="{top}" width="{W - 8 - SPLIT - 2}" height="{sheet_h - top - 1}" '
                f'fill="{colors["bg"]}"/>')
    body.append(vline(SPLIT, top, sheet_h, theme.ink))
    left, bio_end = _left(profile, theme, top)
    body.append(left)
    # raw texture under the bio: a hatched block carrying the sync stamp on a paper label
    hatch_top = int(bio_end + 40) + (-int(bio_end + 40) % 8)
    if sheet_h - hatch_top >= 96:
        synced = live.get("github", {}).get("fetched_at")
        stamp = dt.datetime.fromisoformat(synced).strftime("%d %b %Y").upper() if synced else "PENDING"
        body.append(stamp_block(0, hatch_top, SPLIT, sheet_h - hatch_top, f"SYNCED {stamp}", theme))
    body.append(console)
    desc = " / ".join(plain(f"{k}: {v}") for k, v in rows)
    return document("".join(body), W, H, title="whoami — Swayam Patil", desc=desc, css=CSS,
                    defs=patterns(theme) + cdefs)
