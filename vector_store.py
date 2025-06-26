from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

def split_text_to_chunks(text, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    documents = [Document(page_content=chunk) for chunk in chunks]
    return documents

def get_relevant_chunks(documents, query):
    """Simple keyword-based filter (no embedding, Gemini-only)"""
    return [doc.page_content for doc in documents if any(word in doc.page_content.lower() for word in query.lower().split())][:5]
