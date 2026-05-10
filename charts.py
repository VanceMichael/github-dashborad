import altair as alt
import pandas as pd


def bar_commit_pr(df: pd.DataFrame) -> alt.Chart:
    melted = df.melt(id_vars="repo", value_vars=["commits", "merged_prs"],
                     var_name="metric", value_name="count")
    melted["metric"] = melted["metric"].map({
        "commits": "Commits",
        "merged_prs": "Merged PRs",
    })
    return (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            y=alt.Y("repo:N", title="Repo", sort=alt.SortField("count", order="descending")),
            x=alt.X("count:Q", title="Count (last 90 days)"),
            color=alt.Color("metric:N", title="Metric", scale=alt.Scale(range=["#4C78A8", "#F58518"])),
        )
        .properties(height=alt.Step(30))
    )


def line_star_growth(df: pd.DataFrame) -> alt.Chart:
    if df.empty:
        return alt.Chart().mark_text(text="No data").properties(width=700, height=300)
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("week_start:T", title="Week"),
            y=alt.Y("cumulative_stars:Q", title="Cumulative Stars"),
            color=alt.Color("repo:N", title="Repo"),
        )
        .properties(width=700, height=350)
    )


def heatmap_commit(df: pd.DataFrame) -> alt.Chart:
    if df.empty:
        return alt.Chart().mark_text(text="No data").properties(width=700, height=300)
    return (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("hour:O", title="Hour of Day (UTC)"),
            y=alt.Y("day_name:O", title="Day of Week",
                     sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
            color=alt.Color("count:Q", title="Commits",
                            scale=alt.Scale(scheme="oranges")),
            tooltip=["day_name", "hour", "count"],
        )
        .properties(width=700, height=250)
    )


def contributor_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["#", "Contributor", "Commits"])
    df = df.copy()
    df.index = range(1, len(df) + 1)
    df.index.name = "#"
    df = df.reset_index()
    return df
