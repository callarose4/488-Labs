import streamlit as st
from pydantic import BaseModel
from openai import OpenAI

st.set_page_config(page_title="Lab 6 - Responses Agent")
st.title("Research Agent (Responses API)")
st.caption("This agent has web search enabled for up-to-date answers.")


class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

structured_mode = st.sidebar.checkbox("Return structured summary")
streaming_mode = st.sidebar.checkbox("Enable streaming")

st.subheader("Ask a question")
user_question = st.text_input(
    "Your question:",
    placeholder="e.g. What is the EU AI Act?",
)

if st.button("Submit Question"):
    if user_question:
        with st.spinner("Thinking..."):
            if structured_mode:
                response = client.responses.parse(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Cite your sources.",
                    input=user_question,
                    tools=[{"type": "web_search_preview"}],
                    text_format=ResearchSummary,
                )
            elif streaming_mode:
                stream = client.responses.create(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Cite your sources.",
                    input=user_question,
                    tools=[{"type": "web_search_preview"}],
                    stream=True,
                )
                streamed_text = ""
                container = st.empty()
                for event in stream:
                    if event.type == "response.output_text.delta":
                        streamed_text += event.delta
                        container.markdown(streamed_text)
                    elif event.type == "response.completed":
                        response = event.response
                # Store as a completed response for follow-up chaining
                st.session_state.last_response = response
                st.session_state.last_response_id = response.id
                st.session_state.structured = False
                st.session_state.streamed_text = streamed_text
            else:
                response = client.responses.create(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Cite your sources.",
                    input=user_question,
                    tools=[{"type": "web_search_preview"}],
                )
            if not streaming_mode:
                st.session_state.last_response = response
                st.session_state.last_response_id = response.id
                st.session_state.structured = structured_mode

if "last_response" in st.session_state and not st.session_state.get("streamed_text"):
    if st.session_state.structured:
        summary = st.session_state.last_response.output_parsed
        st.markdown(summary.main_answer)
        for fact in summary.key_facts:
            st.markdown(f"- {fact}")
        st.caption(summary.source_hint)
    else:
        st.markdown(st.session_state.last_response.output_text)

if "streamed_text" in st.session_state:
    del st.session_state["streamed_text"]

if "last_response_id" in st.session_state:
    st.divider()
    st.subheader("Ask a follow-up")
    follow_up = st.text_input(
        "Follow-up question:",
        placeholder="e.g. Can you expand on the second point?",
    )

    if st.button("Submit Follow-Up"):
        if follow_up:
            with st.spinner("Thinking..."):
                if streaming_mode:
                    stream = client.responses.create(
                        model="gpt-4o",
                        instructions="You are a helpful research assistant. Cite your sources.",
                        input=follow_up,
                        tools=[{"type": "web_search_preview"}],
                        previous_response_id=st.session_state.last_response_id,
                        stream=True,
                    )
                    streamed_text = ""
                    container = st.empty()
                    for event in stream:
                        if event.type == "response.output_text.delta":
                            streamed_text += event.delta
                            container.markdown(streamed_text)
                        elif event.type == "response.completed":
                            st.session_state.last_response_id = event.response.id
                else:
                    follow_response = client.responses.create(
                        model="gpt-4o",
                        instructions="You are a helpful research assistant. Cite your sources.",
                        input=follow_up,
                        tools=[{"type": "web_search_preview"}],
                        previous_response_id=st.session_state.last_response_id,
                    )
                    st.session_state.last_response_id = follow_response.id
                    st.markdown(follow_response.output_text)