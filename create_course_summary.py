import json
import os
from datetime import datetime

# File paths
current_dir = os.path.dirname(__file__)
api_data_dir = os.path.join(current_dir, "api_data")
output_dir = os.path.join(current_dir, "course_timetables")

# Create a comprehensive course summary with all courses from all terms
all_courses = []
term_course_mappings = {}

print("\nCreating comprehensive course summary...")

# Get a list of all term directories to understand what terms we have
term_dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith("term_")]

# Extract term IDs and codes from directory names
terms = []
for term_dir in term_dirs:
    parts = term_dir.split("_", 2)
    if len(parts) >= 3:
        term_id = int(parts[1])
        term_code = parts[2]
        
        # Try to extract the term name from the files in the directory
        term_name = term_code.replace("_", " ").upper()
        
        terms.append({
            "id": term_id,
            "code": term_code,
            "name": term_name
        })

print(f"Found {len(terms)} terms from directories")

# First, collect all course data from the API data files
for term in terms:
    term_id = term["id"]
    term_name = term["name"]
    
    # Find all API data files for this term
    term_files = [f for f in os.listdir(api_data_dir) if f.startswith(f"courses_term_{term_id}_")]
    if term_files:
        latest_file = sorted(term_files)[-1]  # Get the most recent file
        file_path = os.path.join(api_data_dir, latest_file)
        
        print(f"  Loading course data for term {term_name} from {latest_file}")
        try:
            with open(file_path, 'r') as f:
                course_data = json.load(f)
                
            if "DataList" in course_data and course_data["DataList"]:
                for course in course_data["DataList"]:
                    # Create a course summary object with essential information
                    course_info = {
                        "id": course["CourseID"],
                        "code": course["CourseCode"],
                        "name": course["CourseDescription"],  # Changed from CourseName to CourseDescription
                        "term_id": term_id,
                        "term_name": term_name,
                        "term_code": term["code"]
                    }
                    
                    all_courses.append(course_info)
                    
                    # Store term mapping
                    if course["CourseCode"] not in term_course_mappings:
                        term_course_mappings[course["CourseCode"]] = []
                    term_course_mappings[course["CourseCode"]].append({
                        "term_id": term_id,
                        "term_name": term_name,
                        "term_code": term["code"]
                    })
        except Exception as e:
            print(f"  Error loading course data from {file_path}: {str(e)}")

# Save the comprehensive course summary
summary_data = {
    "courses": all_courses,
    "term_mappings": term_course_mappings,
    "total_courses": len(all_courses),
    "unique_courses": len(term_course_mappings),
    "terms": [{"id": term["id"], "name": term["name"], "code": term["code"]} for term in terms]
}

summary_file = os.path.join(current_dir, "course_summary.json")
with open(summary_file, "w") as f:
    json.dump(summary_data, f, indent=4)

print(f"Comprehensive course summary saved to {summary_file}")
print(f"  Total courses: {len(all_courses)}")
print(f"  Unique course codes: {len(term_course_mappings)}")
