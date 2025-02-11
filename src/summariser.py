import openai
import wget
import pathlib
import pdfplumber
import requests
import time
import os
from typing import Union
from groq import Groq
from config import GROQ_API_KEY, OPENAI_API_KEY  # Use centralized config

def download_pdf_from_url(url, filename="downloaded_paper.pdf"):
    """Downloads a PDF from a given URL and saves it to the local filesystem."""
    local_path = wget.download(url, filename)
    return pathlib.Path(local_path)

def process_pdf(source: Union[str, pathlib.Path], level: str, engine: str):
    """Processes a PDF from a URL or file object."""
    if isinstance(source, str) and source.startswith(("http://", "https://")):
        pdf_path = download_pdf_from_url(source)
    else:
        pdf_path = source

    text = extract_text_from_pdf(pdf_path)
    tables = extract_tables_from_pdf(pdf_path)
    summary = summarize_text(text, level, engine)  # ✅ Now `summarize_text` exists

    return {"summary": summary, "tables": tables}

def extract_text_from_pdf(pdf_path: pathlib.Path):
    """Extracts text from a given PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_tables_from_pdf(pdf_path: pathlib.Path):
    """Extracts tables from a given PDF file using pdfplumber."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    return tables

def summarize_with_groq(text: str, level: str):
    """Summarizes text using Groq's API with improved error handling."""
    client = Groq(api_key=GROQ_API_KEY)

    summary_prompt = {
        "short": "Give a one-sentence TL;DR summary:",
        "medium": "Summarize this in around 150 words :",
        "long": "Summarize this in detail in arounf 500 words:",
    }

    messages = [
        {"role": "system", "content": "You are a helpful summarization assistant."},
        {"role": "user", "content": summary_prompt[level] + "\n\n" + text},
    ]

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.3,
            max_tokens=140,
        )
        return response.choices[0].message.content
    except Exception as e:
        if "rate_limit_exceeded" in str(e) or "Request too large" in str(e):
            return handle_large_text(text, level, client)
        raise e

def handle_large_text(text, level, client):
    """Splits text into chunks and summarizes each chunk."""
    chunk_size = 500
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    summaries = []

    for chunk in chunks:
        messages = [
            {"role": "system", "content": "You are a helpful summarization assistant."},
            {"role": "user", "content": chunk},
        ]
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.3,
            max_tokens=140,
        )
        summaries.append(response.choices[0].message.content)

    return " ".join(summaries)

def summarize_with_openai(text: str, level: str):
    """Summarizes text using OpenAI's GPT API."""
    openai.api_key = OPENAI_API_KEY

    summary_prompt = {
        "short": "Give a one-sentence TL;DR summary:",
        "medium": "Summarize this in 150 words:",
        "long": "Summarize this in detail within 500 words:",
    }

    max_retries = 5
    retry_delay = 5  # Start with 5 seconds

    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful summarization assistant."},
                    {"role": "user", "content": summary_prompt[level] + "\n\n" + text},
                ],
                temperature=0.3,
                max_tokens=140,
            )
            return response["choices"][0]["message"]["content"]
        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception("Exceeded maximum retries due to OpenAI rate limiting.")
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

def summarize_text(text: str, level: str, engine: str):
    """Chooses between Groq and OpenAI for summarization."""
    if engine == "groq":
        return summarize_with_groq(text, level)
    elif engine == "openai":
        return summarize_with_openai(text, level)
    else:
        raise ValueError("Invalid engine selected. Choose 'groq' or 'openai'.")
