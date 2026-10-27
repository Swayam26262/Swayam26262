"""Live data for the dynamic cards: GitHub (GraphQL, needs a token) and LeetCode.

Results are cached in data/live.json so local builds (and CI runs where an API
hiccups) still render the last known numbers instead of failing.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "data" / "live.json"
UA = "Swayam26262-profile-readme (+https://github.com/Swayam26262/Swayam26262)"

PROFILE_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    login name createdAt
    followers { totalCount }
    following { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        name stargazerCount forkCount pushedAt
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""

YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def _post(url: str, body: dict, headers: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=40) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def _gql(query: str, token: str, **variables) -> dict:
    return _post("https://api.github.com/graphql", {"query": query, "variables": variables},
                 {"Authorization": f"bearer {token}"})


def streaks(days: list[tuple[str, int]], today: dt.date) -> dict:
    """Current and longest daily contribution streaks from (iso-date, count) pairs."""
    counts = {d: c for d, c in days}
    longest = run = 0
    start = best = None
    for d, c in sorted(days):
        if c > 0:
            run += 1
            start = start if run > 1 else d
            if run > longest:
                longest, best = run, (start, d)
        else:
            run = 0
    day = today if counts.get(today.isoformat(), 0) > 0 else today - dt.timedelta(days=1)
    current = 0
    while counts.get(day.isoformat(), 0) > 0:
        current += 1
        day -= dt.timedelta(days=1)
    return {"current": current, "longest": longest, "longest_range": list(best) if best else None}


def languages(repos: list[dict], exclude: set[str], top: int = 6) -> list[dict]:
    sizes: dict[str, list] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in exclude:
                continue
            entry = sizes.setdefault(name, [0, edge["node"]["color"] or "#8b949e", 0])
            entry[0] += edge["size"]
            entry[2] += 1
    total = sum(v[0] for v in sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1][0])
    out = [{"name": n, "color": c, "bytes": b, "repos": r, "pct": round(100 * b / total, 1)}
           for n, (b, c, r) in ranked[:top]]
    rest = sum(v[0] for _, v in ranked[top:])
    if rest:
        out.append({"name": "Other", "color": "#8b949e", "bytes": rest, "repos": 0, "pct": round(100 * rest / total, 1)})
    return out


def fetch_github(login: str, token: str, exclude_languages: set[str], today: dt.date | None = None) -> dict:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    repos, after, user = [], None, None
    while True:
        user = _gql(PROFILE_QUERY, token, login=login, after=after)["user"]
        page = user["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]

    created = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).date()
    days: list[tuple[str, int]] = []
    commits_total = contributions_total = commits_year = 0
    for year in range(created.year, today.year + 1):
        start = max(dt.date(year, 1, 1), created)
        end = min(dt.date(year, 12, 31), today)
        coll = _gql(YEAR_QUERY, token, login=login, **{"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"})
        coll = coll["user"]["contributionsCollection"]
        commits = coll["totalCommitContributions"] + coll["restrictedContributionsCount"]
        commits_total += commits
        if year == today.year:
            commits_year = commits
        contributions_total += coll["contributionCalendar"]["totalContributions"]
        for week in coll["contributionCalendar"]["weeks"]:
            days += [(d["date"], d["contributionCount"]) for d in week["contributionDays"]]
    days = sorted({d: c for d, c in days if d <= today.isoformat()}.items())

    last_year = [(d, c) for d, c in days if d > (today - dt.timedelta(days=365)).isoformat()]
    # the trailing 53 weeks, Sunday-aligned, as a GitHub-style calendar
    first = today - dt.timedelta(days=(today.weekday() + 1) % 7 + 52 * 7)
    index = dict(days)
    calendar = [[(first + dt.timedelta(days=w * 7 + d)).isoformat() for d in range(7)] for w in range(53)]
    calendar = [[(day, index.get(day, 0)) for day in week if day <= today.isoformat()] for week in calendar]
    busiest = max(days, key=lambda dc: dc[1], default=("", 0))
    weekday = [0] * 7
    for d, c in last_year:
        weekday[dt.date.fromisoformat(d).weekday()] += c

    return {
        "login": user["login"],
        "name": user["name"],
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "following": user["following"]["totalCount"],
        "public_repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "pull_requests": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "contributed_to": user["repositoriesContributedTo"]["totalCount"],
        "commits_total": commits_total,
        "commits_year": commits_year,
        "contributions_total": contributions_total,
        "contributions_last_year": sum(c for _, c in last_year),
        "active_days_last_year": sum(1 for _, c in last_year if c),
        "busiest_day": {"date": busiest[0], "count": busiest[1]},
        "weekday_totals": weekday,
        "streak": streaks(days, today),
        "calendar": calendar,
        "languages": languages(repos, exclude_languages),
    }


LEETCODE_QUERY = """
query($username: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $username) {
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
}"""


def fetch_leetcode(username: str) -> dict:
    data = _post("https://leetcode.com/graphql", {"query": LEETCODE_QUERY, "variables": {"username": username}},
                 {"Referer": f"https://leetcode.com/{username}/", "Origin": "https://leetcode.com"})
    user = data["matchedUser"]
    if not user:
        raise RuntimeError(f"LeetCode user {username!r} not found")
    totals = {q["difficulty"]: q["count"] for q in data["allQuestionsCount"]}
    solved = {q["difficulty"]: q["count"] for q in user["submitStatsGlobal"]["acSubmissionNum"]}
    return {
        "username": username,
        "ranking": user["profile"]["ranking"],
        "solved": solved,      # {"All": n, "Easy": n, "Medium": n, "Hard": n}
        "totals": totals,
    }


def load() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def refresh(profile: dict) -> dict:
    """Refresh whatever we can; keep cached values for sources that fail."""
    data = load()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    token = os.environ.get("GITHUB_TOKEN")
    person, links = profile["person"], profile["links"]
    if token:
        try:
            exclude = set(profile.get("stats", {}).get("exclude_languages", []))
            data["github"] = fetch_github(person["github"], token, exclude)
            data["github"]["fetched_at"] = now
            print("github: ok")
        except Exception as exc:  # keep the previous snapshot
            print(f"github: FAILED, keeping cached data ({exc})")
    else:
        print("github: skipped (no GITHUB_TOKEN)")
    if links.get("leetcode_user"):
        try:
            data["leetcode"] = fetch_leetcode(links["leetcode_user"])
            data["leetcode"]["fetched_at"] = now
            print("leetcode: ok")
        except Exception as exc:
            print(f"leetcode: FAILED, keeping cached data ({exc})")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    return data
