import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.mcp import MCPAdapter

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


async def build_graph():
    # 1. Khởi tạo Gemini
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL"),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # 2. Kết nối MCP Server
    mcp_adapter = MCPAdapter("http://127.0.0.1:8000/mcp")

    # 3. Lấy MCP tools
    tools = await mcp_adapter.list_tools()

    # 4. Gắn tools vào Gemini
    model_with_tools = model.bind_tools(tools)

    # 5. Agent node
    async def call_agent(state: MessagesState):
        response = await model_with_tools.ainvoke(
            state["messages"]
        )
        return {"messages": [response]}

    # 6. Xây dựng Graph
    builder = StateGraph(MessagesState)

    builder.add_node("agent", call_agent)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )

    builder.add_edge("tools", "agent")

    # 7. Lưu trạng thái hội thoại
    memory = MemorySaver()

    graph = builder.compile(
        checkpointer=memory
    )

    return graph
