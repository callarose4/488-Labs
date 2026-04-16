import streamlit as st
import json
import os
from openai import OpenAI

st.set_page_config(page_title="Lab 9 - Chatbot with Long-Term Memory")
st.title("Lab 9 - Chatbot with Long-Term Memory")
client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])
MEMORY_FILE = "memories.json"

def load_memories():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []   

def save_memories(memories):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memories, f, indent=2)

memories = load_memories()

if memories: 
    for i, memory in enumerate(memories, 1):
        st.sidebar.write(f"**Memory {i}:** {memory['content']}")
    else:
        st.sidebar.info("No memories yet. Start a conversation to create memories!")

if st.sidebar.button("Clear All Memories"):
    save_memories([])
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
    
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    memories = load_memories()
    system_prompt = "You are a helpful assistant with long-term memory,"
    if memories:
        memory_text = "\n".join(f" -{m['content']}" for m in memories)
        system_prompt += (f" here are things you remember about this user from past conversations:\n" + memory_text)

    api_messages = [{"role": "system", "content": system_prompt}] 
    api_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=api_messages,
        stream=True,
    )

    assistant_reply = st.write_stream(response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    extraction_prompt = (
        "You are a memory extraction assistant. Analyze the following conversation and extract any new facts about the user..."
        f"User said: \"{user_input}\"\n\n"
        f"Assistant replied: \"{assistant_reply}\"\n\n"
    )
    if memories: 
        extraction_prompt += (
            "These memories are already saved, so don't include any duplicates."
            + "\n".join(f" - {m['content']}" for m in memories) 
        )
    extraction_prompt += (
    "Return ONLY a JSON list of strings... If there are no new facts, return: []"
)
    try:
        extraction_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": extraction_prompt}],
        )
        new_facts = json.loads(extraction_response.choices[0].message.content)
        if new_facts:
            for fact in new_facts:
                memories.append({"content": fact})
            save_memories(memories)
    except (json.JSONDecodeError, Exception):
        pass
    
