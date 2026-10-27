import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connect4 import engine, game, play  # noqa: E402
from connect4.engine import AI, HUMAN, Board, choose  # noqa: E402


class EngineTest(unittest.TestCase):
    def test_detects_all_four_directions(self):
        lines = {
            "vertical": [0, 1, 0, 1, 0, 1, 0],
            "horizontal": [0, 0, 1, 1, 2, 2, 3],
            "diagonal /": [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3],
            "diagonal \\": [6, 5, 5, 4, 4, 3, 4, 3, 3, 0, 3],
        }
        for name, moves in lines.items():
            with self.subTest(name):
                board = Board.from_moves(moves)
                self.assertEqual(board.winner(), HUMAN)
                self.assertEqual(len(engine.winning_cells(board.pieces[HUMAN])), 4)

    def test_no_wraparound_between_columns(self):
        # three on top of column 0 plus the bottom of column 1 must not count as four
        board = Board.from_moves([0, 6, 0, 6, 0, 0, 0, 6, 0, 1])
        self.assertIsNone(board.winner())

    def test_full_column_is_rejected(self):
        board = Board.from_moves([0] * 6)
        self.assertFalse(board.can_play(0))
        with self.assertRaises(ValueError):
            board.play(0)

    def test_ai_takes_a_win_over_a_block(self):
        board = Board.from_moves([0, 6, 1, 6, 5, 6, 2])  # humans threaten col 4, AI can finish col 7
        self.assertEqual(choose(board, 6, random.Random(0)), 6)

    def test_ai_blocks_an_open_three(self):
        board = Board.from_moves([0, 6, 1, 6, 2])
        self.assertEqual(choose(board, 6, random.Random(0)), 3)

    def test_ai_never_plays_a_full_column(self):
        board = Board.from_moves([3, 3, 3, 3, 3, 3])
        for seed in range(5):
            self.assertNotEqual(choose(board, 4, random.Random(seed)), 3)


class GameTest(unittest.TestCase):
    def test_parse_title_is_strict(self):
        self.assertEqual(game.parse_title("c4|drop|1"), 0)
        self.assertEqual(game.parse_title("  c4|drop|7 "), 6)
        for bad in ("c4|drop|0", "c4|drop|8", "c4|drop|4; rm -rf /", "c4|drop|", "C4|drop|3", "c4|drop|3|x"):
            self.assertIsNone(game.parse_title(bad), bad)

    def test_human_move_gets_an_ai_reply(self):
        state = game.new_state()
        reply = game.play(state, 3, "octocat", random.Random(1))
        self.assertEqual(len(state["moves"]), 2)
        self.assertEqual(state["players"], ["octocat", None])
        self.assertEqual(state["last"]["human"], 3)
        self.assertIn("column 4", reply)

    def test_full_column_leaves_state_untouched(self):
        state = game.new_state()
        state["moves"] = [0] * 6
        state["players"] = ["a", None] * 3
        before = list(state["moves"])
        reply = game.play(state, 0, "octocat")
        self.assertEqual(state["moves"], before)
        self.assertIn("full", reply)

    def test_human_win_is_scored_and_next_move_starts_a_new_game(self):
        state = game.new_state()
        # humans: 0,1,2 on the bottom row; AI stacked in column 6 (it never gets four there)
        state["moves"] = [0, 6, 1, 6, 2, 5]
        state["players"] = ["a", None, "b", None, "c", None]
        reply = game.play(state, 3, "winner")
        self.assertEqual(state["status"], "humans")
        self.assertEqual(state["score"]["humans"], 1)
        self.assertEqual(state["winners"][-1]["user"], "winner")
        self.assertIn("won game #1", reply)
        game.play(state, 3, "next", random.Random(0))
        self.assertEqual(state["game"], 2)
        self.assertEqual(state["status"], "playing")
        self.assertEqual(len(state["moves"]), 2)

    def test_ai_win_is_scored(self):
        state = game.new_state()
        rng = random.Random(3)
        while state["status"] == "playing":  # a hapless human always plays the leftmost free column
            board = Board.from_moves(state["moves"])
            game.play(state, min(board.legal()), "rando", rng)
        self.assertEqual(state["status"], "ai")
        self.assertEqual(state["score"]["ai"], 1)

    def test_readme_section_links_only_playable_columns(self):
        state = game.new_state()
        state["moves"] = [2] * 6
        state["players"] = ["a", None] * 3
        section = game.readme_section(state, "me/me")
        self.assertIn("col-3-full-dark.svg", section)
        self.assertNotIn("c4%7Cdrop%7C3", section)
        self.assertIn("c4%7Cdrop%7C4", section)
        self.assertTrue(section.startswith(game.START) and section.endswith(game.END))


class FakeGitHub:
    def __init__(self, issues):
        self.issues = issues
        self.replies = []

    def pending(self):
        return [i for i in self.issues if i["number"] not in {n for n, _ in self.replies}]

    def reply(self, number, body):
        self.replies.append((number, body))


class RunTest(unittest.TestCase):
    """End to end: issues in, board + README committed to a scratch remote, issues answered."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        remote = self.tmp / "remote.git"
        work = self.tmp / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True, stderr=subprocess.DEVNULL)
        (work / "README.md").write_text(f"# hi\n{game.START}\n{game.END}\n")
        git = ["git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-qm", "init"], check=True)
        subprocess.run(git + ["push", "-q", "origin", "HEAD:main"], check=True)
        self.work, self.remote = work, remote
        self.saved = (game.ROOT, game.STATE, game.ASSET_DIR, game.README)
        game.ROOT, game.STATE = work, work / "generator" / "data" / "connect4.json"
        game.ASSET_DIR, game.README = work / "assets" / "connect4", work / "README.md"

    def tearDown(self):
        game.ROOT, game.STATE, game.ASSET_DIR, game.README = self.saved

    def test_moves_are_played_pushed_and_answered(self):
        api = FakeGitHub([
            {"number": 1, "title": "c4|drop|4", "user": {"login": "alice"}},
            {"number": 2, "title": "c4|drop|9", "user": {"login": "mallory"}},
            {"number": 3, "title": "c4|drop|3", "user": {"login": "bob"}},
        ])
        play.run(api, "me/me", "main")
        state = game.load()
        self.assertEqual(len(state["moves"]), 4)  # two valid human moves, two AI replies
        self.assertEqual(state["processed"], [1, 2, 3])
        self.assertEqual([n for n, _ in api.replies], [1, 2, 3])
        self.assertIn("couldn't read", api.replies[1][1])
        log = subprocess.run(["git", "--git-dir", str(self.remote), "log", "--oneline", "main"],
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("connect4: play #1, #2, #3", log)
        readme = (self.work / "README.md").read_text()
        self.assertIn("board-1-4-dark.svg", readme)
        self.assertTrue((self.work / "assets" / "connect4" / "board-1-4-dark.svg").exists())

    def test_an_issue_is_never_played_twice(self):
        state = game.new_state()
        state["processed"] = [7]
        game.save(state)
        api = FakeGitHub([{"number": 7, "title": "c4|drop|1", "user": {"login": "alice"}}])
        play.run(api, "me/me", "main", push=False)
        self.assertEqual(game.load()["moves"], [])
        self.assertIn("already played", api.replies[0][1])


if __name__ == "__main__":
    unittest.main()
