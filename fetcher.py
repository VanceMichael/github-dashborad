import json
import time
import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests


GITHUB_API = "https://api.github.com"
CACHE_TTL = 3600


def _get_cache_dir() -> Path:
    cache_dir = Path.home() / ".github_dashboard_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _cache_key(endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
    raw = f"{endpoint}|{json.dumps(params or {}, sort_keys=True)}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _read_cache(cache_key: str) -> Optional[Any]:
    cache_file = _get_cache_dir() / f"{cache_key}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        if time.time() - data["timestamp"] > CACHE_TTL:
            cache_file.unlink()
            return None
        return data["content"]
    except Exception:
        return None


def _write_cache(cache_key: str, content: Any) -> None:
    cache_file = _get_cache_dir() / f"{cache_key}.json"
    with open(cache_file, "w") as f:
        json.dump({"timestamp": time.time(), "content": content}, f)


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _paginate_get(
    url: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    max_pages: int = 30,
    per_page: int = 100,
) -> List[Any]:
    all_results: List[Any] = []
    params = dict(params or {})
    params["per_page"] = per_page

    for page in range(1, max_pages + 1):
        params["page"] = page
        key = _cache_key(url, params)
        cached = _read_cache(key)
        if cached is not None:
            page_results = cached
        else:
            response = requests.get(url, headers=_headers(token), params=params)
            response.raise_for_status()
            page_results = response.json()
            _write_cache(key, page_results)

        if not page_results:
            break
        all_results.extend(page_results)
    return all_results


def fetch_repo_info(repo: str, token: Optional[str] = None) -> Dict[str, Any]:
    url = f"{GITHUB_API}/repos/{repo}"
    key = _cache_key(url)
    cached = _read_cache(key)
    if cached is not None:
        return cached
    response = requests.get(url, headers=_headers(token))
    response.raise_for_status()
    data = response.json()
    _write_cache(key, data)
    return data


def fetch_commits(
    repo: str,
    since: str,
    until: str,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{repo}/commits"
    params = {"since": since, "until": until}
    return _paginate_get(url, token=token, params=params)


def fetch_merged_prs(
    repo: str,
    since: str,
    until: str,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{repo}/pulls"
    params = {"state": "closed", "sort": "updated", "direction": "desc"}
    all_prs = _paginate_get(url, token=token, params=params)
    return [
        pr
        for pr in all_prs
        if pr.get("merged_at")
        and since <= pr["merged_at"] <= until
    ]


def fetch_stargazers(
    repo: str,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{repo}/stargazers"
    headers = _headers(token)
    headers["Accept"] = "application/vnd.github.star+json"
    all_results: List[Any] = []
    for page in range(1, 31):
        params = {"per_page": 100, "page": page}
        key = _cache_key(url, params)
        cached = _read_cache(key)
        if cached is not None:
            page_results = cached
        else:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            page_results = response.json()
            _write_cache(key, page_results)
        if not page_results:
            break
        all_results.extend(page_results)
    return all_results
