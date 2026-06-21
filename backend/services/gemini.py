import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

async def call_gemini_async(prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
    """
    Asynchronously calls the Gemini 2.5 Flash API with the given prompt.
    If json_mode is True, requests Gemini to return a structured JSON string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your backend/.env file.")

    url = f"{GEMINI_API_URL}?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature
        }
    }
    
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if response.status_code != 200:
                raise Exception(f"Gemini API returned error code {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract content from response structure
            candidates = result.get("candidates", [])
            if not candidates:
                raise Exception("Gemini API response did not contain candidates.")
                
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise Exception("Gemini API response candidate did not contain parts.")
                
            text = parts[0].get("text", "")
            return text
            
        except httpx.RequestError as exc:
            raise Exception(f"An error occurred while requesting Gemini API: {exc}")

def call_gemini_sync(prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
    """
    Synchronous wrapper for calling the Gemini API. Useful for background jobs or scripts.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    url = f"{GEMINI_API_URL}?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature}
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200:
            raise Exception(f"Gemini API returned error code {response.status_code}: {response.text}")
        
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text
    except Exception as exc:
        raise Exception(f"An error occurred while requesting Gemini API: {exc}")
