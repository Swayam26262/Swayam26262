"""§01 about: a serif statement and short bio, and a flat console that types
`neofetch` (with live GitHub/LeetCode numbers) and `cat now.md`, then idles on
a blinking block cursor. Side by side on desktop, stacked on phones."""

from __future__ import annotations

import calendar
import datetime as dt
import random
import re

from core import fonts
from core.design import (CSS as BASE, canvas, card, hline, paragraph, patterns, secondary, serif_heading,
                         snap, stamp_block, strip, vline)
from core.motion import BLINK_CSS, Timeline
from core.svg import document, esc, num, text
from core.theme import Theme

SPLIT = 280               # desktop left column width
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


def tokens(line: str) -> list[str]:
    """Words, keeping `code` and **bold** spans whole even when they contain spaces."""
    out = []
    for part in MARKUP.split(line):
        if not part:
            continue
        if MARKUP.fullmatch(part):
            if out and not line[line.index(part) - 1:line.index(part)].isspace() and line.index(part) > 0:
                out[-1] += part
            else:
                out.append(part)
        else:
            words = part.split(" ")
            if out and words and words[0]:
                out[-1] += words[0]
                words = words[1:]
            out += [w for w in words if w]
    return out


def plain(line: str) -> str:
    return MARKUP.sub(lambda m: m.group(0).strip("*`"), line)


def wrap_chars(line: str, limit: int) -> list[str]:
    """Wrap marked-up console text to `limit` visible characters per line."""
    lines, cur = [], ""
    for tok in tokens(line):
        trial = f"{cur} {tok}".strip()
        if cur and len(plain(trial)) > limit:
            lines.append(cur)
            cur = tok
        else:
            cur = trial
    return lines + [cur]


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


class Console:
    """Lays out console lines top to bottom and schedules when each appears."""

    def __init__(self, x: float, y: float, colors: dict, size: float, leading: float):
        self.x, self.y, self.c = x, y, colors
        self.fs, self.lh = size, leading
        self.cw = fonts.width("m", "M", size)
        self.t = .6
        self.body: list[str] = []
        self.cursor_x, self.cursor_y = Timeline(), Timeline()
        self.clips: list[tuple[float, float, Timeline]] = []
        self.rnd = random.Random(7)

    def show(self, markup: str) -> None:
        self.body.append(f'<g class="on" style="animation-delay:{self.t:.2f}s">{markup}</g>')

    def prompt(self) -> float:
        self.show(text(self.x, self.y, "swayam@gpe:~$", "mb", fill=self.c["accent"], size=self.fs))
        return self.x + 14 * self.cw

    def type(self, command: str) -> None:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - self.fs * .82)
        self.t += .4
        width = Timeline()
        width.at(0, 0)
        for k in range(1, len(command) + 1):
            self.t += .06 + self.rnd.uniform(0, .05)
            width.at(self.t, k * self.cw)
            self.cursor_x.at(self.t, x + k * self.cw)
        self.clips.append((x, self.y, width))
        self.body.append(text(x, self.y, command, "m", fill=self.c["text"], size=self.fs,
                              clip_path=f"url(#c{len(self.clips) - 1})"))
        self.t += .3
        self.y += self.lh

    def line(self, markup: str, *, x: float | None = None, gap: float = .05) -> None:
        self.show(f'<text x="{num(self.x if x is None else x)}" y="{num(self.y)}" class="m" '
                  f'font-size="{num(self.fs)}">{markup}</text>')
        self.t += gap
        self.y += self.lh

    def finish(self) -> tuple[str, str]:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - self.fs * .82)
        total = self.t + .1
        defs = "".join(
            f'<clipPath id="c{i}"><rect x="{num(x)}" y="{num(y - self.lh + 4)}" width="0" height="{num(self.lh)}">'
            f'{width.animate("width", total, repeat=False)}</rect></clipPath>'
            for i, (x, y, width) in enumerate(self.clips))
        cursor = (f'<rect class="blink" width="{num(self.cw)}" height="{num(self.fs * 1.1)}" fill="{self.c["accent"]}">'
                  f'{self.cursor_x.animate("x", total, repeat=False)}{self.cursor_y.animate("y", total, repeat=False)}'
                  f'</rect>')
        return defs, "".join(self.body) + cursor


def console_colors(theme: Theme) -> dict:
    dark = theme.dark
    return {
        "bg": "#0a0a0a" if dark else theme.ink,
        "text": theme.ink if dark else theme.paper,
        "muted": theme.muted if dark else theme.soft_inv,
        "accent": theme.accent if dark else theme.accent_inv,
        "teal": theme.teal if dark else theme.teal_inv,
        "strong": "#ffffff",
    }


def run_console(profile: dict, live: dict, today: dt.date, theme: Theme, x: float, top: float,
                mobile: bool) -> tuple[Console, list[tuple[str, str]]]:
    c = console_colors(theme)
    con = Console(x, top + 24 + 17, c, 10.5 if mobile else 12, 24)
    rows = neofetch_rows(profile, live, today)
    con.type("neofetch")
    if mobile:
        ix = x
    else:
        block_top = con.y - 16
        cell, gap = 16, 8
        logo = []
        for r, row in enumerate(IDENTICON):
            for col, on in enumerate(row):
                lx, ly = x + col * (cell + gap), block_top + r * (cell + gap)
                if on == "1":
                    logo.append(f'<rect class="on" x="{lx}" y="{ly}" width="{cell}" height="{cell}" fill="{c["accent"]}" '
                                f'style="animation-delay:{con.t + (r * 5 + col) * .03:.2f}s"/>')
                else:
                    logo.append(f'<rect x="{lx + .5}" y="{ly + .5}" width="{cell - 1}" height="{cell - 1}" fill="none" '
                                f'stroke="{c["muted"]}" stroke-opacity=".6"/>')
        con.body.append("".join(logo))
        ix = x + 5 * cell + 4 * gap + 24
    key_w = 10 * con.cw
    con.line(f'<tspan class="mb" fill="{c["text"]}">swayam</tspan><tspan fill="{c["muted"]}">@</tspan>'
             f'<tspan class="mb" fill="{c["accent"]}">github</tspan>', x=ix)
    con.line(f'<tspan fill="{c["muted"]}">{"-" * 13}</tspan>', x=ix)
    for key, value in rows:
        key, extra = secondary(key)
        con.show(text(ix, con.y, key.lower(), "m", fill=c["teal"] if extra else c["muted"], size=con.fs))
        con.line(rich(value, c["teal"] if extra else c["text"], c["accent"], c["strong"]), x=ix + key_w)
    con.y += con.lh
    con.t += .4

    con.type("cat now.md")
    limit = int((W_CONSOLE_MOBILE if mobile else 504) / con.cw) - 2
    for item in profile["about"]["now"]:
        for i, part in enumerate(wrap_chars(item, limit)):
            body = rich(part, c["text"], c["accent"], c["strong"])
            if i == 0:
                con.line(f'<tspan fill="{c["accent"]}">→ </tspan>' + body, gap=.12)
            else:  # hanging indent under the first word (SVG collapses leading spaces)
                con.line(body, x=con.x + 2 * con.cw, gap=.02)
    con.y += con.lh
    con.t += .3
    return con, rows


W_CONSOLE_MOBILE = 352


def render(profile: dict, theme: Theme, live: dict | None = None, today: dt.date | None = None,
           mobile: bool = False) -> str:
    live = live or {}
    today = today or dt.datetime.now(dt.timezone.utc).date()
    W = canvas(mobile)
    sheet_w = W - 8
    about = profile["about"]
    colors = console_colors(theme)
    top = 40
    head = strip(0, 0, sheet_w, "§01", "Whoami", "Live data · refreshed daily", theme)

    if mobile:
        heading, end = serif_heading(about["heading"], 24, top + 32, sheet_w - 48, theme)
        bio, end = paragraph(about["bio"], 24, end + 16, sheet_w - 48, theme.muted)
        con_top = snap(end + 32)
        con, rows = run_console(profile, live, today, theme, 24, con_top, mobile=True)
        cdefs, console = con.finish()
        H = snap(con.y + 8) + 8
        sheet_h = H - 8
        body = [card(W, H, theme), head, f'<g class="lift" style="animation-delay:.2s">{heading}{bio}</g>',
                hline(0, sheet_w, con_top - 1, theme.ink),
                f'<rect x="1" y="{con_top}" width="{sheet_w - 2}" height="{sheet_h - con_top - 1}" fill="{colors["bg"]}"/>',
                console]
    else:
        con, rows = run_console(profile, live, today, theme, SPLIT + 24, top, mobile=False)
        cdefs, console = con.finish()
        H = snap(con.y + 8) + 8
        sheet_h = H - 8
        heading, end = serif_heading(about["heading"], 32, top + 32, SPLIT - 64, theme)
        bio, end = paragraph(about["bio"], 32, end + 16, SPLIT - 64, theme.muted)
        body = [card(W, H, theme), head,
                f'<rect x="{SPLIT + 1}" y="{top}" width="{sheet_w - SPLIT - 2}" height="{sheet_h - top - 1}" '
                f'fill="{colors["bg"]}"/>',
                vline(SPLIT, top, sheet_h, theme.ink),
                f'<g class="lift" style="animation-delay:.2s">{heading}{bio}</g>']
        hatch_top = snap(end + 40)
        if sheet_h - hatch_top >= 96:
            synced = live.get("github", {}).get("fetched_at")
            stamp = dt.datetime.fromisoformat(synced).strftime("%d %b %Y").upper() if synced else "PENDING"
            body.append(stamp_block(0, hatch_top, SPLIT, sheet_h - hatch_top, f"SYNCED {stamp}", theme))
        body.append(console)
    desc = " / ".join(plain(f"{k.lstrip('+')}: {v}") for k, v in rows)
    return document("".join(body), W, H, title="whoami — Swayam Patil", desc=desc, css=CSS,
                    defs=patterns(theme) + cdefs)
