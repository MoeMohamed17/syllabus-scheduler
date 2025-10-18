import os
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from ai_extractor import extract_deadlines_with_ai
from calendar_generator import generate_calendar

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'extracted_deadlines'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Syllabus Scheduler API',
        'version': '1.0.0',
        'endpoints': {
            'POST /upload': 'Upload and process a PDF syllabus',
            'POST /process-multiple': 'Upload and process multiple PDF syllabi',
            'GET /calendar': 'Generate and download ICS calendar file',
            'GET /deadlines': 'Get all extracted deadlines as JSON'
        }
    }), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process a single PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract deadlines using AI with vision (pass PDF directly)
        deadlines = extract_deadlines_with_ai(filepath, filename)
        
        # Save the deadlines to JSON
        output_filename = f"{os.path.splitext(filename)[0]}_deadlines.json"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(deadlines, f, indent=2, ensure_ascii=False)
        
        # Update the combined all_deadlines.json file
        combined_json_path = os.path.join(OUTPUT_FOLDER, "all_deadlines.json")
        all_deadlines = []
        
        # Load existing deadlines if file exists
        if os.path.exists(combined_json_path):
            with open(combined_json_path, 'r', encoding='utf-8') as f:
                all_deadlines = json.load(f)
        
        # Add new deadlines (avoid duplicates based on source_file)
        existing_sources = [d.get('source_file') for d in all_deadlines]
        if deadlines.get('source_file') not in existing_sources:
            all_deadlines.append(deadlines)
        else:
            # Update existing entry
            all_deadlines = [d if d.get('source_file') != deadlines.get('source_file') else deadlines for d in all_deadlines]
        
        # Save updated combined file
        with open(combined_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_deadlines, f, indent=2, ensure_ascii=False)
        
        # Clean up the uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'deadlines': deadlines,
            'output_file': output_filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process-multiple', methods=['POST'])
def process_multiple():
    """Upload and process multiple PDF files"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files in the request'}), 400
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    results = []
    all_deadlines = []
    
    for file in files:
        if not allowed_file(file.filename):
            results.append({
                'filename': file.filename,
                'success': False,
                'error': 'Invalid file type (only PDF allowed)'
            })
            continue
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract deadlines using AI with vision (pass PDF directly)
            deadlines = extract_deadlines_with_ai(filepath, filename)
            
            # Save individual JSON file
            output_filename = f"{os.path.splitext(filename)[0]}_deadlines.json"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(deadlines, f, indent=2, ensure_ascii=False)
            
            all_deadlines.append(deadlines)
            
            results.append({
                'filename': filename,
                'success': True,
                'deadlines': deadlines
            })
            
            # Clean up the uploaded file
            os.remove(filepath)
            
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'error': str(e)
            })
    
    # Save combined JSON file
    if all_deadlines:
        combined_output_path = os.path.join(OUTPUT_FOLDER, "all_deadlines.json")
        with open(combined_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_deadlines, f, indent=2, ensure_ascii=False)
    
    return jsonify({
        'success': True,
        'total_files': len(files),
        'processed': len([r for r in results if r.get('success')]),
        'failed': len([r for r in results if not r.get('success')]),
        'results': results
    }), 200


@app.route('/calendar', methods=['GET'])
def get_calendar():
    """Generate and download ICS calendar file from all deadlines"""
    try:
        combined_json_path = os.path.join(OUTPUT_FOLDER, "all_deadlines.json")
        
        if not os.path.exists(combined_json_path):
            return jsonify({'error': 'No deadlines found. Please process PDF files first.'}), 404
        
        # Generate calendar
        calendar_path = "schedule.ics"
        generate_calendar(json_file=combined_json_path, output_file=calendar_path)
        
        return send_file(
            calendar_path,
            mimetype='text/calendar',
            as_attachment=True,
            download_name='syllabus_schedule.ics'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deadlines', methods=['GET'])
def get_deadlines():
    """Get all extracted deadlines as JSON"""
    try:
        combined_json_path = os.path.join(OUTPUT_FOLDER, "all_deadlines.json")
        
        if not os.path.exists(combined_json_path):
            return jsonify({'error': 'No deadlines found. Please process PDF files first.'}), 404
        
        with open(combined_json_path, 'r', encoding='utf-8') as f:
            deadlines = json.load(f)
        
        return jsonify({
            'success': True,
            'deadlines': deadlines
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check for monitoring"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

