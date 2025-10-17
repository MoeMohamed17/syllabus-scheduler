from pdf_extract import extract_text

def main():
    print("PDF Parser starting...")

    pdf_path = "syllabi_pdfs/CPSC317-Winter-Term1-2025-Syllabus.docx.pdf"

    try:
        text = extract_text(pdf_path)
        if text:
            print(text)
        else: print("pdf opened but no text extracted")
    except FileNotFoundError:
        print("file not found")
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main()
