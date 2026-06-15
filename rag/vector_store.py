import faiss
import numpy as np
from rag.embedder import get_embedding

class VectorStore:

    def __init__(self):
        self.index = faiss.IndexFlatL2(384)
        self.text_chunks = []

    def add_texts(self, chunks):
        vectors = []

        for chunk in chunks:
            vectors.append(get_embedding(chunk))
            self.text_chunks.append(chunk)

        vectors = np.array(vectors).astype("float32")
        self.index.add(vectors)

    def search(self, query, k=3):
        query_vector = np.array([get_embedding(query)]).astype("float32")

        distances, indices = self.index.search(query_vector, k)

        results = []

        for idx in indices[0]:
            results.append(self.text_chunks[idx])

        return results