import pdfplumber
import re

def debug_session_ids(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[1] # Check page 2 (index 1) as page 1 is often cover
        print(f"--- Debugging Page 2 of {pdf_path} ---")
        
        print("\n--- Checking Lines ---")
        lines = page.extract_text_lines()
        for line in lines:
            if "2100" in line['text']:
                print(f"Line with 2100: '{line['text']}' | x0: {line['x0']}")

if __name__ == "__main__":
    debug_session_ids("spsa_thursday.pdf")
