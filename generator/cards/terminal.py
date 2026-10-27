"""A zsh session that types `whoami`, `neofetch` (with live GitHub numbers) and
`cat now.md`, then idles with a blinking cursor."""

from __future__ import annotations

import calendar
import datetime as dt
import random
import re

from core import fonts
from core.motion import BLINK_CSS, Timeline
from core.svg import document, esc, num, text
from core.theme import Theme

W, PAD, TITLE_H = 840, 28, 40
FS, LH = 13.5, 22
CW = fonts.width("m", "M", FS)

# The identicon from the GitHub avatar, reused as the neofetch logo.
IDENTICON = ["11011", "11111", "00100", "01110", "11111"]

CSS = BLINK_CSS + """
.o{animation:o .18s ease-out both}
@keyframes o{from{opacity:0}}
.px{animation:px .5s cubic-bezier(.3,1.6,.5,1) both;transform-box:fill-box;transform-origin:center}
@keyframes px{from{opacity:0;transform:scale(.2)}}
.sweep{animation:sweep 5s ease-in-out 6s infinite}
@keyframes sweep{0%{transform:translateY(0);opacity:0}10%{opacity:.9}45%{transform:translateY(130px);opacity:0}100%{transform:translateY(130px);opacity:0}}
"""

MARKUP = re.compile(r"(\*\*.+?\*\*|`.+?`)")


def rich(line: str, theme: Theme, base: str) -> str:
    out = []
    for part in MARKUP.split(line):
        if not part:
            continue
        if part.startswith("**"):
            out.append(f'<tspan class="mb" fill="{theme.amber}">{esc(part[2:-2])}</tspan>')
        elif part.startswith("`"):
            out.append(f'<tspan fill="{theme.cyan}">{esc(part[1:-1])}</tspan>')
        else:
            out.append(f'<tspan fill="{base}">{esc(part)}</tspan>')
    return "".join(out)


def plain(line: str) -> str:
    return MARKUP.sub(lambda m: m.group(0).strip("*`"), line)


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
    rows = [tuple(r) for r in profile["terminal"]["neofetch"]]
    joined = dt.date.fromisoformat(profile["person"]["github_joined"])
    rows.append(("Uptime", f"{uptime(joined, today)} on GitHub"))
    gh = live.get("github")
    if gh:
        rows.append(("Repos", f"**{gh['public_repos']}** public · **{gh['stars']}** stars earned"))
        rows.append(("Commits", f"**{gh['commits_total']:,}** all-time · **{gh['commits_year']:,}** in {today.year}"))
        rows.append(("Activity", f"**{gh['contributions_last_year']:,}** contributions in the last year"))
        s = gh["streak"]
        rows.append(("Streak", f"**{s['current']}** day{'s' * (s['current'] != 1)} running · best **{s['longest']}**"))
        rows.append(("Social", f"**{gh['followers']}** followers · **{gh['following']}** following"))
    lc = live.get("leetcode")
    if lc:
        sv = lc["solved"]
        rows.append(("LeetCode", f"**{sv.get('All', 0)}** solved · E {sv.get('Easy', 0)} · M {sv.get('Medium', 0)} · H {sv.get('Hard', 0)}"))
    return rows


class Session:
    """Lays out lines top to bottom while tracking when each one appears."""

    def __init__(self, theme: Theme):
        self.theme = theme
        self.y = TITLE_H + 34
        self.t = 0.5
        self.body: list[str] = []
        self.cursor_x, self.cursor_y = Timeline(), Timeline()
        self.clips: list[tuple[float, float, Timeline]] = []   # x, y, width timeline per typed command
        self.rnd = random.Random(7)

    def show(self, markup: str, delay: float | None = None) -> None:
        self.body.append(f'<g class="o" style="animation-delay:{self.t if delay is None else delay:.2f}s">{markup}</g>')

    def prompt(self) -> float:
        th, x, y = self.theme, PAD, self.y
        top, h, tip = y - 15, 21, 8
        w1 = 9 + 6 * CW + 9
        w2 = 9 + 9 * CW + 9
        ink = th.panel if th.dark else "#ffffff"
        seg2 = (f'<path d="M{num(x + w1)} {num(top)}H{num(x + w1 + tip + w2)}l{tip} {num(h / 2)}l-{tip} {num(h / 2)}'
                f'H{num(x + w1)}Z" fill="{th.border2}"/>')
        seg1 = (f'<path d="M{num(x + 5)} {num(top)}H{num(x + w1)}l{tip} {num(h / 2)}l-{tip} {num(h / 2)}H{num(x + 5)}'
                f'a5 5 0 0 1-5-5v-{num(h - 10)}a5 5 0 0 1 5-5Z" fill="{th.indigo}"/>')
        self.show(seg2 + seg1 + text(x + 9, y, "swayam", "mb", fill=ink, size=FS)
                  + text(x + w1 + tip + 9, y, "~/profile", "m", fill=th.text, size=FS))
        return x + w1 + tip + w2 + tip + 10

    def type(self, command: str) -> None:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - FS * .82)
        self.t += .45
        width = Timeline()
        width.at(0, 0)
        for k in range(1, len(command) + 1):
            self.t += .06 + self.rnd.uniform(0, .05)
            width.at(self.t, k * CW)
            self.cursor_x.at(self.t, x + k * CW)
        cid = f"c{len(self.clips)}"
        self.clips.append((x, self.y, width))
        self.body.append(text(x, self.y, command, "m", fill=self.theme.text, size=FS, clip_path=f"url(#{cid})"))
        self.t += .35
        self.y += LH

    def line(self, markup: str, *, x: float = PAD, gap: float = .05) -> None:
        self.show(f'<text x="{num(x)}" y="{num(self.y)}" class="m" font-size="{FS}">{markup}</text>')
        self.t += gap
        self.y += LH

    def finish(self) -> tuple[str, str, float]:
        x = self.prompt()
        self.cursor_x.at(self.t, x)
        self.cursor_y.at(self.t, self.y - FS * .82)
        total = self.t + .1
        defs = "".join(
            f'<clipPath id="c{i}"><rect x="{num(x)}" y="{num(y - 16)}" width="0" height="22">'
            f'{width.animate("width", total, repeat=False)}</rect></clipPath>'
            for i, (x, y, width) in enumerate(self.clips))
        cursor = (f'<rect class="blink" width="{num(CW)}" height="{num(FS * 1.05)}" rx="1" fill="{self.theme.cyan}" '
                  f'fill-opacity=".85">{self.cursor_x.animate("x", total, repeat=False)}'
                  f'{self.cursor_y.animate("y", total, repeat=False)}</rect>')
        return defs, "".join(self.body) + cursor, self.y


def render(profile: dict, theme: Theme, live: dict | None = None, today: dt.date | None = None) -> str:
    live = live or {}
    today = today or dt.datetime.now(dt.timezone.utc).date()
    th = theme
    s = Session(th)

    # $ whoami
    s.type("whoami")
    who = profile["terminal"]["whoami"].split(" · ", 1)
    s.line(f'<tspan class="mb" fill="{th.text}">{esc(who[0])}</tspan>'
           f'<tspan fill="{th.muted}"> · {esc(who[1]) if len(who) > 1 else ""}</tspan>')
    s.y += 12
    s.t += .4

    # $ neofetch
    s.type("neofetch")
    top = s.y - 14
    cell, gap = 22, 4
    logo_w = 5 * cell + 4 * gap
    ox = PAD + 6
    defs = [f'<linearGradient id="lg" x1="0" y1="0" x2="1" y2="1" gradientUnits="userSpaceOnUse" '
            f'gradientTransform="translate({ox} {top}) scale({logo_w})">'
            f'<stop offset="0" stop-color="{th.cyan}"/><stop offset=".5" stop-color="{th.indigo}"/>'
            f'<stop offset="1" stop-color="{th.pink}"/></linearGradient>']
    cells = []
    for r, row in enumerate(IDENTICON):
        for c, on in enumerate(row):
            x, y = ox + c * (cell + gap), top + r * (cell + gap)
            if on == "1":
                cells.append(f'<rect class="px" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="5" fill="url(#lg)" '
                             f'style="animation-delay:{s.t + (r + c) * .05:.2f}s"/>')
            else:
                cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="5" fill="{th.border}" '
                             f'fill-opacity=".45"/>')
    s.show("".join(cells))
    # a scanline that sweeps the logo every few seconds
    defs.append(f'<clipPath id="lc"><rect x="{ox}" y="{top}" width="{logo_w}" height="{logo_w}" rx="6"/></clipPath>')
    sweep = (f'<g clip-path="url(#lc)"><rect class="sweep" x="{ox}" y="{top - 8}" width="{logo_w}" height="6" '
             f'fill="#fff" fill-opacity="{.35 if th.dark else .6}"/></g>')
    s.body.append(sweep)

    ix = ox + logo_w + 34
    rows = neofetch_rows(profile, live, today)
    key_w = (max(len(k) for k, _ in rows) + 2) * CW
    s.line(f'<tspan class="mb" fill="{th.cyan}">swayam</tspan><tspan fill="{th.muted}">@</tspan>'
           f'<tspan class="mb" fill="{th.pink}">github</tspan>', x=ix)
    s.line(f'<tspan fill="{th.faint}">{"─" * 13}</tspan>', x=ix)
    for key, value in rows:
        s.show(text(ix, s.y, key, "mb", fill=th.indigo, size=FS))
        s.line(rich(value, th, th.text), x=ix + key_w)
    swatches = [th.red, th.amber, th.green, th.cyan, th.blue, th.indigo, th.violet, th.pink]
    s.show("".join(f'<rect x="{num(ix + i * 26)}" y="{num(s.y - 11)}" width="22" height="12" rx="3" fill="{c}"/>'
                   for i, c in enumerate(swatches)))
    s.y = max(s.y + LH + 14, top + logo_w + 30)
    s.t += .5

    # $ cat now.md
    s.type("cat now.md")
    for item in profile["terminal"]["now"]:
        s.line(f'<tspan fill="{th.green}">→ </tspan>{rich(item, th, th.text)}', gap=.12)
    s.y += 12
    s.t += .4

    tdefs, body, bottom = s.finish()
    H = round(bottom + 24)

    # window chrome
    synced = live.get("github", {}).get("fetched_at")
    chrome = [
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{th.panel}" stroke="{th.border}"/>',
        f'<path d="M1 {TITLE_H}V14.5A13.5 13.5 0 0 1 14.5 1h{W - 29}A13.5 13.5 0 0 1 {W - 1} 14.5V{TITLE_H}Z" '
        f'fill="{th.panel2}"/>',
        f'<path d="M1 {TITLE_H}.5H{W - 1}" stroke="{th.border}"/>',
    ]
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        chrome.append(f'<circle cx="{22 + i * 20}" cy="{TITLE_H / 2}" r="6" fill="{c}"/>')
    chrome.append(text(W / 2, TITLE_H / 2 + 4, f"swayam@{profile['terminal']['host']}: ~/profile — zsh", "m",
                       fill=th.muted, size=12, anchor="middle"))
    if synced:
        stamp = dt.datetime.fromisoformat(synced).strftime("%d %b %Y").upper()
        label = f"SYNCED {stamp}"
        lw = fonts.width("m", label, 9.5, 1)
        chrome.append(f'<circle cx="{num(W - 20 - lw - 9)}" cy="{TITLE_H / 2}" r="3" fill="{th.green}"/>')
        chrome.append(text(W - 20, TITLE_H / 2 + 3.5, label, "m", fill=th.faint, size=9.5,
                           anchor="end", letter_spacing="1"))

    desc = " / ".join(plain(f"{k}: {v}") for k, v in rows)
    return document("".join(chrome) + body, W, H, title="whoami — Swayam Patil",
                    desc=desc, css=CSS, defs="".join(defs) + tdefs)
