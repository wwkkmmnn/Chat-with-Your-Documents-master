from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import shutil  # For saving uploaded files
from typing import List  # Import List for type hinting
from langchain_community.document_loaders import PyPDFLoader
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
client = None

#FastAPI
app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Constants
VECTOR_STORE_PATH = "faiss_vector_store"
UPLOAD_FOLDER = "uploaded_documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

vector_store = None
def load_vector_store():
    global vector_store
    try:
        vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        print("Vector store loaded successfully from disk.")
    except Exception as e:
        print(f"Error loading vector store from disk: {e}. Creating a new one.")
        vector_store = FAISS.from_texts(["Initial empty document."], embedding=embeddings)
        vector_store.save_local(VECTOR_STORE_PATH)

load_vector_store()  # Load on application startup

class QueryRequest(BaseModel):
    question: str

def query(question: str):
    global client
    global vector_store
    if vector_store is None:
        return {"answer": "Vector store is not initialized. Please upload a document."}
    if not DEEPSEEK_API_KEY:
        return {"answer": "DeepSeek API key is not configured. Please set DEEPSEEK_API_KEY in your .env file."}
    if client is None:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    relevant_docs = vector_store.similarity_search(question, k=2)
    print(f"len(relevant_docs): {len(relevant_docs)}")
    print(f"relevant_docs: {relevant_docs}")
    context = "\n".join([doc.page_content for doc in relevant_docs])

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "You are an AI assistant. Answer based on the provided context only. Do not use outside information. If you cannot answer, say 'I need more context.'"},
            {"role": "user", "content": f"Question: {question}\nContext: {context}"},
        ],
        stream=False,
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [doc.metadata.get("source", "Unknown") for doc in relevant_docs],
    }


def process_document(file_path: str) -> List[str]:
    """Loads and processes a PDF document, returning texts."""
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        return [text.page_content for text in texts]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF document: {e}")

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    global vector_store  # Access the global variable

    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        texts = process_document(file_path)

        new_vector_store = FAISS.from_texts(texts, embedding=embeddings)
        if vector_store is None:
            vector_store = new_vector_store
        else:
            vector_store.merge_from(new_vector_store) # Fixed merging
        vector_store.save_local(VECTOR_STORE_PATH) # Save updated store
        
        if hasattr(vector_store, 'index') and hasattr(vector_store.index, 'ntotal'):
            index_size = vector_store.index.ntotal
            print(f"FAISS index Size: {index_size}")
        else:
            print("Could not determine FAISS index size.")

        return {"filename": file.filename, "message": "PDF document uploaded and processed successfully."}

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) # Return error as HTTPException
    finally:
        file.file.close()  # Ensure file is closed



@app.post("/query/")
async def ask_question(request: QueryRequest):
    return query(request.question)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
