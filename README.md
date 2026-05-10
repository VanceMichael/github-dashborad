# GitHub Activity Dashboard

一个基于 Python + Streamlit + Altair 的 GitHub 开源项目活跃度看板。

## 功能

- 输入多个 GitHub 仓库（`owner/name` 格式，一行一个）
- 横向柱状图对比最近 90 天的 commit 数和 PR 合并数
- 折线图展示每个仓库的 star 增长（按周聚合）
- 热力图展示某个仓库的"星期几 × 小时段"提交密度，分析核心贡献者时区
- 表格列出最近 30 天该仓库的 Top 5 贡献者
- 支持 Personal Access Token 提高 API 限流
- 数据本地缓存 1 小时

## 环境要求

- Python 3.9+
- pandas >= 2.0

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
streamlit run app.py
```

浏览器会自动打开应用页面。

## 数据缓存目录

所有从 GitHub API 获取的数据会缓存在：

```
~/.github_dashboard_cache/
```

缓存有效期为 1 小时。如需强制刷新数据，可删除该目录。

## 配置 Personal Access Token

GitHub 公开 API 对于未认证的请求限流为每小时 60 次。配置 Token 后可提高到每小时 5000 次。

### 获取 Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 勾选 `public_repo` 权限（仅需要读公开仓库的权限）
4. 点击 "Generate token"，复制生成的 token

### 在应用中使用

在应用左侧侧边栏的 "GitHub Personal Access Token" 输入框中粘贴你的 token 即可。token 仅保存在当前会话的内存中，不会写入磁盘。

## 项目结构

```
.
├── app.py           # Streamlit 主应用（界面层）
├── fetcher.py       # 数据抓取模块（GitHub API + 本地缓存）
├── metrics.py       # 指标计算模块（数据处理）
├── charts.py        # 图表渲染模块（Altair）
├── requirements.txt # 依赖列表
└── README.md        # 项目说明
```

## 模块职责

- **fetcher.py**: 负责与 GitHub REST API 交互，处理分页、请求头、本地文件缓存
- **metrics.py**: 负责数据清洗、指标计算、格式转换为 DataFrame
- **charts.py**: 负责创建 Altair 图表定义
- **app.py**: 负责 Streamlit UI 布局和用户交互流程
