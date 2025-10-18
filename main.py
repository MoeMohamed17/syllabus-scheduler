import os
import json
from pdf_extract import extract_text
from ai_extractor import extract_deadlines_with_ai

def main():
    pdf_folder = "syllabi_pdfs"
    output_folder = "extracted_deadlines"
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all PDF files in the folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}/")
        return
    
    print(f"Processing {len(pdf_files)} PDF file(s)...")
    
    all_deadlines = []
    
    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        try:
            # Extract text from PDF
            text = extract_text(pdf_path)
            
            if not text:
                continue
            
            # Send to OpenAI for deadline extraction
            deadlines = extract_deadlines_with_ai(text, pdf_file)
            
            # Save individual JSON file
            output_filename = f"{os.path.splitext(pdf_file)[0]}_deadlines.json"
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(deadlines, f, indent=2, ensure_ascii=False)
            
            all_deadlines.append(deadlines)
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    # Save combined JSON file with all deadlines
    if all_deadlines:
        combined_output_path = os.path.join(output_folder, "all_deadlines.json")
        with open(combined_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_deadlines, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Complete! Processed {len(all_deadlines)} syllabus file(s).")
        print(f"   Results saved to: {output_folder}/")

if __name__ == "__main__":
    main()
