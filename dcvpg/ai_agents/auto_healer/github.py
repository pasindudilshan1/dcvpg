import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for GitHub API interactions used by the AutoHealer Agent.
    Uses the GitHub REST API v3 via httpx.
    """

    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = f"https://api.github.com/repos/{self.repo}"

    def _http(self):
        try:
            import httpx
            return httpx
        except ImportError:
            raise ImportError("httpx is required for AutoHealer GitHub integration. pip install httpx")

    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch from the tip of base_branch."""
        httpx = self._http()
        # Get the SHA of the base branch HEAD
        r = httpx.get(
            f"{self.base_url}/git/ref/heads/{base_branch}",
            headers=self.headers,
            timeout=15,
        )
        if r.status_code != 200:
            logger.error(f"GitHubClient: could not get SHA for '{base_branch}': {r.status_code} {r.text}")
            return False

        sha = r.json()["object"]["sha"]

        # Create the new ref
        r2 = httpx.post(
            f"{self.base_url}/git/refs",
            headers=self.headers,
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            timeout=15,
        )
        if r2.status_code in (201, 422):  # 422 = branch already exists
            logger.info(f"GitHubClient: branch '{branch_name}' ready")
            return True

        logger.error(f"GitHubClient: create_branch failed: {r2.status_code} {r2.text}")
        return False

    def create_commit(
        self, branch_name: str, file_path: str, new_content: str, message: str
    ) -> bool:
        """Create or update a file on branch_name with new_content."""
        httpx = self._http()
        encoded = base64.b64encode(new_content.encode()).decode()

        # Check if file already exists (to get its blob SHA for updates)
        existing_sha: Optional[str] = None
        r = httpx.get(
            f"{self.base_url}/contents/{file_path}",
            headers=self.headers,
            params={"ref": branch_name},
            timeout=15,
        )
        if r.status_code == 200:
            existing_sha = r.json().get("sha")

        payload: dict = {
            "message": message,
            "content": encoded,
            "branch": branch_name,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        r2 = httpx.put(
            f"{self.base_url}/contents/{file_path}",
            headers=self.headers,
            json=payload,
            timeout=15,
        )
        if r2.status_code in (200, 201):
            logger.info(f"GitHubClient: committed '{file_path}' to '{branch_name}'")
            return True

        logger.error(f"GitHubClient: create_commit failed: {r2.status_code} {r2.text}")
        return False

    def create_pull_request(
        self, title: str, head: str, base: str = "main", body: str = ""
    ) -> Optional[str]:
        """Open a PR from head → base and return the PR HTML URL."""
        httpx = self._http()
        r = httpx.post(
            f"{self.base_url}/pulls",
            headers=self.headers,
            json={"title": title, "head": head, "base": base, "body": body},
            timeout=15,
        )
        if r.status_code == 201:
            url = r.json().get("html_url")
            logger.info(f"GitHubClient: PR created → {url}")
            return url

        logger.error(f"GitHubClient: create_pull_request failed: {r.status_code} {r.text}")
        return None
