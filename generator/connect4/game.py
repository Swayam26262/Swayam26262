"""Connect Four game state, board artwork and the README section.

State lives in generator/data/connect4.json. Humans (yellow) always open;
the AI (red) answers every human move straight away.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import urllib.parse
from pathlib import Path

from core.svg import document, num, text
from core.theme import THEMES, Theme

from .engine import AI, COLS, HUMAN, ROWS, Board, choose, winning_cells

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "generator" / "data" / "connect4.json"
ASSET_DIR = ROOT / "assets" / "connect4"
README = ROOT / "README.md"
START, END = "<!-- CONNECT4:START -->", "<!-- CONNECT4:END -->"

DEPTH = 6               # AI search depth (plies)
CELL, PAD = 56, 16      # board geometry; buttons are CELL wide so they line up with the columns
YELLOW = ("#fde047", "#eab308", "#a16207")
RED = ("#fb7185", "#e11d48", "#9f1239")
MOVE_RE = re.compile(r"^c4\|drop\|([1-7])$")


# ---- state ---------------------------------------------------------------

def new_state() -> dict:
    return {"game": 1, "moves": [], "players": [], "status": "playing",
            "score": {"humans": 0, "ai": 0, "draws": 0}, "movers": {}, "winners": [],
            "last": None, "processed": []}


def load() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else new_state()


def save(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")


def parse_title(title: str) -> int | None:
    """'c4|drop|4' -> column index 3."""
    m = MOVE_RE.match(title.strip())
    return int(m.group(1)) - 1 if m else None


def play(state: dict, col: int, user: str, rng: random.Random | None = None,
         now: dt.datetime | None = None) -> str:
    """Apply a human move (and the AI's reply). Returns a markdown reply for the issue."""
    now = now or dt.datetime.now(dt.timezone.utc)
    started = ""
    if state["status"] != "playing":
        state.update(game=state["game"] + 1, moves=[], players=[], status="playing", last=None)
        started = f"That kicked off **game #{state['game']}**. "
    board = Board.from_moves(state["moves"])
    if not board.can_play(col):
        return f"Column {col + 1} is already full, so nothing changed. Pick another column on the board."

    board.play(col)
    state["moves"].append(col)
    state["players"].append(user)
    state["movers"][user] = state["movers"].get(user, 0) + 1
    last = {"user": user, "human": col, "ai": None, "at": now.replace(microsecond=0).isoformat()}
    state["last"] = last

    if board.winner() == HUMAN:
        state["status"] = "humans"
        state["score"]["humans"] += 1
        state["winners"].append({"game": state["game"], "user": user, "moves": board.moves})
        return (f"{started}You dropped a disc in column {col + 1} and **won game #{state['game']} for the humans!** "
                "Your name is now on the board of fame.")
    if board.full():
        state["status"] = "draw"
        state["score"]["draws"] += 1
        return f"{started}You dropped a disc in column {col + 1}. The board is full: game #{state['game']} is a draw."

    reply = choose(board, DEPTH, rng)
    board.play(reply)
    state["moves"].append(reply)
    state["players"].append(None)
    last["ai"] = reply
    if board.winner() == AI:
        state["status"] = "ai"
        state["score"]["ai"] += 1
        return (f"{started}You dropped a disc in column {col + 1}; the AI answered in column {reply + 1} "
                f"and **won game #{state['game']}**. Click any column to start a rematch.")
    if board.full():
        state["status"] = "draw"
        state["score"]["draws"] += 1
        return (f"{started}You played column {col + 1}, the AI played column {reply + 1}, and the board is full: "
                f"game #{state['game']} is a draw.")
    return f"{started}You dropped a disc in column {col + 1}; the AI answered in column {reply + 1}. Your move!"


# ---- artwork -------------------------------------------------------------

BOARD_CSS = """
.drop{animation:drop .75s cubic-bezier(.33,0,.67,0) both}
@keyframes drop{0%{transform:translateY(var(--from))}70%{transform:translateY(0)}82%{transform:translateY(-10px)}
92%{transform:translateY(0)}96%{transform:translateY(-3px)}100%{transform:translateY(0)}}
.halo{animation:halo 1.8s ease-out 2s infinite both;transform-box:fill-box;transform-origin:center}
@keyframes halo{0%{opacity:0;transform:scale(1)}10%{opacity:.9}100%{opacity:0;transform:scale(1.5)}}
.win{stroke-dasharray:1;animation:win 1s ease-out 1.6s both,glow 1.6s ease-in-out 2.6s infinite alternate}
@keyframes win{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes glow{to{stroke-opacity:.55}}
"""


def disc(cx: float, cy: float, r: float, colors: tuple[str, str, str], gid: str) -> str:
    return (f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="url(#{gid})"/>'
            f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r * .68)}" fill="none" stroke="{colors[2]}" '
            f'stroke-opacity=".35" stroke-width="2"/>'
            f'<ellipse cx="{num(cx - r * .28)}" cy="{num(cy - r * .34)}" rx="{num(r * .3)}" ry="{num(r * .18)}" '
            f'fill="#fff" fill-opacity=".35" transform="rotate(-30 {num(cx - r * .28)} {num(cy - r * .34)})"/>')


def board_svg(state: dict, theme: Theme) -> str:
    board = Board.from_moves(state["moves"])
    w = COLS * CELL + 2 * PAD
    h_board = ROWS * CELL + 2 * PAD
    H = h_board + 26
    dark = theme.dark
    frame = ("#312e81", "#1e1b4b") if dark else ("#6366f1", "#4338ca")
    hole = theme.page if dark else "#eef2ff"
    defs = (
        f'<linearGradient id="fr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{frame[0]}"/>'
        f'<stop offset="1" stop-color="{frame[1]}"/></linearGradient>'
        f'<radialGradient id="dy" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="{YELLOW[0]}"/>'
        f'<stop offset=".6" stop-color="{YELLOW[1]}"/><stop offset="1" stop-color="{YELLOW[2]}"/></radialGradient>'
        f'<radialGradient id="dr" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="{RED[0]}"/>'
        f'<stop offset=".6" stop-color="{RED[1]}"/><stop offset="1" stop-color="{RED[2]}"/></radialGradient>'
        f'<filter id="gl" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>'
    )
    r = CELL * .38
    pieces, holes = [], []
    grid = board.grid()
    moves = state["moves"]
    # which discs to animate: the latest human move and the AI's reply
    animate = {}
    replay = Board()
    for i, c in enumerate(moves):
        row = replay.play(c)
        if i >= len(moves) - 2 and state.get("last"):
            animate[(c, row)] = .25 if i % 2 == 0 else 1.25
    for ri, row in enumerate(grid):
        for c, cell in enumerate(row):
            cx = PAD + c * CELL + CELL / 2
            cy = PAD + ri * CELL + CELL / 2
            holes.append(f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r + 1)}"/>')
            if cell is None:
                continue
            body = disc(cx, cy, r, YELLOW if cell == HUMAN else RED, "dy" if cell == HUMAN else "dr")
            bottom_row = ROWS - 1 - ri
            delay = animate.get((c, bottom_row))
            if delay is not None:
                body = (f'<g class="drop" style="--from:-{num(cy + CELL)}px;animation-delay:{delay}s">{body}</g>')
                if cell == AI:
                    body += (f'<circle class="halo" cx="{num(cx)}" cy="{num(cy)}" r="{num(r + 3)}" fill="none" '
                             f'stroke="{RED[0]}" stroke-width="2.5"/>')
            pieces.append(body)
    win_line = ""
    if state["status"] in ("humans", "ai"):
        cells = winning_cells(board.pieces[HUMAN if state["status"] == "humans" else AI])
        if cells:
            pts = [(PAD + c * CELL + CELL / 2, PAD + (ROWS - 1 - rr) * CELL + CELL / 2) for c, rr in cells]
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            seg = f"M{num(x1)} {num(y1)}L{num(x2)} {num(y2)}"
            win_line = (f'<path class="win" d="{seg}" pathLength="1" stroke="#fff" stroke-width="12" stroke-opacity=".9" '
                        f'stroke-linecap="round" filter="url(#gl)"/>'
                        f'<path class="win" d="{seg}" pathLength="1" stroke="#fff" stroke-width="5" stroke-linecap="round"/>')
    # discs sit behind the board face, which has holes punched through it (even-odd)
    face = f"M14 0H{w - 14}a14 14 0 0 1 14 14V{h_board - 14}a14 14 0 0 1-14 14H14a14 14 0 0 1-14-14V14a14 14 0 0 1 14-14Z"
    hole_paths = "".join(
        f"M{num(PAD + c * CELL + CELL / 2 - r - 1)} {num(PAD + ri * CELL + CELL / 2)}"
        f"a{num(r + 1)} {num(r + 1)} 0 1 0 {num(2 * r + 2)} 0a{num(r + 1)} {num(r + 1)} 0 1 0 -{num(2 * r + 2)} 0Z"
        for ri in range(ROWS) for c in range(COLS))
    body = (
        f'<g fill="{hole}">{"".join(holes)}</g>'
        + "".join(pieces)
        + f'<path d="{face}{hole_paths}" fill="url(#fr)" fill-rule="evenodd"/>'
        + f'<path d="{face}" fill="none" stroke="#fff" stroke-opacity=".12"/>'
        + win_line
        + "".join(text(PAD + c * CELL + CELL / 2, h_board + 18, str(c + 1), "mb", fill=theme.faint if dark else theme.muted,
                       size=11, anchor="middle") for c in range(COLS))
    )
    status = {"playing": "your move", "humans": "humans win", "ai": "AI wins", "draw": "draw"}[state["status"]]
    return document(body, w, H, title=f"Connect Four, game #{state['game']} ({status})",
                    desc=f"Board after {len(moves)} moves.", css=BOARD_CSS, defs=defs)


BUTTON_CSS = """
.bob{animation:bob 1.6s ease-in-out infinite}
@keyframes bob{50%{transform:translateY(4px)}}
"""


def button_svg(col: int, theme: Theme, full: bool) -> str:
    s = CELL
    fill = theme.panel2 if theme.dark else "#ffffff"
    if full:
        body = (f'<rect x="4.5" y="4.5" width="{s - 9}" height="{s - 9}" rx="13" fill="{fill}" stroke="{theme.border}" '
                f'stroke-dasharray="3 3"/>'
                + text(s / 2, s / 2 + 4, "FULL", "mb", fill=theme.faint, size=9, anchor="middle", letter_spacing="1"))
        return document(body, s, s, title=f"Column {col + 1} is full")
    body = (f'<rect x="4.5" y="4.5" width="{s - 9}" height="{s - 9}" rx="13" fill="{fill}" stroke="{theme.border2}"/>'
            f'<g class="bob" style="animation-delay:{col * .12:.2f}s">'
            f'<circle cx="{s / 2}" cy="{s / 2 - 4}" r="11" fill="url(#d)"/>'
            f'<path d="M{s / 2 - 5} {s / 2 + 12}l5 5 5-5" stroke="{theme.muted}" stroke-width="2" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/></g>')
    defs = (f'<radialGradient id="d" cx=".38" cy=".32" r=".75"><stop offset="0" stop-color="{YELLOW[0]}"/>'
            f'<stop offset=".6" stop-color="{YELLOW[1]}"/><stop offset="1" stop-color="{YELLOW[2]}"/></radialGradient>')
    return document(body, s, s, title=f"Drop a disc in column {col + 1}", css=BUTTON_CSS, defs=defs)


def board_name(state: dict, theme: Theme) -> str:
    return f"board-{state['game']}-{len(state['moves'])}-{theme.name}.svg"


def write_assets(state: dict) -> list[Path]:
    """Render buttons and the current board; drop boards from older states."""
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for theme in THEMES:
        for col in range(COLS):
            for full in (False, True):
                p = ASSET_DIR / f"col-{col + 1}{'-full' if full else ''}-{theme.name}.svg"
                svg = button_svg(col, theme, full)
                if not p.exists() or p.read_text() != svg:
                    p.write_text(svg)
                    written.append(p)
        p = ASSET_DIR / board_name(state, theme)
        svg = board_svg(state, theme)
        if not p.exists() or p.read_text() != svg:
            p.write_text(svg)
            written.append(p)
    keep = {board_name(state, t) for t in THEMES}
    for old in ASSET_DIR.glob("board-*.svg"):
        if old.name not in keep:
            old.unlink()
            written.append(old)
    return written


# ---- README --------------------------------------------------------------

def picture(dark: str, light: str, alt: str, **attrs) -> str:
    extra = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{dark}">'
            f'<img src="{light}"{extra} alt="{alt}"></picture>')


def issue_url(repo: str, col: int) -> str:
    title = urllib.parse.quote(f"c4|drop|{col + 1}", safe="")
    body = urllib.parse.quote(
        "Just press **Create** (or **Submit new issue**), no need to write anything.\n\n"
        "A GitHub Action will drop your disc, let the AI reply and update the board in about a minute.",
        safe="")
    return f"https://github.com/{repo}/issues/new?title={title}&body={body}"


def user_link(user: str) -> str:
    return f'<a href="https://github.com/{user}">@{user}</a>'


def readme_section(state: dict, repo: str) -> str:
    board = Board.from_moves(state["moves"])
    game, status, score = state["game"], state["status"], state["score"]
    if status == "humans":
        headline = f"🎉 <b>The humans won game #{game}</b> in {len(state['moves'])} moves! Click any column to start game #{game + 1}."
    elif status == "ai":
        headline = f"🤖 <b>The AI won game #{game}.</b> Click any column to start game #{game + 1} and get revenge."
    elif status == "draw":
        headline = f"🤝 <b>Game #{game} is a draw.</b> Click any column to start game #{game + 1}."
    elif not state["moves"]:
        headline = f"<b>Game #{game}</b> · 🟡 humans vs 🔴 AI · you open. Pick a column 👇"
    else:
        ai = state["last"]["ai"] if state.get("last") else None
        reply = f" The AI just played column {ai + 1}." if ai is not None else ""
        headline = f"<b>Game #{game}</b> · move {len(state['moves']) + 1} · your turn, humans!{reply}"

    over = status != "playing"
    buttons = []
    for c in range(COLS):
        full = not over and not board.can_play(c)
        suffix = "-full" if full else ""
        img = picture(f"assets/connect4/col-{c + 1}{suffix}-dark.svg", f"assets/connect4/col-{c + 1}{suffix}-light.svg",
                      f"Column {c + 1} is full" if full else f"Drop a disc in column {c + 1}", width=CELL)
        buttons.append(img if full else f'<a href="{issue_url(repo, c)}">{img}</a>')
    board_img = picture(f"assets/connect4/{board_name(state, THEMES[0])}",
                        f"assets/connect4/{board_name(state, THEMES[1])}",
                        f"Connect Four board, game #{game}", width=COLS * CELL + 2 * PAD)
    lines = [START, f'<p align="center">{headline}</p>',
             f'<p align="center">{"".join(buttons)}<br>{board_img}</p>']
    last = state.get("last")
    if last:
        when = dt.datetime.fromisoformat(last["at"]).strftime("%d %b %Y, %H:%M UTC")
        reply = f" · the AI replied in column {last['ai'] + 1}" if last.get("ai") is not None else ""
        lines.append(f'<p align="center"><sub>Last move: {user_link(last["user"])} dropped in column '
                     f'{last["human"] + 1}{reply} · {when}</sub></p>')
    movers = sorted(state["movers"].items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    lines += [
        "<details>",
        "<summary><b>Scoreboard, hall of fame and how it works</b></summary>",
        "",
        "| 🟡 Humans | 🔴 AI | 🤝 Draws |",
        "| :-: | :-: | :-: |",
        f"| {score['humans']} | {score['ai']} | {score['draws']} |",
        "",
    ]
    if state["winners"]:
        lines.append("**Winning moves:** " + " · ".join(
            f"{user_link(w['user'])} (game #{w['game']})" for w in state["winners"][-6:][::-1]))
        lines.append("")
    if movers:
        lines.append("**Most moves played:** " + " · ".join(f"{user_link(u)} ×{n}" for u, n in movers))
        lines.append("")
    lines += [
        "**How it works:** clicking a column opens a pre-filled issue. A GitHub Action reads it, drops your disc, "
        f"lets a negamax AI with alpha-beta pruning ({DEPTH} plies deep) reply, redraws the board and commits this "
        "README. Everyone plays the same game, so coordinate in the issues if you want to win.",
        "",
        "</details>",
        END,
    ]
    return "\n".join(lines)


def update_readme(state: dict, repo: str) -> bool:
    text_ = README.read_text()
    if START not in text_ or END not in text_:
        raise RuntimeError("README.md is missing the CONNECT4 markers")
    head, rest = text_.split(START, 1)
    _, tail = rest.split(END, 1)
    new = head + readme_section(state, repo) + tail
    if new == text_:
        return False
    README.write_text(new)
    return True
