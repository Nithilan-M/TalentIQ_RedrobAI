import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from backend.embeddings.vector_store import vector_store_manager

# File paths
INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MAPPING_FILE = os.path.join(INDEX_DIR, "candidates_ids.json")
EMBEDDINGS_FILE = os.path.join(INDEX_DIR, "candidates_embeddings.npy")

class CandidateIndexManager:
    def __init__(self):
        os.makedirs(INDEX_DIR, exist_ok=True)
        self.candidate_ids: List[str] = []
        self.embeddings: List[List[float]] = []
        self.load_index()

    def get_candidate_text_block(self, candidate: Dict[str, Any]) -> str:
        """
        Creates a rich textual representation of a candidate for embedding generation.
        """
        profile = candidate.get("profile", {})
        skills_raw = candidate.get("skills", [])
        skills = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills_raw]
        
        text = (
            f"Title: {profile.get('current_title', '')}. "
            f"Headline: {profile.get('headline', '')}. "
            f"Skills: {', '.join(skills[:15])}."
        )
        return text

    def build_and_save_index(self, candidates: List[Dict[str, Any]]):
        """
        Builds the embeddings for all candidates in batches and saves them to disk.
        """
        print(f"Generating BGE embeddings for {len(candidates)} candidates...")
        
        self.candidate_ids = []
        self.embeddings = []
        
        # Batch size for CPU embedding generation
        batch_size = 256
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            batch_texts = [self.get_candidate_text_block(c) for c in batch]
            
            # Generate embeddings in batch
            batch_embs = vector_store_manager.get_embeddings(batch_texts)
            
            for idx, emb in enumerate(batch_embs):
                self.candidate_ids.append(batch[idx]["candidate_id"])
                self.embeddings.append(emb)
                
            if (i + len(batch)) % 1024 == 0 or (i + len(batch)) == len(candidates) or True:
                # We can print for every batch to show clean progress
                print(f"Processed {i + len(batch)}/{len(candidates)} candidate vectors...")

        # Save mapping and embeddings
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(self.candidate_ids, f)
            
        np.save(EMBEDDINGS_FILE, np.array(self.embeddings, dtype=np.float32))
        print("Embeddings index saved successfully to disk.")
        
        # Sync the singleton vector store manager
        self.sync_vector_store()

    def load_index(self):
        """Loads index mapping and embeddings from local disk files."""
        if os.path.exists(MAPPING_FILE) and os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                    self.candidate_ids = json.load(f)
                
                embeddings_matrix = np.load(EMBEDDINGS_FILE)
                self.embeddings = embeddings_matrix.tolist()
                
                # Load them into the vector store
                self.sync_vector_store()
                print(f"Loaded {len(self.candidate_ids)} candidate vectors from local index files.")
            except Exception as e:
                print(f"Failed to load vector index files: {e}. Index will need to be rebuilt.")

    def sync_vector_store(self):
        """Loads coordinates into the local vector store manager index."""
        if self.embeddings:
            # Re-map our candidates to format: [{"candidate_id": id, "embedding": list}]
            # Wait, our vector store manager expects candidate_id to be numeric, but in Redrob it is a string!
            # To fix this, we can store index coordinates in the vector store manager, and then resolve them!
            # Let's map candidate_ids as string list and embeddings in the vector_store_manager,
            # or modify the vector store manager to handle string candidate_ids!
            # Since we modified vector_store_manager earlier, let's look at its build_index method:
            # It maps position to candidate_id: self.candidate_ids.append(item["candidate_id"]).
            # If item["candidate_id"] is a string, it will append a string! That works perfectly!
            # Because python lists support strings. The only thing to check is that FAISS and NumPy returns indices
            # and we resolve them. Yes, self.candidate_ids[idx] will resolve to the string CAND_xxxxxxx!
            # This is 100% compatible out of the box!
            c_data = [
                {"candidate_id": cid, "embedding": emb}
                for cid, emb in zip(self.candidate_ids, self.embeddings)
            ]
            vector_store_manager.build_index(c_data)

    def search_candidates(self, query: str, top_k: int = 1000) -> List[Tuple[str, float]]:
        """
        Performs semantic vector search and returns a list of (candidate_id, score) tuples.
        """
        # Call the vector store manager search
        results = vector_store_manager.search(query, top_k=top_k)
        # Results are tuples of (candidate_id, score) where candidate_id is the string CAND_xxxxxxx
        return results

candidate_index_manager = CandidateIndexManager()
