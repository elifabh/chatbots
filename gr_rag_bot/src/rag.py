# src/rag.py

from document_retrieval import DocumentRetrieval

class RAG:
    def __init__(self):
        self.retrieval = DocumentRetrieval()
        self.retrieval.load_index()
    
    def get_relevant_documents(self, query, top_k=3):
        return self.retrieval.search(query, top_k=top_k)