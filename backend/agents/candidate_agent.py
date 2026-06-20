import json
from backend.services.gemini import call_gemini_async

async def parse_candidate_resume(resume_text: str) -> dict:
    """
    Uses Gemini to analyze raw resume text and extract candidate details.
    """
    prompt = f"""
    You are an expert technical resume parser. Analyze the following resume text and extract key information.
    
    You must output a JSON object containing EXACTLY these keys:
    1. "name": Candidate's full name. If not found, deduce or leave blank.
    2. "email": Candidate's email address.
    3. "phone": Candidate's phone number.
    4. "skills": A list of technical skills (e.g. ["React", "TypeScript", "Python"]).
    5. "technical_summary": A concise technical summary of the candidate's career.
    6. "achievements": A list of major achievements/awards.
    7. "languages": A list of languages spoken.
    8. "experience": A list of experience objects. Each object MUST contain:
       - "company": Name of the company.
       - "role": Job title.
       - "duration": Dates of employment (e.g. "Jan 2020 - Dec 2022" or "3 years").
       - "description": Key projects and activities in this role.
    9. "education": A list of education objects. Each object MUST contain:
       - "degree": Degree name (e.g. "B.S.", "M.S.", "Ph.D.").
       - "field_of_study": Field of study (e.g. "Computer Science").
       - "institution": School or University name.
       - "year": Graduation year or range.
    10. "projects": A list of project objects. Each object MUST contain:
       - "title": Name of the project.
       - "description": Description of the project.
       - "technologies": List of technologies used (e.g. ["Python", "Flask"]).
    11. "certifications": A list of certification objects. Each object MUST contain:
       - "name": Name of the certification.
       - "issuing_organization": Organization that issued it (e.g. "AWS", "Google").
       - "year": Year obtained.
    12. "leadership_experience": A list of strings describing any leadership experiences or roles (e.g. "Led a team of 4 frontend devs").

    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.
    
    Resume text:
    ---
    {resume_text}
    ---
    """
    
    response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.1)
    
    try:
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"Failed to parse candidate agent JSON response: {e}. Raw: {response_text}")
        return {
            "name": "Unknown Candidate",
            "email": "",
            "phone": "",
            "skills": [],
            "technical_summary": "",
            "achievements": [],
            "languages": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "leadership_experience": []
        }
