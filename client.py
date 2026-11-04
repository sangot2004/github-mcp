
import anyio
from mcp import Client


async def main():

    async with Client("http://localhost:8000/mcp") as client:

        response = await client.list_tools()

        print("\nVAILABLE MCP TOOLS")

        for index, tool in enumerate(response.tools, start=1):
            print(f"{index}. {tool.name}")
            print(f"   {tool.description}")

        tool_names = [tool.name for tool in response.tools]

        print("\nNhập tên tool muốn sử dụng:")
        tool_name = input("> ").strip()

        if tool_name not in tool_names:
            print("Tool không tồn tại!")
            return

        args = {}

        if tool_name == "list_public_repositories":
            args["username"] = input("GitHub username: ")
            args["limit"] = int(input("Số repository muốn lấy: "))

        elif tool_name == "get_repository":
            args["owner"] = input("Repository owner: ")
            args["repo"] = input("Repository name: ")

        elif tool_name in ("list_issues", "list_pull_requests"):
            args["owner"] = input("Repository owner: ")
            args["repo"] = input("Repository name: ")
            args["state"] = input("State (open/closed/all): ") or "open"
            args["limit"] = int(input("Số kết quả: "))

        elif tool_name == "list_commits":
            args["owner"] = input("Repository owner: ")
            args["repo"] = input("Repository name: ")
            args["limit"] = int(input("Số commit: "))

        elif tool_name == "get_file_contents":
            args["owner"] = input("Repository owner: ")
            args["repo"] = input("Repository name: ")
            args["path"] = input("File path (ví dụ README.md): ")
            args["ref"] = input("Branch/ref (Enter = default): ")

        print("\nCalling MCP tool...")

        result = await client.call_tool(tool_name, args)

        print("\nTOOL RESULT")

        if result.is_error:
            print("Tool returned an error.")

        for item in result.content:
            if hasattr(item, "text"):
                print(item.text)


if __name__ == "__main__":
    anyio.run(main)
