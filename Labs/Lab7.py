# Lab 7: Running a Local Model
# Requires Ollama installed and running locally (ollama.com)


import streamlit as st

# Check if ollama is available
try:
    from ollama import chat
    ollama_available = True
except ImportError:
    ollama_available = False

# Page setup
st.title("Local AI Chatbot")
st.caption("Powered by Ollama - running entirely offline")

# Check for Ollama connection
def check_ollama_connection():
    try:
        from ollama import list as ollama_list
        ollama_list()
        return True
    except Exception:
        return False

if not ollama_available:
    st.error("The `ollama` Python package is not installed. Run `pip install ollama` to install it.")
    st.stop()

if not check_ollama_connection():
    st.warning("⚠️ Cannot connect to Ollama server. This app requires Ollama to be installed and running locally.")
    st.info(
        "**To run this app locally:**\n"
        "1. Download and install Ollama from [ollama.com](https://ollama.com)\n"
        "2. Open a terminal and run: `ollama pull qwen3:4b` and `ollama pull mistral`\n"
        "3. Run this app locally with: `streamlit run Labs/Lab7.py`\n\n"
        "This app cannot run on Streamlit Cloud because it requires a local Ollama server. "
        "That is the core concept of this lab - running LLMs on your own hardware instead of through a cloud API."
    )
    st.stop()

model_choice = st.sidebar.selectbox(
    "Select Model",
    ["qwen3:4b", "mistral"],
    index=0
)

use_web_search = st.sidebar.toggle("Enable Web Search", value=False)

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Web search tool definition for Part D
web_search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information on a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
}

# Handle new user input
if prompt := st.chat_input("Ask a question", key="chat_input"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Build the chat call arguments
    chat_kwargs = {
        "model": model_choice,
        "messages": st.session_state.messages,
        "stream": True,
    }

    # Add web search tool if enabled (Part D)
    if use_web_search:
        chat_kwargs["tools"] = [web_search_tool]
        chat_kwargs["stream"] = False
        response = chat(**chat_kwargs)

        # Check if the model wants to use web search
        if response.message.tool_calls:
            tool_call = response.message.tool_calls[0]
            query = tool_call.function.arguments.get("query", prompt)

            # Perform the web search using ollama
            from ollama import web_search as ollama_web_search
            try:
                search_result = ollama_web_search(query)
                st.session_state.messages.append({"role": "assistant", "content": response.message.content or ""})
                st.session_state.messages.append({
                    "role": "tool",
                    "content": str(search_result)
                })
                follow_up = chat(
                    model=model_choice,
                    messages=st.session_state.messages,
                    stream=False
                )
                full_response = follow_up.message.content
            except Exception:
                full_response = response.message.content or "I tried to search the web but encountered an error."
        else:
            full_response = response.message.content

        with st.chat_message("assistant"):
            st.write(full_response)
    else:
       
        stream = chat(**chat_kwargs)
        with st.chat_message("assistant"):
            def stream_response():
                for chunk in stream:
                    yield chunk.message.content
            full_response = st.write_stream(stream_response())

    st.session_state.messages.append({"role": "assistant", "content": full_response})