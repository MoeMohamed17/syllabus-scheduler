import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_pdf_to_openai(client: OpenAI, pdf_path: str) -> str:
    """
    Upload a PDF to OpenAI Files API.
    
    Args:
        client (OpenAI): OpenAI client instance
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: File ID from OpenAI
    """
    with open(pdf_path, "rb") as pdf_file:
        result = client.files.create(
            file=pdf_file,
            purpose="user_data"
        )
        return result.id

def extract_deadlines_with_ai(pdf_path: str, filename: str) -> dict:
    """
    Uses OpenAI API to extract assignment and exam deadlines from syllabus PDF.
    OpenAI automatically extracts both text and images from the PDF.
    
    Args:
        pdf_path (str): Path to the PDF file
        filename (str): The name of the PDF file being processed
    
    Returns:
        dict: JSON object containing extracted deadlines
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    os.environ["OPENAI_API_KEY"] = api_key
    client = OpenAI()
    
    system_prompt = """You are a syllabus analyzer. Extract all assignment deadlines and exam deadlines from the provided syllabus PDF.

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

CRITICAL: When reading dates from calendar/schedule tables:
- Pay close attention to which column or row the date appears in
- Match the assignment/exam name with the correct date column
- If an item is in the Nov 24 column, the date is Nov 24, NOT Nov 28
- Double-check table layouts carefully to avoid date mismatches

If dates are relative (e.g., "Week 3"), include them as-is. Extract as much information as possible. Analyze all pages carefully including any tables, schedules, or diagrams."""

    try:
        # Upload PDF to OpenAI
        file_id = upload_pdf_to_openai(client, pdf_path)
        
        # Build input array with PDF and prompt for GPT-5
        input_content = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": file_id
                    },
                    {
                        "type": "input_text",
                        "text": f"{system_prompt}\n\nExtract all assignment and exam deadlines from this syllabus PDF. Analyze all pages carefully including any tables, schedules, or diagrams."
                    }
                ]
            }
        ]
        
        # Call OpenAI API with PDF (using gpt-5 for best vision accuracy)
        response = client.responses.create(
            model="gpt-5",
            input=input_content,
            reasoning={"effort": "high"},  # Use high reasoning for better table understanding
            text={"verbosity": "medium"}
        )
        
        result = json.loads(response.output_text)
        result["source_file"] = filename
        
        # Cleanup: delete uploaded file from OpenAI
        try:
            client.files.delete(file_id)
        except:
            pass
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "source_file": filename,
            "assignments": [],
            "exams": []
        }
