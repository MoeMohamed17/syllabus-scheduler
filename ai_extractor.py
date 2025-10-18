import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_deadlines_with_ai(text: str, filename: str) -> dict:
    """
    Uses OpenAI API to extract assignment and exam deadlines from syllabus text.
    
    Args:
        text (str): The extracted text from the PDF
        filename (str): The name of the PDF file being processed
    
    Returns:
        dict: JSON object containing extracted deadlines
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # client = OpenAI(api_key=api_key) 
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    
    system_prompt = """You are a syllabus analyzer. Extract all assignment deadlines and exam deadlines from the provided syllabus text.

Return ONLY a valid JSON object in this exact format:
{
    "course_name": "Course name if found",
    "course_code": "Course code if found",
    "term": "Term/semester if found",
    "assignments": [
        {
            "name": "Assignment name",
            "due_date": "YYYY-MM-DD or original date string",
            "description": "Brief description if available"
        }
    ],
    "exams": [
        {
            "name": "Exam name (e.g., Midterm, Final)",
            "date": "YYYY-MM-DD or original date string",
            "description": "Additional details if available"
        }
    ]
}

If dates are relative (e.g., "Week 3"), include them as-is. Extract as much information as possible. Make sure to look through the entire text before creating the json."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract deadlines from this syllabus:\n\n{text}"}
            ],
            temperature=0.1,  
            response_format={"type": "json_object"}  # Ensures JSON output
        )
        
        result = json.loads(response.choices[0].message.content)
        result["source_file"] = filename
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source_file": filename,
            "assignments": [],
            "exams": []
        }

