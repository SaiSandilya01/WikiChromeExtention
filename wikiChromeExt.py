import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.retrievers import WikipediaRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model

# --------------------------
# 1️⃣ Set your API key
# --------------------------
os.environ["GOOGLE_API_KEY"] = "api_key"

# --------------------------
# 2️⃣ Initialize components
# --------------------------
# Wikipedia retriever
retriever = WikipediaRetriever()

# Gemini LLM
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

# Prompt
prompt = ChatPromptTemplate.from_template(
    """
    Answer the question based only on the context provided.
    Context: {context}
    Question: {question}
    """
)

# Helper: format retrieved docs
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Build the chain
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --------------------------
# 3️⃣ Define FastAPI service
# --------------------------
app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "Wikipedia Gemini QA Service is running!"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer = chain.invoke(request.question)
    return {"question": request.question, "answer": answer}

# For direct run: uvicorn entry
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wikiChromeExt:app", host="0.0.0.0", port=8000, reload=True)
