import csv
from typing import List, Dict, Any

CORE_AI_SKILLS = {
    "embeddings", "vector databases", "python", "search", "retrieval", 
    "ranking", "ndcg", "mrr", "map", "evaluations", "sentence-transformers", 
    "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "opensearch", 
    "faiss", "xgboost", "lightgbm", "pytorch", "tensorflow", "scikit-learn"
}

class SubmissionGenerator:
    @staticmethod
    def generate_reasoning(candidate_raw: Dict[str, Any]) -> str:
        """
        Generates a factual template reasoning based on candidate achievements,
        strictly avoiding hosted LLM API dependencies.
        Format: "{Title} with {yrs} yrs; {core_skills} AI core skills; response rate {rate}."
        """
        profile = candidate_raw.get("profile", {})
        skills = candidate_raw.get("skills", [])
        signals = candidate_raw.get("redrob_signals", {})

        title = profile.get("current_title", "Engineer")
        years_exp = float(profile.get("years_of_experience", 0.0))
        
        # Count matched core AI skills
        cand_skill_names = {s.get("name", "").lower().strip() for s in skills}
        matched_count = len(cand_skill_names.intersection(CORE_AI_SKILLS))

        # Get response rate (handle negative/missing default)
        response_rate = float(signals.get("recruiter_response_rate", 0.75))
        if response_rate < 0:
            response_rate = 0.5

        return f"{title} with {years_exp:.1f} yrs; {matched_count} AI core skills; response rate {response_rate:.2f}."

    @staticmethod
    def write_submission_csv(ranked_candidates: List[Dict[str, Any]], output_path: str):
        """
        Selects exactly the top 100 candidates, formats scores,
        runs tie-breaker sorting, compiles reasons, and writes the CSV.
        """
        # Ensure tie-breaker sorting condition is met
        # (-score, candidate_id)
        # Score is divided by 100.0 to stay in the 0-1 range
        candidates_to_process = []
        for c in ranked_candidates:
            score_normalized = round(c["score"] / 100.0, 4)
            reason = SubmissionGenerator.generate_reasoning(c["candidate_raw"])
            candidates_to_process.append({
                "candidate_id": c["candidate_id"],
                "score": score_normalized,
                "reasoning": reason
            })

        # Sort: score descending, then candidate_id ascending
        candidates_to_process.sort(key=lambda x: (-x["score"], x["candidate_id"]))

        # Select exactly top 100
        submission_candidates = candidates_to_process[:100]

        # Ensure exactly 100 rows
        if len(submission_candidates) < 100:
            print(f"Warning: Only {len(submission_candidates)} candidates available for submission (required: 100).")

        # Write to CSV
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Write Header
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            
            # Write rows with sequential rank from 1 to 100
            for idx, c in enumerate(submission_candidates, 1):
                writer.writerow([
                    c["candidate_id"],
                    idx, # rank
                    f"{c['score']:.4f}", # 4 decimal places float
                    c["reasoning"]
                ])
                
        print(f"Submission CSV successfully written to '{output_path}' ({len(submission_candidates)} rows).")
