import os
from fastapi import FastAPI
from pydantic import BaseModel
import wikipedia
from urllib.parse import urlparse, unquote
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from langchain_community.retrievers import WikipediaRetriever

# Set Gemini API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAIF4iJTC0eI0zWb8coM7Embaho1yykjfc"

# Init LLM and parser
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
parser = StrOutputParser()

# FastAPI app
app = FastAPI()

class QuestionRequest(BaseModel):
    wiki_url: str
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

# Helper: build and invoke chat-style prompt chain
def ask_wiki_ai(context: str, question: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", context),
        ("human", "{input}")
    ])
    chain = prompt | llm | parser
    return chain.invoke({"input": question})

# Routes
@app.get("/")
def root():
    return {"message": "Wikipedia Gemini QA Service is running with chat-style prompts!"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    title = get_title_from_url(request.wiki_url)
    context = fetch_wiki_content(title)
    answer = ask_wiki_ai(context, request.question)
    return {
        "wiki_title": title,
        "question": request.question,
        "answer": answer
    }

# For direct run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wikiChromeExt:app", host="0.0.0.0", port=8000, reload=True)
