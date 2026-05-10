from datetime import datetime, timedelta, timezone

import pandas as pd


def _iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def commit_pr_counts(commits_by_repo: dict[str, list], prs_by_repo: dict[str, list]) -> pd.DataFrame:
    rows = []
    for repo, commits in commits_by_repo.items():
        prs = prs_by_repo.get(repo, [])
        rows.append({
            "repo": repo,
            "commits": len(commits),
            "merged_prs": len(prs),
        })
    return pd.DataFrame(rows)


def star_growth(stargazers_by_repo: dict[str, list], weeks: int = 13) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(weeks=weeks)
    rows = []
    for repo, stars in stargazers_by_repo.items():
        dates = []
        for s in stars:
            starred_at = s.get("starred_at")
            if starred_at:
                dates.append(datetime.fromisoformat(starred_at.replace("Z", "+00:00")))
        if not dates:
            continue
        df = pd.DataFrame({"starred_at": dates})
        df["week"] = df["starred_at"].dt.isocalendar().week.astype(int)
        df["year"] = df["starred_at"].dt.isocalendar().year.astype(int)
        weekly = df.groupby(["year", "week"]).size().reset_index(name="new_stars")
        weekly["week_start"] = weekly.apply(
            lambda r: datetime.fromisocalendar(int(r["year"]), int(r["week"]), 1),
            axis=1,
        )
        weekly = weekly[weekly["week_start"] >= cutoff.replace(tzinfo=None)]
        weekly = weekly.sort_values("week_start")
        weekly["cumulative_stars"] = weekly["new_stars"].cumsum()
        weekly["repo"] = repo
        rows.append(weekly[["repo", "week_start", "cumulative_stars"]])
    if not rows:
        return pd.DataFrame(columns=["repo", "week_start", "cumulative_stars"])
    return pd.concat(rows, ignore_index=True)


def commit_heatmap(commits: list) -> pd.DataFrame:
    if not commits:
        return pd.DataFrame(columns=["day_of_week", "hour", "count"])
    rows = []
    for c in commits:
        sha = c.get("sha", "")
        commit_data = c.get("commit", {})
        author = commit_data.get("author", commit_data.get("committer", {}))
        date_str = author.get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        rows.append({"day_of_week": dt.weekday(), "hour": dt.hour})
    if not rows:
        return pd.DataFrame(columns=["day_of_week", "hour", "count"])
    df = pd.DataFrame(rows)
    result = df.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result["day_name"] = result["day_of_week"].map(lambda d: day_names[d])
    result["day_of_week"] = result["day_of_week"].astype(int)
    result["hour"] = result["hour"].astype(int)
    return result


def top_contributors(commits: list, top_n: int = 5) -> pd.DataFrame:
    if not commits:
        return pd.DataFrame(columns=["contributor", "commits"])
    since = _iso(30)
    rows = []
    for c in commits:
        commit_data = c.get("commit", {})
        author = commit_data.get("author", {})
        date_str = author.get("date", "")
        if date_str < since:
            continue
        name = author.get("name", "Unknown")
        rows.append(name)
    if not rows:
        return pd.DataFrame(columns=["contributor", "commits"])
    df = pd.DataFrame({"contributor": rows})
    counts = df["contributor"].value_counts().head(top_n).reset_index()
    counts.columns = ["contributor", "commits"]
    return counts
