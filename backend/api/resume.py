import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import (
    JobDescription, Candidate, Experience, Education, Project, 
    Certification, CandidateEmbedding, RankingResult, Recommendation, 
    InterviewQuestion, User
)
from backend.api.auth import get_current_user
from backend.parsers.doc_parser import parse_document
from backend.agents.candidate_agent import parse_candidate_resume
from backend.agents.ranking_engine import evaluate_and_rank_candidate
from backend.agents.advocate_agent import generate_advocate_feedback
from backend.agents.skeptic_agent import generate_skeptic_feedback
from backend.agents.judge_agent import evaluate_committee_decision
from backend.agents.explainability import generate_explainability_data
from backend.agents.interview_agent import generate_interview_questions
from backend.embeddings.vector_store import vector_store_manager

router = APIRouter(prefix="/api/resume", tags=["Resumes"])

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

def update_vector_store(db: Session):
    """
    Helper function to rebuild the FAISS/NumPy search index using embeddings from the database.
    """
    embeddings_list = db.query(CandidateEmbedding).all()
    candidates_data = [
        {"candidate_id": item.candidate_id, "embedding": item.embedding}
        for item in embeddings_list
    ]
    vector_store_manager.build_index(candidates_data)

@router.post("/upload-resumes", status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    job_description_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple resumes, parse them, extract fields via Gemini, generate BGE-small embeddings,
    save to database, calculate ranking, run AI hiring committee agents, and update search index.
    """
    # Verify job description exists
    jd = db.query(JobDescription).filter(JobDescription.id == job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID {job_description_id} not found."
        )

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

    successful_uploads = []
    failed_uploads = []

    for file in files:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".pdf", ".docx", ".txt"]:
            failed_uploads.append({"filename": file.filename, "error": "Unsupported file format."})
            continue

        temp_file_path = os.path.join(TEMP_DIR, f"resume_{current_user.id}_{file.filename}")
        
        try:
            # 1. Save file locally
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 2. Extract raw text
            raw_text = parse_document(temp_file_path)
            if not raw_text.strip():
                failed_uploads.append({"filename": file.filename, "error": "File text extraction resulted in empty content."})
                continue

            # 3. Call Candidate Agent to structure CV details
            cv_profile = await parse_candidate_resume(raw_text)
            
            # Start database save transaction block
            # 4. Insert Candidate profile
            db_candidate = Candidate(
                job_description_id=job_description_id,
                name=cv_profile.get("name", file.filename.split(".")[0]),
                email=cv_profile.get("email", ""),
                phone=cv_profile.get("phone", ""),
                skills=cv_profile.get("skills", []),
                technical_summary=cv_profile.get("technical_summary", ""),
                achievements=cv_profile.get("achievements", []),
                languages=cv_profile.get("languages", [])
            )
            db.add(db_candidate)
            db.flush() # Flushes candidate to generate ID

            # 5. Insert subcomponents: Experience, Education, Projects, Certifications
            for exp in cv_profile.get("experience", []):
                db_exp = Experience(
                    candidate_id=db_candidate.id,
                    company=exp.get("company", ""),
                    role=exp.get("role", ""),
                    duration=exp.get("duration", ""),
                    description=exp.get("description", "")
                )
                db.add(db_exp)

            for edu in cv_profile.get("education", []):
                db_edu = Education(
                    candidate_id=db_candidate.id,
                    degree=edu.get("degree", ""),
                    field_of_study=edu.get("field_of_study", ""),
                    institution=edu.get("institution", ""),
                    year=str(edu.get("year", ""))
                )
                db.add(db_edu)

            for proj in cv_profile.get("projects", []):
                db_proj = Project(
                    candidate_id=db_candidate.id,
                    title=proj.get("title", ""),
                    description=proj.get("description", ""),
                    technologies=proj.get("technologies", [])
                )
                db.add(db_proj)

            for cert in cv_profile.get("certifications", []):
                db_cert = Certification(
                    candidate_id=db_candidate.id,
                    name=cert.get("name", ""),
                    issuing_organization=cert.get("issuing_organization", ""),
                    year=str(cert.get("year", ""))
                )
                db.add(db_cert)

            # 6. Generate embedding based on skills + technical summary
            summary_text_for_embedding = f"Name: {db_candidate.name}. Skills: {', '.join(db_candidate.skills)}. Summary: {db_candidate.technical_summary}"
            embedding_vector = vector_store_manager.get_embedding(summary_text_for_embedding)
            
            db_emb = CandidateEmbedding(
                candidate_id=db_candidate.id,
                embedding=embedding_vector
            )
            db.add(db_emb)

            # 7. Evaluate and Rank candidate
            ranking_scores = await evaluate_and_rank_candidate(cv_profile, jd_data)
            db_rank = RankingResult(
                candidate_id=db_candidate.id,
                job_description_id=job_description_id,
                overall_score=ranking_scores["overall_score"],
                skill_match_score=ranking_scores["skill_match_score"],
                experience_score=ranking_scores["experience_score"],
                projects_score=ranking_scores["projects_score"],
                education_score=ranking_scores["education_score"],
                certifications_score=ranking_scores["certifications_score"],
                leadership_score=ranking_scores["leadership_score"],
                soft_skills_score=ranking_scores["soft_skills_score"]
            )
            db.add(db_rank)

            # 8. Run Committee Debate: Advocate & Skeptic Agents
            advocate_report = await generate_advocate_feedback(cv_profile, jd_data)
            skeptic_report = await generate_skeptic_feedback(cv_profile, jd_data)
            
            # 9. Run Judge Agent to Reconcile
            judge_evaluation = await evaluate_committee_decision(
                cv_profile, jd_data, advocate_report, skeptic_report
            )
            db_recommendation = Recommendation(
                candidate_id=db_candidate.id,
                job_description_id=job_description_id,
                advocate_feedback=advocate_report,
                skeptic_feedback=skeptic_report,
                judge_decision=judge_evaluation.get("decision", "Borderline"),
                judge_confidence=float(judge_evaluation.get("confidence_score", 50)),
                judge_summary=judge_evaluation.get("summary", "")
            )
            db.add(db_recommendation)

            # 10. Generate custom interview questions
            interview_qs = await generate_interview_questions(cv_profile, jd_data)
            db_questions = InterviewQuestion(
                candidate_id=db_candidate.id,
                job_description_id=job_description_id,
                questions=interview_qs
            )
            db.add(db_questions)

            # Commit all inserts for this specific candidate
            db.commit()
            
            successful_uploads.append({
                "candidate_id": db_candidate.id,
                "name": db_candidate.name,
                "email": db_candidate.email,
                "overall_score": db_rank.overall_score,
                "decision": db_recommendation.judge_decision
            })

        except Exception as e:
            db.rollback()
            print(f"Failed to process resume {file.filename}: {e}")
            failed_uploads.append({"filename": file.filename, "error": str(e)})
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    # 11. Synchronize the local Vector Store FAISS/NumPy index
    try:
        update_vector_store(db)
    except Exception as e:
        print(f"Failed to update vector store index: {e}")

    return {
        "message": f"Processed {len(files)} resume(s).",
        "successful": successful_uploads,
        "failed": failed_uploads
    }
