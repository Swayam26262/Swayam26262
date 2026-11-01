"""Connect Four game state, board artwork and the README section.

State lives in generator/data/connect4.json. Humans (orange discs) always
open; the AI (black discs) answers every human move straight away.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import urllib.parse
from pathlib import Path

from core.design import CSS as BASE, SHADOW, box, card, patterns
from core.svg import document, num, text, write
from core.theme import THEMES, Theme

from .engine import AI, COLS, HUMAN, ROWS, Board, choose, winning_cells

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "generator" / "data" / "connect4.json"
ASSET_DIR = ROOT / "assets" / "connect4"
README = ROOT / "README.md"
START, END = "<!-- CONNECT4:START -->", "<!-- CONNECT4:END -->"

DEPTH = 6               # AI search depth (plies)
CELL, PAD = 56, 16      # board geometry; buttons are CELL wide so they line up with the columns
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

BOARD_CSS = BASE + """
.drop{animation:drop .7s cubic-bezier(.5,0,.75,0) both}
@keyframes drop{0%{transform:translateY(var(--from))}72%{transform:translateY(0)}84%{transform:translateY(-8px)}
94%{transform:translateY(0)}100%{transform:translateY(0)}}
.ring{animation:ring 1s steps(1,end) 2s infinite}
@keyframes ring{50%{opacity:0}}
.win{stroke-dasharray:1;animation:win .8s cubic-bezier(.7,0,.3,1) 1.6s both}
@keyframes win{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
"""


def disc_colors(theme: Theme) -> dict:
    return {HUMAN: theme.accent, AI: theme.ink}


def board_svg(state: dict, theme: Theme) -> str:
    """Flat board: paper face, hard rules, ink-ringed holes, solid discs."""
    board = Board.from_moves(state["moves"])
    w = COLS * CELL + 2 * PAD
    h_board = ROWS * CELL + 2 * PAD
    H = h_board + SHADOW + 32
    r = CELL * .36
    colors = disc_colors(theme)
    moves = state["moves"]
    animate = {}
    replay = Board()
    for i, c in enumerate(moves):
        row = replay.play(c)
        if i >= len(moves) - 2 and state.get("last"):
            animate[(c, row)] = .25 if i % 2 == 0 else 1.2
    holes, pieces = [], []
    for ri, row in enumerate(board.grid()):
        for c, cell in enumerate(row):
            cx = PAD + c * CELL + CELL / 2
            cy = PAD + ri * CELL + CELL / 2
            holes.append(f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}"/>')
            if cell is None:
                continue
            disc = f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="{colors[cell]}"/>'
            delay = animate.get((c, ROWS - 1 - ri))
            if delay is not None:
                disc = f'<g class="drop" style="--from:-{num(cy + CELL)}px;animation-delay:{delay}s">{disc}</g>'
                if cell == AI:  # mark the AI's latest reply with a blinking square ring
                    disc += (f'<rect class="ring" x="{num(cx - r - 4.5)}" y="{num(cy - r - 4.5)}" '
                             f'width="{num(2 * r + 9)}" height="{num(2 * r + 9)}" fill="none" stroke="{theme.accent}" '
                             f'stroke-width="2"/>')
            pieces.append(disc)
    win_line = ""
    if state["status"] in ("humans", "ai"):
        cells = winning_cells(board.pieces[HUMAN if state["status"] == "humans" else AI])
        if cells:
            pts = [(PAD + c * CELL + CELL / 2, PAD + (ROWS - 1 - rr) * CELL + CELL / 2) for c, rr in cells]
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            stroke = theme.paper if state["status"] == "ai" else theme.ink
            win_line = (f'<path class="win" d="M{num(x1)} {num(y1)}L{num(x2)} {num(y2)}" pathLength="1" '
                        f'stroke="{stroke}" stroke-width="6" stroke-linecap="square"/>')
    labels = "".join(text(PAD + c * CELL + CELL / 2, h_board + SHADOW + 21, str(c + 1), "mb", fill=theme.muted,
                          size=11, anchor="middle") for c in range(COLS))
    body = (card(w + SHADOW, h_board + SHADOW, theme)
            + f'<g fill="{theme.paper2}" stroke="{theme.ink}">{"".join(holes)}</g>'
            + "".join(pieces) + win_line + labels)
    status = {"playing": "your move", "humans": "humans win", "ai": "AI wins", "draw": "draw"}[state["status"]]
    return document(body, w + SHADOW, H, title=f"Connect Four, game #{state['game']} ({status})",
                    desc=f"Board after {len(moves)} moves.", css=BOARD_CSS)


BUTTON_CSS = BASE + """
.bob{animation:bob 1.2s steps(2,end) infinite}
@keyframes bob{50%{transform:translateY(3px)}}
"""


def button_svg(col: int, theme: Theme, full: bool) -> str:
    """A column key. The first key carries the board's left padding so the row lines up."""
    lead = PAD if col == 0 else 0
    w, h = CELL + lead, 48
    x = lead
    if full:
        body = (f'<rect x="{x}" y="0" width="{CELL}" height="{h}" fill="{theme.paper}"/>'
                + f'<rect x="{x}" y="0" width="{CELL}" height="{h}" fill="url(#hatch)" opacity=".5"/>'
                + box(x, 0, CELL, h, theme.ink)
                + text(x + CELL / 2, 29, "FULL", "mb", fill=theme.ink, size=9, anchor="middle", letter_spacing="1.2"))
        return document(body, w, h, title=f"Column {col + 1} is full", defs=patterns(theme), css=BASE)
    body = (box(x, 0, CELL, h, theme.ink, theme.paper)
            + text(x + 12, 20, f"{col + 1}", "mb", fill=theme.muted, size=10)
            + f'<g class="bob" style="animation-delay:{col * .1:.1f}s">'
            + f'<rect x="{x + CELL / 2 - 8}" y="18" width="16" height="16" fill="{theme.accent}"/>'
            + f'<path d="M{x + CELL / 2 - 5} 38l5 5 5-5" stroke="{theme.ink}" stroke-width="1.5" fill="none" '
              f'stroke-linecap="square"/></g>')
    return document(body, w, h, title=f"Drop a disc in column {col + 1}", css=BUTTON_CSS)


def header_svg(theme: Theme) -> str:
    """§07 section header for the game, matching the other sheets."""
    from core.design import W, strip
    H = 40 + 96 + SHADOW
    body = (card(W, H, theme) + strip(0, 0, W - SHADOW, "§07", "Play — humans vs. machine", "Connect Four", theme)
            + text(32, 40 + 56, "One shared game.", "sr", fill=theme.ink, size=40)
            + text(32 + _serif_width("One shared game. ", 40), 40 + 56, "You vs. my AI.", "si", fill=theme.accent, size=40)
            + text(W - SHADOW - 24, 40 + 52, "PICK A COLUMN → PRESS CREATE ON THE ISSUE", "m", fill=theme.muted,
                   size=9.5, anchor="end", letter_spacing="1.2")
            + text(W - SHADOW - 24, 40 + 72, "THE AI REPLIES IN ABOUT A MINUTE", "m", fill=theme.muted,
                   size=9.5, anchor="end", letter_spacing="1.2"))
    return document(body, W, H, title="Play Connect Four against my AI",
                    desc="Everyone on GitHub plays one shared game of Connect Four against my AI.", css=BASE)


def _serif_width(s_: str, size: float) -> float:
    from core import fonts
    return fonts.width("sr", s_, size)


def board_name(state: dict, theme: Theme) -> str:
    return f"board-{state['game']}-{len(state['moves'])}-{theme.name}.svg"


def write_assets(state: dict) -> list[Path]:
    """Render header, keys and the current board; drop boards from older states."""
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    files = {}
    for theme in THEMES:
        files[f"header-{theme.name}.svg"] = header_svg(theme)
        for col in range(COLS):
            for full in (False, True):
                files[f"col-{col + 1}{'-full' if full else ''}-{theme.name}.svg"] = button_svg(col, theme, full)
        files[board_name(state, theme)] = board_svg(state, theme)
    written = [ASSET_DIR / name for name, svg in files.items() if write(ASSET_DIR / name, svg)]
    for old in ASSET_DIR.glob("board-*.svg"):
        if old.name not in files:
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
    moves = len(state["moves"])
    if status == "humans":
        headline = f"<b>Game {game}: the humans won</b> in {moves} moves. Any column starts game {game + 1}."
    elif status == "ai":
        headline = f"<b>Game {game}: the AI won.</b> Any column starts game {game + 1}. Revenge is on the table."
    elif status == "draw":
        headline = f"<b>Game {game} is a draw.</b> Any column starts game {game + 1}."
    elif not moves:
        headline = f"<b>Game {game}</b>, move 1. You play orange and open; the AI plays black."
    else:
        ai = state["last"]["ai"] if state.get("last") else None
        reply = f" The AI just answered in column {ai + 1}." if ai is not None else ""
        headline = f"<b>Game {game}</b>, move {moves + 1}. Your turn.{reply}"

    over = status != "playing"
    keys = []
    for c in range(COLS):
        full = not over and not board.can_play(c)
        suffix = "-full" if full else ""
        img = picture(f"assets/connect4/col-{c + 1}{suffix}-dark.svg", f"assets/connect4/col-{c + 1}{suffix}-light.svg",
                      f"Column {c + 1} is full" if full else f"Drop a disc in column {c + 1}",
                      width=CELL + (PAD if c == 0 else 0))
        keys.append(img if full else f'<a href="{issue_url(repo, c)}">{img}</a>')
    header = picture("assets/connect4/header-dark.svg", "assets/connect4/header-light.svg",
                     "Section 07, play: one shared game of Connect Four against my AI", width="100%")
    board_img = picture(f"assets/connect4/{board_name(state, THEMES[0])}",
                        f"assets/connect4/{board_name(state, THEMES[1])}",
                        f"Connect Four board, game {game}", width=COLS * CELL + 2 * PAD + SHADOW)
    lines = [START, header, "", f"<p>{headline}</p>", f'<p>{"".join(keys)}<br>{board_img}</p>']
    last = state.get("last")
    if last:
        when = dt.datetime.fromisoformat(last["at"]).strftime("%d %b %Y, %H:%M UTC")
        reply = f", the AI replied in column {last['ai'] + 1}" if last.get("ai") is not None else ""
        lines.append(f'<p><sub>Last move: {user_link(last["user"])} played column {last["human"] + 1}{reply} '
                     f'({when}).</sub></p>')
    movers = sorted(state["movers"].items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    lines += [
        "<details>",
        "<summary><b>Scoreboard and how it works</b></summary>",
        "",
        "| Humans | AI | Draws |",
        "| :-: | :-: | :-: |",
        f"| {score['humans']} | {score['ai']} | {score['draws']} |",
        "",
    ]
    if state["winners"]:
        lines.append("**Winning moves:** " + " / ".join(
            f"{user_link(w['user'])} (game {w['game']})" for w in state["winners"][-6:][::-1]))
        lines.append("")
    if movers:
        lines.append("**Most moves played:** " + " / ".join(f"{user_link(u)} ×{n}" for u, n in movers))
        lines.append("")
    lines += [
        "**How it works:** a column opens a pre-filled issue. A GitHub Action reads it, drops your disc, "
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
