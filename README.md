# GitHub 开源项目活跃度看板

基于 Python + Streamlit + Altair 的 GitHub 开源项目活跃度可视化看板。

## 功能

- 横向柱状图：对比多个 repo 最近 90 天的 commit 数和 PR 合并数
- 折线图：每个 repo 的 star 增长趋势（按周聚合）
- 热力图：选定 repo 的「星期几 × 小时段」提交密度，推测核心贡献者时区
- 表格：最近 30 天 top 5 贡献者（按 commit 数排名）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

## 数据缓存

所有通过 GitHub API 获取的数据会在本地缓存 **1 小时**，缓存目录：

```
.cache/github_dashboard/
```

缓存为 JSON 文件，以请求 URL 的哈希值命名。如需强制刷新数据，删除该目录即可：

```bash
rm -rf .cache/github_dashboard/
```

## 配置 Personal Access Token

GitHub 公开 REST API 有速率限制（未认证 60 次/小时，认证后 5000 次/小时）。在应用**左侧边栏**的 Token 输入框中粘贴你的 Personal Access Token 即可提高限额。

> Token 仅在当前会话中使用，不会存储到任何远程服务器。

生成 Token 步骤：

1. 打开 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 无需勾选任何权限范围（公开仓库只读无需额外权限）
4. 复制生成的 Token 粘贴到侧边栏

## 项目结构

```
├── app.py          # Streamlit 主入口，UI 布局
├── fetcher.py      # GitHub API 数据抓取 + 本地缓存
├── metrics.py      # 指标计算（commit/PR 统计、star 增长、热力图数据、top 贡献者）
├── charts.py       # Altair 图表渲染
└── requirements.txt
```
