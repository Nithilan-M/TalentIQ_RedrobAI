import os
import sys

# Add the project root to sys.path so backend imports resolve when run directly from this folder
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.connection import engine, Base, SessionLocal
from backend.database.models import User, CandidateEmbedding
from backend.api import auth, job_desc, resume, candidate, analytics, reports, challenge
from backend.api.auth import get_password_hash
from backend.embeddings.vector_store import vector_store_manager

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Hiring Committee API",
    description="Enterprise-grade AI-powered recruiter platform backend.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Vite frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(job_desc.router)
app.include_router(resume.router)
app.include_router(candidate.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(challenge.router)


@app.on_event("startup")
def startup_event():
    """
    Runs on server startup:
    1. Seeds a default recruiter account if the database is empty.
    2. Syncs/rebuilds the FAISS/NumPy in-memory vector search index.
    """
    db = SessionLocal()
    try:
        # Seed default admin recruiter user if none exists
        admin_email = "admin@talent_iq.ai"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            hashed_pw = get_password_hash("password123")
            admin_user = User(email=admin_email, hashed_password=hashed_pw)
            db.add(admin_user)
            db.commit()
            print(f"Seeded default recruiter recruiter: {admin_email} (password: password123)")

        # Sync/build semantic vector search index
        print("Synchronizing semantic vector index from database...")
        embeddings_list = db.query(CandidateEmbedding).all()
        candidates_data = [
            {"candidate_id": item.candidate_id, "embedding": item.embedding}
            for item in embeddings_list
        ]
        vector_store_manager.build_index(candidates_data)
        print("Semantic vector index synchronized successfully.")
        
    except Exception as e:
        print(f"Error during server startup: {e}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "AI Hiring Committee API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
