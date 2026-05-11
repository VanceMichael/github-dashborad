import streamlit as st
import pandas as pd
from fetcher import GitHubFetcher
import metrics
import charts


def init_session_state():
    if "commit_pr_data" not in st.session_state:
        st.session_state.commit_pr_data = None
    if "star_data" not in st.session_state:
        st.session_state.star_data = None
    if "repo_commits_90" not in st.session_state:
        st.session_state.repo_commits_90 = {}
    if "repo_commits_30" not in st.session_state:
        st.session_state.repo_commits_30 = {}
    if "analyzed_repos" not in st.session_state:
        st.session_state.analyzed_repos = []
    if "analysis_done" not in st.session_state:
        st.session_state.analysis_done = False


def main():
    st.set_page_config(
        page_title="GitHub Repo Activity Dashboard",
        page_icon="📊",
        layout="wide"
    )

    init_session_state()

    st.title("📊 GitHub Open Source Project Activity Dashboard")
    st.markdown("---")

    with st.sidebar:
        st.header("⚙️ Settings")
        github_token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            placeholder="ghp_xxxxxxxxxxxx",
            help="Enter your GitHub token to increase API rate limits"
        )

        st.markdown("---")
        st.markdown("### Cache Info")
        st.markdown("Data is cached locally for 1 hour in `.cache/` directory")

        st.markdown("---")
        st.markdown("### How to get a token:")
        st.markdown("1. Go to GitHub Settings → Developer settings → Personal access tokens")
        st.markdown("2. Generate a new token with `public_repo` scope")
        st.markdown("3. Paste it here")

    fetcher = GitHubFetcher(token=github_token if github_token else None)

    st.header("📝 Enter Repositories")
    default_repos = """vuejs/vue
facebook/react
tensorflow/tensorflow"""
    
    repo_input = st.text_area(
        "Repositories (one per line, format: owner/name)",
        value=default_repos,
        height=120
    )

    repos = [r.strip() for r in repo_input.strip().split("\n") if r.strip()]
    repos = list(set(repos))

    analyze_button = st.button("🔍 Analyze", type="primary")

    if analyze_button and repos:
        all_commit_pr_data = []
        all_star_data = []
        repo_commits_90 = {}
        repo_commits_30 = {}

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, repo in enumerate(repos):
            progress = (i) / len(repos)
            progress_bar.progress(progress)
            status_text.text(f"Fetching data for {repo}...")

            try:
                commits_90 = fetcher.get_commits(repo, days=90)
                pulls_90 = fetcher.get_pulls(repo, days=90)
                stargazers = fetcher.get_stargazers(repo)
                commits_30 = fetcher.get_commits(repo, days=30)

                commit_pr_df = metrics.calculate_commit_pr_counts(commits_90, pulls_90, repo)
                all_commit_pr_data.append(commit_pr_df)

                star_df = metrics.calculate_star_growth(stargazers, repo)
                all_star_data.append(star_df)

                repo_commits_90[repo] = commits_90
                repo_commits_30[repo] = commits_30

            except Exception as e:
                st.error(f"Error fetching data for {repo}: {str(e)}")

        progress_bar.progress(1.0)
        status_text.text("Done!")

        st.session_state.commit_pr_data = all_commit_pr_data
        st.session_state.star_data = all_star_data
        st.session_state.repo_commits_90 = repo_commits_90
        st.session_state.repo_commits_30 = repo_commits_30
        st.session_state.analyzed_repos = repos
        st.session_state.analysis_done = True

    elif not repos and analyze_button:
        st.warning("Please enter at least one repository")

    if st.session_state.analysis_done and st.session_state.analyzed_repos:
        st.markdown("---")
        st.header("📈 Analysis Results")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Commits vs PRs Merged")
            if st.session_state.commit_pr_data:
                commit_pr_combined = pd.concat(st.session_state.commit_pr_data, ignore_index=True)
                commit_pr_chart = charts.create_commit_pr_chart(commit_pr_combined)
                st.altair_chart(commit_pr_chart, use_container_width=True)
            else:
                st.info("No data available")

        with col2:
            st.subheader("⭐ Star Growth")
            if st.session_state.star_data:
                star_combined = pd.concat(st.session_state.star_data, ignore_index=True)
                star_chart = charts.create_star_growth_chart(star_combined)
                st.altair_chart(star_chart, use_container_width=True)
            else:
                st.info("No data available")

        st.markdown("---")

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🔥 Commit Heatmap")
            if st.session_state.analyzed_repos:
                selected_repo = st.selectbox(
                    "Select a repository for heatmap",
                    st.session_state.analyzed_repos,
                    key="heatmap_select"
                )
                if selected_repo in st.session_state.repo_commits_90:
                    heatmap_df = metrics.calculate_commit_heatmap(st.session_state.repo_commits_90[selected_repo])
                    heatmap_chart = charts.create_commit_heatmap(heatmap_df, selected_repo)
                    st.altair_chart(heatmap_chart, use_container_width=True)

        with col4:
            st.subheader("👥 Top Contributors")
            if st.session_state.analyzed_repos:
                selected_repo_contrib = st.selectbox(
                    "Select a repository for contributors",
                    st.session_state.analyzed_repos,
                    key="contrib_select"
                )
                if selected_repo_contrib in st.session_state.repo_commits_30:
                    contributors_df = metrics.calculate_top_contributors(
                        st.session_state.repo_commits_30[selected_repo_contrib],
                        top_n=5
                    )
                    if not contributors_df.empty:
                        st.dataframe(
                            contributors_df,
                            column_config={
                                "author": "Contributor",
                                "commits": "Commits",
                                "avatar_url": None
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        contrib_chart = charts.create_contributors_table(contributors_df)
                        st.altair_chart(contrib_chart, use_container_width=True)
                    else:
                        st.info("No contributor data available")

    st.markdown("---")
    st.markdown(
        "💡 **Tip:** Use a GitHub Personal Access Token in the sidebar to increase API rate limits. "
        "Without a token, you're limited to 60 requests per hour."
    )


if __name__ == "__main__":
    main()
