import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import live  # noqa: E402


def days(start: str, counts: list[int]) -> list[tuple[str, int]]:
    d0 = dt.date.fromisoformat(start)
    return [((d0 + dt.timedelta(days=i)).isoformat(), c) for i, c in enumerate(counts)]


class StreakTest(unittest.TestCase):
    def test_current_streak_survives_an_empty_today(self):
        cal = days("2026-10-20", [0, 1, 2, 3, 1, 4, 2, 0])  # the 27th has nothing yet
        s = live.streaks(cal, dt.date(2026, 10, 27))
        self.assertEqual(s["current"], 6)
        self.assertEqual(s["longest"], 6)
        self.assertEqual(s["longest_range"], ["2026-10-21", "2026-10-26"])

    def test_current_streak_counts_today(self):
        cal = days("2026-10-25", [5, 0, 1])
        self.assertEqual(live.streaks(cal, dt.date(2026, 10, 27))["current"], 1)

    def test_broken_streak(self):
        cal = days("2026-10-20", [1, 1, 1, 0, 0, 0, 0, 0])
        s = live.streaks(cal, dt.date(2026, 10, 27))
        self.assertEqual((s["current"], s["longest"]), (0, 3))


class LanguageTest(unittest.TestCase):
    def test_aggregates_excludes_and_folds(self):
        def repo(*langs):
            return {"languages": {"edges": [{"size": s, "node": {"name": n, "color": "#000"}} for n, s in langs]}}
        repos = [repo(("TypeScript", 600), ("CSS", 50)), repo(("Python", 300), ("Jupyter Notebook", 10_000)),
                 repo(("TypeScript", 0), ("Shell", 50))]
        out = live.languages(repos, {"Jupyter Notebook"}, top=2)
        self.assertEqual([lang["name"] for lang in out], ["TypeScript", "Python", "Other"])
        self.assertEqual(out[0]["repos"], 2)
        self.assertAlmostEqual(sum(lang["pct"] for lang in out), 100, delta=.2)


if __name__ == "__main__":
    unittest.main()
