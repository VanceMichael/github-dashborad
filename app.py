from typing import Optional, List, Dict, Any

import streamlit as st

import fetcher
import metrics
import charts


def parse_repos(text: str) -> List[str]:
    repos = []
    for line in text.strip().splitlines():
        repo = line.strip()
        if repo and "/" in repo:
            repos.append(repo)
    return repos


def fetch_all_data(
    repos: List[str],
    token: Optional[str],
    progress_cb,
):
    since_90, until_90 = metrics.get_90_day_window()
    since_30, until_30 = metrics.get_30_day_window()

    total = len(repos)
    activities = []
    stars_data: Dict[str, Any] = {}
    commits_90_data: Dict[str, Any] = {}
    commits_30_data: Dict[str, Any] = {}

    for i, repo in enumerate(repos):
        progress_cb(f"Fetching data for {repo}...", (i + 1) / total)

        commits_90 = fetcher.fetch_commits(repo, since_90, until_90, token)
        merged_prs_90 = fetcher.fetch_merged_prs(repo, since_90, until_90, token)
        activity = metrics.compute_repo_activity(repo, commits_90, merged_prs_90)
        activities.append(activity)
        commits_90_data[repo] = commits_90

        stargazers = fetcher.fetch_stargazers(repo, token)
        stars_df = metrics.compute_stars_by_week(stargazers)
        stars_data[repo] = stars_df

        commits_30 = fetcher.fetch_commits(repo, since_30, until_30, token)
        commits_30_data[repo] = commits_30

    progress_cb("Done!", 1.0)

    return {
        "activities": activities,
        "stars_data": stars_data,
        "commits_90_data": commits_90_data,
        "commits_30_data": commits_30_data,
    }


def main():
    st.set_page_config(page_title="GitHub Activity Dashboard", layout="wide")

    st.title("GitHub Open Source Activity Dashboard")

    with st.sidebar:
        st.header("Settings")
        token = st.text_input(
            "GitHub Personal Access Token (optional)",
            type="password",
            help="Improves rate limits",
        )
        st.markdown(
            "Data is cached locally for 1 hour at `~/.github_dashboard_cache`"
        )
        st.markdown(
            "Get a token: https://github.com/settings/tokens"
        )

    st.subheader("Enter repositories (one per line, format: owner/name)")

    default_repos = "vuejs/vue\nfacebook/react\npython/cpython"
    repos_text = st.text_area("Repositories", value=default_repos, height=120)

    analyze = st.button("Analyze", type="primary")

    if analyze:
        repos = parse_repos(repos_text)
        if not repos:
            st.error("Please enter at least one repository in owner/name format.")
            st.session_state.clear()
            return

        progress_placeholder = st.empty()
        progress_bar = st.progress(0.0)

        def progress_cb(status: str, pct: float):
            progress_placeholder.text(status)
            progress_bar.progress(pct)

        try:
            data = fetch_all_data(repos, token or None, progress_cb)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.session_state.clear()
            return

        progress_placeholder.empty()
        progress_bar.empty()

        st.session_state["data"] = data
        st.session_state["repos"] = repos

    if "data" not in st.session_state or "repos" not in st.session_state:
        st.info("Enter repository names and click Analyze to begin.")
        return

    data = st.session_state["data"]
    repos = st.session_state["repos"]

    st.divider()

    activity_df = metrics.activity_to_dataframe(data["activities"])
    st.altair_chart(charts.activity_bar_chart(activity_df), use_container_width=True)

    st.divider()

    st.altair_chart(
        charts.stars_line_chart(data["stars_data"]), use_container_width=True
    )

    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Heatmap & Contributors")
        selected_repo = st.selectbox("Select a repository", repos)

    if selected_repo:
        with col2:
            heatmap_df = metrics.compute_commit_heatmap(
                data["commits_90_data"].get(selected_repo, [])
            )
            st.altair_chart(
                charts.commit_heatmap(heatmap_df, selected_repo),
                use_container_width=True,
            )

        st.divider()

        st.subheader(f"Top 5 Contributors — {selected_repo} (Last 30 Days)")
        contributors_df = metrics.compute_top_contributors(
            data["commits_30_data"].get(selected_repo, [])
        )
        st.dataframe(contributors_df, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
