/* ics.js - ICS file generator for JavaScript */
(function() {
    'use strict';
    
    if (typeof window === 'undefined' && typeof module !== 'undefined') {
        module.exports = ics;
    } else {
        window.ics = ics;
    }
    
    function ics() {
        const SEPARATOR = (navigator.appVersion.indexOf('Win') !== -1) ? '\r\n' : '\n';
        const calendarEvents = [];
        const calendarStart = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Swinburne Timetable//ICS Generator//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH'
        ].join(SEPARATOR);
        const calendarEnd = SEPARATOR + 'END:VCALENDAR';
        
        return {
            addEvent: function(subject, description, location, start, end, rrule) {
                const event = [
                    'BEGIN:VEVENT',
                    'UID:' + (Math.random().toString(36).substring(2, 15) + 
                             Math.random().toString(36).substring(2, 15)),
                    'DTSTAMP:' + dateToICS(new Date()),
                    'DTSTART:' + dateToICS(start),
                    'DTEND:' + dateToICS(end),
                    'SUMMARY:' + escapeICSText(subject)
                ];
                
                if (description) {
                    event.push('DESCRIPTION:' + escapeICSText(description));
                }
                
                if (location) {
                    event.push('LOCATION:' + escapeICSText(location));
                }
                
                if (rrule) {
                    event.push(rrule);
                }
                
                // Add alarm 15 minutes before
                event.push(
                    'BEGIN:VALARM',
                    'TRIGGER:-PT15M',
                    'ACTION:DISPLAY',
                    'DESCRIPTION:Reminder',
                    'END:VALARM'
                );
                
                event.push('END:VEVENT');
                calendarEvents.push(event.join(SEPARATOR));
                
                return this;
            },
            
            build: function() {
                if (calendarEvents.length < 1) {
                    return null;
                }
                
                const calendar = [
                    calendarStart,
                    calendarEvents.join(SEPARATOR),
                    calendarEnd
                ].join(SEPARATOR);
                
                return calendar;
            },
            
            download: function(filename) {
                if (calendarEvents.length < 1) {
                    return false;
                }
                
                filename = (typeof filename !== 'undefined') ? filename : 'swinburne-timetable.ics';
                const calendar = this.build();
                const blob = new Blob([calendar], {type: 'text/calendar;charset=utf-8'});
                
                if (navigator.msSaveBlob) {
                    return navigator.msSaveBlob(blob, filename);
                } else {
                    const link = document.createElement('a');
                    link.href = window.URL.createObjectURL(blob);
                    link.setAttribute('download', filename);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    return true;
                }
            }
        };
    }
    
    function escapeICSText(text) {
        return text
            .replace(/[\\;,]/g, function(match) {
                return '\\' + match;
            })
            .replace(/\n/g, '\\n');
    }
    
    function dateToICS(date) {
        if (!date) {
            return '';
        }
        
        // Format: YYYYMMDDTHHMMSSZ
        const year = date.getUTCFullYear();
        const month = (date.getUTCMonth() + 1).toString().padStart(2, '0');
        const day = date.getUTCDate().toString().padStart(2, '0');
        const hours = date.getUTCHours().toString().padStart(2, '0');
        const minutes = date.getUTCMinutes().toString().padStart(2, '0');
        const seconds = date.getUTCSeconds().toString().padStart(2, '0');
        
        return year + month + day + 'T' + hours + minutes + seconds + 'Z';
    }
})();