from typing import Dict, List

import altair as alt
import pandas as pd


def activity_bar_chart(df: pd.DataFrame) -> alt.Chart:
    if df.empty:
        return alt.Chart().mark_bar().properties(title="No data")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Count"),
            y=alt.Y("repo:N", title="Repository"),
            color=alt.Color(
                "metric:N",
                title="Metric",
                scale=alt.Scale(scheme="category10"),
            ),
            tooltip=["repo", "metric", "count"],
        )
        .properties(
            title="Commits and Merged PRs (Last 90 Days)",
            width=600,
            height=alt.Step(40),
        )
        .configure_title(fontSize=16, anchor="start")
    )
    return chart


def stars_line_chart(stars_data: Dict[str, pd.DataFrame]) -> alt.Chart:
    all_dfs = []
    for repo, df in stars_data.items():
        if df.empty:
            continue
        df = df.copy()
        df["repo"] = repo
        all_dfs.append(df)

    if not all_dfs:
        return alt.Chart().mark_line().properties(title="No data")

    combined = pd.concat(all_dfs, ignore_index=True)

    chart = (
        alt.Chart(combined)
        .mark_line(point=True)
        .encode(
            x=alt.X("week:T", title="Week"),
            y=alt.Y("count:Q", title="Stars Added"),
            color=alt.Color(
                "repo:N",
                title="Repository",
                scale=alt.Scale(scheme="category10"),
            ),
            tooltip=["repo", "week", "count"],
        )
        .properties(
            title="Star Growth by Week",
            width=700,
            height=400,
        )
        .configure_title(fontSize=16, anchor="start")
        .interactive()
    )
    return chart


def commit_heatmap(df: pd.DataFrame, repo: str) -> alt.Chart:
    if df.empty:
        return alt.Chart().mark_rect().properties(title="No data")

    max_count = df["count"].max() if not df.empty else 1

    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X(
                "hour:O",
                title="Hour of Day (UTC)",
                axis=alt.Axis(values=list(range(0, 24, 2))),
            ),
            y=alt.Y("day:O", title="Day of Week"),
            color=alt.Color(
                "count:Q",
                title="Commits",
                scale=alt.Scale(
                    scheme="viridis",
                    domain=[0, max_count],
                ),
            ),
            tooltip=["day", "hour", "count"],
        )
        .properties(
            title=f"Commit Density by Day × Hour — {repo}",
            width=700,
            height=280,
        )
        .configure_title(fontSize=16, anchor="start")
    )
    return chart
