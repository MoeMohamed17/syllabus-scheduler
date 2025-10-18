import json
from ics import Calendar, Event
from datetime import datetime
import os

def parse_date(date_string: str) -> datetime:
    """
    Parse various date formats into datetime object.
    
    Args:
        date_string: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_string or date_string.lower() == "not specified":
        return None
    
    # Try different date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2025-09-28 23:59:59
        "%Y-%m-%d",            # 2025-09-28
        "%m/%d/%Y",            # 09/28/2025
        "%d/%m/%Y",            # 28/09/2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    print(f"⚠️  Could not parse date: {date_string}")
    return None

def generate_calendar(json_file: str = "extracted_deadlines/all_deadlines.json", 
                     output_file: str = "schedule.ics"):
    """
    Generate an ICS calendar file from the deadlines JSON.
    
    Args:
        json_file: Path to the all_deadlines.json file
        output_file: Path for the output ICS file
    """
    # Load JSON data
    if not os.path.exists(json_file):
        print(f"❌ Error: {json_file} not found!")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    
    # Create a new calendar
    calendar = Calendar()
    event_count = 0
    skipped_count = 0
    
    # Loop through each course
    for course in courses:
        course_code = course.get('course_code', 'Unknown')
        course_name = course.get('course_name', 'Unknown Course')
        
        # Add assignment deadlines
        for assignment in course.get('assignments', []):
            due_date = parse_date(assignment.get('due_date', ''))
            
            if due_date:
                event = Event()
                event.name = f"[{course_code}] {assignment['name']}"
                event.begin = due_date
                event.description = f"{course_name}\n\nAssignment: {assignment.get('description', assignment['name'])}"
                event.duration = {"hours": 0}  # All-day event
                calendar.events.add(event)
                event_count += 1
            else:
                skipped_count += 1
                print(f"⏭️  Skipped assignment (no valid date): [{course_code}] {assignment.get('name')}")
        
        # Add exam dates
        for exam in course.get('exams', []):
            exam_date = parse_date(exam.get('date', ''))
            
            if exam_date:
                event = Event()
                event.name = f"[{course_code}] {exam['name']}"
                event.begin = exam_date
                event.description = f"{course_name}\n\nExam: {exam.get('description', exam['name'])}"
                event.duration = {"hours": 2}  # 2-hour exam by default
                calendar.events.add(event)
                event_count += 1
            else:
                skipped_count += 1
                print(f"⏭️  Skipped exam (no valid date): [{course_code}] {exam.get('name')}")
    
    # Write the ICS file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(calendar.serialize_iter())
    
    print(f"\n✅ {output_file} created successfully!")
    print(f"   Added {event_count} events to calendar")
    if skipped_count > 0:
        print(f"   Skipped {skipped_count} events (missing or invalid dates)")

if __name__ == "__main__":
    generate_calendar()

