import streamlit as st
import requests
import os

# FastAPI Backend URL
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/summarize/")

def main():
    st.title("Academic Paper Summarizer")

    # Ensure session state
    if "summary" not in st.session_state:
        st.session_state["summary"] = None

    # Input options
    file = st.file_uploader("Upload a PDF file", type=["pdf"])
    url = st.text_input("Or provide a URL to a PDF")

    # Summarization options
    level = st.selectbox("Select summary level", ["short", "medium", "long"], key="summary_level")
    engine = st.selectbox("Select engine", ["groq", "openai"], key="engine_option")

    # Debugging print statement to verify selected values
    st.write(f"Selected level: {level}, Engine: {engine}")

    if st.button("Summarize"):
        summarize(file, url, level, engine)

    if st.session_state["summary"]:
        st.markdown("### Summary:")
        st.write(st.session_state["summary"])

def summarize(file, url, level, engine):
    """Handles API request to summarize text."""
    if not file and not url:
        st.error("Provide a file or a URL.")
        return

    try:
        params = {"level": level, "engine": engine}  # Send level correctly
        if file:
            files = {"file": file}
            response = requests.post(API_URL, files=files, data=params)
        else:
            response = requests.post(API_URL, data={**params, "url": url})

        if response.status_code == 200:
            result = response.json()
            st.session_state["summary"] = result["summary"]
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
