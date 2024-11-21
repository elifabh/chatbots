# src/document_retrieval.py

import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

class DocumentRetrieval:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
    
    def load_documents(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(folder_path, filename)
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text += extracted_text + " "
                self.documents.append(text)
    
    def create_embeddings(self):
        embeddings = self.model.encode(self.documents, convert_to_tensor=False)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
    
    def save_index(self, index_path='data/faiss.index', docs_path='data/documents.pkl'):
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def load_index(self, index_path='data/faiss.index', docs_path='data/documents.pkl'):
        self.index = faiss.read_index(index_path)
        with open(docs_path, 'rb') as f:
            self.documents = pickle.load(f)
    
    def search(self, query, top_k=3):
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.documents[i] for i in indices[0]]