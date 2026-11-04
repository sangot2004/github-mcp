
import json
import urllib.request
import urllib.error
import urllib.parse
import base64

from mcp.server import MCPServer

mcp = MCPServer("GitHub MCP Server")

GITHUB_API = "https://api.github.com"


# Hàm dùng chung để gọi GitHub REST API
def github_get(endpoint: str, params: dict | None = None):
    url = GITHUB_API + endpoint

    if params:
        url += "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHub-MCP-Demo",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise ValueError(f"GitHub API HTTP {e.code}: {body[:500]}")

    except urllib.error.URLError as e:
        raise ValueError(f"Cannot connect to GitHub: {e.reason}")


# TOOL 1: Liệt kê repository công khai
@mcp.tool()
def list_public_repositories(
    username: str,
    limit: int = 10
) -> str:
    """Liệt kê repository công khai của một GitHub user."""

    if not 1 <= limit <= 100:
        return "Limit phải nằm trong khoảng 1-100."

    try:
        data = github_get(
            f"/users/{urllib.parse.quote(username, safe='')}/repos",
            {"sort": "updated", "per_page": limit}
        )

        result = [
            {
                "name": repo["name"],
                "description": repo["description"],
                "url": repo["html_url"],
                "language": repo["language"],
                "stars": repo["stargazers_count"]
            }
            for repo in data
        ]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return str(e)


# TOOL 2: Lấy thông tin chi tiết repository
@mcp.tool()
def get_repository(owner: str, repo: str) -> str:
    """Lấy thông tin chi tiết của một repository."""

    try:
        data = github_get(
            f"/repos/{owner}/{repo}"
        )

        result = {
            "name": data["name"],
            "full_name": data["full_name"],
            "description": data["description"],
            "url": data["html_url"],
            "language": data["language"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "open_issues": data["open_issues_count"],
            "default_branch": data["default_branch"]
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return str(e)


# TOOL 3: Liệt kê Issues
@mcp.tool()
def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10
) -> str:
    """Liệt kê Issues của repository, không bao gồm Pull Requests."""

    if state not in ("open", "closed", "all"):
        return "State phải là open, closed hoặc all."

    if not 1 <= limit <= 100:
        return "Limit phải nằm trong khoảng 1-100."

    try:
        data = github_get(
            f"/repos/{owner}/{repo}/issues",
            {"state": state, "per_page": limit}
        )

        # GitHub Issues API cũng trả về Pull Requests.
        # Loại bỏ các phần tử có trường pull_request.
        result = [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "url": issue["html_url"],
                "created_at": issue["created_at"],
                "user": issue["user"]["login"]
            }
            for issue in data
            if "pull_request" not in issue
        ]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return str(e)


# TOOL 4: Liệt kê Pull Requests
@mcp.tool()
def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10
) -> str:
    """Liệt kê Pull Requests của repository."""

    if state not in ("open", "closed", "all"):
        return "State phải là open, closed hoặc all."

    if not 1 <= limit <= 100:
        return "Limit phải nằm trong khoảng 1-100."

    try:
        data = github_get(
            f"/repos/{owner}/{repo}/pulls",
            {"state": state, "per_page": limit}
        )

        result = [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "url": pr["html_url"],
                "created_at": pr["created_at"],
                "user": pr["user"]["login"],
                "base_branch": pr["base"]["ref"],
                "head_branch": pr["head"]["ref"]
            }
            for pr in data
        ]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return str(e)


# TOOL 5: Xem lịch sử commit
@mcp.tool()
def list_commits(
    owner: str,
    repo: str,
    limit: int = 10
) -> str:
    """Lấy lịch sử commit gần đây của repository."""

    if not 1 <= limit <= 100:
        return "Limit phải nằm trong khoảng 1-100."

    try:
        data = github_get(
            f"/repos/{owner}/{repo}/commits",
            {"per_page": limit}
        )

        result = [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "url": commit["html_url"]
            }
            for commit in data
        ]

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return str(e)


# TOOL 6: Đọc nội dung file trong repository
@mcp.tool()
def get_file_contents(
    owner: str,
    repo: str,
    path: str,
    ref: str = ""
) -> str:
    """Đọc nội dung một file trong repository công khai."""

    try:
        safe_path = urllib.parse.quote(path, safe="/")

        endpoint = f"/repos/{owner}/{repo}/contents/{safe_path}"

        params = {"ref": ref} if ref else None

        data = github_get(endpoint, params)

        if isinstance(data, list):
            return "Đường dẫn này là thư mục, không phải file."

        if data.get("type") != "file":
            return "Đường dẫn không phải file."

        if data.get("encoding") != "base64":
            return "GitHub không trả nội dung file ở dạng Base64."

        content = base64.b64decode(data["content"]).decode(
            "utf-8",
            errors="replace"
        )

        return json.dumps(
            {
                "name": data["name"],
                "path": data["path"],
                "size": data["size"],
                "content": content[:20000]
            },
            ensure_ascii=False,
            indent=2
        )

    except ValueError as e:
        return str(e)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
