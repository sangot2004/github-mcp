
import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.mcp import MCPAdapter


load_dotenv()


def text_only(content):
    if isinstance(content, str):
        return content

    blocks = content if isinstance(content, (list, tuple)) else [content]
    text_parts = []

    for block in blocks:
        if isinstance(block, str):
            text_parts.append(block)
        elif isinstance(block, dict):
            text = block.get("text")
            if isinstance(text, str):
                text_parts.append(text)
        else:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                text_parts.append(text)

    return "\n".join(text_parts)


async def main():

    model = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    mcp_adapter = MCPAdapter("http://127.0.0.1:8000/mcp")

    tools = await mcp_adapter.list_tools()

    print("Connected to GitHub MCP Server!")
    print(f"Discovered {len(tools)} tools:")

    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""
        You are a GitHub AI Assistant.

        You can use GitHub MCP tools to retrieve public
        repository information, issues, pull requests,
        commits and file contents.

        Instructions:
        - Understand the user's request.
        - Choose the appropriate GitHub tools.
        - You may call multiple tools if necessary.
        - Only report information returned by GitHub.
        - If information is unavailable, explain why.
        - Respond in Vietnamese.
        """
    )

    print("\nGitHub AI Assistant is ready!")
    print("Type 'exit' to quit.\n")

    while True:

        question = input("You: ").strip()

        if question.lower() in ["exit", "quit"]:
            break

        if not question:
            continue

        try:
            response = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
                }
            )

            final_message = response["messages"][-1]

            print("\nAI:", text_only(final_message.content))
            print("\n" + "=" * 60 + "\n")

        except Exception as e:
            print(f"\nAgent error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
