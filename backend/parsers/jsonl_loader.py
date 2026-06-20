import json
import os
from typing import Generator, Dict, Any

class CandidateSchemaValidator:
    @staticmethod
    def validate(candidate: Dict[str, Any], line_num: int) -> bool:
        """
        Validates the parsed candidate dictionary against the official Redrob schema.
        Returns True if valid, raises ValueError if invalid.
        """
        required_keys = ["candidate_id", "profile", "career_history", "education", "skills", "certifications", "languages", "redrob_signals"]
        for key in required_keys:
            if key not in candidate:
                raise ValueError(f"Line {line_num}: Missing primary key '{key}' in candidate data.")
        
        # Profile validation
        prof = candidate["profile"]
        profile_reqs = ["anonymized_name", "headline", "summary", "location", "country", "years_of_experience", "current_title", "current_company", "current_company_size", "current_industry"]
        for p_key in profile_reqs:
            if p_key not in prof:
                raise ValueError(f"Line {line_num}: Profile missing '{p_key}' key.")

        # Types validation
        if not isinstance(candidate["candidate_id"], str):
            raise ValueError(f"Line {line_num}: 'candidate_id' must be a string, got {type(candidate['candidate_id'])}.")
        
        if not isinstance(candidate["skills"], list):
            raise ValueError(f"Line {line_num}: 'skills' must be a list of skill objects.")

        if not isinstance(candidate["career_history"], list):
            raise ValueError(f"Line {line_num}: 'career_history' must be a list of job history objects.")

        if not isinstance(candidate["education"], list):
            raise ValueError(f"Line {line_num}: 'education' must be a list of education objects.")

        # Behavioral signals validation
        beh = candidate["redrob_signals"]
        if not isinstance(beh, dict):
            raise ValueError(f"Line {line_num}: 'redrob_signals' must be a JSON object.")
            
        return True

def is_candidate_relevant(cand: Dict[str, Any]) -> bool:
    """
    Heuristic check to determine if a candidate profile is relevant to Software/AI engineering roles.
    Filters out non-technical roles, consulting-only career histories, and profiles with zero AI keywords.
    """
    profile = cand.get("profile", {})
    title = profile.get("current_title", "").lower()
    
    # 1. Tech Title Filter
    tech_keywords = {'engineer', 'developer', 'architect', 'programmer', 'analyst', 'scientist', 'specialist', 'lead', 'staff', 'principal', 'cto', 'vp', 'manager'}
    exclude_keywords = {'civil', 'mechanical', 'electrical', 'chemical', 'industrial', 'marketing', 'sales', 'hr', 'human resources', 'support', 'operations', 'recruiter', 'writer', 'accountant', 'financial', 'scrum', 'designer'}
    
    is_tech = any(tk in title for tk in tech_keywords)
    is_excluded = any(ek in title for ek in exclude_keywords)
    if not is_tech or is_excluded:
        return False
        
    # 2. Consulting firm only check
    career = cand.get("career_history", [])
    consulting_firms = {'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'tata consultancy', 'hcl', 'tech mahindra', 'l&t', 'lnt', 'mindtree', 'deloitte', 'pwc', 'ey', 'kpmg'}
    if len(career) > 0:
        all_consulting = True
        for job in career:
            comp = job.get("company", "").lower()
            if not any(cf in comp for cf in consulting_firms):
                all_consulting = False
                break
        if all_consulting:
            return False
            
    # 3. Target Title or AI Skill Check
    target_keywords = {'software', 'developer', 'programmer', 'backend', 'fullstack', 'full-stack', 'data', 'ml', 'ai', 'machine learning', 'deep learning', 'nlp', 'search', 'retrieval', 'ranking', 'algorithms', 'systems'}
    ai_ml_skills = {'embeddings', 'vector', 'search', 'retrieval', 'ranking', 'ndcg', 'mrr', 'map', 'transformer', 'bert', 'llm', 'rag', 'pinecone', 'weaviate', 'qdrant', 'milvus', 'faiss', 'xgboost', 'lightgbm', 'pytorch', 'tensorflow', 'scikit-learn'}
    
    is_target_title = any(tk in title for tk in target_keywords)
    skills = {s.get("name", "").lower() for s in cand.get("skills", [])}
    has_ai_skill = any(s in ai_ml_skills or any(ts in s for ts in ai_ml_skills) for s in skills)
    
    return is_target_title or has_ai_skill

def stream_candidates(file_path: str, filter_relevant: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Streams candidate dictionaries from a JSONL dataset file one by one.
    This ensures we keep memory usage low (well below the 16GB limit)
    even when scanning 100,000 candidate records.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at path: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            try:
                candidate = json.loads(line_stripped)
                CandidateSchemaValidator.validate(candidate, line_num)
                if filter_relevant and not is_candidate_relevant(candidate):
                    continue
                yield candidate
            except json.JSONDecodeError as jde:
                print(f"Skipping line {line_num}: Invalid JSON encoding. Error: {jde}")
            except ValueError as ve:
                print(f"Skipping line {line_num}: Schema validation failed. Error: {ve}")
            except Exception as e:
                print(f"Skipping line {line_num}: Unexpected error parsing row. Error: {e}")
