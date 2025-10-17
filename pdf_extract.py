import pdfplumber

"""
Extracts text from all pages of a PDF file using pdfplumber
Args: 
    path (str): Path to the PDF file.
Returns:
    str: Combined text from all pages.
"""
def extract_text(path: str) -> str:
    full_text = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                # removes any non-breaking space character with a normal space and leading/trailing whitespace
                text = text.replace('\u00a0', ' ').strip()
                # Adds the cleaned text to the full_text list, with a little header showing which page it came from
                full_text.append(f"\n\n--- Page {i+1} ---\n{text}")
            else:
                print(f"No text found on page {i+1} (might be scanned).")

    return "\n".join(full_text)
