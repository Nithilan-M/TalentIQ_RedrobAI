import os
import sys

# Programmatically add the workspace root to Python search paths
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, workspace_root)

print("Checking Python environment...")
print(f"Python version: {sys.version}")
print(f"Workspace root injected: {workspace_root}")

# 1. Test standard ML & parsing libraries
try:
    import fitz
    print("[Success] PyMuPDF (fitz) imported successfully")
except Exception as e:
    print(f"[Failure] PyMuPDF import failed: {e}")

try:
    import docx
    print("[Success] python-docx imported successfully")
except Exception as e:
    print(f"[Failure] python-docx import failed: {e}")

try:
    import numpy as np
    print("[Success] NumPy imported successfully")
except Exception as e:
    print(f"[Failure] NumPy import failed: {e}")

try:
    import faiss
    print("[Success] FAISS imported successfully")
except Exception as e:
    print(f"[Failure] FAISS import failed: {e}")

try:
    import sentence_transformers
    print("[Success] Sentence Transformers imported successfully")
except Exception as e:
    print(f"[Failure] Sentence Transformers import failed: {e}")

try:
    import reportlab
    print("[Success] ReportLab imported successfully")
except Exception as e:
    print(f"[Failure] ReportLab import failed: {e}")

# 2. Test custom modules
try:
    from backend.database.connection import engine, Base
    from backend.database.models import User, Candidate
    print("[Success] Relational Database models loaded successfully")
except Exception as e:
    print(f"[Failure] Custom DB models import failed: {e}")

try:
    from backend.embeddings.vector_store import vector_store_manager
    print("[Success] Vector Store manager imported successfully")
except Exception as e:
    print(f"[Failure] Custom Vector Store import failed: {e}")

try:
    from backend.services.gemini import call_gemini_async
    from backend.agents.jd_agent import parse_job_description
    from backend.agents.candidate_agent import parse_candidate_resume
    from backend.agents.ranking_engine import evaluate_and_rank_candidate
    from backend.agents.advocate_agent import generate_advocate_feedback
    from backend.agents.skeptic_agent import generate_skeptic_feedback
    from backend.agents.judge_agent import evaluate_committee_decision
    from backend.agents.explainability import generate_explainability_data
    from backend.agents.interview_agent import generate_interview_questions
    print("[Success] All 7 Gemini Committee Agent modules imported successfully")
except Exception as e:
    print(f"[Failure] Custom AI Agents import failed: {e}")

try:
    from fastapi import FastAPI
    from backend.main import app
    print("[Success] FastAPI Application compiled successfully")
except Exception as e:
    print(f"[Failure] FastAPI Application import failed: {e}")

print("Verification complete.")
sys.exit(0)
