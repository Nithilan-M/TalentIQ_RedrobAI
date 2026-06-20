import os
import json
import csv
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Dict, Any


from backend.database.connection import get_db
from backend.database.models import User
from backend.api.auth import get_current_user
from backend.offline_pipeline.pipeline_runner import run_offline_ranking_pipeline, SUBMISSION_CSV_PATH
from backend.parsers.jd_loader import JD_JSON_PATH
from backend.validator.submission_validator import SubmissionValidator

router = APIRouter(prefix="/api/challenge", tags=["Redrob Challenge"])

@router.post("/run", status_code=status.HTTP_200_OK)
async def run_challenge_pipeline(
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the end-to-end offline candidate discovery and ranking pipeline.
    """
    try:
        temp_jsonl_path = None
        if file:
            import shutil
            # Save uploaded candidates.jsonl to temp directory
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            temp_jsonl_path = os.path.join(temp_dir, "challenge_uploaded_candidates.jsonl")
            with open(temp_jsonl_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        results = await run_offline_ranking_pipeline(input_jsonl=temp_jsonl_path)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )

@router.get("/jd", status_code=status.HTTP_200_OK)
def get_structured_jd(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the parsed and structured Job Description criteria.
    """
    if not os.path.exists(JD_JSON_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description criteria not parsed yet. Run the pipeline first."
        )
    
    with open(JD_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/validate", status_code=status.HTTP_200_OK)
def validate_current_submission(
    current_user: User = Depends(get_current_user)
):
    """
    Runs validation on the current generated submission CSV file.
    """
    if not os.path.exists(SUBMISSION_CSV_PATH):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No submission file found at {SUBMISSION_CSV_PATH}. Run the pipeline first."
        )
        
    validation = SubmissionValidator.validate_csv(SUBMISSION_CSV_PATH)
    return validation

@router.get("/analytics", status_code=status.HTTP_200_OK)
def get_challenge_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    Compiles summary statistics and distributions for the dashboard views.
    """
    # Run a quick lightweight pipeline dry-run or load from files if available
    # For speed, we will read the current submission CSV if it exists and compile analytics
    if not os.path.exists(SUBMISSION_CSV_PATH):
        return {
            "pipeline_executed": False,
            "feature_importances": {},
            "risk_distribution": {"Low": 0, "Medium": 0, "High": 0},
            "score_distribution": []
        }

    try:
        # Load sample features importance from LTR model
        from backend.learning_to_rank.ltr_model import LearningToRankModel
        model = LearningToRankModel()
        importances = model.get_feature_importances()

        # Parse CSV to compile scores and risk approximations
        scores = []
        with open(SUBMISSION_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores.append(float(row["score"]))

        # For challenge dashboard, we can return pre-calculated distributions
        score_bins = {"0.9-1.0": 0, "0.8-0.9": 0, "0.7-0.8": 0, "0.6-0.7": 0, "under 0.6": 0}
        for s in scores:
            if s >= 0.9: score_bins["0.9-1.0"] += 1
            elif s >= 0.8: score_bins["0.8-0.9"] += 1
            elif s >= 0.7: score_bins["0.7-0.8"] += 1
            elif s >= 0.6: score_bins["0.6-0.7"] += 1
            else: score_bins["under 0.6"] += 1

        score_distribution = [{"range": k, "count": v} for k, v in score_bins.items()]

        return {
            "pipeline_executed": True,
            "feature_importances": importances,
            "score_distribution": score_distribution
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics compilation failed: {str(e)}"
        )
