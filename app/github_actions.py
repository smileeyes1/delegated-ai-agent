"""
GitHub execution module
Handles approved actions using GitHub REST API.
"""

import requests


class GitHubClient:
    def __init__(self, token: str):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

    def create_issue(self, owner: str, repo: str, title: str, body: str):
        """
        Create a GitHub issue in a repository.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        payload = {
            "title": title,
            "body": body
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
