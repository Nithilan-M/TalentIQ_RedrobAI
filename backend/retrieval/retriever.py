import os
from typing import Dict, Any, List, Tuple
from backend.faiss.index_manager import candidate_index_manager

class CandidateRetriever:
    def __init__(self):
        self.candidates_cache: Dict[str, Dict[str, Any]] = {}

    def load_candidates_to_cache(self, jsonl_path: str):
        """
        Streams and parses candidates into an in-memory cache for fast O(1) retrieval.
        Consumes around 200MB of RAM for 100,000 candidates, satisfying performance constraints.
        """
        from backend.parsers.jsonl_loader import stream_candidates
        print(f"Loading candidates from '{jsonl_path}' into fast in-memory cache...")
        
        self.candidates_cache = {}
        count = 0
        for cand in stream_candidates(jsonl_path):
            self.candidates_cache[cand["candidate_id"]] = cand
            count += 1
            if count % 20000 == 0:
                print(f"Loaded {count} profiles into cache...")
        print(f"Candidate cache loaded successfully with {len(self.candidates_cache)} profiles.")

    def retrieve_top_candidates(self, jd_data: Dict[str, Any], top_k: int = 1000) -> List[Tuple[Dict[str, Any], float]]:
        """
        Converts the job description into a semantic query,
        retrieves the top K matches using FAISS, and retrieves their full candidate records.
        """
        # Formulate rich semantic query from Job Description
        title = jd_data.get("title", "")
        skills = jd_data.get("skills_required", [])
        technologies = jd_data.get("technologies", [])
        responsibilities = jd_data.get("responsibilities", [])
        
        jd_query = (
            f"Role: {title}. "
            f"Core skills required: {', '.join(skills)}. "
            f"Technologies: {', '.join(technologies)}. "
            f"Responsibilities: {', '.join(responsibilities[:4])}."
        )

        # Vector search
        search_results = candidate_index_manager.search_candidates(jd_query, top_k=top_k)
        
        retrieved_candidates = []
        for cid, score in search_results:
            cand_profile = self.candidates_cache.get(cid)
            if cand_profile:
                retrieved_candidates.append((cand_profile, score))
                
        return retrieved_candidates

# Singleton retriever instance
candidate_retriever = CandidateRetriever()
