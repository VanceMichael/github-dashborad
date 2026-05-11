import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class GitHubFetcher:
    def __init__(self, token: Optional[str] = None, cache_dir: str = ".cache"):
        self.base_url = "https://api.github.com"
        self.token = token
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=1)
        os.makedirs(cache_dir, exist_ok=True)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "github-dashboard"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _get_cache_path(self, cache_key: str) -> str:
        safe_key = cache_key.replace("/", "_").replace("?", "_").replace("&", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(cache_key)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            
            cache_time = datetime.fromtimestamp(data["timestamp"])
            if datetime.now() - cache_time < self.cache_duration:
                return data["content"]
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def _save_to_cache(self, cache_key: str, content: Any) -> None:
        cache_path = self._get_cache_path(cache_key)
        data = {
            "timestamp": time.time(),
            "content": content
        }
        with open(cache_path, "w") as f:
            json.dump(data, f)

    def _make_request(self, endpoint: str, params: Optional[Dict] = None, per_page: int = 100) -> List[Dict]:
        all_results = []
        page = 1
        cache_key = f"{endpoint}_{json.dumps(params or {})}_{page}"
        
        while True:
            page_params = dict(params or {})
            page_params["page"] = page
            page_params["per_page"] = per_page
            
            page_cache_key = f"{endpoint}_{json.dumps(page_params, sort_keys=True)}"
            cached = self._load_from_cache(page_cache_key)
            if cached is not None:
                if not cached:
                    break
                all_results.extend(cached)
                if len(cached) < per_page:
                    break
                page += 1
                continue
            
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.get(url, headers=self._get_headers(), params=page_params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                self._save_to_cache(page_cache_key, [])
                break
            
            self._save_to_cache(page_cache_key, data)
            all_results.extend(data)
            
            if len(data) < per_page:
                break
            page += 1
        
        return all_results

    def get_repo_info(self, repo: str) -> Dict:
        endpoint = f"repos/{repo}"
        cache_key = f"repo_info_{repo}"
        
        cached = self._load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        data = response.json()
        self._save_to_cache(cache_key, data)
        return data

    def get_commits(self, repo: str, days: int = 90) -> List[Dict]:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        return self._make_request(f"repos/{repo}/commits", {"since": since})

    def get_pulls(self, repo: str, state: str = "closed", days: int = 90) -> List[Dict]:
        pulls = self._make_request(f"repos/{repo}/pulls", {"state": state})
        cutoff = datetime.now() - timedelta(days=days)
        merged_pulls = []
        for pr in pulls:
            if pr.get("merged_at"):
                merged_at = datetime.strptime(pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
                if merged_at >= cutoff:
                    merged_pulls.append(pr)
        return merged_pulls

    def get_stargazers(self, repo: str) -> List[Dict]:
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.v3.star+json"
        all_stars = []
        page = 1
        
        while True:
            cache_key = f"stargazers_{repo}_{page}"
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                if not cached:
                    break
                all_stars.extend(cached)
                if len(cached) < 100:
                    break
                page += 1
                continue
            
            url = f"{self.base_url}/repos/{repo}/stargazers"
            response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
            if response.status_code == 403:
                break
            response.raise_for_status()
            data = response.json()
            
            if not data:
                self._save_to_cache(cache_key, [])
                break
            
            self._save_to_cache(cache_key, data)
            all_stars.extend(data)
            
            if len(data) < 100:
                break
            page += 1
        
        return all_stars

    def get_contributors(self, repo: str, days: int = 30) -> List[Dict]:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        return self._make_request(f"repos/{repo}/stats/contributors")
