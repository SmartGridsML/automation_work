import openai
import wget
import pathlib
import pdfplumber
import numpy as np
import config
import os
from typing import Union
from dotenv import load_dotenv
import time
import requests
from groq import Groq

load_dotenv()


GROQ_API_URL = "https://api.groq.com/v1/chat/completions"

def download_pdf_from_url(url, filename="downloaded_paper.pdf"):
    """Downloads a PDF from a given URL and saves it to the local filesystem."""
    local_path = wget.download(url, filename)
    return pathlib.Path(local_path)

def process_pdf(source, level, engine):
    """
    Processes a PDF from either a URL or a file object.
    """
    if isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
        pdf_path = download_pdf_from_url(source)  # Download and get path
    else:
        pdf_path = source  # Use the file object directly for uploaded files

    # Process the PDF
    text = extract_text_from_pdf(pdf_path)
    tables = extract_tables_from_pdf(pdf_path)
    summary = summarize_text(text, level, engine)

    return {"summary": summary, "tables": tables}



def extract_text_from_pdf(pdf_source):
    """Extracts text from a given PDF file or file-like object using pdfplumber."""
    text = ""
    if isinstance(pdf_source, pathlib.Path):  # If it's a file path
        with pdfplumber.open(pdf_source) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    else:  # Handle file-like objects
        with pdfplumber.open(pdf_source) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    return text.strip()



def extract_tables_from_pdf(pdf_source):
    """Extracts tables from a given PDF file or file-like object using pdfplumber."""
    tables = []
    if isinstance(pdf_source, pathlib.Path):  # If it's a file path
        with pdfplumber.open(pdf_source) as pdf:
            for page in pdf.pages:
                tables.extend(page.extract_tables())
    else:  # Handle file-like objects
        with pdfplumber.open(pdf_source) as pdf:
            for page in pdf.pages:
                tables.extend(page.extract_tables())
    return tables


def summarize_with_groq(text, level):
    """Summarizes text using Groq's official Python client."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Initialize the Groq client

    # Define the summary prompt based on the desired level
    summary_prompt = {
        "short": "Give a one-sentence TL;DR summary:",
        "medium": "Summarize this in 150 words:",
        "long": "Summarize this in detail within 500 words:",
    }

    # Prepare the chat messages
    messages = [
        {"role": "system", "content": "You are a helpful summarization assistant."},
        {"role": "user", "content": summary_prompt[level] + "\n\n" + text},
    ]

    try:
        # Call the chat completions endpoint
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # Specify the model
            messages=messages,
            temperature=0.3,
            max_tokens=140,
        )
        content = response.choices[0].message.content
        print(content)  # For debugging purposes
        return content

    except Exception as e:
        error_response = str(e)
        if "Request too large" in error_response or "rate_limit_exceeded" in error_response:
            print("Request too large, splitting text into smaller chunks...")
            chunk_size = 500  # Adjust chunk size based on token limits
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

            # Summarize each chunk and combine the results
            summaries = []
            for i, chunk in enumerate(chunks):
                print(f"Summarizing chunk {i + 1}/{len(chunks)}")
                chunk_messages = [
                    {"role": "system", "content": "You are a helpful summarization assistant."},
                    {"role": "user", "content": summary_prompt[level] + "\n\n" + chunk},
                ]
                chunk_response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=chunk_messages,
                    temperature=0.3,
                    max_tokens=140,
                )
                summaries.append(chunk_response.choices[0].message.content)
            return " ".join(summaries)
        else:
            raise e


def summarize_text(text, level, engine):
    """Chooses Groq or OpenAI for summarization."""
    if engine == "groq":
        return summarize_with_groq(text, level)
    else:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        summary_prompt = {
            "short": "Give a one-sentence TL;DR summary:",
            "medium": "Summarize this in around 150 words:",
            "long": "Summarize this in detail within 500 words:",
        }

        client = openai.OpenAI()
        max_retries = 5
        retry_delay = 5  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use "gpt-4" or "gpt-3.5-turbo"
                    messages=[
                        {"role": "system", "content": "You are a helpful summarization assistant."},
                        {"role": "user", "content": summary_prompt[level] + "\n\n" + text},
                    ],
                    temperature=0.3,
                    max_tokens=140,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].message.content
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception("Exceeded maximum retries due to rate limiting.")
            except Exception as e:
                raise Exception(f"OpenAI API error: {e}")