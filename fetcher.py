from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import requests

CACHE_DIR = Path(".cache/github_dashboard")
CACHE_TTL = 3600

GITHUB_API = "https://api.github.com"


def _cache_path(url: str, params: dict | None = None) -> Path:
    key = url
    if params:
        key += json.dumps(params, sort_keys=True)
    h = hashlib.sha256(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def _read_cache(path: Path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data["_ts"] < CACHE_TTL:
            return data["payload"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _write_cache(path: Path, payload):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"_ts": time.time(), "payload": payload}, ensure_ascii=False),
        encoding="utf-8",
    )


def _get(url: str, token: str | None = None, params: dict | None = None) -> dict | list:
    cp = _cache_path(url, params)
    cached = _read_cache(cp)
    if cached is not None:
        return cached

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    _write_cache(cp, payload)
    return payload


def _paginate(url: str, token: str | None = None, params: dict | None = None, pages: int = 10) -> list:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items: list = []
    params = dict(params or {})
    params["page"] = 1
    params.setdefault("per_page", 100)

    for _ in range(pages):
        cp = _cache_path(url, params)
        cached = _read_cache(cp)
        if cached is not None:
            items = cached
        else:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            items = resp.json()
            _write_cache(cp, items)

        if not items:
            break
        all_items.extend(items)
        if len(items) < params["per_page"]:
            break
        params["page"] += 1

    return all_items


def fetch_repo_info(owner: str, repo: str, token: str | None = None) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    return _get(url, token)


def fetch_commits(owner: str, repo: str, since: str, token: str | None = None) -> list:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    params = {"since": since}
    return _paginate(url, token, params, pages=10)


def fetch_merged_prs(owner: str, repo: str, since: str, token: str | None = None) -> list:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    params = {"state": "closed", "sort": "updated", "direction": "desc"}
    pulls = _paginate(url, token, params, pages=5)
    return [p for p in pulls if p.get("merged_at") and p["merged_at"] >= since]


def fetch_stargazers(owner: str, repo: str, token: str | None = None) -> list:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/stargazers"
    headers = {"Accept": "application/vnd.github.v3.star+json"}
    params: dict = {"per_page": 100, "page": 1}

    all_items: list = []
    for _ in range(40):
        cp = _cache_path(url, params)
        cached = _read_cache(cp)
        if cached is not None:
            items = cached
        else:
            req_headers = dict(headers)
            if token:
                req_headers["Authorization"] = f"Bearer {token}"
            resp = requests.get(url, headers=req_headers, params=params, timeout=30)
            resp.raise_for_status()
            items = resp.json()
            _write_cache(cp, items)

        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        params["page"] += 1

    return all_items
