import json
from backend.services.gemini import call_gemini_async

async def parse_job_description(jd_text: str) -> dict:
    """
    Uses Gemini to analyze raw Job Description text and extract structured information.
    """
    prompt = f"""
    You are an expert technical recruiter. Analyze the following Job Description text and extract key details.
    
    You must output a JSON object containing EXACTLY these keys:
    1. "title": The formal job title. If not clearly specified, deduce a suitable title.
    2. "skills_required": A list of essential technical skills required for this job (e.g. ["React", "Python", "SQL"]).
    3. "skills_preferred": A list of nice-to-have or preferred technical skills (e.g. ["Docker", "AWS", "FastAPI"]).
    4. "experience_required": A text summary of required experience (e.g. "5+ years of software engineering experience").
    5. "education_required": A text summary of minimum/preferred education (e.g. "Bachelor's in Computer Science or equivalent").
    6. "responsibilities": A list of key responsibilities and duties (e.g. ["Design scalable databases", "Mentor junior engineers"]).
    7. "industry": The industry field (e.g. "SaaS", "FinTech", "Healthcare").
    8. "soft_skills": A list of soft skills requested (e.g. ["Communication", "Agile leadership", "Team collaboration"]).
    9. "leadership_requirements": A list of leadership requirements or qualities (e.g. ["Lead engineering teams", "Prioritize features"]).
    10. "technologies": A list of key programming languages, frameworks, or developer tools mentioned (e.g. ["TypeScript", "FastAPI", "PostgreSQL"]).

    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.
    
    Job Description text:
    ---
    {jd_text}
    ---
    """
    
    response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.1)
    
    try:
        data = json.loads(response_text)
        return data
    except Exception as e:
        # Fallback in case of parse error - return schema with empty values
        print(f"Failed to parse JD agent JSON response: {e}. Raw: {response_text}")
        return {
            "title": "Software Engineer",
            "skills_required": [],
            "skills_preferred": [],
            "experience_required": "",
            "education_required": "",
            "responsibilities": [],
            "industry": "",
            "soft_skills": [],
            "leadership_requirements": [],
            "technologies": []
        }
