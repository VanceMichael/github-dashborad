import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def calculate_commit_pr_counts(commits: List[Dict], pulls: List[Dict], repo_name: str) -> pd.DataFrame:
    commit_count = len(commits)
    pr_count = len(pulls)
    
    return pd.DataFrame({
        "repo": [repo_name, repo_name],
        "metric": ["Commits", "PRs Merged"],
        "count": [commit_count, pr_count]
    })


def calculate_star_growth(stargazers: List[Dict], repo_name: str) -> pd.DataFrame:
    if not stargazers:
        return pd.DataFrame(columns=["repo", "date", "stars", "cumulative_stars"])
    
    star_dates = []
    for star in stargazers:
        starred_at = star.get("starred_at")
        if starred_at:
            star_dates.append(datetime.strptime(starred_at, "%Y-%m-%dT%H:%M:%SZ"))
    
    if not star_dates:
        return pd.DataFrame(columns=["repo", "date", "stars", "cumulative_stars"])
    
    df = pd.DataFrame({"date": star_dates})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    weekly = df.resample("W").size().reset_index(name="stars")
    weekly["cumulative_stars"] = weekly["stars"].cumsum()
    weekly["repo"] = repo_name
    
    one_year_ago = datetime.now() - timedelta(days=365)
    weekly = weekly[weekly["date"] >= one_year_ago]
    
    return weekly


def calculate_commit_heatmap(commits: List[Dict]) -> pd.DataFrame:
    if not commits:
        return pd.DataFrame(columns=["day", "hour", "count"])
    
    commit_times = []
    for commit in commits:
        commit_info = commit.get("commit", {})
        author_info = commit_info.get("author", {})
        date_str = author_info.get("date")
        if date_str:
            commit_times.append(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ"))
    
    if not commit_times:
        return pd.DataFrame(columns=["day", "hour", "count"])
    
    df = pd.DataFrame({"datetime": commit_times})
    df["day"] = df["datetime"].dt.day_name()
    df["hour"] = df["datetime"].dt.hour
    
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["day"] = pd.Categorical(df["day"], categories=day_order, ordered=True)
    
    heatmap = df.groupby(["day", "hour"]).size().reset_index(name="count")
    
    all_combinations = pd.MultiIndex.from_product(
        [day_order, range(24)],
        names=["day", "hour"]
    ).to_frame(index=False)
    
    heatmap = all_combinations.merge(heatmap, on=["day", "hour"], how="left").fillna(0)
    heatmap["count"] = heatmap["count"].astype(int)
    
    return heatmap


def calculate_top_contributors(commits: List[Dict], top_n: int = 5) -> pd.DataFrame:
    if not commits:
        return pd.DataFrame(columns=["author", "commits", "avatar_url"])
    
    author_counts = {}
    for commit in commits:
        author = commit.get("author")
        if author:
            login = author.get("login")
            if login:
                if login not in author_counts:
                    author_counts[login] = {
                        "commits": 0,
                        "avatar_url": author.get("avatar_url", "")
                    }
                author_counts[login]["commits"] += 1
    
    if not author_counts:
        return pd.DataFrame(columns=["author", "commits", "avatar_url"])
    
    df = pd.DataFrame([
        {"author": login, **data}
        for login, data in author_counts.items()
    ])
    
    df = df.sort_values("commits", ascending=False).head(top_n).reset_index(drop=True)
    return df
