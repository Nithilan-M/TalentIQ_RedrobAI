from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.database.connection import get_db
from backend.database.models import (
    Candidate, JobDescription, RankingResult, Recommendation, 
    InterviewQuestion, Experience, Education, Project, Certification, User
)
from backend.api.auth import get_current_user
from backend.embeddings.vector_store import vector_store_manager
from backend.agents.explainability import generate_explainability_data
from backend.agents.interview_agent import generate_interview_questions

router = APIRouter(prefix="/api/candidate", tags=["Candidates"])

class CompareRequest(BaseModel):
    candidate_ids: List[int]

@router.get("/list")
def get_candidates(
    job_description_id: int,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get candidates for a job description.
    Supports optional semantic search query.
    If query is provided, candidate results are filtered and sorted by vector similarity.
    Otherwise, sorted by candidate overall match score.
    """
    # Verify JD ownership
    jd = db.query(JobDescription).filter(JobDescription.id == job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    # Base query for candidates linked to this JD
    candidates = db.query(Candidate).filter(Candidate.job_description_id == job_description_id).all()
    if not candidates:
        return []

    candidate_map = {c.id: c for c in candidates}

    # If semantic search query is present
    if query and query.strip():
        # Rebuild vector store in memory if empty (resilience safeguard)
        if not vector_store_manager.candidate_ids:
            all_embeddings = db.query(CandidateEmbedding).all()
            c_data = [{"candidate_id": e.candidate_id, "embedding": e.embedding} for e in all_embeddings]
            vector_store_manager.build_index(c_data)

        # Search using FAISS / NumPy
        search_results = vector_store_manager.search(query.strip(), top_k=50)
        
        ranked_candidates = []
        for candidate_id, similarity_score in search_results:
            if candidate_id in candidate_map:
                c = candidate_map[candidate_id]
                # Fetch ranking result
                rank = db.query(RankingResult).filter(RankingResult.candidate_id == c.id).first()
                overall_score = rank.overall_score if rank else 0.0
                
                # Fetch Recommendation decision
                rec = db.query(Recommendation).filter(Recommendation.candidate_id == c.id).first()
                decision = rec.judge_decision if rec else "Borderline"

                ranked_candidates.append({
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "skills": c.skills,
                    "overall_score": overall_score,
                    "decision": decision,
                    "similarity_score": round(similarity_score, 4)
                })
        
        # Add any candidates linked to this JD that were not returned by vector store search
        seen_ids = {item["id"] for item in ranked_candidates}
        for c_id, c in candidate_map.items():
            if c_id not in seen_ids:
                rank = db.query(RankingResult).filter(RankingResult.candidate_id == c_id).first()
                rec = db.query(Recommendation).filter(Recommendation.candidate_id == c_id).first()
                ranked_candidates.append({
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "skills": c.skills,
                    "overall_score": rank.overall_score if rank else 0.0,
                    "decision": rec.judge_decision if rec else "Borderline",
                    "similarity_score": 0.0
                })
        return ranked_candidates
    else:
        # Standard query sorted by Match Score descending
        ranked_candidates = []
        for c in candidates:
            rank = db.query(RankingResult).filter(RankingResult.candidate_id == c.id).first()
            overall_score = rank.overall_score if rank else 0.0
            
            rec = db.query(Recommendation).filter(Recommendation.candidate_id == c.id).first()
            decision = rec.judge_decision if rec else "Borderline"
            
            ranked_candidates.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "skills": c.skills,
                "overall_score": overall_score,
                "decision": decision,
                "similarity_score": None
            })
        
        # Sort by match score descending
        ranked_candidates.sort(key=lambda x: x["overall_score"], reverse=True)
        return ranked_candidates

@router.get("/{id}")
async def get_candidate_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all information for a specific candidate.
    Calculates explainability data dynamically.
    """
    c = db.query(Candidate).filter(Candidate.id == id).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    # Verify JD owner
    jd = db.query(JobDescription).filter(JobDescription.id == c.job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to this candidate's details."
        )

    # Load child entities
    experiences = db.query(Experience).filter(Experience.candidate_id == id).all()
    educations = db.query(Education).filter(Education.candidate_id == id).all()
    projects = db.query(Project).filter(Project.candidate_id == id).all()
    certifications = db.query(Certification).filter(Certification.candidate_id == id).all()
    
    # Load rankings & recommendations
    rank = db.query(RankingResult).filter(RankingResult.candidate_id == id).first()
    rec = db.query(Recommendation).filter(Recommendation.candidate_id == id).first()
    questions = db.query(InterviewQuestion).filter(InterviewQuestion.candidate_id == id).first()

    # Dynamic Explainability metrics
    jd_data = {
        "title": jd.title,
        "skills_required": jd.skills_required,
        "skills_preferred": jd.skills_preferred,
        "experience_required": jd.experience_required,
        "education_required": jd.education_required,
        "responsibilities": jd.responsibilities,
        "industry": jd.industry,
        "soft_skills": jd.soft_skills,
        "leadership_requirements": jd.leadership_requirements,
        "technologies": jd.technologies
    }
    
    cv_data = {
        "name": c.name,
        "skills": c.skills,
        "technical_summary": c.technical_summary,
        "achievements": c.achievements,
        "languages": c.languages,
        "experience": [{"company": e.company, "role": e.role, "duration": e.duration, "description": e.description} for e in experiences],
        "education": [{"degree": ed.degree, "field_of_study": ed.field_of_study, "institution": ed.institution, "year": ed.year} for ed in educations],
        "projects": [{"title": p.title, "description": p.description, "technologies": p.technologies} for p in projects],
        "certifications": [{"name": ce.name, "issuing_organization": ce.issuing_organization, "year": ce.year} for ce in certifications]
    }

    rank_dict = {
        "overall_score": rank.overall_score,
        "skill_match_score": rank.skill_match_score,
        "experience_score": rank.experience_score,
        "projects_score": rank.projects_score,
        "education_score": rank.education_score,
        "certifications_score": rank.certifications_score,
        "leadership_score": rank.leadership_score,
        "soft_skills_score": rank.soft_skills_score
    } if rank else {
        "overall_score": 0.0,
        "skill_match_score": 0.0,
        "experience_score": 0.0,
        "projects_score": 0.0,
        "education_score": 0.0,
        "certifications_score": 0.0,
        "leadership_score": 0.0,
        "soft_skills_score": 0.0
    }

    # Generate explainability details using Gemini
    try:
        explain_data = await generate_explainability_data(cv_data, jd_data, rank_dict)
    except Exception as e:
        print(f"Error generating explainability report: {e}")
        explain_data = {
            "risk_score": 40,
            "potential_score": 60,
            "missing_skills": [],
            "strengths": [],
            "weaknesses": [],
            "evidence": ["Evidence loaded from static candidate records."]
        }

    return {
        "candidate": {
            "id": c.id,
            "job_description_id": c.job_description_id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "skills": c.skills,
            "technical_summary": c.technical_summary,
            "achievements": c.achievements,
            "languages": c.languages,
            "experiences": [{
                "company": exp.company,
                "role": exp.role,
                "duration": exp.duration,
                "description": exp.description
            } for exp in experiences],
            "educations": [{
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "institution": edu.institution,
                "year": edu.year
            } for edu in educations],
            "projects": [{
                "title": proj.title,
                "description": proj.description,
                "technologies": proj.technologies
            } for proj in projects],
            "certifications": [{
                "name": cert.name,
                "issuing_organization": cert.issuing_organization,
                "year": cert.year
            } for cert in certifications]
        },
        "ranking": rank_dict,
        "recommendation": {
            "advocate_feedback": rec.advocate_feedback if rec else "",
            "skeptic_feedback": rec.skeptic_feedback if rec else "",
            "judge_decision": rec.judge_decision if rec else "Borderline",
            "judge_confidence": rec.judge_confidence if rec else 50.0,
            "judge_summary": rec.judge_summary if rec else ""
        } if rec else None,
        "explainability": explain_data,
        "interview_questions": questions.questions if questions else []
    }

@router.post("/compare")
def compare_candidates(
    req: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare multiple candidates side-by-side.
    Returns composite dataset for chart generation and side-by-side tables.
    """
    if not req.candidate_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one candidate ID to compare."
        )

    results = []
    for cid in req.candidate_ids:
        c = db.query(Candidate).filter(Candidate.id == cid).first()
        if not c:
            continue
        
        # Verify ownership
        jd = db.query(JobDescription).filter(JobDescription.id == c.job_description_id, JobDescription.user_id == current_user.id).first()
        if not jd:
            continue

        rank = db.query(RankingResult).filter(RankingResult.candidate_id == cid).first()
        rec = db.query(Recommendation).filter(Recommendation.candidate_id == cid).first()
        
        # Get count of projects, certifications, experiences
        experience_count = db.query(Experience).filter(Experience.candidate_id == cid).count()
        project_count = db.query(Project).filter(Project.candidate_id == cid).count()
        cert_count = db.query(Certification).filter(Certification.candidate_id == cid).count()
        
        results.append({
            "id": c.id,
            "name": c.name,
            "skills": c.skills,
            "experience_count": experience_count,
            "project_count": project_count,
            "certification_count": cert_count,
            "overall_score": rank.overall_score if rank else 0.0,
            "skill_match_score": rank.skill_match_score if rank else 0.0,
            "experience_score": rank.experience_score if rank else 0.0,
            "projects_score": rank.projects_score if rank else 0.0,
            "education_score": rank.education_score if rank else 0.0,
            "certifications_score": rank.certifications_score if rank else 0.0,
            "leadership_score": rank.leadership_score if rank else 0.0,
            "soft_skills_score": rank.soft_skills_score if rank else 0.0,
            "decision": rec.judge_decision if rec else "Borderline",
            "confidence": rec.judge_confidence if rec else 50.0,
            "summary": rec.judge_summary if rec else ""
        })

    return results

@router.post("/{id}/regenerate-interview")
async def regenerate_interview(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerates interview questions for a candidate.
    """
    c = db.query(Candidate).filter(Candidate.id == id).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    # Verify JD owner
    jd = db.query(JobDescription).filter(JobDescription.id == c.job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access."
        )

    experiences = db.query(Experience).filter(Experience.candidate_id == id).all()
    educations = db.query(Education).filter(Education.candidate_id == id).all()
    projects = db.query(Project).filter(Project.candidate_id == id).all()
    certifications = db.query(Certification).filter(Certification.candidate_id == id).all()

    jd_data = {
        "title": jd.title,
        "skills_required": jd.skills_required,
        "skills_preferred": jd.skills_preferred,
        "experience_required": jd.experience_required,
        "education_required": jd.education_required,
        "responsibilities": jd.responsibilities,
        "industry": jd.industry,
        "soft_skills": jd.soft_skills,
        "leadership_requirements": jd.leadership_requirements,
        "technologies": jd.technologies
    }
    
    cv_data = {
        "name": c.name,
        "skills": c.skills,
        "technical_summary": c.technical_summary,
        "achievements": c.achievements,
        "languages": c.languages,
        "experience": [{"company": e.company, "role": e.role, "duration": e.duration, "description": e.description} for e in experiences],
        "education": [{"degree": ed.degree, "field_of_study": ed.field_of_study, "institution": ed.institution, "year": ed.year} for ed in educations],
        "projects": [{"title": p.title, "description": p.description, "technologies": p.technologies} for p in projects],
        "certifications": [{"name": ce.name, "issuing_organization": ce.issuing_organization, "year": ce.year} for ce in certifications]
    }

    try:
        new_qs = await generate_interview_questions(cv_data, jd_data)
        
        # Save to DB
        db_qs = db.query(InterviewQuestion).filter(InterviewQuestion.candidate_id == id).first()
        if db_qs:
            db_qs.questions = new_qs
        else:
            db_qs = InterviewQuestion(
                candidate_id=id,
                job_description_id=c.job_description_id,
                questions=new_qs
            )
            db.add(db_qs)
        
        db.commit()
        return new_qs
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate questions: {str(e)}"
        )
