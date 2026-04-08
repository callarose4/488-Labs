import streamlit as st
from openai import OpenAI
import requests 
import base64

openai_api_key = st.secrets["OPEN_API_KEY"]  
client = OpenAI(api_key=openai_api_key)

st.title("Lab 8 - Image Analysis + Music Match")
st.header("Option 1: Image URL")
st.write("Paste a direct image URL (must link directly to an image file).")

url = st.text_input("Enter an image URL to analyze and get a music recommendation:")

if "url_response" not in st.session_state:
    st.session_state.url_response = None 


if st.button("Generate Music Recommendation from URL") and url:
    st.session_state.url_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1024,
        messages=[
            {"role": "user",
             "content": [
                 {"type": "image_url", "image_url": {"url": url, "detail": "auto"}}, 
                    {"type": "text", "text": "Analyze the image and recommend a song that matches the mood of the image. Provide a brief explanation for your recommendation. Describe the artist and genre."}
             ]
            }
        ]
    )
if st.session_state.url_response:
    st.image(url)
    st.write(st.session_state.url_response.choices[0].message.content)
if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

st.header("Option 2: Image Upload")
uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp", "gif"])
if st.button("Generate Music Recommendation from Upload") and uploaded:
    b64 = base64.b64encode(uploaded.read()).decode("utf-8")
    mime = uploaded.type
    data_uri = f"data:{mime};base64,{b64}"
    st.session_state.upload_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1024,
        messages=[
            {"role": "user",
             "content": [
                 {"type": "image_url", "image_url": {"url": data_uri, "detail": "auto"}}, 
                    {"type": "text", "text": "Analyze the image and recommend a song that matches the mood of the image. Provide a brief explanation for your recommendation. Describe the artist and genre."}
             ]
            }
        ]
    )
if st.session_state.upload_response:
    st.image(uploaded)
    st.write(st.session_state.upload_response.choices[0].message.content)