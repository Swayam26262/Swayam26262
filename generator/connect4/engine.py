"""Connect Four on bitboards, plus a negamax AI with alpha-beta pruning.

Cell (col, row) lives at bit col * 7 + row (row 0 is the bottom); the 7th bit
of each column is a sentinel that keeps the win checks from wrapping.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

COLS, ROWS = 7, 6
H1 = ROWS + 1
ORDER = (3, 2, 4, 1, 5, 0, 6)  # centre-first move ordering
HUMAN, AI = 0, 1
WIN = 1_000_000


def _windows() -> list[int]:
    """Bitmasks of every line of four on the board (69 of them)."""
    out = []
    for c in range(COLS):
        for r in range(ROWS):
            for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
                cells = [(c + k * dc, r + k * dr) for k in range(4)]
                if all(0 <= cc < COLS and 0 <= rr < ROWS for cc, rr in cells):
                    out.append(sum(1 << (cc * H1 + rr) for cc, rr in cells))
    return out


WINDOWS = _windows()
CENTER = sum(1 << (3 * H1 + r) for r in range(ROWS))


def wins(bits: int) -> bool:
    for shift in (1, H1, H1 - 1, H1 + 1):  # vertical, horizontal, both diagonals
        m = bits & (bits >> shift)
        if m & (m >> (2 * shift)):
            return True
    return False


def winning_cells(bits: int) -> list[tuple[int, int]]:
    """(col, row) of a winning line of four in `bits`, or [] if there is none."""
    for w in WINDOWS:
        if bits & w == w:
            return [(i // H1, i % H1) for i in range(COLS * H1) if w >> i & 1]
    return []


@dataclass
class Board:
    pieces: list[int] = field(default_factory=lambda: [0, 0])   # bitboards for HUMAN, AI
    heights: list[int] = field(default_factory=lambda: [c * H1 for c in range(COLS)])
    moves: int = 0

    @classmethod
    def from_moves(cls, columns: list[int]) -> "Board":
        b = cls()
        for c in columns:
            b.play(c)
        return b

    @property
    def turn(self) -> int:
        return self.moves % 2  # humans always open

    def can_play(self, col: int) -> bool:
        return 0 <= col < COLS and self.heights[col] < col * H1 + ROWS

    def legal(self) -> list[int]:
        return [c for c in ORDER if self.can_play(c)]

    def play(self, col: int) -> int:
        """Drop a disc for whoever's turn it is. Returns the row it landed in."""
        if not self.can_play(col):
            raise ValueError(f"column {col + 1} is full")
        bit = self.heights[col]
        self.pieces[self.turn] |= 1 << bit
        self.heights[col] += 1
        self.moves += 1
        return bit - col * H1

    def undo(self, col: int) -> None:
        self.moves -= 1
        self.heights[col] -= 1
        self.pieces[self.turn] &= ~(1 << self.heights[col])

    def winner(self) -> int | None:
        for p in (HUMAN, AI):
            if wins(self.pieces[p]):
                return p
        return None

    def full(self) -> bool:
        return self.moves == COLS * ROWS

    def grid(self) -> list[list[int | None]]:
        """Rows top to bottom; each cell is HUMAN, AI or None."""
        out = []
        for r in range(ROWS - 1, -1, -1):
            row = []
            for c in range(COLS):
                bit = 1 << (c * H1 + r)
                row.append(HUMAN if self.pieces[HUMAN] & bit else AI if self.pieces[AI] & bit else None)
            out.append(row)
        return out


def evaluate(board: Board, me: int) -> int:
    """Static score from `me`'s point of view: open lines and centre control."""
    mine, theirs = board.pieces[me], board.pieces[1 - me]
    score = 3 * ((mine & CENTER).bit_count() - (theirs & CENTER).bit_count())
    for w in WINDOWS:
        a, b = (mine & w).bit_count(), (theirs & w).bit_count()
        if a and b:
            continue
        if a == 3:
            score += 40
        elif a == 2:
            score += 6
        elif b == 3:
            score -= 50
        elif b == 2:
            score -= 6
    return score


EXACT, LOWER, UPPER = 0, 1, 2


def negamax(board: Board, depth: int, alpha: int, beta: int, table: dict) -> int:
    me = board.turn
    key = (board.pieces[0], board.pieces[1])
    alpha0 = alpha
    hit = table.get(key)
    if hit and hit[0] >= depth:
        _, flag, value = hit
        if flag == EXACT:
            return value
        if flag == LOWER:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)
        if alpha >= beta:
            return value
    if board.full():
        return 0
    legal = board.legal()
    for c in legal:  # take an immediate win (sooner wins score higher)
        board.play(c)
        won = wins(board.pieces[me])
        board.undo(c)
        if won:
            return WIN + depth
    if depth == 0:
        return evaluate(board, me)
    best = -10 * WIN
    for c in legal:
        board.play(c)
        score = -negamax(board, depth - 1, -beta, -alpha, table)
        board.undo(c)
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    flag = UPPER if best <= alpha0 else LOWER if best >= beta else EXACT
    table[key] = (depth, flag, best)
    return best


def choose(board: Board, depth: int = 6, rng: random.Random | None = None) -> int:
    """Best column for the player to move; ties are broken at random."""
    rng = rng or random.Random()
    me = board.turn
    legal = board.legal()
    for c in legal:  # win now if we can
        board.play(c)
        won = wins(board.pieces[me])
        board.undo(c)
        if won:
            return c
    scores = {}
    table: dict = {}
    for c in legal:
        board.play(c)
        scores[c] = -negamax(board, depth - 1, -10 * WIN, 10 * WIN, table)
        board.undo(c)
    top = max(scores.values())
    return rng.choice([c for c in legal if scores[c] == top])
