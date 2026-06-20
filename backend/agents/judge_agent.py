import json
from backend.services.gemini import call_gemini_async

async def evaluate_committee_decision(
    candidate_profile: dict, 
    job_description: dict, 
    advocate_report: str, 
    skeptic_report: str
) -> dict:
    """
    Simulates the Judge agent in the hiring committee.
    Reconciles the Advocate and Skeptic reports to produce a final recommendation.
    """
    prompt = f"""
    You are the "Judge Agent" on an elite AI Hiring Committee.
    You have received the candidate's profile, the job requirements, the Advocate's recommendation report, and the Skeptic's critical review.
    
    Your task is to weigh both sides objectively and deliver the final verdict.
    
    You must output a JSON object containing EXACTLY these keys:
    1. "decision": Must be one of the following string options:
       - "Strong Hire": The candidate has exceptional strengths with minor/negligible risks.
       - "Hire": The candidate is well-qualified, strengths outweigh the manageable risks.
       - "Borderline": The candidate has notable gaps, but could succeed; requires careful interview screening.
       - "No Hire": The candidate has critical skill/experience gaps or major hiring risks.
    2. "confidence_score": An integer between 0 and 100 representing your level of confidence in this verdict.
    3. "summary": A detailed, objective paragraph summarizing the committee's consensus, detailing why the decision was reached, and how the recruiter should proceed (e.g. key areas to test).

    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}

    Advocate Report:
    {advocate_report}

    Skeptic Report:
    {skeptic_report}
    """
    
    try:
        response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.2)
        decision_data = json.loads(response_text)
        return decision_data
    except Exception as e:
        print(f"Failed to parse judge agent: {e}")
        return {
            "decision": "Borderline",
            "confidence_score": 50,
            "summary": "Committee decision generated under rate-limit fallback. Advise manual profile check."
        }
