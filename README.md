# GitHub Open Source Project Activity Dashboard

A dashboard for analyzing GitHub repository activity with beautiful visualizations.

## Features

- **Commits & PRs Comparison**: Horizontal bar chart comparing commit counts and merged PRs across repos (last 90 days)
- **Star Growth Trend**: Line chart showing weekly star growth over time
- **Commit Heatmap**: Visualize commit density by day of week and hour of day (UTC)
- **Top Contributors**: List of top 5 contributors by commit count (last 30 days)

## Tech Stack

- **Python 3.8+**
- **Streamlit** - Web application framework
- **Altair** - Declarative visualization
- **Pandas >= 2.0** - Data manipulation
- **GitHub REST API** - Data source

## Project Structure

```
.
├── app.py          # Main Streamlit application (UI layer)
├── fetcher.py      # GitHub API data fetching and caching
├── metrics.py      # Metric calculation and data processing
├── charts.py       # Altair chart rendering
├── requirements.txt
├── .cache/        # Local cache directory (auto-created)
└── README.md
```

## Installation

1. Clone or download this project

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

## Usage

1. **Enter Repositories**: Type repository names in the text area, one per line, in `owner/name` format:
   ```
   vuejs/vue
   facebook/react
   tensorflow/tensorflow
   ```

2. **Click "Analyze" Button**: Fetch and visualize the data

3. **(Optional) GitHub Token**: Paste a Personal Access Token in the sidebar to increase API rate limits

## GitHub Personal Access Token Configuration

### Why use a token?

- **Without token**: 60 requests per hour (GitHub's public API limit)
- **With token**: 5,000 requests per hour

### How to create a token:

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" (classic)
3. Select the `public_repo` scope
4. Generate and copy the token
5. Paste it in the sidebar's token input field

## Data Caching

- **Location**: `.cache/` directory in the project folder
- **Duration**: 1 hour
- **Purpose**: Avoid repeated API calls for the same data
- **Clear cache**: Delete the `.cache/` directory to force fresh data

## Notes:
- Cached files are in JSON format with timestamps
- Cache automatically expires after 1 hour
- Each API response is cached separately

## Troubleshooting

**API Rate Limit Exceeded**:
- Wait for the rate limit to reset (usually 1 hour)
- Or use a GitHub Personal Access Token to increase limits

**Missing Data**:
- Some repositories may have limited stargazer history
- Very large repositories may take longer to fetch
- Check your internet connection

**Cache Issues**:
- Delete the `.cache/` folder if you see stale data
- Cache files can be safely deleted at any time

## Modules

### `fetcher.py`
- `GitHubFetcher` class handles all GitHub API communication
- Built-in 1-hour local file caching
- Automatic pagination for large datasets
- Token-based authentication support

### `metrics.py`
- `calculate_commit_pr_counts()`: Aggregates commit and PR counts
- `calculate_star_growth()`: Weekly star growth aggregation
- `calculate_commit_heatmap()`: Day × hour commit density matrix
- `calculate_top_contributors()`: Top N contributors by commits

### `charts.py`
- `create_commit_pr_chart()`: Horizontal grouped bar chart
- `create_star_growth_chart()`: Multi-series line chart
- `create_commit_heatmap()`: Day-hour heatmap
- `create_contributors_table()`: Contributor bar chart

## License

MIT License
