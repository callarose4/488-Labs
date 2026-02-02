import streamlit as st
from openai import OpenAI

# -----------------------------
# App setup
# -----------------------------
st.set_page_config(page_title="Lab 3 - Chatbot with Memory", page_icon="💬")

st.title("Lab 3: Streaming Chatbot with Memory")

# You can hardcode a model or keep it simple:
MODEL = "gpt-4.1-nano"

# Token-buffer max (prompt tokens sent to model each turn).
# This is NOT the model's output tokens; it's the input prompt budget.
MAX_PROMPT_TOKENS = 900

client = OpenAI(api_key=st.secrets["OPEN_API_KEY"])

# -----------------------------
# Token counting helper
# -----------------------------
def estimate_tokens(text: str) -> int:
    """
    Lightweight estimate so you don't need extra libraries.
    Rule of thumb: ~4 characters per token in English.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)

def count_message_tokens(messages) -> int:
    """
    Approx token count of a list of chat messages.
    Includes role overhead roughly.
    """
    total = 0
    for m in messages:
        # small overhead for role + formatting
        total += 4
        total += estimate_tokens(m.get("content", ""))
    return total

# -----------------------------
# Buffering helper (keeps system prompt)
# -----------------------------
def build_buffered_messages(full_messages, max_prompt_tokens: int):
    """
    Returns a buffered message list that:
      - Always keeps the system message
      - Then keeps as many recent messages as fit in max_prompt_tokens
    """
    if not full_messages:
        return []

    system_msg = None
    rest = []

    for m in full_messages:
        if m["role"] == "system" and system_msg is None:
            system_msg = m
        else:
            rest.append(m)

    if system_msg is None:
        # fallback, but your app will set it so this shouldn't happen
        system_msg = {"role": "system", "content": "You are a helpful assistant."}

    # Start from most recent and work backwards until token budget is hit
    kept = []
    # We will keep messages from the end (most recent) backwards
    for m in reversed(rest):
        tentative = [system_msg] + list(reversed(kept)) + [m]
        if count_message_tokens(tentative) <= max_prompt_tokens:
            kept.append(m)
        else:
            break

    buffered = [system_msg] + list(reversed(kept))
    return buffered

def build_last_two_user_turns(full_messages):
    """
    Keeps:
      - System message
      - Only last two USER messages and the ASSISTANT messages that follow them
    """
    system_msg = None
    convo = []
    for m in full_messages:
        if m["role"] == "system" and system_msg is None:
            system_msg = m
        else:
            convo.append(m)

    if system_msg is None:
        system_msg = {"role": "system", "content": "You are a helpful assistant."}

    # Identify user turns positions from the end
    user_indices = [i for i, m in enumerate(convo) if m["role"] == "user"]
    if len(user_indices) <= 2:
        return [system_msg] + convo

    # Keep from the second-to-last
