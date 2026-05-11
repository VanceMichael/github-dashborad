import altair as alt
import pandas as pd
from typing import Optional


def create_commit_pr_chart(df: pd.DataFrame) -> alt.Chart:
    chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("repo:N", title="Repository", sort="-x"),
        x=alt.X("count:Q", title="Count"),
        color=alt.Color("metric:N", title="Metric", scale=alt.Scale(scheme="category10")),
        row=alt.Row("metric:N", title=None),
        tooltip=["repo", "metric", "count"]
    ).properties(
        title="Commits vs PRs Merged (Last 90 Days)",
        height=alt.Step(30)
    ).configure_facet(
        spacing=0
    ).configure_view(
        stroke=None
    )
    return chart


def create_star_growth_chart(df: pd.DataFrame) -> alt.Chart:
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_point()
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("cumulative_stars:Q", title="Cumulative Stars"),
        color=alt.Color("repo:N", title="Repository"),
        tooltip=["repo", "date", "cumulative_stars", "stars"]
    ).properties(
        title="Star Growth (Weekly Aggregation)",
        height=400
    ).interactive()
    return chart


def create_commit_heatmap(df: pd.DataFrame, repo_name: str) -> alt.Chart:
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_rect()
    
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X("hour:O", title="Hour of Day (UTC)"),
        y=alt.Y("day:O", title="Day of Week"),
        color=alt.Color("count:Q", title="Commits", scale=alt.Scale(scheme="blues")),
        tooltip=["day", "hour", "count"]
    ).properties(
        title=f"Commit Heatmap (Day × Hour) - {repo_name}",
        height=300
    )
    return chart


def create_contributors_table(df: pd.DataFrame) -> alt.Chart:
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text()
    
    chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("author:N", title="Contributor", sort="-x"),
        x=alt.X("commits:Q", title="Number of Commits"),
        tooltip=["author", "commits"]
    ).properties(
        title="Top 5 Contributors (Last 30 Days)",
        height=alt.Step(40)
    )
    return chart
