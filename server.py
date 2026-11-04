from mcp.server import MCPServer
import urllib.request
import urllib.error
import json

# Khởi tạo MCP Server
mcp = MCPServer("GitHub MCP Server")


@mcp.tool()
def list_public_repositories(
    username: str,
    limit: int = 10
) -> str:
    """
    Lấy danh sách repository công khai của một GitHub user.
    """

    if not 1 <= limit <= 100:
        return "Limit phải nằm trong khoảng 1-100."

    url = (
        f"https://api.github.com/users/{username}"
        f"/repos?sort=updated&per_page={limit}"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GitHub-MCP-Demo"}
    )

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))

        repositories = []

        for repo in data:
            repositories.append({
                "name": repo["name"],
                "description": repo["description"],
                "url": repo["html_url"],
                "language": repo["language"],
                "stars": repo["stargazers_count"]
            })

        return json.dumps(
            repositories,
            ensure_ascii=False,
            indent=2
        )

    except urllib.error.HTTPError as e:
        return f"GitHub API error: HTTP {e.code}"

    except urllib.error.URLError as e:
        return f"Connection error: {e.reason}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
