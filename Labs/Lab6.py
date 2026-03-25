import streamlit as st
from pydantic import BaseModel
from openai import OpenAI
st.set_page_config(page_title="Lab 6 - Responses Agent")
st.title("Research Agent (Responses API)")

class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str

#set up OpenAI client
client = OpenAI (api_key=st.secrets["OPEN_API_KEY"])

#PART A
st.subheader ("Ask a question")
user_question = st.text_input("Your question:", placeholder="e.g. What is the EU AI Act, note: the agent has web search enabled?")


structured_mode = st.sidebar.checkbox(
    "Return strcuted summary",
)



if st.button("Submit Question"):
    if user_question:
        with st.spinner("Thinking..."):
            if structured_mode:
                response = client.responses.parse(
        model="gpt-4o",
        instructions="You are a helpful research assistant.", 
        input=user_question,
        text_format=ResearchSummary,
        )

    else: 
        response = client.responses.create(
            model="gpt-4o",
            instructions="You are a helpful research assistant.",
            input=user_question
        )
        st.session_state.last_response=response
        st.session_state.last_response_id=response.id
if "last response" in st.session_state:
    if st.session_state.structured:
        summary = st.session_state.last_response.output_parsed
        st.markdwon(summary.main_answer)
        for fact in summary.key_facts:
            st.markdown(f"-{fact}")
        st.caption(summary.source_hint)
    else: 
        st.markdown(st.session_state.last_response.output_text)

if "last_response_id" in st.session_state:
    st.subheader("Ask a follow-up")
    follow_up = st.text_input("Follow-up question:", placeholder="e.g. Can you expand on the second point")

if st.button("Submit Follow-Up"):
    if follow_up:
        with st.spinner("Thinking..."):
            follow_response = client.responses.create(
                model="gpt-4o",
                instructions="You are a helpful research assistant.",
                input=follow_up,
                tools=[{"type":"web_search_preview"}],
                previous_response_id=st.session_state.last_response_id,
            )
        st.markdown(follow_response.output_text)

