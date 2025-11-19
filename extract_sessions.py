import pdfplumber
import json
import re
import os

def extract_sessions_from_pdf(pdf_path, day_name):
    sessions = []
    current_session = None
    
    # Layout constants based on inspection
    SESSION_ID_X_MAX = 100 
    PARTICIPANT_HEADER_X = 139.58
    PAPER_TITLE_X = 139.58
    AUTHOR_X = 161.18
    
    # Font styles (approximate based on inspection)
    # Bold: Section Title, Session Title, "Participants", "Chair", "Discussants"
    # Italic: Time, Location
    # Regular: Session ID, Paper Title, Author Name
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract words for precise coordinate checking
            words = page.extract_words(extra_attrs=["fontname", "size"])
            
            # Extract lines for general text flow
            lines = page.extract_text_lines()
            
            # We need to iterate through lines to find structure
            i = 0
            while i < len(lines):
                line = lines[i]
                text = line['text']
                x0 = line['x0']
                
                # 1. Detect Session ID (e.g., "2100")
                # It's usually a 4-digit number on the left column
                # NOTE: extract_text_lines might merge ID with the next text if close
                match = re.match(r'^(\d{4})\s+(.*)', text.strip())
                is_standalone_id = re.match(r'^\d{4}$', text.strip())
                
                if x0 < SESSION_ID_X_MAX and (match or is_standalone_id):
                    session_id = match.group(1) if match else text.strip()
                    remainder_text = match.group(2) if match else ""
                    
                    # Save previous session if exists
                    if current_session:
                        sessions.append(current_session)
                    
                    current_session = {
                        "day": day_name,
                        "id": session_id,
                        "start_time": "",
                        "end_time": "",
                        "location": "",
                        "section": "", 
                        "title": "", 
                        "participants": []
                    }
                    
                    # If there was text after the ID, it's likely the Section Title
                    if remainder_text:
                        current_session["section"] = remainder_text
                    
                    # The next few lines contain the metadata
                    # We need to look ahead to fill in the details
                    # This part is tricky because the order varies slightly, but usually:
                    # Line 1 (after ID): Section Title (Bold)
                    # Line 2: Time
                    # Line 3: Location
                    # Line 4: Session Title (Bold)
                    
                    # Let's try to capture the block of text associated with this session header
                    # The session header info is usually in the column to the right of the ID
                    # We can look for lines that are roughly top-aligned with the ID or slightly below
                    
                    # A simpler approach: consume lines until "Participants", "Chair", or next ID
                    # But we need to distinguish between Section, Time, Location, Title
                    
                    # Let's advance `i` to process the header lines
                    i += 1
                    header_lines = []
                    while i < len(lines):
                        next_line = lines[i]
                        if next_line['x0'] < SESSION_ID_X_MAX and re.match(r'^\d{4}$', next_line['text'].strip()):
                            # Found next session, stop
                            i -= 1 # Backtrack
                            break
                        if "Participants" in next_line['text']:
                            # Found participants section
                            i -= 1 # Backtrack so the main loop catches it
                            break
                        
                        # Check for Time pattern (e.g., 8:00am-9:15am)
                        time_match = re.search(r'(\d{1,2}:\d{2}[ap]m)-(\d{1,2}:\d{2}[ap]m)', next_line['text'])
                        
                        # Check font attributes if available (using words to check font of first word)
                        # This is hard with lines. Let's stick to text patterns and order for now, but be smarter.
                        
                        text = next_line['text'].strip()
                        
                        if time_match:
                            current_session["start_time"] = time_match.group(1)
                            current_session["end_time"] = time_match.group(2)
                        elif "Floor" in text or "Building" in text or "Room" in text or "Hall" in text or "Level" in text:
                             # Heuristic for location
                             if not current_session["location"]:
                                 current_session["location"] = text
                             else:
                                 current_session["location"] += " " + text
                        elif not current_session["section"]:
                            # First text line is likely Section
                            current_session["section"] = text
                        elif current_session["section"] and not current_session["title"] and not time_match:
                             # Text after section (and maybe time/loc) is likely Title
                             # But sometimes Section is multi-line.
                             # If it's all caps or bold (we can't see bold easily in lines), assume Section?
                             # Let's assume if we haven't seen time/loc yet, it might still be Section.
                             if not current_session["start_time"]:
                                 current_session["section"] += " " + text
                             else:
                                 current_session["title"] = text
                        else:
                            # Append to previous fields
                            if current_session["title"]:
                                current_session["title"] += " " + text
                            elif current_session["location"]:
                                current_session["location"] += " " + text
                            elif current_session["section"]:
                                current_session["section"] += " " + text
                        
                        i += 1
                    
                # 2. Detect Participants Section
                elif current_session and "Participants" in text:
                    # Start parsing participants
                    i += 1
                    current_paper = None
                    
                    while i < len(lines):
                        p_line = lines[i]
                        p_text = p_line['text']
                        p_x0 = p_line['x0']
                        
                        # Stop conditions
                        if "Discussants" in p_text or "Chair" in p_text:
                            if current_paper:
                                current_session["participants"].append(current_paper)
                                current_paper = None
                            break
                        if p_x0 < SESSION_ID_X_MAX and (re.match(r'^\d{4}$', p_text.strip()) or re.match(r'^\d{4}\s+', p_text.strip())):
                            i -= 1
                            if current_paper:
                                current_session["participants"].append(current_paper)
                                current_paper = None
                            break
                            
                        # Check for new paper start (Title)
                        # Heuristic: Indentation is around 139.58
                        if abs(p_x0 - PAPER_TITLE_X) < 10:
                            # Check if this is actually a continuation of the previous author line (rare but possible)
                            # Or a continuation of the previous title?
                            # If we have a current paper and NO author yet, this is likely a title continuation
                            if current_paper and not current_paper["name"]:
                                current_paper["title"] += " " + p_text
                            else:
                                if current_paper:
                                    current_session["participants"].append(current_paper)
                                
                                current_paper = {
                                    "title": p_text,
                                    "name": "",
                                    "affiliation": ""
                                }
                        
                        # Check for Author/Affiliation
                        # Heuristic: Indentation is around 161.18
                        elif abs(p_x0 - AUTHOR_X) < 10:
                             # If it looks like an author line (has comma?)
                             if "," in p_text or "University" in p_text or "College" in p_text:
                                parts = p_text.split(',', 1)
                                name = parts[0].strip()
                                affiliation = parts[1].strip() if len(parts) > 1 else ""
                                
                                if current_paper:
                                    if not current_paper["name"]:
                                        current_paper["name"] = name
                                        current_paper["affiliation"] = affiliation
                                    else:
                                        # New participant, same paper
                                        current_session["participants"].append(current_paper)
                                        current_paper = {
                                            "title": current_paper["title"],
                                            "name": name,
                                            "affiliation": affiliation
                                        }
                                else:
                                    # Orphan author line? Skip or attach to last session?
                                    pass
                             else:
                                 # Might be title continuation if no author yet
                                 if current_paper and not current_paper["name"]:
                                     current_paper["title"] += " " + p_text
                                 elif current_paper and current_paper["name"]:
                                     # Affiliation continuation?
                                     current_paper["affiliation"] += " " + p_text
                                    
                        else:
                            # Unknown indentation
                            # Assume title continuation if no author
                            if current_paper and not current_paper["name"]:
                                current_paper["title"] += " " + p_text
                            elif current_paper:
                                current_paper["affiliation"] += " " + p_text
                        
                        i += 1
                    
                    if current_paper:
                        current_session["participants"].append(current_paper)

                i += 1
                
    if current_session:
        sessions.append(current_session)
        
    return sessions

def main():
    files = [
        ("spsa_thursday.pdf", "Thursday"),
        ("spsa_friday.pdf", "Friday"),
        ("spsa_saturday.pdf", "Saturday")
    ]
    
    all_sessions = []
    for pdf_file, day in files:
        if os.path.exists(pdf_file):
            print(f"Processing {pdf_file}...")
            sessions = extract_sessions_from_pdf(pdf_file, day)
            all_sessions.extend(sessions)
        else:
            print(f"File {pdf_file} not found.")
            
    with open("schedule_all.json", "w") as f:
        json.dump(all_sessions, f, indent=2)
    
    print(f"Extracted {len(all_sessions)} sessions to schedule_all.json")

if __name__ == "__main__":
    main()
