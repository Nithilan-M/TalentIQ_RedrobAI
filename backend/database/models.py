import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    
    # Extracted fields from Gemini
    skills_required = Column(JSON, default=[])       # List of strings
    skills_preferred = Column(JSON, default=[])      # List of strings
    experience_required = Column(String, nullable=True)
    education_required = Column(String, nullable=True)
    responsibilities = Column(JSON, default=[])      # List of strings
    industry = Column(String, nullable=True)
    soft_skills = Column(JSON, default=[])           # List of strings
    leadership_requirements = Column(JSON, default=[]) # List of strings
    technologies = Column(JSON, default=[])          # List of strings
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="job_descriptions")
    candidates = relationship("Candidate", back_populates="job_description", cascade="all, delete-orphan")
    rankings = relationship("RankingResult", back_populates="job_description", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="job_description", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="job_description", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    skills = Column(JSON, default=[])                 # List of strings
    technical_summary = Column(Text, nullable=True)
    achievements = Column(JSON, default=[])           # List of strings
    languages = Column(JSON, default=[])              # List of strings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="candidates")
    
    # Candidate detailed subcomponents
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    embedding = relationship("CandidateEmbedding", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    
    # Ranking & Evaluation results
    rankings = relationship("RankingResult", back_populates="candidate", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="candidate", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="candidate", cascade="all, delete-orphan")

class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    duration = Column(String, nullable=True)  # e.g., "Jan 2020 - Dec 2022" or "3 years"
    description = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="experiences")

class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    degree = Column(String, nullable=False)
    field_of_study = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    year = Column(String, nullable=True)

    candidate = relationship("Candidate", back_populates="educations")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=[])

    candidate = relationship("Candidate", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    name = Column(String, nullable=False)
    issuing_organization = Column(String, nullable=True)
    year = Column(String, nullable=True)

    candidate = relationship("Candidate", back_populates="certifications")

class CandidateEmbedding(Base):
    __tablename__ = "candidate_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    embedding = Column(JSON, nullable=False) # Store float list

    candidate = relationship("Candidate", back_populates="embedding")

class RankingResult(Base):
    __tablename__ = "ranking_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    # Specific dimensions out of 100
    overall_score = Column(Float, nullable=False)
    skill_match_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    projects_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    certifications_score = Column(Float, nullable=False)
    leadership_score = Column(Float, nullable=False)
    soft_skills_score = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="rankings")
    job_description = relationship("JobDescription", back_populates="rankings")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    advocate_feedback = Column(Text, nullable=False)
    skeptic_feedback = Column(Text, nullable=False)
    judge_decision = Column(String, nullable=False) # Strong Hire, Hire, Borderline, No Hire
    judge_confidence = Column(Float, nullable=False)
    judge_summary = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="recommendations")
    job_description = relationship("JobDescription", back_populates="recommendations")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    questions = Column(JSON, default=[]) # List of question objects
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interview_questions")
    job_description = relationship("JobDescription", back_populates="interview_questions")
