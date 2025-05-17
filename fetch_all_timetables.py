import json
import os
import requests
from datetime import datetime, timedelta


def is_current_or_future_term(term_name, current_date):
    """
    Determine if a term is current or future based on its name and current date.
    A term is considered valid if it started within the last 3 months or will start in the future.

    Args:
        term_name: String like "2025 May Term 2" or "2024 October Term 4"
        current_date: Current datetime object

    Returns:
        Boolean indicating if the term is current or future
    """
    # Extract year and month from term name
    parts = term_name.split()
    if len(parts) < 2:
        return False

    try:
        year = int(parts[0])
        month_name = parts[1].lower()

        # Map month names to numbers
        month_map = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sep": 9,
            "sept": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }

        month = month_map.get(month_name.lower())
        if not month:
            return False

        # Create a date object for the term's start
        term_start = datetime(year, month, 1)

        # Calculate term end (3 months after start)
        term_end = term_start + timedelta(days=90)

        # Term is valid if it hasn't ended yet (current date is before or equal to term end)
        return current_date <= term_end
    except (ValueError, IndexError):
        return False


def fetch_courses_from_api(term_id, headers):
    """
    Fetch course data directly from the API for a given term ID

    Args:
        term_id: Term ID to fetch courses for
        headers: API request headers including token

    Returns:
        Dictionary containing course data or None if request failed
    """
    url = "https://custom-100380.campusnexus.cloud/WebServices/api/CourseRegistration/GetAllCoursesByTermId"
    payload = {"TermId": term_id}

    try:
        print(f"Fetching course data for term {term_id} from API...")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            course_data = response.json()
            print(
                f"Successfully retrieved {len(course_data.get('DataList', []))} courses from API"
            )

            # Save the data to a file for future reference
            current_dir = os.path.dirname(__file__)
            api_data_dir = os.path.join(current_dir, "api_data")
            if not os.path.exists(api_data_dir):
                os.makedirs(api_data_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(
                api_data_dir, f"courses_term_{term_id}_{timestamp}.json"
            )
            with open(file_path, "w") as f:
                json.dump(course_data, f, indent=4)
            print(f"Course data saved to {file_path}")

            return course_data
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"Error fetching course data: {str(e)}")
        return None


def main():
    # File paths
    current_dir = os.path.dirname(__file__)
    output_dir = os.path.join(current_dir, "course_timetables")

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Prompt for API token
    print("\nYou'll need to get a new token from the Swinburne website.")
    print("To do this:")
    print("1. Login to https://custom-100380.campusnexus.cloud/PortalExtension/")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Network tab")
    print("4. Navigate to class timetable section")
    print("5. Look for API requests and find the 'token' header value")
    new_token = input("\nPaste your new token here: ")
    token = new_token.strip()
    if not token:
        print("No token provided. Exiting.")
        return

    # Headers for the API request
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "content-type": "application/json",
        "origin": "https://custom-100380.campusnexus.cloud",
        "referer": "https://custom-100380.campusnexus.cloud/PortalExtension/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        "token": token,
    }

    GetTimeTablePublishedTerms = "https://custom-100380.campusnexus.cloud/WebServices/api/HelperService/GetTimeTablePublishedTerms"
    payload = {}

    try:
        print("Fetching terms from API...")
        response = requests.post(
            GetTimeTablePublishedTerms, json=payload, headers=headers
        )
        if response.status_code == 200:
            terms_data = response.json()
            print(f"Successfully retrieved {len(terms_data)} terms from API")
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return
    except Exception as e:
        print(f"Error fetching terms data: {str(e)}")
        return
    # Extract terms from the response
    terms = []
    current_date = datetime.now()
    for term in terms_data["DataList"]:
        if is_current_or_future_term(term["DropdownName"], current_date):
            terms.append(
                {
                    "id": term["DropdownId"],
                    "name": term["DropdownName"],
                    "code": term["DropdownCode"],
                }
            )

    print(f"Found {len(terms)} current and upcoming terms")

    # Ask if user wants to proceed with all terms or specify specific ones
    choice = input(
        "\nDo you want to: \n1. Proceed with all terms\n2. Specify term IDs\n> "
    )

    if choice == "2":
        term_ids_input = input(
            "\nEnter term IDs separated by commas (e.g., 303,312,345): "
        )
        term_ids = [
            int(id.strip()) for id in term_ids_input.split(",") if id.strip().isdigit()
        ]
        terms = [term for term in terms if term["id"] in term_ids]
        print(
            f"Selected {len(terms)} terms: {', '.join([str(term['id']) for term in terms])}"
        )
    else:
        print("Proceeding with all terms")

    if not terms:
        print("No valid terms selected. Exiting.")
        return
    # Base URL for the timetable API - updated to correct endpoint
    base_url = "https://custom-100380.campusnexus.cloud/WebServices/api/CourseRegistration/GetClassScheduleByTermId"

    # Print warning about API rate limiting
    print(
        "\nWARNING: This script will attempt to fetch timetables for all current and upcoming terms."
    )
    print(
        "This may take some time and might result in API rate limiting or token expiration."
    )
    print("You may want to specify specific terms by ID instead.")

    # Track overall statistics
    total_success_count = 0
    total_error_count = 0

    # Process each term separately
    for term in terms:
        term_id = term["id"]
        term_dir = os.path.join(output_dir, f"term_{term['id']}_{term['code']}")

        if not os.path.exists(term_dir):
            os.makedirs(term_dir)
            print(f"Created term directory: {term_dir}")

        print(f"\n=== Processing Term: {term['name']} (ID: {term['id']}) ===")

        # Fetch course data for this specific term
        course_data = fetch_courses_from_api(term_id, headers)
        if (
            not course_data
            or "DataList" not in course_data
            or not course_data["DataList"]
        ):
            print(f"No courses found for term {term['name']}. Skipping.")
            continue

        # Extract course IDs and codes for this term only
        term_course_ids = []
        term_course_codes = {}
        for course in course_data["DataList"]:
            term_course_ids.append(course["CourseID"])
            term_course_codes[course["CourseID"]] = course["CourseCode"]

        print(f"Found {len(term_course_ids)} courses for term {term['name']}")

        # Process courses in batches to avoid too long URL
        batch_size = 10  # Process 10 courses at a time
        batches = [
            term_course_ids[i : i + batch_size]
            for i in range(0, len(term_course_ids), batch_size)
        ]

        # Process each batch for this term
        success_count = 0
        error_count = 0

        for batch_num, batch in enumerate(batches):
            try:
                # Convert the batch to comma-separated string
                course_ids_str = ",".join(map(str, batch))
                print(
                    f"Processing batch {batch_num + 1}/{len(batches)}: Course IDs {course_ids_str}"
                )
                
                # Payload structure based on the curl command
                payload = {
                    "TermId": term["id"],  # Use the current term ID
                    "CourseIds": course_ids_str,
                    "IsAllWeek": True,
                }
                
                # Make the actual API call
                response = requests.post(base_url, json=payload, headers=headers)

                if response.status_code == 200:
                    timetable_data = response.json()

                    # Save full batch response in the term directory
                    batch_file = os.path.join(
                        term_dir, f"batch_{batch_num + 1}_timetable.json"
                    )
                    with open(batch_file, "w") as file:
                        json.dump(timetable_data, file, indent=4)

                    print(f"  Success: Found data for batch {batch_num + 1}")
                    
                    # Also save individual course files if needed
                    for course_id in batch:
                        course_code = term_course_codes.get(
                            course_id, f"Unknown_{course_id}"
                        )
                        course_file = os.path.join(
                            term_dir, f"{course_code}_timetable.json"
                        )

                        # Filter the data for just this course (if the API returns data for all courses in one go)
                        # This might need adjustment based on the actual structure of the response
                        course_data = timetable_data  # Default to full data

                        with open(course_file, "w") as file:
                            json.dump(course_data, file, indent=4)

                    success_count += 1
                else:
                    print(f"  Error: API returned status code {response.status_code}")
                    print(
                        f"  Response: {response.text[:200]}..."
                    )  # Print first 200 chars of response
                    error_count += 1

            except Exception as e:
                print(f"  Error processing batch {batch_num + 1}: {str(e)}")
                error_count += 1
                
        print(f"\nTerm {term['id']} ({term['name']}) processing complete!")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Results saved to: {term_dir}")
        
        total_success_count += success_count
        total_error_count += error_count
    
    # Create a comprehensive course summary with all courses from all terms
    all_courses = []
    term_course_mappings = {}
    
    print("\nCreating comprehensive course summary...")
    
    # First, collect all course data from the API data files
    api_data_dir = os.path.join(current_dir, "api_data")
    for term in terms:
        term_id = term["id"]
        term_name = term["name"]
        
        # Find the most recent API data file for this term
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
                            "name": course["CourseName"],
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

    print(f"\n=== All Terms Processing Complete ===")
    print(f"Total terms processed: {len(terms)}")
    print(f"Total Success: {total_success_count}")
    print(f"Total Errors: {total_error_count}")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Total execution time: {duration}")
