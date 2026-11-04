import anyio
from mcp import Client
from mcp.types import TextContent


async def main():

    # Kết nối đến MCP Server
    async with Client("http://localhost:8000/mcp") as client:

        print("Connected to MCP Server!")

        # Bước 1: Khám phá các tool
        tools = await client.list_tools()

        print("\nAvailable tools:")

        for tool in tools.tools:
            print(f"- {tool.name}")
            print(f"  Description: {tool.description}")

        # Bước 2: Gọi tool
        username = input("\nNhập GitHub username: ")

        result = await client.call_tool(
            "list_public_repositories",
            {
                "username": username,
                "limit": 5
            }
        )

        # Bước 3: Nhận kết quả
        print("\nGitHub repositories:")

        for content in result.content:
            if isinstance(content, TextContent):
                print(content.text)


if __name__ == "__main__":
    anyio.run(main)
