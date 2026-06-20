import os
import json
import numpy as np
from dotenv import load_dotenv
from typing import List
import httpx

# Load env variables
load_dotenv()

# Try importing local ML libraries, flag fallbacks if missing
HAS_FAISS = False
HAS_SENTENCE_TRANSFORMERS = False

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    print("Warning: faiss-cpu not found. Using numpy fallback for vector search.")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    print("Warning: sentence-transformers not found. Using Gemini Embedding API fallback.")

class VectorStoreManager:
    def __init__(self):
        self.model = None
        self.index = None
        self.dimension = 384 # BGE-small-en-v1.5 default
        self.candidate_ids = [] # Maps index position to SQL candidate database ID
        self.embeddings_list = [] # Used for NumPy fallback

        # Initialize the embedding model if available
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                # Load BGE-small-en-v1.5 locally
                print("Loading local BGE Small embedding model...")
                self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                self.dimension = 384
                print("Local BGE Small model loaded successfully.")
            except Exception as e:
                print(f"Error loading local sentence-transformer model: {e}. Falling back to Gemini Embedding API.")
                self.model = None

    def get_embedding(self, text: str) -> list:
        """Generate a vector embedding for the given text."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        # Primary: Local BGE Small
        if HAS_SENTENCE_TRANSFORMERS and self.model is not None:
            try:
                embedding = self.model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                print(f"Local embedding failed: {e}. Trying Gemini API...")

        # Fallback: Gemini Embedding API
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                # Call Gemini embedding API
                # https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={gemini_api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": "models/text-embedding-004",
                    "content": {
                        "parts": [{"text": text}]
                    }
                }
                response = httpx.post(url, headers=headers, json=data, timeout=15.0)
                if response.status_code == 200:
                    result = response.json()
                    embedding = result["embedding"]["values"]
                    # Adjust dimension dynamically if it is different
                    self.dimension = len(embedding)
                    return embedding
                else:
                    print(f"Gemini embedding API error: {response.text}")
            except Exception as e:
                print(f"Gemini embedding fallback failed: {e}")

        # Fallback 2: Deterministic pseudo-embedding (TF-IDF mock) if completely offline/no-keys
        # Return a simple normalized vector based on character frequencies to avoid total crash
        print("Warning: All embedding methods failed. Using fallback pseudo-embedding.")
        vector = np.zeros(self.dimension)
        for i, char in enumerate(text[:self.dimension]):
            vector[i % self.dimension] += ord(char)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts in batch mode."""
        if not texts:
            return []

        # Primary: Local BGE Small
        if HAS_SENTENCE_TRANSFORMERS and self.model is not None:
            try:
                # model.encode supports batch encoding directly
                embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                return embeddings.tolist()
            except Exception as e:
                print(f"Local batch embedding failed: {e}. Falling back to single-item loops...")

        # Fallback: Loop and call get_embedding
        return [self.get_embedding(t) for t in texts]

    def build_index(self, candidates_data: list):
        """
        Rebuild index from database data.
        candidates_data is a list of dicts: [{"candidate_id": int, "embedding": list}]
        """
        self.candidate_ids = []
        self.embeddings_list = []
        
        if not candidates_data:
            self.index = None
            return

        # Get embedding dimension from first candidate
        first_emb = candidates_data[0]["embedding"]
        self.dimension = len(first_emb)

        embeddings_np = []
        for item in candidates_data:
            self.candidate_ids.append(item["candidate_id"])
            self.embeddings_list.append(item["embedding"])
            embeddings_np.append(item["embedding"])

        embeddings_matrix = np.array(embeddings_np, dtype=np.float32)

        # Primary: FAISS Index
        if HAS_FAISS:
            try:
                self.index = faiss.IndexFlatIP(self.dimension) # Inner Product for cosine similarity (with normalized vectors)
                # Normalize vectors to ensure inner product equals cosine similarity
                faiss.normalize_L2(embeddings_matrix)
                self.index.add(embeddings_matrix)
                print(f"FAISS index built with {len(self.candidate_ids)} candidates.")
                return
            except Exception as e:
                print(f"Failed to build FAISS index: {e}. Falling back to NumPy index.")

        # Fallback: NumPy in-memory list
        self.index = None
        print(f"NumPy index built with {len(self.candidate_ids)} candidates.")

    def search(self, query: str, top_k: int = 10) -> list:
        """
        Search for candidates semantically.
        Returns list of tuples: (candidate_id, match_score)
        """
        if not self.candidate_ids:
            return []

        query_vector = self.get_embedding(query)
        query_np = np.array([query_vector], dtype=np.float32)

        # Primary: FAISS search
        if HAS_FAISS and self.index is not None:
            try:
                # Normalize query vector
                faiss.normalize_L2(query_np)
                scores, indices = self.index.search(query_np, min(top_k, len(self.candidate_ids)))
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx != -1 and idx < len(self.candidate_ids):
                        results.append((self.candidate_ids[idx], float(score)))
                return results
            except Exception as e:
                print(f"FAISS search failed: {e}. Falling back to NumPy search.")

        # Fallback: NumPy cosine similarity search
        try:
            query_vector_np = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_vector_np)
            if query_norm == 0:
                query_norm = 1.0

            results = []
            for i, emb in enumerate(self.embeddings_list):
                emb_np = np.array(emb, dtype=np.float32)
                emb_norm = np.linalg.norm(emb_np)
                if emb_norm == 0:
                    emb_norm = 1.0
                
                # Cosine similarity formula
                similarity = np.dot(emb_np, query_vector_np) / (emb_norm * query_norm)
                results.append((self.candidate_ids[i], float(similarity)))
            
            # Sort by score descending
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            print(f"NumPy search failed: {e}")
            return []

# Singleton instance of vector store manager
vector_store_manager = VectorStoreManager()
