import streamlit as st
import requests

# Define the FastAPI backend URL
API_URL = "http://127.0.0.1:8000/summarize/"

# Streamlit app
def main():
    st.title("Academic Paper Summarizer")

    # Input options
    st.markdown("### Choose input method:")
    file = st.file_uploader("Upload a PDF file", type=["pdf"])
    url = st.text_input("Or provide a URL to a PDF")

    # Summarization options
    st.markdown("### Summarization options:")
    level = st.selectbox("Select summary level", ["short", "medium", "long"], key="summary_level")
    engine = st.selectbox("Select engine", ["groq", "openai"], key="engine_option")

    # Automatically trigger summarization when inputs are changed
    if st.session_state.get("trigger_summary") is None:
        st.session_state["trigger_summary"] = False

    # Submit button logic
    trigger_summary = st.button("Summarize") or st.session_state["trigger_summary"]

    # Update session state for trigger
    if trigger_summary:
        st.session_state["trigger_summary"] = True
    else:
        st.session_state["trigger_summary"] = False

    # Validate inputs
    if trigger_summary:
        if file and url:
            st.error("Please provide either a file or a URL, not both.")
        elif not file and not url:
            st.error("Please provide a file or a URL.")
        else:
            # Prepare the request
            try:
                if file:
                    # Send file to FastAPI
                    files = {"file": file}
                    response = requests.post(API_URL, files=files, data={"level": level, "engine": engine})
                else:
                    # Send URL to FastAPI
                    params = {"url": url, "level": level, "engine": engine}
                    response = requests.post(API_URL, data=params)

                # Handle response
                if response.status_code == 200:
                    result = response.json()
                    st.success("Summary generated successfully!")
                    st.markdown("### Summary:")
                    st.write(result["summary"])
                    if "tables" in result and result["tables"]:
                        st.markdown("### Extracted Tables:")
                        for table in result["tables"]:
                            st.write(table)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
