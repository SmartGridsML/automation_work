# Start the FastAPI server in the background
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit app
streamlit run ui.py --server.port 8501 --server.address 0.0.0.0
