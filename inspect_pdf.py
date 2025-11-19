import pdfplumber

def inspect_pdf(pdf_path, num_pages=3):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:num_pages]):
            print(f"--- Page {i+1} ---")
            text = page.extract_text()
            print(text)
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    inspect_pdf("spsa_thursday.pdf")
