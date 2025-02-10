from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
from summariser import process_pdf
import os

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Welcome to the Academic Paper Summarizer!"}

@app.post("/summarize/")
async def summarize_pdf(
    file: UploadFile = None, 
    url: str = Query(None), 
    level: str = "short", 
    engine: str = "groq"
):
    """
    Summarize an academic paper from an uploaded file or a URL.
    """
    if file and url:
        return JSONResponse({"error": "Provide either a file or a URL, not both."}, status_code=400)
    
    if not file and not url:
        return JSONResponse({"error": "Provide either a file or a URL."}, status_code=400)

    source = file.file if file else url
    result = process_pdf(source, level, engine)
    return JSONResponse(result)
