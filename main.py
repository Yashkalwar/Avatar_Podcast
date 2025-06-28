from fastapi import FastAPI, Query
from pydantic import BaseModel
from arvix.core import run_ai_arxiv_search
from typing import List
from heygen_podcast_bot.main import gen_runner
app = FastAPI()

class ArxivQuery(BaseModel):
    prompt: str
    max_results: int = 3

@app.post("/search/")
def search_arxiv_api(query: ArxivQuery):
    papers = run_ai_arxiv_search(query.prompt, max_results=query.max_results)


    # Script Generations
    # script_generation =


    return { "results": papers}
