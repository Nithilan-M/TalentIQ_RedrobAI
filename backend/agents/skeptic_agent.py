from backend.services.gemini import call_gemini_async
import json

async def generate_skeptic_feedback(candidate_profile: dict, job_description: dict) -> str:
    """
    Simulates the Skeptic agent in the hiring committee.
    Focuses on weaknesses, missing skills, employment gaps, inconsistencies, and hiring risks.
    """
    prompt = f"""
    You are the "Skeptic Agent" on an elite AI Hiring Committee.
    Your sole task is to conduct a critical analysis of the candidate. You are NOT looking to reject them blindly, but rather to uncover potential hiring risks, missing capabilities, or inconsistencies that a recruiter must know.
    
    Analyze the candidate's profile and the job description. Draft a professional, constructive critic report highlighting:
    1. Key missing skills (both required and preferred skills that are not present or weak in the resume).
    2. Employment gaps, short tenures, or frequency of changing jobs.
    3. Inconsistencies between their projects, education, and technical experience.
    4. Potential hiring risks (e.g., lack of team experience, missing scale/production experience, or credential mismatches).
    5. Areas where the candidate might struggle in the role and what questions should be asked to verify their capability.

    Write your feedback in clean Markdown format with professional bullet points and headers. Do not include strengths or positive aspects.

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}
    """
    
    try:
        feedback = await call_gemini_async(prompt, json_mode=False, temperature=0.7)
        return feedback
    except Exception as e:
        print(f"Skeptic agent failed: {e}. Falling back to default report.")
        return f"""### Skeptic Evaluation (Fallback)
- **Hiring Risks**: Some required skills in the job description are not explicitly highlighted in the resume.
- **Experience Gaps**: Verify employment duration and active project contributions during interviews.
- **Areas of Concern**: Need to test deep technical expertise on production systems and architectural designs.
"""
