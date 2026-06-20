import json
from backend.services.gemini import call_gemini_async

async def generate_interview_questions(
    candidate_profile: dict, 
    job_description: dict
) -> list:
    """
    Generates tailored interview questions for a candidate based on their background and job gaps.
    """
    prompt = f"""
    You are an expert technical interviewer. Review the candidate's profile and the job description.
    Generate a curated list of custom interview questions designed to test the candidate's actual depth in areas where they are either strong, weak, or have gaps.

    You must generate exactly 10 questions.
    Categorize each question by:
    - "category": One of "Technical", "Coding", "System Design", "Behavioral", "Leadership".
    - "difficulty": One of "Easy", "Medium", "Hard".

    You must output a JSON object containing a SINGLE key "questions", which is a list of question objects.
    Each question object MUST contain:
    - "category": string ("Technical", "Coding", "System Design", "Behavioral", "Leadership")
    - "difficulty": string ("Easy", "Medium", "Hard")
    - "question": The question text. Make it specific to the candidate's background and the job requirements (e.g. refer to projects on their resume or specific technologies).
    - "guidance": What the interviewer should look for in a good answer.

    Be creative. Do not output generic questions. Target the candidate's specific projects and missing technologies.
    Ensure the output is a single valid JSON object. Do not include markdown code block formatting (like ```json ... ```) in the raw response, just return the plain JSON.

    Job Description:
    {json.dumps(job_description, indent=2)}

    Candidate Profile:
    {json.dumps(candidate_profile, indent=2)}
    """
    
    try:
        response_text = await call_gemini_async(prompt, json_mode=True, temperature=0.5)
        data = json.loads(response_text)
        return data.get("questions", [])
    except Exception as e:
        print(f"Failed to generate interview questions: {e}")
        return [
            {
                "category": "Behavioral",
                "difficulty": "Medium",
                "question": "Can you walk me through a complex technical challenge you solved recently?",
                "guidance": "Look for structured communication, problem solving, and details about their technical approach."
            },
            {
                "category": "Technical",
                "difficulty": "Hard",
                "question": "Explain how you would design a high-throughput data processing pipeline for this role.",
                "guidance": "Look for familiarity with message queues, load balancing, databases, and scalability constraints."
            }
        ]
