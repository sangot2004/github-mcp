import asyncio
import threading
import uuid

import streamlit as st

from graph_agent import build_graph


class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.ready.wait()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.ready.set()
        self.loop.run_forever()

    def run(self, coroutine):
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return future.result()


# --------------------------------
# 1. Page configuration
# --------------------------------

st.set_page_config(
    page_title="GitHub MCP Assistant",
    page_icon="🐙",
    layout="wide"
)

st.title("🐙 GitHub MCP AI Assistant")
st.caption(
    "Ask questions about GitHub repositories, issues, "
    "pull requests, commits and source files."
)


# --------------------------------
# 2. Initialize Graph
# --------------------------------

@st.cache_resource
def get_async_runtime():
    return AsyncLoopThread()


@st.cache_resource
def get_graph():
    return get_async_runtime().run(build_graph())


try:
    graph = get_graph()
except Exception as e:
    st.error(f"Cannot initialize Agent: {e}")
    st.stop()


# --------------------------------
# 3. Initialize chat session
# --------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


# --------------------------------
# 4. Sidebar
# --------------------------------

with st.sidebar:
    st.header("GitHub MCP Assistant")

    st.write("Available capabilities:")
    st.markdown("""
    - List public repositories
    - Get repository details
    - List Issues
    - List Pull Requests
    - List commits
    - Read repository files
    """)

    st.divider()

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    st.caption("Powered by Gemini + LangGraph + MCP")


# --------------------------------
# 5. Display chat history
# --------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------
# 6. Chat input
# --------------------------------

if prompt := st.chat_input("Ask something about GitHub..."):

    # Display user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call LangGraph
    with st.chat_message("assistant"):

        with st.spinner("Gemini is analyzing your request..."):

            try:
                result = get_async_runtime().run(
                    graph.ainvoke(
                        {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        },
                        config={
                            "configurable": {
                                "thread_id": st.session_state.thread_id
                            }
                        }
                    )
                )

                final_message = result["messages"][-1]
                content = final_message.content

                # Handle both string and block-based content
                if isinstance(content, list):
                    content = "\n".join(
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict)
                    )

                response = str(content)

                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception as e:
                st.error(f"Agent error: {e}")
