import json

def verify_extraction():
    with open("schedule_all.json", "r") as f:
        sessions = json.load(f)
        
    print(f"Total Sessions: {len(sessions)}")
    
    # 1. Check for the example session (Thursday 2100)
    target_id = "2100"
    found = False
    for s in sessions:
        if s["id"] == target_id:
            found = True
            print("\n--- Found Target Session 2100 ---")
            print(json.dumps(s, indent=2))
            break
            
    if not found:
        print(f"\nERROR: Session {target_id} not found!")

    # 2. Check for empty fields
    empty_counts = {"start_time": 0, "location": 0, "section": 0, "title": 0, "participants": 0}
    for s in sessions:
        for key in empty_counts:
            if not s[key] or (key == "participants" and len(s[key]) == 0):
                empty_counts[key] += 1
                
    print("\n--- Empty Field Counts ---")
    print(empty_counts)
    
    # 3. Check participant quality
    print("\n--- Participant Quality Check (First 3 with participants) ---")
    count = 0
    for s in sessions:
        if s["participants"]:
            print(f"Session {s['id']}:")
            for p in s["participants"][:2]: # Show first 2 participants
                print(f"  - {p}")
            count += 1
            if count >= 3:
                break

if __name__ == "__main__":
    verify_extraction()
