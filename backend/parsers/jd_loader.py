import os
import json
import docx
from typing import Dict, Any
from backend.services.gemini import call_gemini_sync, call_gemini_async


project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JD_DOCX_PATH = os.path.join(project_root, "India_runs_data_and_ai_challenge", "job_description.docx")
JD_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "job_description_criteria.json")

class JobDescriptionLoader:
    def __init__(self):
        os.makedirs(os.path.dirname(JD_JSON_PATH), exist_ok=True)

    def extract_text_from_docx(self, path: str) -> str:
        """Extracts all text paragraphs from the Word document."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Job Description docx not found at: {path}")
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    async def get_structured_jd(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Loads the structured Job Description JSON. If not cached, reads the
        docx and parses it via Gemini 2.5 Flash, then saves/caches the JSON.
        """
        if os.path.exists(JD_JSON_PATH) and not force_reload:
            try:
                with open(JD_JSON_PATH, "r", encoding="utf-8") as f:
                    print("Loading cached structured Job Description criteria...")
                    return json.load(f)
            except Exception:
                pass

        print("No cached Job Description JSON found. Parsing docx...")
        raw_text = self.extract_text_from_docx(JD_DOCX_PATH)
        
        prompt = f"""
        You are an expert AI recruiting architect. Parse this Job Description text and extract structured fields.
        
        You must output a single JSON object containing EXACTLY these keys:
        1. "title": The formal job title (e.g. "Senior ML/AI Engineer - Search, Retrieval & Ranking").
        2. "skills_required": List of technical skills the candidate MUST absolutely have.
        3. "skills_preferred": List of nice-to-have skills.
        4. "experience_required": Text summary of years of experience required.
        5. "responsibilities": List of main responsibilities.
        6. "industry": Core industry target.
        7. "technologies": List of core technologies/databases/libraries needed (e.g. ["Python", "FAISS", "LightGBM"]).
        8. "leadership_expectations": List of leadership expectations.
        9. "product_mindset": Key product mindset requirements.
        10. "must_have_skills": A list of must-have skills/qualifications.
        11. "nice_to_have_skills": A list of nice-to-have skills/qualifications.

        Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.
        
        Job Description:
        ---
        {raw_text}
        ---
        """
        
        print("Calling Gemini 2.5 Flash to extract job criteria...")
        response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.1)
        
        try:
            data = json.loads(response_text)
            
            # Save cache
            with open(JD_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            print(f"Structured Job Description criteria cached in '{JD_JSON_PATH}'.")
            return data
        except Exception as e:
            print(f"Failed to parse JD JSON: {e}. Raw response: {response_text}")
            # Fallback static criteria mapped from job_description text
            fallback = {
                "title": "Senior ML/AI Engineer - Search, Retrieval & Ranking",
                "skills_required": ["Python", "embeddings", "vector databases", "evaluation frameworks", "search", "retrieval", "ranking"],
                "skills_preferred": ["LLM fine-tuning", "Learning-to-rank", "distributed systems", "large-scale inference"],
                "experience_required": "5-9 years of experience in product companies",
                "responsibilities": ["Own the intelligence layer", "Audit search algorithms", "Ship v2 ranking system", "Set up evaluation infrastructure"],
                "industry": "HR-tech / marketplaces",
                "technologies": ["Python", "FAISS", "sentence-transformers", "XGBoost", "LightGBM", "Scikit-Learn"],
                "leadership_expectations": ["Mentoring next round of hires", "Working with PMs", "System architecture decisions"],
                "product_mindset": ["Bias toward shipping over research", "Willingness to write code", "Mentorship focus"],
                "must_have_skills": ["Python", "embeddings-based retrieval systems", "vector databases or hybrid search", "evaluation frameworks (NDCG, MRR, MAP)"],
                "nice_to_have_skills": ["XGBoost", "LightGBM", "LLM fine-tuning", "marketplace product exposure"]
            }
            with open(JD_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(fallback, f, indent=2)
            return fallback

# Singleton instance
jd_loader = JobDescriptionLoader()
