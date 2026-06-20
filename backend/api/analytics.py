from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import (
    Candidate, JobDescription, RankingResult, Recommendation, 
    Experience, Education, User
)
from backend.api.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/")
def get_analytics(
    job_description_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate aggregate metrics and charts payload for the recruiter dashboard.
    """
    # Verify job description ownership
    jd = db.query(JobDescription).filter(JobDescription.id == job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    candidates = db.query(Candidate).filter(Candidate.job_description_id == job_description_id).all()
    if not candidates:
        return {
            "total_candidates": 0,
            "average_match_score": 0.0,
            "high_potential_count": 0,
            "skill_distribution": [],
            "experience_distribution": [],
            "education_distribution": [],
            "hiring_funnel": [
                {"name": "Strong Hire", "value": 0},
                {"name": "Hire", "value": 0},
                {"name": "Borderline", "value": 0},
                {"name": "No Hire", "value": 0}
            ],
            "score_distribution": []
        }

    total_candidates = len(candidates)
    candidate_ids = [c.id for c in candidates]

    # 1. Calculate Average Match Score and High Potential Count (Score >= 80)
    rankings = db.query(RankingResult).filter(RankingResult.candidate_id.in_(candidate_ids)).all()
    scores = [r.overall_score for r in rankings]
    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    high_potential_count = sum(1 for s in scores if s >= 80)

    # 2. Skill Distribution
    skill_counts = {}
    for c in candidates:
        for skill in c.skills:
            skill_cleaned = skill.strip()
            if skill_cleaned:
                skill_counts[skill_cleaned] = skill_counts.get(skill_cleaned, 0) + 1
    
    # Sort and take top 10 skills for visualizations
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    skill_distribution = [{"skill": s[0], "count": s[1]} for s in sorted_skills[:10]]

    # 3. Experience Distribution
    # Group candidates by years of experience. We check candidate experiences
    experience_counts = {"Junior (< 2 yrs)": 0, "Mid-level (2-5 yrs)": 0, "Senior (5-8 yrs)": 0, "Lead/Staff (8+ yrs)": 0}
    
    for cid in candidate_ids:
        # Fetch all experiences for candidate
        exps = db.query(Experience).filter(Experience.candidate_id == cid).all()
        # Estimate total duration in years. For local robustness, we look at the durations
        # If no explicit durations, we estimate years of experience from their experience score or default to 2
        # Let's count experience entries or try to parse years from duration strings
        total_years = 0
        for e in exps:
            dur = e.duration.lower() if e.duration else ""
            if "year" in dur or "yr" in dur:
                # Extract digits
                digits = [int(s) for s in dur.split() if s.isdigit()]
                if digits:
                    total_years += digits[0]
                else:
                    total_years += 1
            elif "month" in dur or "mo" in dur:
                digits = [int(s) for s in dur.split() if s.isdigit()]
                if digits:
                    total_years += digits[0] / 12
            else:
                total_years += 1.5 # Default estimate per role if not parseable

        if total_years < 2:
            experience_counts["Junior (< 2 yrs)"] += 1
        elif 2 <= total_years < 5:
            experience_counts["Mid-level (2-5 yrs)"] += 1
        elif 5 <= total_years < 8:
            experience_counts["Senior (5-8 yrs)"] += 1
        else:
            experience_counts["Lead/Staff (8+ yrs)"] += 1

    exp_distribution = [{"range": k, "count": v} for k, v in experience_counts.items()]

    # 4. Education Distribution
    edu_counts = {"Bachelor's": 0, "Master's": 0, "Doctorate (Ph.D.)": 0, "Other/Associate": 0}
    for cid in candidate_ids:
        edus = db.query(Education).filter(Education.candidate_id == cid).all()
        has_phd = False
        has_masters = False
        has_bachelors = False
        
        for ed in edus:
            degree_lower = ed.degree.lower()
            if "ph" in degree_lower or "doctor" in degree_lower:
                has_phd = True
            elif "master" in degree_lower or "m.s" in degree_lower or "mba" in degree_lower or "m.tech" in degree_lower:
                has_masters = True
            elif "bachelor" in degree_lower or "b.s" in degree_lower or "b.tech" in degree_lower or "b.a" in degree_lower:
                has_bachelors = True
                
        if has_phd:
            edu_counts["Doctorate (Ph.D.)"] += 1
        elif has_masters:
            edu_counts["Master's"] += 1
        elif has_bachelors:
            edu_counts["Bachelor's"] += 1
        else:
            edu_counts["Other/Associate"] += 1
            
    edu_distribution = [{"degree": k, "count": v} for k, v in edu_counts.items()]

    # 5. Hiring Funnel
    recommendations = db.query(Recommendation).filter(Recommendation.candidate_id.in_(candidate_ids)).all()
    funnel_counts = {"Strong Hire": 0, "Hire": 0, "Borderline": 0, "No Hire": 0}
    for r in recommendations:
        dec = r.judge_decision
        if dec in funnel_counts:
            funnel_counts[dec] += 1
        else:
            funnel_counts["Borderline"] += 1 # Safety net
            
    hiring_funnel = [{"name": k, "value": v} for k, v in funnel_counts.items()]

    # 6. Score Distribution (0-20, 21-40, 41-60, 61-80, 81-100)
    score_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scores:
        if s <= 20:
            score_ranges["0-20"] += 1
        elif s <= 40:
            score_ranges["21-40"] += 1
        elif s <= 60:
            score_ranges["41-60"] += 1
        elif s <= 80:
            score_ranges["61-80"] += 1
        else:
            score_ranges["81-100"] += 1
            
    score_distribution = [{"range": k, "count": v} for k, v in score_ranges.items()]

    return {
        "total_candidates": total_candidates,
        "average_match_score": average_score,
        "high_potential_count": high_potential_count,
        "skill_distribution": skill_distribution,
        "experience_distribution": exp_distribution,
        "education_distribution": edu_distribution,
        "hiring_funnel": hiring_funnel,
        "score_distribution": score_distribution
    }
