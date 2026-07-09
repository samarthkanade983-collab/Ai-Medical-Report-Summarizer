"""
Medical Report Summarization Web Application
Flask backend with rule-based analysis and NLP summarization
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import PyPDF2
import re
import time
import os
from datetime import datetime
from nlp_processor import summarize_medical_report
from database import save_report, get_all_reports, get_report_by_id, delete_report, get_statistics
from probabilistic_models import ProbabilisticAnalyzer

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Initialize Probabilistic Models
prob_analyzer = ProbabilisticAnalyzer()

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF file
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text string
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_medical_values(text):
    """
    Extract medical values from report text using regex
    
    Returns:
        Dictionary with extracted values (glucose, hemoglobin, cholesterol)
    """
    values = {
        'glucose': None,
        'hemoglobin': None,
        'cholesterol': None
    }
    
    # Extract Glucose (mg/dL)
    glucose_pattern = r'glucose[:\s]*(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)?|(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)\s*glucose'
    glucose_match = re.search(glucose_pattern, text, re.IGNORECASE)
    if glucose_match:
        values['glucose'] = float(glucose_match.group(1) or glucose_match.group(2))
    
    # Alternative pattern for glucose
    if not values['glucose']:
        alt_glucose = re.search(r'(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL).*?glucose|glucose.*?(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)', text, re.IGNORECASE)
        if alt_glucose:
            values['glucose'] = float(alt_glucose.group(1) or alt_glucose.group(2))
    
    # Extract Hemoglobin (g/dL)
    hemo_pattern = r'hemoglobin[:\s]*(\d+(?:\.\d+)?)\s*(?:g/dL|g\/dL)?|(\d+(?:\.\d+)?)\s*(?:g/dL|g\/dL)\s*hemoglobin'
    hemo_match = re.search(hemo_pattern, text, re.IGNORECASE)
    if hemo_match:
        values['hemoglobin'] = float(hemo_match.group(1) or hemo_match.group(2))
    
    # Alternative pattern for hemoglobin
    if not values['hemoglobin']:
        alt_hemo = re.search(r'(\d+(?:\.\d+)?)\s*(?:g/dL|g\/dL).*?hemoglobin|hemoglobin.*?(\d+(?:\.\d+)?)\s*(?:g/dL|g\/dL)', text, re.IGNORECASE)
        if alt_hemo:
            values['hemoglobin'] = float(alt_hemo.group(1) or alt_hemo.group(2))
    
    # Extract Cholesterol (mg/dL)
    chol_pattern = r'cholesterol[:\s]*(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)?|(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)\s*cholesterol'
    chol_match = re.search(chol_pattern, text, re.IGNORECASE)
    if chol_match:
        values['cholesterol'] = float(chol_match.group(1) or chol_match.group(2))
    
    # Alternative pattern for cholesterol
    if not values['cholesterol']:
        alt_chol = re.search(r'(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL).*?cholesterol|cholesterol.*?(\d+(?:\.\d+)?)\s*(?:mg/dL|mg\/dL)', text, re.IGNORECASE)
        if alt_chol:
            values['cholesterol'] = float(alt_chol.group(1) or alt_chol.group(2))
    
    return values


def analyze_medical_values(values):
    """
    Apply rule-based analysis to medical values
    
    Returns:
        List of detected issues with explanations
    """
    issues = []
    explanations = []
    
    # Glucose analysis (> 140 mg/dL is high)
    if values['glucose']:
        if values['glucose'] > 140:
            issues.append("High Blood Sugar (Diabetes Risk)")
            explanations.append({
                'metric': 'Glucose',
                'value': values['glucose'],
                'threshold': '> 140 mg/dL',
                'finding': f"Glucose is {values['glucose']} (>140), so diabetes risk detected",
                'severity': 'high'
            })
        elif values['glucose'] < 70:
            issues.append("Low Blood Sugar (Hypoglycemia Risk)")
            explanations.append({
                'metric': 'Glucose',
                'value': values['glucose'],
                'threshold': '< 70 mg/dL',
                'finding': f"Glucose is {values['glucose']} (<70), so hypoglycemia risk detected",
                'severity': 'medium'
            })
    
    # Hemoglobin analysis (< 12 g/dL is low)
    if values['hemoglobin']:
        if values['hemoglobin'] < 12:
            issues.append("Low Hemoglobin (Anemia Risk)")
            explanations.append({
                'metric': 'Hemoglobin',
                'value': values['hemoglobin'],
                'threshold': '< 12 g/dL',
                'finding': f"Hemoglobin is {values['hemoglobin']} (<12), so anemia risk detected",
                'severity': 'medium'
            })
        elif values['hemoglobin'] > 17:
            issues.append("High Hemoglobin")
            explanations.append({
                'metric': 'Hemoglobin',
                'value': values['hemoglobin'],
                'threshold': '> 17 g/dL',
                'finding': f"Hemoglobin is {values['hemoglobin']} (>17), which is above normal range",
                'severity': 'low'
            })
    
    # Cholesterol analysis (> 200 mg/dL is high)
    if values['cholesterol']:
        if values['cholesterol'] > 200:
            issues.append("High Cholesterol")
            explanations.append({
                'metric': 'Cholesterol',
                'value': values['cholesterol'],
                'threshold': '> 200 mg/dL',
                'finding': f"Cholesterol is {values['cholesterol']} (>200), so high cholesterol detected",
                'severity': 'high'
            })
        elif values['cholesterol'] < 125:
            issues.append("Low Cholesterol")
            explanations.append({
                'metric': 'Cholesterol',
                'value': values['cholesterol'],
                'threshold': '< 125 mg/dL',
                'finding': f"Cholesterol is {values['cholesterol']} (<125), which is below normal range",
                'severity': 'low'
            })
    
    return issues, explanations


def generate_summary(issues, values):
    """
    Generate simple English summary based on detected issues
    
    Returns:
        Summary string
    """
    if not issues:
        return "Your report appears normal. No significant health issues detected."
    
    summary_parts = ["Your report shows"]
    
    # Build summary based on issues
    issue_map = {
        "High Blood Sugar (Diabetes Risk)": "high blood sugar",
        "Low Blood Sugar (Hypoglycemia Risk)": "low blood sugar",
        "Low Hemoglobin (Anemia Risk)": "low hemoglobin",
        "High Hemoglobin": "high hemoglobin",
        "High Cholesterol": "high cholesterol",
        "Low Cholesterol": "low cholesterol"
    }
    
    detected = [issue_map[issue] for issue in issues if issue in issue_map]
    
    if len(detected) == 1:
        summary_parts.append(detected[0])
    elif len(detected) == 2:
        summary_parts.append(f"{detected[0]} and {detected[1]}")
    else:
        summary_parts.append(", ".join(detected[:-1]) + f", and {detected[-1]}")
    
    return " ".join(summary_parts) + "."


def generate_advice(issues):
    """
    Provide health advice based on detected issues
    
    Returns:
        Advice string
    """
    advice_list = []
    
    if not issues:
        return "Continue maintaining a healthy lifestyle. Regular check-ups are recommended."
    
    # Specific advice for each issue
    advice_map = {
        "High Blood Sugar (Diabetes Risk)": [
            "Reduce sugar and carbohydrate intake",
            "Exercise regularly (30 minutes daily)",
            "Monitor blood sugar levels frequently"
        ],
        "Low Blood Sugar (Hypoglycemia Risk)": [
            "Eat regular meals and snacks",
            "Keep quick-sugar foods handy",
            "Avoid skipping meals"
        ],
        "Low Hemoglobin (Anemia Risk)": [
            "Increase iron-rich foods (spinach, red meat, beans)",
            "Take vitamin C to help iron absorption",
            "Consider iron supplements after consulting doctor"
        ],
        "High Hemoglobin": [
            "Stay hydrated",
            "Avoid smoking",
            "Consult a doctor for underlying causes"
        ],
        "High Cholesterol": [
            "Reduce saturated and trans fats",
            "Increase fiber intake",
            "Exercise regularly",
            "Consider heart-healthy diet"
        ],
        "Low Cholesterol": [
            "Maintain balanced nutrition",
            "Include healthy fats in diet",
            "Consult healthcare provider"
        ]
    }
    
    # Collect relevant advice
    for issue in issues:
        if issue in advice_map:
            advice_list.extend(advice_map[issue])
    
    # Remove duplicates and limit to top 3-4 recommendations
    unique_advice = list(dict.fromkeys(advice_list))[:4]
    
    # Add general advice
    general_advice = [
        "Consult a healthcare professional for proper diagnosis",
        "Maintain a healthy diet",
        "Exercise regularly",
        "Get adequate sleep",
        "Stay hydrated"
    ]
    
    # Combine specific and general advice
    final_advice = unique_advice + [general_advice[0]]  # Always add "consult doctor"
    
    return " • ".join(final_advice)


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """
    Upload and process PDF file
    
    Returns JSON response with:
    - success: boolean
    - text: extracted text from PDF
    - filename: original filename
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Only PDF files are allowed'
            }), 400
        
        # Secure the filename and save
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(filepath)
        
        # Clean up: delete uploaded file after extraction
        try:
            os.remove(filepath)
        except:
            pass  # Ignore cleanup errors
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({
                'error': 'Could not extract text from PDF. The PDF may be scanned or image-based.'
            }), 400
        
        # Get page count properly
        try:
            with open(filepath, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                page_count = len(pdf_reader.pages)
        except:
            page_count = 0
        
        return jsonify({
            'success': True,
            'text': extracted_text,
            'filename': filename,
            'pages': page_count
        })
    
    except Exception as e:
        # Clean up on error
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'error': str(e),
            'details': 'Failed to process PDF file'
        }), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze medical report endpoint
    
    Expected JSON input:
    {
        "report_text": "Patient medical report text..."
    }
    
    Returns JSON response with:
    - summary
    - issues
    - advice
    - explanations
    - nlp_summary
    - comparison
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'report_text' not in data:
            return jsonify({
                'error': 'No report text provided'
            }), 400
        
        report_text = data['report_text'].strip()
        
        if not report_text:
            return jsonify({
                'error': 'Report text is empty'
            }), 400
        
        # Step 1: Extract medical values
        values = extract_medical_values(report_text)
        
        # Step 2: Rule-based analysis
        rule_start = time.time()
        issues, explanations = analyze_medical_values(values)
        rule_time = round((time.time() - rule_start) * 1000, 2)
        
        # Step 3: Generate summary
        summary = generate_summary(issues, values)
        
        # Step 4: Generate advice
        advice = generate_advice(issues)
        
        # Step 5: NLP summarization
        nlp_start = time.time()
        nlp_result = summarize_medical_report(report_text)
        nlp_time = nlp_result['processing_time']
        
        # Step 5b: Probabilistic Models (Naive Bayes & GaussianNB)
        prob_start = time.time()
        department_prediction = prob_analyzer.predict_department(report_text)
        risk_prediction = prob_analyzer.predict_disease_risk(values)
        prob_time = round((time.time() - prob_start) * 1000, 2)
        
        # Step 6: Calculate comparison metrics
        total_time = round((time.time() - start_time) * 1000, 2)
        
        comparison = {
            'rule_based': {
                'method': 'Rule-Based Analysis',
                'accuracy': 'High (for structured data)',
                'speed': f'{rule_time}ms',
                'complexity': 'Low',
                'strengths': ['Precise value extraction', 'Clear thresholds', 'Explainable'],
                'weaknesses': ['Requires specific format', 'Limited flexibility']
            },
            'nlp': {
                'method': 'NLP Summarization',
                'accuracy': 'Medium-High',
                'speed': f'{nlp_time}ms',
                'complexity': 'Medium',
                'strengths': ['Handles free text', 'Extracts key points', 'Flexible'],
                'weaknesses': ['May miss specific values', 'Context dependent']
            }
        }
        
        # Build response
        response = {
            'success': True,
            'summary': summary,
            'issues': issues,
            'advice': advice,
            'explanations': explanations,
            'extracted_values': values,
            'nlp_summary': nlp_result['summary'],
            'probabilistic_analysis': {
                'department': department_prediction,
                'disease_risk': risk_prediction,
                'processing_time_ms': prob_time
            },
            'comparison': comparison,
            'processing_time': total_time,
            'original_text_length': len(report_text),
            'nlp_compression': nlp_result.get('compression_ratio', 0)
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'details': 'An error occurred while processing the report'
        }), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS)"""
    return send_from_directory(app.static_folder, filename)


if __name__ == '__main__':
    print("=" * 60)
    print("Medical Report Summarization System")
    print("=" * 60)
    print("Starting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
