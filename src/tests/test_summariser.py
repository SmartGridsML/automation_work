import pytest
from summariser import extract_text_from_pdf, extract_tables_from_pdf, summarize_text
import pathlib

@pytest.fixture
def sample_pdf():
    return pathlib.Path("test.pdf")

def test_extract_text_from_pdf(sample_pdf):
    text = extract_text_from_pdf(sample_pdf)
    assert isinstance(text, str)
    assert len(text) > 10  # Ensure meaningful content

def test_extract_tables_from_pdf(sample_pdf):
    tables = extract_tables_from_pdf(sample_pdf)
    assert isinstance(tables, list)

def test_summarize_text():
    text = "Deep learning has revolutionized AI."
    summary = summarize_text(text, level="short", engine="groq")
    assert isinstance(summary, str)
    assert len(summary) > 10
