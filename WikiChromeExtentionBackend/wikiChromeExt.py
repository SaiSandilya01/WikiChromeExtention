import os


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import wikipedia
from urllib.parse import urlparse, unquote
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from langchain_community.retrievers import WikipediaRetriever
import json


os.environ["GOOGLE_API_KEY"] = "API key"


llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
parser = StrOutputParser()


app = FastAPI()

class QuestionRequest(BaseModel):
    url: str
    question: str

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
# Helper: extract title from URL
def get_title_from_url(url: str) -> str:
    try:
        path = urlparse(url).path
        if not path.startswith("/wiki/"):
            raise ValueError("Not a valid Wikipedia article URL")
        title = path.split("/wiki/")[1]
        return unquote(title.replace("_", " "))
    except Exception as e:
        raise ValueError(f"Invalid Wikipedia URL format: {e}")

# Helper: fetch Wikipedia page content
def fetch_wiki_content(title: str) -> str:
    try:
        retriever = WikipediaRetriever()
        docs = retriever.invoke(title)
        formatted_docs = format_docs(docs)
        #page = wikipedia.page(title)
        return formatted_docs
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Disambiguation error: multiple results found for '{title}'. Options: {e.options}"
    except wikipedia.exceptions.PageError:
        return f"Page not found for '{title}'."
    except Exception as ex:
        return f"An error occurred: {str(ex)}"


def ask_wiki_ai(context: str, question: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", context+ " Answer in 1-2 sentences only."),
        ("human", "{input}")
    ])
    chain = prompt | llm | parser
    return chain.invoke({"input": question})

def load_markdown_store(directory_path: str) -> dict:
    markdown_store = {}
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    url = content.get("metadata", {}).get("url")
                    markdown = content.get("markdown")
                    if url and markdown:
                        markdown_store[url.lower()] = markdown
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
    return markdown_store

def get_markdown_by_url(url: str, store: dict) -> str:
    return store.get(url.lower(), None)



#%%
url = "https://www.tiaa.org/public"
store = load_markdown_store("tiaahomepage")
markdown = get_markdown_by_url(url, store)


@app.get("/")
def root():
    return {"message": "Wikipedia Gemini QA Service is running with chat-style prompts!"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    url = request.url.strip().lower()
    question = request.question.strip()

    context = get_markdown_by_url(url, store)

    if not context:
        raise HTTPException(status_code=404, detail="No markdown found for the provided URL.")

    answer = ask_wiki_ai(context, question)

    return {
        "url": url,
        "question": question,
        "answer": answer
    }

# For direct run
if __name__ == "__main__":
    import uvicorn
    print(markdown)
    uvicorn.run("wikiChromeExt:app", host="0.0.0.0", port=8000, reload=True)
