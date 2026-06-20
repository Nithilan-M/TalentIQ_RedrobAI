import json
from backend.services.gemini import call_gemini_async

async def generate_explainability_data(
    candidate_profile: dict, 
    job_description: dict, 
    ranking_scores: dict
) -> dict:
    """
    Generates explainability metrics and evidence for why a candidate received their match scores.
    """
    prompt = f"""
    You are an expert AI HR explainability engine. Analyze the candidate profile, job description, and the scoring results.
    Provide a detailed breakdown of the explanation parameters so the recruiter clearly understands WHY the candidate received their score.

    You must output a JSON object containing EXACTLY these keys:
    1. "risk_score": An integer (0 to 100) representing the hiring risk (e.g. gaps, missing critical skills, short durations).
    2. "potential_score": An integer (0 to 100) representing growth potential, learning ability, and projects alignment.
    3. "missing_skills": A list of strings showing critical skills from the job description that the candidate lacks.
    4. "strengths": A list of the top 3-4 professional strengths of the candidate.
    5. "weaknesses": A list of the top 2-3 professional weaknesses or gaps.
    6. "evidence": A list of string statements pointing to specific facts in the resume that justify the scoring (e.g. "Over 4 years of experience using React", "Managed a team of engineers at TechCorp").

    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}

    Scoring Context:
    {json.dumps(ranking_scores, indent=2)}
    """
    
    response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.1)
    
    try:
        explainability_data = json.loads(response_text)
        return explainability_data
    except Exception as e:
        print(f"Failed to parse explainability JSON response: {e}. Raw: {response_text}")
        return {
            "risk_score": 50,
            "potential_score": 50,
            "missing_skills": [],
            "strengths": [],
            "weaknesses": [],
            "evidence": ["Evaluation metrics generated under default criteria."]
        }
