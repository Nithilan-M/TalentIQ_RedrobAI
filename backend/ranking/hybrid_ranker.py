import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from backend.feature_engineering.feature_calculator import CandidateFeatureCalculator
from backend.learning_to_rank.ltr_model import LearningToRankModel
from backend.behavior_engine.behavior_scorer import BehaviorScorer
from backend.risk_engine.trap_detector import TrapDetector


class HybridRanker:
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initializes the ranker with configurable weights for features.
        """
        # Default weights if not specified (sums to 1.0)
        self.weights = weights or {
            "embedding_similarity": 0.20,
            "skill_match_score": 0.25,
            "experience_score": 0.15,
            "career_progression_score": 0.10,
            "behavioral_score": 0.10,
            "industry_match": 0.05,
            "education_tier_score": 0.05,
            "certification_score": 0.03,
            "leadership_score": 0.04,
            "company_quality": 0.03
        }
        self.ltr_model = LearningToRankModel()
        # Blending ratio between LTR predictions and the manual hybrid score
        # 0.8 LTR + 0.2 Manual is a standard product configuration
        self.ltr_blend_ratio = 0.8

    def calculate_manual_score(self, features: Dict[str, float]) -> float:
        """Computes a manual weighted score based on hand-crafted business logic."""
        score = 0.0
        for feat, weight in self.weights.items():
            val = features.get(feat, 0.0)
            if feat == "embedding_similarity":
                # Convert 0-1 similarity to 0-100 scale
                score += val * 100.0 * weight
            else:
                score += val * weight
        return round(score, 2)

    def rank_retrieved_candidates(
        self, 
        retrieved_candidates: List[Tuple[Dict[str, Any], float]], 
        jd_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Computes final scores for retrieved candidates by blending LTR inference
        with manual heuristics, detects profile traps, and outputs a sorted list.
        """
        if not retrieved_candidates:
            return []

        calculator = CandidateFeatureCalculator(jd_data)
        candidates_features = []
        candidate_records = []

        # 1. Engineer features and calculate manual scores
        for cand, emb_sim in retrieved_candidates:
            features = calculator.compute_all_features(cand, emb_sim)
            manual_score = self.calculate_manual_score(features)
            
            # Detect trap risks
            risk_analysis = TrapDetector.detect_traps(cand)
            
            candidates_features.append(features)
            candidate_records.append({
                "candidate": cand,
                "features": features,
                "manual_score": manual_score,
                "risk": risk_analysis
            })

        # 2. Convert features to DataFrame for LTR model prediction
        df_features = pd.DataFrame(candidates_features)
        
        # Load and run LTR model
        try:
            ltr_scores = self.ltr_model.predict(df_features)
            # Normalize LTR scores to 0-100 scale (Min-Max scaling to ensure bounds)
            if len(ltr_scores) > 1:
                min_s, max_s = np.min(ltr_scores), np.max(ltr_scores)
                if max_s - min_s > 0:
                    ltr_scores = ((ltr_scores - min_s) / (max_s - min_s)) * 100.0
                else:
                    ltr_scores = np.full(len(ltr_scores), 50.0)
            else:
                ltr_scores = np.array([100.0])
        except Exception as e:
            print(f"LTR prediction failed: {e}. Blending using manual score only.")
            ltr_scores = [rec["manual_score"] for rec in candidate_records]

        # 3. Blend LTR and Manual score, and adjust based on risk
        final_list = []
        for i, rec in enumerate(candidate_records):
            manual = rec["manual_score"]
            ltr = float(ltr_scores[i])
            
            # Blend
            blend_score = (ltr * self.ltr_blend_ratio) + (manual * (1.0 - self.ltr_blend_ratio))
            
            # Penalize final score based on risk (High risk deducts up to 30 points)
            risk_score = rec["risk"]["risk_score"]
            penalty = (risk_score / 100.0) * 30.0
            final_score = max(0.0, min(100.0, blend_score - penalty))
            
            rec["final_score"] = round(final_score, 2)
            
            # Output record
            final_list.append({
                "candidate_id": rec["candidate"]["candidate_id"],
                "profile": rec["candidate"]["profile"],
                "score": rec["final_score"],
                "features": rec["features"],
                "risk": rec["risk"],
                "candidate_raw": rec["candidate"]
            })

        # 4. Strict tie-breaker sorting:
        # We sort by: final score descending, then candidate_id ascending (alphabetical order)
        # This is a strict challenge requirement verified by validate_submission.py!
        final_list.sort(key=lambda x: (-x["score"], x["candidate_id"]))
        
        return final_list
