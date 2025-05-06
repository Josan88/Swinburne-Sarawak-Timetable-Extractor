import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import os
import glob

# File paths
current_dir = os.path.dirname(__file__)
timetables_dir = os.path.join(current_dir, 'course_timetables')
course_summary_file = os.path.join(current_dir, 'course_summary.json')

print("Loading course summary...")
# Load course ID to course code mapping
with open(course_summary_file, 'r') as file:
    course_lookup = json.load(file)

# Process all batch timetable files
print("Processing timetable data...")
batch_files = glob.glob(os.path.join(timetables_dir, 'batch_*_timetable.json'))
print(f"Found {len(batch_files)} batch files to process")

# Process the schedule data
classes = []
total_events = 0

for batch_file in batch_files:
    print(f"Processing {os.path.basename(batch_file)}...")
    with open(batch_file, 'r') as file:
        schedule_data = json.load(file)
    
    # Process each event in the batch
    if 'DataList' in schedule_data:
        batch_events = 0
        for event in schedule_data['DataList']:
            try:
                event_date = datetime.strptime(event['EventDate'], '%Y-%m-%dT%H:%M:%S')
                event_start = datetime.strptime(event['EventStartTime'], '%Y-%m-%dT%H:%M:%S')
                event_end = datetime.strptime(event['EventEndTime'], '%Y-%m-%dT%H:%M:%S')
                
                # Extract day of week and hour
                day_of_week = event_date.strftime('%A')
                start_hour = event_start.hour
                end_hour = event_end.hour
                
                # Extract course code - use either from the event or lookup by course ID
                course_code = None
                if 'CourseCode' in event:
                    course_code = event['CourseCode']
                elif 'CourseID' in event and str(event['CourseID']) in course_lookup:
                    course_code = course_lookup[str(event['CourseID'])]
                
                # If we still don't have a course code, try to extract from description
                if not course_code:
                    description = event['EventDescription']
                    if ' - ' in description:
                        course_code = description.split(' - ')[0]
                    else:
                        course_code = 'Unknown'
                
                # Create a record for each hour block the class occupies
                for hour in range(start_hour, end_hour + 1):
                    classes.append({
                        'Day': day_of_week,
                        'Hour': hour,
                        'CourseCode': course_code,
                        'StartHour': start_hour,
                        'EndHour': end_hour,
                        'Description': event['EventDescription'],
                        'EventDate': event_date.strftime('%Y-%m-%d')
                    })
                batch_events += 1
            except (ValueError, KeyError) as e:
                # Skip events with invalid format
                print(f"  Warning: Skipped an event due to {str(e)}")
                continue
        
        total_events += batch_events
        print(f"  Processed {batch_events} events")
    else:
        print(f"  Warning: No data list found in {batch_file}")

# Convert to DataFrame for easier analysis
df = pd.DataFrame(classes)

print(f"Total events processed: {total_events}")
print(f"Total class hours: {len(df)}")

# Create pivot table for the heatmap
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
hours_range = list(range(8, 22))  # 8am to 9pm

# Count classes by day and hour
heatmap_data = pd.pivot_table(
    df, 
    values='CourseCode', 
    index='Hour', 
    columns='Day', 
    aggfunc='count',
    fill_value=0
)

# Reorder columns to standard week order
heatmap_data = heatmap_data.reindex(columns=days_order)

# Create a more complete heatmap with all hours
complete_heatmap = pd.DataFrame(
    index=hours_range,
    columns=days_order,
    data=0
)

# Fill in the data we have
for hour in heatmap_data.index:
    for day in heatmap_data.columns:
        if day in complete_heatmap.columns and hour in complete_heatmap.index:
            complete_heatmap.at[hour, day] = heatmap_data.at[hour, day]

# Plotting
plt.figure(figsize=(14, 10))
ax = sns.heatmap(
    complete_heatmap,
    cmap="YlOrRd",
    linewidths=0.5,
    annot=True,
    fmt=".0f",
    cbar_kws={'label': 'Number of Classes'}
)

# Format the plot
plt.title('Class Schedule Heatmap - Number of Classes by Day and Hour', fontsize=16)
plt.xlabel('Day of Week', fontsize=12)
plt.ylabel('Hour of Day (24h format)', fontsize=12)

# Save the figure
plt.tight_layout()
output_file = os.path.join(current_dir, 'class_schedule_heatmap.png')
plt.savefig(output_file, dpi=300)
print(f"Saved heatmap to {output_file}")
plt.close()

# ADDITIONAL ANALYSIS: Classes per day
plt.figure(figsize=(10, 6))
day_counts = df.groupby('Day')['CourseCode'].nunique().reindex(days_order)
sns.barplot(x=day_counts.index, y=day_counts.values)
plt.title('Number of Unique Courses per Day', fontsize=16)
plt.xlabel('Day of Week', fontsize=12)
plt.ylabel('Number of Courses', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
output_file = os.path.join(current_dir, 'classes_per_day.png')
plt.savefig(output_file, dpi=300)
print(f"Saved classes per day chart to {output_file}")
plt.close()

# ADDITIONAL ANALYSIS: Classes per hour
plt.figure(figsize=(10, 6))
hour_counts = df.groupby('Hour')['CourseCode'].nunique()
sns.barplot(x=hour_counts.index, y=hour_counts.values)
plt.title('Number of Unique Courses per Hour', fontsize=16)
plt.xlabel('Hour of Day (24h format)', fontsize=12)
plt.ylabel('Number of Courses', fontsize=12)
plt.tight_layout()
output_file = os.path.join(current_dir, 'classes_per_hour.png')
plt.savefig(output_file, dpi=300)
print(f"Saved classes per hour chart to {output_file}")
plt.close()

# NEW ANALYSIS: Top 10 courses with most class hours
plt.figure(figsize=(12, 6))
course_hours = df['CourseCode'].value_counts().head(10)
sns.barplot(x=course_hours.index, y=course_hours.values)
plt.title('Top 10 Courses with Most Class Hours', fontsize=16)
plt.xlabel('Course Code', fontsize=12)
plt.ylabel('Number of Class Hours', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
output_file = os.path.join(current_dir, 'top_courses_by_hours.png')
plt.savefig(output_file, dpi=300)
print(f"Saved top courses chart to {output_file}")
plt.close()

print(f"\nAnalysis complete! Images saved to: {current_dir}")
print(f"Total class sessions analyzed: {len(df['Description'].unique())}")
print(f"Total unique courses found: {df['CourseCode'].nunique()}")