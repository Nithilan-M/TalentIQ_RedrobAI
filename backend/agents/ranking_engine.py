import json
from backend.services.gemini import call_gemini_async

async def evaluate_and_rank_candidate(candidate_profile: dict, job_description: dict) -> dict:
    """
    Evaluates a candidate profile against a job description.
    Uses Gemini to score 7 dimensions, then mathematically computes the weighted overall score.
    """
    
    prompt = f"""
    You are an elite corporate technical evaluator. Evaluate the candidate profile against the Job Description.
    Assign a score from 0 to 100 for each of the following dimensions based on suitability, relevance, and strength.
    Provide a concise explanation/justification for each score.

    Dimensions:
    1. Skill Match: How closely the candidate's skills match the required and preferred skills in the job description.
    2. Experience: How well the candidate's work experience matches the required duration, level of seniority, and domain expertise.
    3. Projects: The relevance, complexity, and technology alignment of the candidate's projects.
    4. Education: How well the candidate's degrees and fields of study align with what's required/preferred.
    5. Certifications: The presence and relevance of industry certifications (AWS, GCP, Scrum, etc.) to the role.
    6. Leadership: Candidates' leadership experiences, leading teams, mentoring, or driving project ownership.
    7. Soft Skills: Evidence of collaboration, communication, agility, and team problem-solving.

    You must output a JSON object containing EXACTLY these keys:
    - "skill_match_score": integer (0 to 100)
    - "skill_match_explanation": string
    - "experience_score": integer (0 to 100)
    - "experience_explanation": string
    - "projects_score": integer (0 to 100)
    - "projects_explanation": string
    - "education_score": integer (0 to 100)
    - "education_explanation": string
    - "certifications_score": integer (0 to 100)
    - "certifications_explanation": string
    - "leadership_score": integer (0 to 100)
    - "leadership_explanation": string
    - "soft_skills_score": integer (0 to 100)
    - "soft_skills_explanation": string

    Be objective, strict, and professional. Do not make up facts; grade solely on the data provided below.
    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```).

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}
    """
    
    response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.2)
    
    try:
        scores = json.loads(response_text)
    except Exception as e:
        print(f"Failed to parse ranking engine JSON response: {e}. Raw: {response_text}")
        scores = {
            "skill_match_score": 50,
            "skill_match_explanation": "Default score due to evaluation parsing error.",
            "experience_score": 50,
            "experience_explanation": "Default score.",
            "projects_score": 50,
            "projects_explanation": "Default score.",
            "education_score": 50,
            "education_explanation": "Default score.",
            "certifications_score": 50,
            "certifications_explanation": "Default score.",
            "leadership_score": 50,
            "leadership_explanation": "Default score.",
            "soft_skills_score": 50,
            "soft_skills_explanation": "Default score."
        }

    # Extract score values
    skill_score = float(scores.get("skill_match_score", 50))
    exp_score = float(scores.get("experience_score", 50))
    proj_score = float(scores.get("projects_score", 50))
    edu_score = float(scores.get("education_score", 50))
    cert_score = float(scores.get("certifications_score", 50))
    lead_score = float(scores.get("leadership_score", 50))
    soft_score = float(scores.get("soft_skills_score", 50))

    # Calculate overall weighted score:
    # Skill Match: 40%
    # Experience: 20%
    # Projects: 15%
    # Education: 10%
    # Certifications: 5%
    # Leadership: 5%
    # Soft Skills: 5%
    overall_score = (
        (skill_score * 0.40) +
        (exp_score * 0.20) +
        (proj_score * 0.15) +
        (edu_score * 0.10) +
        (cert_score * 0.05) +
        (lead_score * 0.05) +
        (soft_score * 0.05)
    )

    scores["overall_score"] = round(overall_score, 2)
    return scores
