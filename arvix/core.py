import os
import feedparser
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def refine_query(user_query, model="gpt-4"):
    prompt = f"""Refine the following academic search query for arXiv to be more specific and relevant:

Original query: "{user_query}"

Improved query:"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research assistant helping refine academic search queries for better arXiv results. You are working for a content creator that will produce reels, so the papers tyou find should be hyped and interesting"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip().strip('"')
    except:
        return user_query

def search_arxiv(query, max_results=5):
    query_url = f"http://export.arxiv.org/api/query?search_query=all:{query.replace(' ', '+')}&start=0&max_results={max_results}"
    feed = feedparser.parse(query_url)
    print(query)

    results = []
    for entry in feed.entries:
        paper = {
            "title": entry.title.strip(),
            "authors": [author.name for author in entry.authors],
            "summary": entry.summary.strip().replace("\n", " "),
            "published": entry.published,
            "url": entry.id,
            "pdf_url": next((link.href for link in entry.links if link.type == "application/pdf"), None)
        }
        # response = requests.get(paper['pdf_url'])
        # response.raise_for_status()  # Raise exception for bad status codes
        #
        # with open(save_path, 'wb') as f:
        #     f.write(response.content)
        #
        # print(f"✅ PDF downloaded to: {save_path}")
        results.append(paper)

    # print(results)
    return results


# def summarize_with_gpt(text, model="gpt-4"):
#     prompt = f"Summarize the following academic abstract in 3 bullet points:\n\n{text}"
#     try:
#         response = openai.ChatCompletion.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": "You are a helpful research assistant."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3,
#         )
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         return f"Summary failed: {e}"
#

def run_ai_arxiv_search(user_query, max_results=5):
    print(f"📝 Original query: {user_query}")
    refined_query = refine_query(user_query)
    print(f"🔍 Refined query: {refined_query}")

    papers = search_arxiv(refined_query, max_results=max_results)
    print(papers)

    if not papers:
        print("❌ No papers found.")
        return
    output = []
    for idx, paper in enumerate(papers, 1):
        print("*****************************************")
        print(f"\n📄 Paper {idx}: {paper['title']}")
        print(f"👥 Authors: {', '.join(paper['authors'])}")
        print(f"📅 Published: {paper['published']}")
        print(f"🔗 PDF: {paper['pdf_url']}")
        # print(f"DOI : {paper['doi']}")
        print("\n🧠 AI Summary:")
        paper_pdf = requests.get(paper['pdf_url'])
        print(paper_pdf)
        save_path = "/home/arihant/researchbot/arvix/pdf/" + paper['pdf_url'].split("/")[-1] + ".pdf"
        with open(save_path, 'wb') as f:
            f.write(paper_pdf.content)
        paper['file_path'] = save_path
        output.append(paper)
    return paper


# Example usage
if __name__ == "__main__":
    user_query = input("Enter your arXiv search query: ")
    run_ai_arxiv_search(user_query, max_results=3)
