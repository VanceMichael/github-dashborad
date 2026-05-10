from datetime import datetime, timedelta, timezone

import streamlit as st

from fetcher import fetch_commits, fetch_merged_prs, fetch_stargazers
from metrics import commit_pr_counts, star_growth, commit_heatmap, top_contributors
from charts import bar_commit_pr, line_star_growth, heatmap_commit, contributor_table

st.set_page_config(page_title="GitHub 活跃度看板", layout="wide")

token = st.sidebar.text_input("GitHub Personal Access Token", type="password",
                               help="粘贴 Token 可将 API 限流从 60 次/小时提升到 5000 次/小时")
st.sidebar.caption("Token 仅在当前会话中使用，不会上传到任何服务器。")

st.title("GitHub 开源项目活跃度看板")

repo_input = st.text_area("输入 repo（owner/name 格式，一行一个）",
                           value="vuejs/vue\nfacebook/react", height=120)
repos = [r.strip() for r in repo_input.strip().splitlines() if r.strip()]

if st.button("分析", type="primary"):
    if not repos:
        st.warning("请至少输入一个 repo")
        st.stop()

    since_90 = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    commits_by_repo: dict = {}
    prs_by_repo: dict = {}
    stars_by_repo: dict = {}

    progress = st.progress(0, text="正在获取数据...")
    total = len(repos)
    for i, repo in enumerate(repos):
        parts = repo.split("/")
        if len(parts) != 2:
            st.error(f"无效格式: {repo}，请使用 owner/name")
            continue
        owner, name = parts
        label = repo
        try:
            with st.spinner(f"获取 {label} 的 commits..."):
                commits_by_repo[label] = fetch_commits(owner, name, since_90, token or None)
            with st.spinner(f"获取 {label} 的 merged PRs..."):
                prs_by_repo[label] = fetch_merged_prs(owner, name, since_90, token or None)
            with st.spinner(f"获取 {label} 的 stargazers..."):
                stars_by_repo[label] = fetch_stargazers(owner, name, token or None)
        except Exception as e:
            st.error(f"获取 {label} 失败: {e}")
        progress.progress((i + 1) / total, text=f"已完成 {i + 1}/{total}")

    progress.empty()

    if not commits_by_repo:
        st.error("未能获取任何数据，请检查 repo 名称或网络。")
        st.stop()

    st.session_state["commits_by_repo"] = commits_by_repo
    st.session_state["prs_by_repo"] = prs_by_repo
    st.session_state["stars_by_repo"] = stars_by_repo

if "commits_by_repo" not in st.session_state:
    st.info("输入 repo 后点击「分析」开始")
    st.stop()

commits_by_repo = st.session_state["commits_by_repo"]
prs_by_repo = st.session_state["prs_by_repo"]
stars_by_repo = st.session_state["stars_by_repo"]

st.header("Commits vs Merged PRs（最近 90 天）")
df_bar = commit_pr_counts(commits_by_repo, prs_by_repo)
st.altair_chart(bar_commit_pr(df_bar), use_container_width=True)

st.header("Star 增长趋势（按周聚合）")
df_stars = star_growth(stars_by_repo)
st.altair_chart(line_star_growth(df_stars), use_container_width=True)

st.header("提交密度热力图")
selected_repo = st.selectbox("选择 repo", list(commits_by_repo.keys()))
df_heat = commit_heatmap(commits_by_repo.get(selected_repo, []))
st.altair_chart(heatmap_commit(df_heat), use_container_width=True)

st.header(f"Top 5 贡献者（最近 30 天 — {selected_repo}）")
df_top = top_contributors(commits_by_repo.get(selected_repo, []))
st.dataframe(contributor_table(df_top), use_container_width=True, hide_index=True)
