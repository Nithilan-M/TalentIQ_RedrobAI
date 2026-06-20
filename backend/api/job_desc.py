import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import JobDescription, User
from backend.api.auth import get_current_user
from backend.parsers.doc_parser import parse_document
from backend.agents.jd_agent import parse_job_description

router = APIRouter(prefix="/api/job-description", tags=["Job Descriptions"])

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_jd(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a job description file (PDF, DOCX, TXT), parse its content, 
    run the Gemini parsing agent, and save the structured details in the database.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF, DOCX, and TXT are allowed."
        )

    # Save uploaded file temporarily
    temp_file_path = os.path.join(TEMP_DIR, f"jd_{current_user.id}_{file.filename}")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse text from file
        raw_text = parse_document(temp_file_path)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file appears to be empty or unreadable."
            )

        # Call Gemini JD Agent to extract structured schema
        structured_data = await parse_job_description(raw_text)

        # Create new JobDescription model instance
        db_jd = JobDescription(
            title=structured_data.get("title", file.filename.split(".")[0]),
            raw_text=raw_text,
            skills_required=structured_data.get("skills_required", []),
            skills_preferred=structured_data.get("skills_preferred", []),
            experience_required=structured_data.get("experience_required", ""),
            education_required=structured_data.get("education_required", ""),
            responsibilities=structured_data.get("responsibilities", []),
            industry=structured_data.get("industry", ""),
            soft_skills=structured_data.get("soft_skills", []),
            leadership_requirements=structured_data.get("leadership_requirements", []),
            technologies=structured_data.get("technologies", []),
            user_id=current_user.id
        )

        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)
        
        return {
            "message": "Job description uploaded and processed successfully",
            "id": db_jd.id,
            "title": db_jd.title,
            "skills_required": db_jd.skills_required,
            "technologies": db_jd.technologies
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the job description: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.get("/latest")
def get_latest_jd(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest uploaded Job Description for the current recruiter.
    """
    jd = db.query(JobDescription)\
        .filter(JobDescription.user_id == current_user.id)\
        .order_by(JobDescription.created_at.desc())\
        .first()
        
    if not jd:
        return None
        
    return {
        "id": jd.id,
        "title": jd.title,
        "skills_required": jd.skills_required,
        "skills_preferred": jd.skills_preferred,
        "experience_required": jd.experience_required,
        "education_required": jd.education_required,
        "responsibilities": jd.responsibilities,
        "industry": jd.industry,
        "soft_skills": jd.soft_skills,
        "leadership_requirements": jd.leadership_requirements,
        "technologies": jd.technologies,
        "created_at": jd.created_at
    }

@router.get("/list")
def list_jds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all job descriptions uploaded by the current recruiter.
    """
    jds = db.query(JobDescription)\
        .filter(JobDescription.user_id == current_user.id)\
        .order_by(JobDescription.created_at.desc())\
        .all()
        
    return [
        {
            "id": jd.id,
            "title": jd.title,
            "created_at": jd.created_at
        } for jd in jds
    ]

@router.get("/{id}")
def get_jd_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific job description details by ID.
    """
    jd = db.query(JobDescription).filter(JobDescription.id == id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    return {
        "id": jd.id,
        "title": jd.title,
        "raw_text": jd.raw_text,
        "skills_required": jd.skills_required,
        "skills_preferred": jd.skills_preferred,
        "experience_required": jd.experience_required,
        "education_required": jd.education_required,
        "responsibilities": jd.responsibilities,
        "industry": jd.industry,
        "soft_skills": jd.soft_skills,
        "leadership_requirements": jd.leadership_requirements,
        "technologies": jd.technologies,
        "created_at": jd.created_at
    }
