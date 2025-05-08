document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const courseSearch = document.getElementById('course-search');
    const searchResults = document.getElementById('search-results');
    const selectedCoursesList = document.getElementById('selected-courses-list');
    const downloadIcsBtn = document.getElementById('download-ics');
    const timetablePreview = document.getElementById('timetable-preview');
    
    // PWA Installation
    let deferredPrompt;
    const headerElement = document.querySelector('header');
    
    // Create install button but don't show it yet
    const installButton = document.createElement('button');
    installButton.id = 'install-btn';
    installButton.className = 'btn install-btn';
    installButton.textContent = 'Install App';
    installButton.style.display = 'none';
    
    // Add the install button to the header
    headerElement.appendChild(installButton);
    
    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome 76+ from automatically showing the prompt
        e.preventDefault();
        
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        
        // Show the install button
        installButton.style.display = 'block';
        
        console.log('App can be installed, showing install button');
    });
    
    // Installation button click handler
    installButton.addEventListener('click', async () => {
        // Hide the app provided install promotion
        installButton.style.display = 'none';
        
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        
        // Log the outcome
        console.log(`User response to the install prompt: ${outcome}`);
        
        // We've used the prompt, and can't use it again, clear it
        deferredPrompt = null;
    });
    
    // Listen for app installed event
    window.addEventListener('appinstalled', (e) => {
        // Log install to analytics or save user preference
        console.log('Timetable app was installed');
        
        // Hide the install button if it's still showing
        installButton.style.display = 'none';
    });
    
    // State
    let availableCourses = {};
    let selectedCourses = [];
    let timetableData = {};
    let groupSelections = {}; // Store user's group selections for each course
    
    // Load course data
    loadCourseSummary();
    
    // Event listeners
    courseSearch.addEventListener('input', handleSearchInput);
    searchResults.addEventListener('click', handleSearchResultClick);
    downloadIcsBtn.addEventListener('click', generateAndDownloadICS);
    
    // Load the course summary JSON
    function loadCourseSummary() {
        fetch('course_summary.json')
            .then(response => response.json())
            .then(data => {
                availableCourses = data;
                console.log('Course summary loaded:', Object.keys(availableCourses).length, 'courses');
            })
            .catch(error => {
                console.error('Error loading course summary:', error);
            });
    }
    
    // Handle search input
    function handleSearchInput(event) {
        const query = event.target.value.trim().toUpperCase();
        
        // Clear previous results
        searchResults.innerHTML = '';
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        // Filter courses based on query
        const filteredCourses = Object.entries(availableCourses)
            .filter(([id, code]) => code.includes(query))
            .slice(0, 10); // Limit to 10 results
        
        if (filteredCourses.length === 0) {
            searchResults.style.display = 'none';
            return;
        }
        
        // Display results
        filteredCourses.forEach(([id, code]) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.textContent = code;
            resultItem.dataset.id = id;
            resultItem.dataset.code = code;
            searchResults.appendChild(resultItem);
        });
        
        searchResults.style.display = 'block';
    }
    
    // Handle search result click
    function handleSearchResultClick(event) {
        if (event.target.classList.contains('result-item')) {
            const courseId = event.target.dataset.id;
            const courseCode = event.target.dataset.code;
            
            // Don't add duplicates
            if (selectedCourses.some(course => course.code === courseCode)) {
                searchResults.style.display = 'none';
                courseSearch.value = '';
                return;
            }
            
            // Add to selected courses
            selectedCourses.push({ id: courseId, code: courseCode });
            
            // Initialize group selections for this course
            groupSelections[courseCode] = {
                includedGroups: [],
                availableGroups: []
            };
            
            // Add to UI
            addCourseToUI(courseId, courseCode);
            
            // Load timetable data for this course
            loadTimetableData(courseCode);
            
            // Clear search
            searchResults.style.display = 'none';
            courseSearch.value = '';
        }
    }
    
    // Add course to UI list
    function addCourseToUI(id, code) {
        const courseItem = document.createElement('li');
        courseItem.dataset.code = code;
        courseItem.innerHTML = `
            <div class="course-header">
                <span>${code}</span>
                <span class="remove-course" data-code="${code}">✕</span>
            </div>
            <div class="course-groups" id="groups-${code}">
                <p class="loading-text">Loading available groups...</p>
            </div>
        `;
        
        courseItem.querySelector('.remove-course').addEventListener('click', function() {
            removeCourse(code);
        });
        
        selectedCoursesList.appendChild(courseItem);
    }
    
    // Remove course from selection
    function removeCourse(code) {
        selectedCourses = selectedCourses.filter(course => course.code !== code);
        
        // Remove from UI
        const courseItems = selectedCoursesList.querySelectorAll('li');
        courseItems.forEach(item => {
            if (item.dataset.code === code) {
                item.remove();
            }
        });
        
        // Remove from timetable data and group selections
        delete timetableData[code];
        delete groupSelections[code];
        
        // Update preview
        updateTimetablePreview();
    }
    
    // Load timetable data for a course
    function loadTimetableData(courseCode) {
        const timetableUrl = `course_timetables/${courseCode}_timetable.json`;
        
        fetch(timetableUrl)
            .then(response => response.json())
            .then(data => {
                timetableData[courseCode] = data;
                
                // Extract available groups for this course
                extractAvailableGroups(courseCode, data);
                
                // Update the UI with group selection options
                updateGroupSelectionUI(courseCode);
                
                // Update preview
                updateTimetablePreview();
            })
            .catch(error => {
                console.error(`Error loading timetable for ${courseCode}:`, error);
                removeCourse(courseCode); // Remove if we can't load timetable
                alert(`Could not load timetable for ${courseCode}. The course has been removed.`);
            });
    }
    
    // Extract available groups from timetable data
    function extractAvailableGroups(courseCode, data) {
        if (!data || !data.DataList || !data.DataList.length) {
            return;
        }
        
        const groups = new Map();
        
        data.DataList.forEach(event => {
            if (event.EventDescription.includes(courseCode)) {
                // Extract group information from description
                // Format is typically: "COURSECODE - TYPE# - GROUP#, Instructor; Location - dates"
                // For example: "COS10003 - TU1 - 01, Colin Choon Lin Tan; G401 - 03/06 to 04/10, 04/24 to 05/29"
                const match = event.EventDescription.match(/([A-Z0-9]+) - ([A-Z]+\d+) - (\d+)/);
                
                if (match && match.length >= 4) {
                    const eventCourseCode = match[1];
                    const sessionType = match[2];    // e.g., "TU1", "LA1", "LE1"
                    const groupNumber = match[3];    // e.g., "01", "02"
                    
                    // Skip lecture groups - we'll include all lectures automatically
                    if (sessionType.startsWith('LE')) {
                        return;
                    }
                    
                    // Create a unique group identifier
                    const groupId = `${sessionType}-${groupNumber}`;
                    
                    if (!groups.has(groupId)) {
                        groups.set(groupId, {
                            id: groupId,
                            type: sessionType,
                            number: groupNumber,
                            description: `${sessionType} Group ${groupNumber}`
                        });
                    }
                }
            }
        });
        
        // Sort groups by type and number
        const sortedGroups = Array.from(groups.values()).sort((a, b) => {
            if (a.type === b.type) {
                return parseInt(a.number) - parseInt(b.number);
            }
            return a.type.localeCompare(b.type);
        });
        
        // Store available groups
        groupSelections[courseCode].availableGroups = sortedGroups;
    }
    
    // Update UI with group selection options
    function updateGroupSelectionUI(courseCode) {
        const courseGroupsDiv = document.getElementById(`groups-${courseCode}`);
        if (!courseGroupsDiv) return;
        
        const availableGroups = groupSelections[courseCode].availableGroups;
        
        if (!availableGroups || availableGroups.length === 0) {
            courseGroupsDiv.innerHTML = '<p>No tutorial or lab groups available for this course</p>';
            return;
        }
        
        // Group the groups by type (e.g., TU, LA)
        const groupsByType = {};
        availableGroups.forEach(group => {
            const type = group.type.replace(/\d+/g, ''); // Remove numbers to get just the type (e.g., "TU" from "TU1")
            if (!groupsByType[type]) {
                groupsByType[type] = [];
            }
            groupsByType[type].push(group);
        });
        
        // Create HTML for group selection
        let html = '';
        
        // Show note that all lectures will be included automatically
        html += `<p class="note">All lectures will be included automatically. Please select one group for each type below.</p>`;
        
        Object.entries(groupsByType).forEach(([type, groups]) => {
            let typeLabel = '';
            switch(type) {
                case 'TU': typeLabel = 'Tutorial'; break;
                case 'LA': typeLabel = 'Lab'; break;
                default: typeLabel = type; break;
            }
            
            html += `<div class="group-type">
                <h4>${typeLabel} Groups: <span class="required">*</span></h4>
                <div class="group-options">`;
            
            groups.forEach(group => {
                html += `<label class="group-option">
                    <input type="radio" name="${courseCode}-${type}" 
                           value="${group.id}" 
                           data-course="${courseCode}" 
                           data-group="${group.id}"
                           data-type="${type}"
                           class="group-radio">
                    Group ${group.number}
                </label>`;
            });
            
            html += `</div></div>`;
        });
        
        courseGroupsDiv.innerHTML = html;
        
        // Add event listeners to radio buttons
        const radios = courseGroupsDiv.querySelectorAll('.group-radio');
        radios.forEach(radio => {
            radio.addEventListener('change', handleGroupSelectionChange);
        });
    }
    
    // Handle group selection change
    function handleGroupSelectionChange(event) {
        const courseCode = event.target.dataset.course;
        const groupId = event.target.dataset.group;
        const groupType = event.target.dataset.type;
        
        if (!groupSelections[courseCode]) {
            groupSelections[courseCode] = { includedGroups: [], availableGroups: [] };
        }
        
        // Remove any other groups of the same type for this course
        const updatedGroups = groupSelections[courseCode].includedGroups.filter(g => {
            // Keep groups that don't start with this type
            return !g.startsWith(`${groupType}`);
        });
        
        // Add the new selected group
        updatedGroups.push(groupId);
        
        // Update the selected groups
        groupSelections[courseCode].includedGroups = updatedGroups;
        
        // Update preview
        updateTimetablePreview();
    }
    
    // Update timetable preview
    function updateTimetablePreview() {
        // Reset preview
        timetablePreview.innerHTML = '';
        
        if (selectedCourses.length === 0) {
            timetablePreview.innerHTML = '<p class="placeholder-text">Select courses to see a preview of your timetable</p>';
            return;
        }
        
        // Get all events from selected courses with applied group filters
        let allEvents = [];
        
        Object.entries(timetableData).forEach(([courseCode, data]) => {
            if (data && data.DataList) {
                const selectedGroups = groupSelections[courseCode]?.includedGroups || [];
                
                data.DataList.forEach(event => {
                    // Check if the event belongs to the course
                    if (event.EventDescription.includes(courseCode)) {
                        let shouldInclude = false;
                        
                        // Extract session type if possible
                        const match = event.EventDescription.match(/([A-Z0-9]+) - ([A-Z]+\d+) - (\d+)/);
                        
                        if (match) {
                            const sessionType = match[2];
                            const groupNumber = match[3];
                            const groupId = `${sessionType}-${groupNumber}`;
                            
                            // Always include lectures
                            if (sessionType.startsWith('LE')) {
                                shouldInclude = true;
                            } 
                            // For tutorials and labs, check if the specific group is selected
                            else if (selectedGroups.includes(groupId)) {
                                shouldInclude = true;
                            }
                        } else {
                            // If we can't parse the group info, include the event
                            shouldInclude = true;
                        }
                        
                        if (shouldInclude) {
                            allEvents.push({
                                date: new Date(event.EventDate),
                                start: new Date(event.EventStartTime),
                                end: new Date(event.EventEndTime),
                                description: event.EventDescription,
                                courseCode: courseCode
                            });
                        }
                    }
                });
            }
        });
        
        // Group by date
        const eventsByDate = {};
        
        allEvents.forEach(event => {
            // Use day of the week (0-6) as the key for grouping
            const dayOfWeek = event.start.getDay(); 
            if (!eventsByDate[dayOfWeek]) {
                eventsByDate[dayOfWeek] = [];
            }
            eventsByDate[dayOfWeek].push(event);
        });
        
        // Display events, sorted by day of the week (Sun=0, Mon=1, ...)
        const days = Object.keys(eventsByDate).sort();
        
        if (days.length === 0) {
            timetablePreview.innerHTML = '<p class="placeholder-text">No events to display. Please select group(s) for your courses.</p>';
            return;
        }
        
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        
        days.forEach(dayIndex => {
            const dayName = dayNames[parseInt(dayIndex)];
            const dateHeading = document.createElement('h3');
            dateHeading.textContent = dayName;
            timetablePreview.appendChild(dateHeading);
            
            // Sort events within the day by start time
            eventsByDate[dayIndex].sort((a, b) => a.start - b.start);
            
            eventsByDate[dayIndex].forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.className = 'event';
                
                const timeStr = `${formatTime(event.start)} - ${formatTime(event.end)}`;
                
                // No need to show the day again within the event details
                eventElement.innerHTML = `
                    <div class="event-time">${timeStr}</div>
                    <div class="event-description">${event.description}</div>
                `;
                
                timetablePreview.appendChild(eventElement);
            });
        });
        
        // Remove the "more dates" note as we now show by day of the week
        const moreEventsNote = timetablePreview.querySelector('.more-events-note');
        if (moreEventsNote) {
            moreEventsNote.remove();
        }
    }
    
    // Format time for display
    function formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Generate and download ICS file
    function generateAndDownloadICS() {
        if (selectedCourses.length === 0) {
            alert('Please select at least one course');
            return;
        }
        
        // Validate that all required groups are selected
        const missingSelections = [];
        
        selectedCourses.forEach(course => {
            const courseCode = course.code;
            
            // Skip validation if no groups are available for this course
            if (!groupSelections[courseCode] || 
                !groupSelections[courseCode].availableGroups || 
                groupSelections[courseCode].availableGroups.length === 0) {
                return;
            }
            
            // Get the group types available for this course
            const groupTypes = new Set();
            groupSelections[courseCode].availableGroups.forEach(group => {
                const type = group.type.replace(/\d+/g, '');
                groupTypes.add(type);
            });
            
            // Check if a selection has been made for each group type
            groupTypes.forEach(type => {
                const hasSelectionForType = groupSelections[courseCode].includedGroups.some(groupId => 
                    groupId.startsWith(type)
                );
                
                if (!hasSelectionForType) {
                    missingSelections.push(`${courseCode}: ${type === 'TU' ? 'Tutorial' : type === 'LA' ? 'Lab' : type} group`);
                }
            });
        });
        
        if (missingSelections.length > 0) {
            alert(`Please select required groups:\n\n${missingSelections.join('\n')}`);
            return;
        }
        
        const cal = window.ics();
        let eventCount = 0;
        let totalStudyHours = 0;
        
        // Process events from selected courses with applied group filters
        Object.entries(timetableData).forEach(([courseCode, data]) => {
            if (data && data.DataList) {
                const selectedGroups = groupSelections[courseCode]?.includedGroups || [];
                const filteredEvents = [];
                
                // First filter events based on selected groups
                data.DataList.forEach(event => {
                    // Check if the event belongs to the course
                    if (event.EventDescription.includes(courseCode)) {
                        let shouldInclude = false;
                        
                        // Extract session type if possible
                        const match = event.EventDescription.match(/([A-Z0-9]+) - ([A-Z]+\d+) - (\d+)/);
                        
                        if (match) {
                            const sessionType = match[2];
                            const groupNumber = match[3];
                            const groupId = `${sessionType}-${groupNumber}`;
                            const basicType = sessionType.replace(/\d+/g, '');
                            
                            // Always include lectures
                            if (basicType === 'LE') {
                                shouldInclude = true;
                            } 
                            // For tutorials and labs, check if the specific group is selected
                            else if (selectedGroups.includes(groupId)) {
                                shouldInclude = true;
                            }
                        } else {
                            // If we can't parse the group info, include the event
                            shouldInclude = true;
                        }
                        
                        if (shouldInclude) {
                            filteredEvents.push(event);
                        }
                    }
                });
                
                // Process the filtered events
                processEvents(filteredEvents, cal);
                eventCount += filteredEvents.length;
            }
        });
        
        if (eventCount === 0) {
            alert('No events to download. Please check your course and group selections.');
            return;
        }
        
        // Generate file name
        const coursesList = selectedCourses.map(c => c.code).join('-');
        const fileName = `swinburne-timetable-${coursesList}.ics`;
        
        // Download
        cal.download(fileName);
        
        // Show summary
        const studyHoursPerWeek = Math.round(totalStudyHours * 10) / 10;
        alert(`Timetable downloaded with ${eventCount} classes.\nEstimated study hours per week: ${studyHoursPerWeek} hours`);
        
        // Helper function to parse event description
        function parseEventDescription(description) {
            try {
                const parts = description.split(' - ');
                const courseCode = parts[0].trim();
                
                let sessionType = '';
                let groupNumber = '';
                
                if (parts.length > 1) {
                    const sessionParts = parts[1].split(' ');
                    sessionType = sessionParts[0].trim();
                    
                    if (sessionParts.length > 1) {
                        groupNumber = sessionParts[sessionParts.length - 1].trim();
                    }
                }
                
                let instructor = '';
                let location = '';
                let dateRanges = [];
                
                if (parts.length > 2) {
                    const detailParts = parts[2].split(';');
                    if (detailParts.length > 0) {
                        instructor = detailParts[0].trim();
                    }
                    
                    if (detailParts.length > 1) {
                        const locationAndDates = detailParts[1].trim().split(' - ');
                        if (locationAndDates.length > 0) {
                            location = locationAndDates[0].trim();
                        }
                        
                        if (locationAndDates.length > 1) {
                            const datesText = locationAndDates.slice(1).join(' - ');
                            const dateRangeParts = datesText.split(',');
                            
                            dateRanges = dateRangeParts.map(range => range.trim());
                        }
                    }
                }
                
                return {
                    courseCode,
                    sessionType,
                    groupNumber,
                    instructor,
                    location,
                    dateRanges
                };
            } catch (e) {
                // If parsing fails, return a basic object with the full description
                console.warn('Failed to parse event description:', description);
                return {
                    courseCode: description,
                    description
                };
            }
        }
        
        // Helper function to process events into recurring calendar events
        function processEvents(events, cal) {
            events.forEach(event => {
                // Parse the description to extract important information
                const descInfo = parseEventDescription(event.EventDescription);
                
                // Extract location and date ranges from the description
                const parts = event.EventDescription.split(";");
                const title = parts[0].trim();
                
                for (let i = 1; i < parts.length; i++) {
                    let info = parts[i].split("-");
                    let eventLocation = info[0].trim();
                    
                    // Extract date ranges (e.g., "03/03 to 04/07, 04/21 to 05/26")
                    let dateRangeText = info.slice(1).join("-").trim();
                    let dateRangeParts = dateRangeText.split(",");
                    
                    dateRangeParts.forEach(rangePart => {
                        let dateRange = rangePart.trim().match(/(\d+\/\d+)\s+to\s+(\d+\/\d+)/);
                        
                        if (dateRange) {
                            let startDate = dateRange[1];
                            let endDate = dateRange[2];
                            
                            createSeriesEvent(startDate, endDate, event, title, eventLocation, cal);
                        }
                    });
                }
            });
        }
        
        // Create recurring series events
        function createSeriesEvent(startDateStr, endDateStr, event, title, eventLocation, cal) {
            // Convert MM/DD format to Date objects with current year (2025)
            const currentYear = new Date().getFullYear();
            
            // Parse the date strings (format: MM/DD)
            let [startMonth, startDay] = startDateStr.split('/').map(Number);
            let [endMonth, endDay] = endDateStr.split('/').map(Number);
            
            // Create date objects
            let startDate = new Date(currentYear, startMonth - 1, startDay);
            let endDate = new Date(currentYear, endMonth - 1, endDay);
            
            // If end month is earlier than start month, assume it's next year
            if (endMonth < startMonth) {
                endDate.setFullYear(currentYear + 1);
            }
            
            // Get start and end times from the event
            let startTime = new Date(event.EventStartTime);
            let endTime = new Date(event.EventEndTime);
            
            // Create the event start date/time
            let eventStart = new Date(startDate);
            eventStart.setHours(startTime.getHours());
            eventStart.setMinutes(startTime.getMinutes());
            eventStart.setSeconds(0);
            
            // Create the event end date/time
            let eventEnd = new Date(startDate);
            eventEnd.setHours(endTime.getHours());
            eventEnd.setMinutes(endTime.getMinutes());
            eventEnd.setSeconds(0);
            
            // Calculate study hours for this class
            let studyHours = (eventEnd - eventStart) / (1000 * 60 * 60);
            totalStudyHours += studyHours;
            
            // Set recurrence end date (inclusive)
            let recurrenceEnd = new Date(endDate);
            recurrenceEnd.setDate(recurrenceEnd.getDate() + 1); // Add one day to include the end date
            
            // Generate recurrence rule
            const rrule = `RRULE:FREQ=WEEKLY;UNTIL=${formatDateForICal(recurrenceEnd)}`;
            
            // Create the calendar event with recurrence
            cal.addEvent(
                title, // Summary/title
                event.EventDescription, // Description
                eventLocation, // Location
                eventStart, // Start time
                eventEnd, // End time
                rrule // Recurrence rule
            );
        }
        
        // Helper function to format date for iCalendar
        function formatDateForICal(date) {
            return date.toISOString().replace(/[-:]/g, '').substring(0, 15) + 'Z';
        }
    }
});