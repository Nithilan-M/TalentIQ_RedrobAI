from backend.services.gemini import call_gemini_async
import json

async def generate_advocate_feedback(candidate_profile: dict, job_description: dict) -> str:
    """
    Simulates the Advocate agent in the hiring committee.
    Focuses on strengths, projects, achievements, leadership, and potential.
    """
    prompt = f"""
    You are the "Advocate Agent" on an elite AI Hiring Committee.
    Your sole task is to build the strongest possible case for hiring the candidate for the specified job.
    
    Analyze the candidate's profile and the job description. Draft a professional, persuasive argument highlighting:
    1. Key strengths and technical competencies that align perfectly with the role.
    2. Notable projects and practical achievements that demonstrate their execution capabilities.
    3. Leadership, initiative, learning agility, or self-improvement evidence.
    4. Why this candidate would make a fantastic addition to the team and their potential long-term value.

    Write your feedback in clean Markdown format with professional bullet points and headers. Do not include weaknesses or risks.

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}
    """
    
    try:
        feedback = await call_gemini_async(prompt, json_mode=False, temperature=0.7)
        return feedback
    except Exception as e:
        print(f"Advocate agent failed: {e}. Falling back to default report.")
        return f"""### Advocate Evaluation (Fallback)
- **Key Strengths**: Candidate possesses a solid technical background matching the core requirements.
- **Projects**: Relevant practical projects demonstrating software engineering competency.
- **Leadership**: Good initiative and communication demonstrated.
- **Decision Support**: Strong recommendation to advance to the next round based on skills profile.
"""
