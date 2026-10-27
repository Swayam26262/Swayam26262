"""Play every pending Connect Four move (one per open `c4|drop|N` issue).

Run by .github/workflows/connect4.yml. All pending issues are handled oldest
first, so a run that GitHub cancels in a burst of moves loses nothing: the
next run picks those issues up. Issues are only answered and closed after the
new board is pushed, and handled issue numbers are remembered in the state so
nothing is ever played twice.

  python generator/connect4/play.py            # needs GITHUB_TOKEN and GITHUB_REPOSITORY
  python generator/connect4/play.py --render   # just redraw the board and README section
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connect4 import game  # noqa: E402

API = "https://api.github.com"
PROFILE = "https://github.com/{owner}"


class GitHub:
    def __init__(self, repo: str, token: str):
        self.repo, self.token = repo, token

    def _call(self, method: str, path: str, body: dict | None = None):
        req = urllib.request.Request(
            f"{API}/repos/{self.repo}{path}", method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "connect4-readme"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        return json.loads(raw) if raw else None

    def pending(self) -> list[dict]:
        out, page = [], 1
        while True:
            batch = self._call("GET", f"/issues?state=open&sort=created&direction=asc&per_page=100&page={page}")
            out += [i for i in batch if "pull_request" not in i and i["title"].strip().startswith("c4|")]
            if len(batch) < 100:
                return out
            page += 1

    def reply(self, number: int, body: str) -> None:
        self._call("POST", f"/issues/{number}/comments", {"body": body})
        self._call("PATCH", f"/issues/{number}", {"state": "closed", "state_reason": "completed"})


def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=game.ROOT, check=True)


def publish(message: str, branch: str) -> None:
    git("add", "README.md", str(game.STATE.relative_to(game.ROOT)), str(game.ASSET_DIR.relative_to(game.ROOT)))
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=game.ROOT).returncode == 0:
        return
    git("-c", "user.name=github-actions[bot]",
        "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-q", "-m", message)
    for attempt in range(4):
        try:
            git("pull", "-q", "--rebase", "origin", branch)
            git("push", "-q", "origin", f"HEAD:{branch}")
            return
        except subprocess.CalledProcessError:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("could not push the new board")


def footer(owner: str) -> str:
    return f"\n\n[Back to the board]({PROFILE.format(owner=owner)}) 🎮"


def run(api, repo: str, branch: str, push: bool = True) -> list[tuple[int, str]]:
    state = game.load()
    owner = repo.split("/")[0]
    done = set(state["processed"])
    replies: list[tuple[int, str]] = []
    for issue in api.pending():
        number, user = issue["number"], issue["user"]["login"]
        if number in done:  # played already; the earlier run just didn't get to close it
            replies.append((number, "This move was already played." + footer(owner)))
            continue
        col = game.parse_title(issue["title"])
        if col is None:
            message = ("I couldn't read that move. Use the column buttons on the profile: they open an issue "
                       "titled like `c4|drop|4`.")
        else:
            message = game.play(state, col, user)
        state["processed"] = (state["processed"] + [number])[-500:]
        done.add(number)
        replies.append((number, f"@{user} {message}" + footer(owner)))
    if not replies:
        print("no pending moves")
        return []
    game.save(state)
    game.write_assets(state)
    game.update_readme(state, repo)
    if push:
        moves = ", ".join(f"#{n}" for n, _ in replies)
        publish(f"connect4: play {moves}", branch)
    for number, body in replies:
        api.reply(number, body)
        print(f"answered #{number}")
    return replies


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--render", action="store_true", help="only redraw the board and README section")
    args = ap.parse_args()
    repo = os.environ.get("GITHUB_REPOSITORY", "Swayam26262/Swayam26262")
    if args.render:
        state = game.load()
        game.save(state)
        game.write_assets(state)
        game.update_readme(state, repo)
        return 0
    api = GitHub(repo, os.environ["GITHUB_TOKEN"])
    run(api, repo, os.environ.get("GITHUB_REF_NAME", "main"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
