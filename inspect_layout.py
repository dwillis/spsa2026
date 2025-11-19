import pdfplumber

def inspect_layout(pdf_path, page_num=2):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        print(f"--- Page {page_num+1} Layout ---")
        for char in page.chars[:500]: # Inspect first 500 chars to get a sense of styles
             pass # Just to load chars
        
        # Group chars into words/lines to see font attributes
        words = page.extract_words(extra_attrs=["fontname", "size"])
        for word in words[:50]:
            print(f"{word['text']} | Font: {word['fontname']} | Size: {word['size']}")

        print("\n" + "="*50 + "\n")
        
        # Focus on the Participants section to check indentation and vertical spacing
        print("Checking indentation and vertical spacing in Participants section:")
        in_participants = False
        last_bottom = 0
        for line in page.extract_text_lines():
            text = line['text']
            if "Participants" in text:
                in_participants = True
                print(f"HEADER: {text} | x0: {line['x0']} | bottom: {line['bottom']}")
                last_bottom = line['bottom']
                continue
            if in_participants:
                if "Discussants" in text or "Chair" in text:
                    in_participants = False
                    break
                
                # Filter out left column noise
                if line['x0'] < 100:
                    continue
                    
                gap = line['top'] - last_bottom
                print(f"LINE: {text} | x0: {line['x0']} | gap: {gap:.2f}")
                last_bottom = line['bottom']

if __name__ == "__main__":
    inspect_layout("spsa_thursday.pdf", page_num=0) # Page 1 might be cover, let's check page 0 (first page)
