import os
import time
import json
import pandas as pd
from typing import Dict, Any, List

from backend.parsers.jd_loader import jd_loader
from backend.retrieval.retriever import candidate_retriever
from backend.faiss.index_manager import candidate_index_manager
from backend.ranking.hybrid_ranker import HybridRanker
from backend.submission.csv_generator import SubmissionGenerator
from backend.validator.submission_validator import SubmissionValidator

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSONL_PATH = os.path.join(project_root, "India_runs_data_and_ai_challenge", "candidates.jsonl")
SUBMISSION_CSV_PATH = os.path.join(project_root, "India_runs_data_and_ai_challenge", "participant_submission.csv")

async def run_offline_ranking_pipeline(input_jsonl: str = None, output_csv: str = SUBMISSION_CSV_PATH) -> Dict[str, Any]:
    """
    Executes the complete offline ranking pipeline and validates the result.
    Tracks time for each step.
    """
    timers = {}
    print("="*60)
    print("STARTING REDROB CHALLENGE OFFLINE RANKING PIPELINE")
    print("="*60)
    
    overall_start = time.time()

    # Step 1: Load Job Description (Must-have/Nice-to-have JSON)
    start = time.time()
    # Await the structured JD directly (runs asynchronously)
    jd_data = await jd_loader.get_structured_jd()
    timers["load_jd"] = time.time() - start
    print(f"[Timer] Loaded Job Description in {timers['load_jd']:.4f} seconds.")

    # Step 2: Load Candidates into cache
    start = time.time()
    jsonl_to_use = input_jsonl if input_jsonl else JSONL_PATH
    if input_jsonl or not candidate_retriever.candidates_cache:
        if input_jsonl:
            print("Clearing candidate cache for new dataset upload...")
            candidate_retriever.candidates_cache = {}
        candidate_retriever.load_candidates_to_cache(jsonl_to_use)
    timers["load_cache"] = time.time() - start
    print(f"[Timer] Loaded {len(candidate_retriever.candidates_cache)} profiles into cache in {timers['load_cache']:.4f} seconds.")

    # Step 3: Check and Load FAISS/NumPy index
    start = time.time()
    # If index does not exist or a custom input dataset is provided, build it from the cache
    from backend.faiss.index_manager import MAPPING_FILE, EMBEDDINGS_FILE
    if input_jsonl or not os.path.exists(MAPPING_FILE) or not os.path.exists(EMBEDDINGS_FILE):
        print("Building index from cached profiles (custom or first-run build)...")
        candidates_list = list(candidate_retriever.candidates_cache.values())
        candidate_index_manager.build_and_save_index(candidates_list)
    else:
        # Load index
        candidate_index_manager.load_index()
    timers["load_vector_index"] = time.time() - start
    print(f"[Timer] Loaded/Built vector index in {timers['load_vector_index']:.4f} seconds.")

    # Step 4: Semantic Retrieval (Retrieve Top 1000 candidates)
    start = time.time()
    retrieved_candidates = candidate_retriever.retrieve_top_candidates(jd_data, top_k=1000)
    timers["semantic_retrieval"] = time.time() - start
    print(f"[Timer] Retrieved Top {len(retrieved_candidates)} candidates using FAISS in {timers['semantic_retrieval']:.4f} seconds.")

    if not retrieved_candidates:
        print("[Error] No candidates retrieved. Pipeline aborted.")
        return {"success": False, "error": "No candidates retrieved."}

    # Step 5: Feature Engineering & Hybrid Ranking Engine
    start = time.time()
    ranker = HybridRanker()
    ranked_results = ranker.rank_retrieved_candidates(retrieved_candidates, jd_data)
    timers["feature_eng_and_ranking"] = time.time() - start
    print(f"[Timer] Engineered features & ranked top candidates in {timers['feature_eng_and_ranking']:.4f} seconds.")

    # Step 6: Generate CSV Submission (Top 100 Candidates)
    start = time.time()
    SubmissionGenerator.write_submission_csv(ranked_results, output_csv)
    timers["write_csv"] = time.time() - start
    print(f"[Timer] Exported Top 100 CSV to '{output_csv}' in {timers['write_csv']:.4f} seconds.")

    # Step 7: Submission Validation
    start = time.time()
    val_result = SubmissionValidator.validate_csv(output_csv)
    timers["validation"] = time.time() - start
    print(f"[Timer] Validated submission CSV in {timers['validation']:.4f} seconds.")

    total_time = time.time() - overall_start
    print("="*60)
    print("PIPELINE EXECUTION COMPLETE")
    print(f"Total Pipeline Runtime: {total_time:.4f} seconds")
    print(f"Submission Validation Passed: {val_result['passed']}")
    if not val_result["passed"]:
        print(f"Validation Errors: {val_result['errors']}")
    print("="*60)

    # Compile analytics summary for display
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    scores = []
    for cand in ranked_results[:100]:
        risk_level = cand["risk"]["risk_level"]
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        scores.append(cand["score"])

    # Load LTR feature importances
    feat_importances = ranker.ltr_model.get_feature_importances()

    return {
        "success": True,
        "total_runtime_seconds": round(total_time, 4),
        "validation_passed": val_result["passed"],
        "validation_errors": val_result["errors"],
        "validation_warnings": val_result["warnings"],
        "candidate_count": len(ranked_results),
        "average_top_score": round(sum(scores)/len(scores), 2) if scores else 0.0,
        "risk_distribution": risk_counts,
        "feature_importances": feat_importances,
        "timers": timers,
        "results": [
            {
                "candidate_id": c["candidate_id"],
                "name": c["profile"]["anonymized_name"],
                "score": c["score"],
                "title": c["profile"]["current_title"],
                "risk_level": c["risk"]["risk_level"],
                "explanation": c["risk"]["risk_explanation"]
            } for c in ranked_results[:100]
        ]
    }

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_offline_ranking_pipeline())
