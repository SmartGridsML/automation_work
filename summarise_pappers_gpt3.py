import openai
import wget
import pathlib
import pdfplumber
import numpy as np
import config

def getarxivPaper(paper_url, filename = "random_paper.pdf"):
    """
    Downloads paper from arxiv url and returns local path to file

    """
    dlpaper = wget.download(paper_url , filename)
    downloaded_filePath = pathlib.Path(dlpaper)
    
    return downloaded_filePath

#‘Understanding training and generalization in deep learning by Fourier analysis’ 
# author: Zhi-Qin John Xu.
PATH_FILE =  "https://arxiv.org/pdf/1808.04295.pdf"
paperFilePath = getarxivPaper(PATH_FILE)

def displayPaperContent(paperContent , page_start = 0 , page_end = 5):
    print("---------")
    for page in paperContent[page_start : page_end]:
        print(f"{page.extract_text()}")
        
paperContent = pdfplumber.open(paperFilePath).pages        
displayPaperContent(paperContent)

def showPaperSummary(paperContent):
    tldr_tag = "\n tl;dr:"
    
    openai.organization = ""
    openai.api_key = config.OPEN_AI_API_KEY
    engine_list = openai.Engine.list()
    for page in paperContent:
        text = page.extract_text() + tldr_tag
        response = openai.Completion.create(engine="davinci", prompt=text, temperature=0.3,
                                            max_tokens=140,
                                            top_p=1,
                                            frequency_penalty=0,
                                            presence_penalty=0,
                                            stop=["\n"]
                                            )
        print(response["choices"][0]["text"])

showPaperSummary(paperContent)
