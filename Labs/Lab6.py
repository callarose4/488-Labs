import streamlit as st
from openai import OpenAI
st.set_page_config(page_title="Lab 6 - Responses Agent")
st.title("Research Agent (Responses API)")

#set up OpenAI client
client = OpenAI (api_key=st.secrets["OPEN_API_KEY"])

#PART A
st.subheader ("Ask a question")
user_question = st.text_input("Your question:", placeholder="e.g. What is the EU AI Act?")

if user_question:
    with st.spinner("Thinking..."):
        response = client.responses.create(
    model="gpt-4o",
    instructions="You are a helpful research assistant.", 
    input=user_question
)
st.markdown(response.output_text)