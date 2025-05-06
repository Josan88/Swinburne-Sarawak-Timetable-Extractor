import json
import os
import requests
import time
from datetime import datetime

def main():
    # File paths
    current_dir = os.path.dirname(__file__)
    courses_file = os.path.join(current_dir, 'GetAllCoursesByTermId.json')
    output_dir = os.path.join(current_dir, 'course_timetables')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load course data
    print("Loading course data...")
    with open(courses_file, 'r') as file:
        course_data = json.load(file)
    
    # Extract all course IDs
    course_ids = []
    course_codes = {}  # Map of course ID to course code for filename purposes
    for course in course_data['DataList']:
        course_ids.append(course['CourseID'])
        course_codes[course['CourseID']] = course['CourseCode']
    
    print(f"Found {len(course_ids)} courses")
    
    # Base URL for the timetable API - updated to correct endpoint
    base_url = "https://custom-100380.campusnexus.cloud/WebServices/api/CourseRegistration/GetClassScheduleByTermId"
    
    # Headers for the API request - updated based on the curl command
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "content-type": "application/json",
        "origin": "https://custom-100380.campusnexus.cloud",
        "referer": "https://custom-100380.campusnexus.cloud/PortalExtension/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        "token": "f3ksI93w7dangJn4GR1JUwB6HenX3YLfWC6ZDF65rzkM0s+QoFDmv7+K/EJ2EcSmiN6dnCDPc6ZYdN4MXF4T1ZTQqDObHDvVaZb27k3v+yyJYtEFkCcYIikTU3TkV10Gc7uuz4UqPe/8mn7utGtbCSB7gMAsLpjuhL7cvpbioH3Vmx3AevjN7zw9HDc4c7UcqG3TLcXxNCeQz9nKBvPKJCVikkIP8uKSgQlhOdCRV5HGpAhKpVTq3QPWBSS0bqCi4OG54RWhe8YUjnjy05d6HUP5CL9zhRVLEfon4ij7LUljR8anGzDvzjkdKdNFnXxrDsOqprwar4df9baHZjaxIok+uEM1vIC+8owCABU9kgSa1lk/FHVBRjDAfvtYygHtNw3/dnxlvjl3Q4vM/Ur8Ye00+DJQmK6FUlW0XHJSwfazvsiCyhGQgVcZFCZ9avzl2RxfKq4owV31X/xzkiLhdWVz59wkl6BR3hjD1YAiGuHW8y304kKeVRiiwodHxm4mil1oN+PPYdIhq5tekQ353MxeKWpJAkaTRpcvwgzDIj9hBuuw2cCp1jIVyf5sXFSvKawxzxFlSfjSC8TDn3Hcbw+eEXJaHZh/4CAz76VUuqAVvH6eYe7lHCUQQJCu4ACeFwIcjL/WzXNW5pGsFoalmKDsfUYoFQ52F/HR+r14PUZY2AOU2xMN7094e18vv8JvsRepJSVXRdQRJs1InjkOgaEl4fpZOJi1hlHL9+DIrX2qB2k2N3RT2ZPonlCxCfMsIbb5kn1YVteJg1bQmqJW/AN+xo63+UPvsSx0HAaqk3AiDcCcYk+NLcy69SuKaQPiFgh6Td7KAcCL81PwHnqIJ8sZnf1q8O6syhFCh589FTmK75FsNZXwkOr1LZIZ0ad4SQJz8Yb/2pO1AzEF91jpbdI7CiSKuoE12Y/GH4Ywms1zW2eJUul6K97rZGrnTWUWGH40GrPQKKXEsJ0/uF8bekqb3XNXJuC7ECSwGdfq2KRxlMSWSvUvZ+TyCIco+E0U5ai1qekEUaEo6Rp0FskpN5H7SqqPoFL4E5y6JHLWueURNmlXcOgljpqzmX6iRJh3HORAaMcHucUc7jnTUNZAn5dD83rOlBAlKutrA1b6dRyPga07Ilh0wXJVZHpK/Kxw/Z2Yuqj/JLPxwbVUp+oLyrye1zHW6bh4VJRbze0U6zkZkPl28cXSnjZxgovbJSB/B5po8YeM2PXN2s1lEHSUxO6nj6x8qZYt84nRnNNZzZrIwgYYa3aZP/LjIfp7xwKOQHC77ZSnra3Tz4nRRtgXJfqMFysCK74ireh37snhDnJt3FaGXCL0d7U5k7VFhecPB8y/70omVM+TwvaB+56NJ0RHPeogJcJAmOTpzXmUfJuRU+CBFr0ZATQ4zkq8IHntmNo7Fm0s8bGOX2mPQctgaR/WWtQkF/HHKNtFpHMIt4Fa8nrPS4a6v+W8wEJEC0LOG+xEY/6UQ7MjAxTEfW3sFTjuD5quLCfy3red01p5VW1Qfv5MPRaJgDWl6vIQ6Fg2HAqVnxckmjUqxoKo76L0Jvch2bZ1Ncbi32I5cvqmUBOlJf/QSQFqWcXd5GzslyvTV1QxAzs032jIq8JGT8ZyclIG9DW9RecxIiWTZ57eY8/+ZKl3jdAbIcfbAB80H2Sb7B1AW8cekDinkdzYbPG2vDPoEgGiFCozaUz64+LrHf1A7sPpG6QEfQcA2MkctGNWDsR6KUmAPCsWCq67UlWWr6v+hjkn+M+7EXsxhzYq1EWQcSasU794r6TXfcSz/mjFIYMX0AMKuoVL57yCeZ2MFqA+KnDvZOL7YJUPBA65uYyP9BOXuEZc7vP5+PwNUKU2uVPaq1UwXfFpw+2WV2v1SbbmrVmlHnlM+gEY6OTcJLDvAkYtDlgLhK8MJ3oPkFURr8jcuUFt3PcBTl2zqc8hFA=="
    }
    

    
    # Process courses in batches to avoid too long URL
    batch_size = 10  # Process 10 courses at a time
    batches = [course_ids[i:i + batch_size] for i in range(0, len(course_ids), batch_size)]
    
    # Process each batch
    success_count = 0
    error_count = 0
    
    for batch_num, batch in enumerate(batches):
        try:
            # Convert the batch to comma-separated string
            course_ids_str = ",".join(map(str, batch))
            print(f"Processing batch {batch_num + 1}/{len(batches)}: Course IDs {course_ids_str}")
            
            # Payload structure based on the curl command
            payload = {
                "TermId": 303,  # From the curl command
                "CourseIds": course_ids_str,
                "IsAllWeek": True
            }
            
            # Make the actual API call
            response = requests.post(base_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                timetable_data = response.json()
                
                # Save full batch response
                batch_file = os.path.join(output_dir, f"batch_{batch_num + 1}_timetable.json")
                with open(batch_file, 'w') as file:
                    json.dump(timetable_data, file, indent=4)
                
                print(f"  Success: Found data for batch {batch_num + 1}")
                
                # Also save individual course files if needed
                for course_id in batch:
                    course_code = course_codes.get(course_id, f"Unknown_{course_id}")
                    course_file = os.path.join(output_dir, f"{course_code}_timetable.json")
                    
                    # Filter the data for just this course (if the API returns data for all courses in one go)
                    # This might need adjustment based on the actual structure of the response
                    course_data = timetable_data  # Default to full data
                    
                    with open(course_file, 'w') as file:
                        json.dump(course_data, file, indent=4)
                
                success_count += 1
            else:
                print(f"  Error: API returned status code {response.status_code}")
                print(f"  Response: {response.text[:200]}...")  # Print first 200 chars of response
                break
            
            # Add a small delay to avoid overwhelming the server
            time.sleep(1.5)
            
        except Exception as e:
            print(f"  Error processing batch {batch_num + 1}: {str(e)}")
            error_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Total batches: {len(batches)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Results saved to: {output_dir}")
    
    # Create a summary file with all course codes and their IDs
    summary_file = os.path.join(current_dir, 'course_summary.json')
    with open(summary_file, 'w') as file:
        summary = {str(id): code for id, code in course_codes.items()}
        json.dump(summary, file, indent=4)
    print(f"Course summary saved to: {summary_file}")

if __name__ == "__main__":
    start_time = datetime.now()
    main()
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Total execution time: {duration}")