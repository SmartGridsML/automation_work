import openai
import wget
import pathlib
import pdfplumber
import numpy as np
import config
import os
from typing import Union
from dotenv import load_dotenv

import requests

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
    """Summarizes text using Groq API."""
    headers = {"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"}
    summary_prompt = {
        "short": "Give a one-sentence TL;DR summary:",
        "medium": "Summarize this in 150 words:",
        "long": "Summarize this in detail within 500 words:",
    }
    payload = {
        "model": "llama2-70b-chat",
        "messages": [{"role": "user", "content": summary_prompt[level] + text}],
        "temperature": 0.3,
        "max_tokens": 140
    }
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

def summarize_text(text, level, engine):
    """Chooses Groq or OpenAI for summarization."""
    if engine == "groq":
        return summarize_with_groq(text, level)
    else:
    #     openai.api_key = os.environ["OPENAI_API_KEY"]
    #     summary_prompt = {
    #     "short": "Give a one-sentence TL;DR summary:",
    #     "medium": "Summarize this in 150 words:",
    #     "long": "Summarize this in detail within 500 words:",
    #     }

    #     response = openai.ChatCompletion.create(
    #         model="gpt-4",  # Use "gpt-4" or "gpt-3.5-turbo"
    #         messages=[
    #             {"role": "system", "content": "You are a helpful summarization assistant."},
    #             {"role": "user", "content": summary_prompt[level] + "\n\n" + text},
    #         ],
    #         temperature=0.3,
    #         max_tokens=140,
    #         top_p=1,
    #         frequency_penalty=0,
    #         presence_penalty=0,
    #     )
    # return response["choices"][0]["message"]["content"]
        openai.api_key = os.environ["OPENAI_API_KEY"]
        summary_prompt = {
            "short": "Give a one-sentence TL;DR summary:",
            "medium": "Summarize this in 150 words:",
            "long": "Summarize this in detail within 500 words:",
        }

        client = openai.OpenAI()

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
