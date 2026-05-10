from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

import pandas as pd


def _utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_90_day_window() -> Tuple[str, str]:
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=90)
    return _utc_iso(since), _utc_iso(until)


def get_30_day_window() -> Tuple[str, str]:
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=30)
    return _utc_iso(since), _utc_iso(until)


def compute_repo_activity(
    repo: str,
    commits: List[Dict[str, Any]],
    merged_prs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "repo": repo,
        "commits": len(commits),
        "merged_prs": len(merged_prs),
    }


def activity_to_dataframe(activities: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for act in activities:
        rows.append(
            {"repo": act["repo"], "metric": "Commits", "count": act["commits"]}
        )
        rows.append(
            {"repo": act["repo"], "metric": "Merged PRs", "count": act["merged_prs"]}
        )
    return pd.DataFrame(rows)


def compute_stars_by_week(
    stargazers: List[Dict[str, Any]],
) -> pd.DataFrame:
    rows = []
    for star in stargazers:
        starred_at = star.get("starred_at")
        if not starred_at:
            continue
        dt = datetime.strptime(starred_at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        week_start = dt - timedelta(days=dt.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        rows.append({"week": week_start.date()})
    if not rows:
        return pd.DataFrame(columns=["week", "count"])
    df = pd.DataFrame(rows)
    df = df.groupby("week").size().reset_index(name="count")
    df = df.sort_values("week").reset_index(drop=True)
    return df


def compute_commit_heatmap(commits: List[Dict[str, Any]]) -> pd.DataFrame:
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    rows = []
    for commit in commits:
        commit_info = commit.get("commit", {}) or {}
        author_info = commit_info.get("author", {}) or {}
        date_str = author_info.get("date")
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except Exception:
            continue
        day_name = day_names[dt.weekday()]
        hour = dt.hour
        rows.append({"day": day_name, "hour": hour})
    if not rows:
        return pd.DataFrame(columns=["day", "hour", "count"])
    df = pd.DataFrame(rows)
    df = df.groupby(["day", "hour"]).size().reset_index(name="count")
    all_days = pd.DataFrame({"day": day_names, "_key": 0})
    all_hours = pd.DataFrame({"hour": list(range(24)), "_key": 0})
    grid = pd.merge(all_days, all_hours, on="_key").drop(columns="_key")
    result = pd.merge(grid, df, on=["day", "hour"], how="left")
    result["count"] = result["count"].fillna(0).astype(int)
    result["day"] = pd.Categorical(result["day"], categories=day_names, ordered=True)
    result = result.sort_values(["day", "hour"]).reset_index(drop=True)
    return result


def compute_top_contributors(commits: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for commit in commits:
        author = commit.get("author") or {}
        login = author.get("login")
        commit_info = commit.get("commit", {}) or {}
        commit_author = commit_info.get("author", {}) or {}
        name = commit_author.get("name")
        if not login and not name:
            continue
        rows.append({"login": login or name, "name": name or login})
    if not rows:
        return pd.DataFrame(columns=["rank", "login", "name", "commits"])
    df = pd.DataFrame(rows)
    grouped = (
        df.groupby(["login", "name"]).size().reset_index(name="commits")
    )
    grouped = grouped.sort_values("commits", ascending=False).head(5)
    grouped = grouped.reset_index(drop=True)
    grouped.insert(0, "rank", grouped.index + 1)
    return grouped
