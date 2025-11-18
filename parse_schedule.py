#!/usr/bin/env python3
"""
Conference Schedule Parser
Extracts schedule data from conference PDFs and generates JSON files.
"""

import PyPDF2
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class ScheduleParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.sessions = []

    def parse(self) -> List[Dict[str, Any]]:
        """Parse the PDF and extract all sessions."""
        with open(self.pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"

        # Split into sessions by session ID pattern (4 digits at start of line)
        session_blocks = re.split(r'\n(?=\d{4}\s+)', full_text)

        for block in session_blocks:
            if not block.strip() or len(block.strip()) < 10:
                continue

            session = self.parse_session(block)
            if session:
                self.sessions.append(session)

        return self.sessions

    def parse_session(self, text: str) -> Dict[str, Any]:
        """Parse a single session block."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            return None

        # Extract session ID
        first_line = lines[0]
        session_id_match = re.match(r'^(\d{4})', first_line)
        if not session_id_match:
            return None

        session_id = session_id_match.group(1)

        # Find the title (usually follows the session ID)
        title = ""
        day_time = ""
        location = ""
        category = ""
        chair = []
        participants = []
        discussants = []

        current_section = None
        current_participant = {}

        i = 0
        while i < len(lines):
            line = lines[i]

            # Session ID and title usually on first line or next line
            if i == 0 or i == 1:
                # Remove session ID from line if present
                line_clean = re.sub(r'^\d{4}\s+', '', line)
                if not title and line_clean and not self.is_metadata_line(line_clean):
                    title = line_clean
                i += 1
                continue

            # Check for day/time patterns
            if re.match(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', line, re.IGNORECASE):
                day_time = line
                i += 1
                continue

            # Check for time patterns
            if re.match(r'\d{1,2}:\d{2}[ap]m', line, re.IGNORECASE):
                if not day_time or 'Floor' in day_time or 'Building' in day_time:
                    day_time = line
                else:
                    day_time += " " + line
                i += 1
                continue

            # Location usually has Floor, Building, Room names
            if any(keyword in line for keyword in ['Floor', 'Building', 'Room', 'Bridge', 'Riverside', 'Churchill', 'Canal', 'Cambridge']):
                if not location:
                    location = line
                else:
                    location += " " + line
                i += 1
                continue

            # Category keywords
            category_keywords = ['Undergraduate Research', 'Comparative Politics', 'Public Opinion',
                                'Conference Within A Conference', 'Political Methodology', 'International Conflict',
                                'Human Rights', 'Race and Ethnicity', 'Women, Gender, and Politics',
                                'Environmental Politics', 'American Political Development', 'Presidential',
                                'Local and Urban Politics', 'Political Theory', 'Teaching Political Science',
                                'Meetings', 'Political Psychology']

            for keyword in category_keywords:
                if keyword in line:
                    category = line
                    i += 1
                    break

            if category and category in line:
                i += 1
                continue

            # Section headers
            if line.lower() == 'chair' or line.lower() == 'chair:':
                current_section = 'chair'
                i += 1
                continue

            if line.lower() == 'participants' or line.lower() == 'participants:':
                current_section = 'participants'
                # Save any pending participant
                if current_participant and current_participant.get('name'):
                    participants.append(current_participant)
                    current_participant = {}
                i += 1
                continue

            if line.lower().startswith('discussant'):
                current_section = 'discussants'
                # Save any pending participant
                if current_participant and current_participant.get('name'):
                    participants.append(current_participant)
                    current_participant = {}
                i += 1
                continue

            # Parse chair
            if current_section == 'chair':
                if self.looks_like_person(line):
                    name, affiliation = self.parse_person_line(line)
                    chair.append({'name': name, 'affiliation': affiliation})
                else:
                    current_section = None

            # Parse participants
            elif current_section == 'participants':
                if self.looks_like_person(line):
                    # Save previous participant if exists
                    if current_participant and current_participant.get('name'):
                        participants.append(current_participant)

                    name, affiliation = self.parse_person_line(line)
                    current_participant = {
                        'name': name,
                        'affiliation': affiliation,
                        'paper': ''
                    }
                elif current_participant:
                    # This is likely a paper title
                    if not current_participant.get('paper'):
                        current_participant['paper'] = line
                    else:
                        current_participant['paper'] += ' ' + line

            # Parse discussants
            elif current_section == 'discussants':
                if self.looks_like_person(line):
                    name, affiliation = self.parse_person_line(line)
                    discussants.append({'name': name, 'affiliation': affiliation})

            i += 1

        # Save last participant
        if current_participant and current_participant.get('name'):
            participants.append(current_participant)

        session = {
            'id': session_id,
            'title': title,
            'day_time': day_time,
            'location': location,
            'category': category,
            'chair': chair,
            'participants': participants,
            'discussants': discussants
        }

        return session

    def is_metadata_line(self, line: str) -> bool:
        """Check if a line is metadata (day, time, location, etc.)"""
        metadata_patterns = [
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
            r'\d{1,2}:\d{2}[ap]m',
            r'Floor',
            r'Building',
            r'Room'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in metadata_patterns)

    def looks_like_person(self, line: str) -> bool:
        """Heuristic to identify if a line contains a person's name and affiliation."""
        # Typically: Name, Affiliation
        # Has a comma and contains a university/institution keyword
        if ',' not in line:
            return False

        institution_keywords = ['University', 'College', 'Institute', 'School', 'Center', 'State',
                               'Student', 'Professor', 'Dr.', 'MIT', 'UCLA', 'USC']
        return any(keyword in line for keyword in institution_keywords)

    def parse_person_line(self, line: str) -> tuple:
        """Extract name and affiliation from a person line."""
        parts = line.split(',', 1)
        name = parts[0].strip()
        affiliation = parts[1].strip() if len(parts) > 1 else ''
        return name, affiliation


def parse_all_pdfs():
    """Parse all three PDF files and generate JSON files."""
    pdf_files = {
        'thursday': 'spsa_thursday.pdf',
        'friday': 'spsa_friday.pdf',
        'saturday': 'spsa_saturday.pdf'
    }

    all_sessions = {}

    for day, pdf_file in pdf_files.items():
        pdf_path = Path(pdf_file)
        if not pdf_path.exists():
            print(f"Warning: {pdf_file} not found, skipping...")
            continue

        print(f"Parsing {pdf_file}...")
        parser = ScheduleParser(str(pdf_path))
        sessions = parser.parse()

        all_sessions[day] = sessions

        # Write individual day JSON
        output_file = f'schedule_{day}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)

        print(f"  Found {len(sessions)} sessions")
        print(f"  Saved to {output_file}")

    # Write combined JSON
    with open('schedule_all.json', 'w', encoding='utf-8') as f:
        json.dump(all_sessions, f, indent=2, ensure_ascii=False)

    print(f"\nTotal sessions parsed: {sum(len(s) for s in all_sessions.values())}")
    print("All data saved to schedule_all.json")

    return all_sessions


if __name__ == '__main__':
    parse_all_pdfs()
