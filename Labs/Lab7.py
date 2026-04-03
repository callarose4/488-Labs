import streamlit as st
from ollama import chat

# Page setup
st.title("Local AI Chatbot")
st.caption("Powered by Ollama - running entirely offline")

# Sidebar for model selection (helps with reflection - comparing models)
model_choice = st.sidebar.selectbox(
    "Select Model",
    ["qwen3:4b", "mistral", "llama3.2:1b"],
    index=0
)

# Toggle for web search (Part D)
use_web_search = st.sidebar.toggle("Enable Web Search", value=False)

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Button to clear chat when switching models
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
        # When tools are enabled, streaming may not work the same way
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
                # Add the tool response back to the conversation
                st.session_state.messages.append({"role": "assistant", "content": response.message.content or ""})
                st.session_state.messages.append({
                    "role": "tool",
                    "content": str(search_result)
                })
                # Get a final response incorporating the search results
                follow_up = chat(
                    model=model_choice,
                    messages=st.session_state.messages,
                    stream=False
                )
                full_response = follow_up.message.content
            except Exception:
                # Fallback: just use the original response
                full_response = response.message.content or "I tried to search the web but encountered an error."
        else:
            full_response = response.message.content

        with st.chat_message("assistant"):
            st.write(full_response)
    else:
        # Standard streaming response (Part C)
        stream = chat(**chat_kwargs)
        with st.chat_message("assistant"):
            def stream_response():
                for chunk in stream:
                    yield chunk.message.content
            full_response = st.write_stream(stream_response())

    st.session_state.messages.append({"role": "assistant", "content": full_response})