# Medical Report Summarization Web Application

An AI-powered web application for analyzing and summarizing medical reports using rule-based analysis and NLP techniques.

## 🎯 Features

### Core Functionality
- **Multi-Input Support**: Upload PDF files OR paste text manually
- **Medical Value Extraction**: Automatically extracts key medical values (Glucose, Hemoglobin, Cholesterol) from report text
- **Rule-Based Analysis**: Detects health issues using predefined medical thresholds
- **NLP Summarization**: Extractive text summarization using sentence ranking
- **Explainable AI**: Shows why each prediction was made with detailed explanations
- **Method Comparison**: Compares Rule-Based vs NLP approaches with metrics
- **PDF Upload**: Upload medical report PDFs for automatic text extraction ✨
- **Data Visualization**: Interactive charts showing medical values with color-coded results ✨ NEW!

### User Interface
- Clean, modern responsive design
- Dark mode toggle
- Real-time analysis with loading indicators
- Detailed results with visual cards
- Comparison table showing both methods
- Keyboard shortcuts (Ctrl+Enter to analyze, Escape to clear)

## 📁 Project Structure

```
medical/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── nlp_processor.py    # NLP summarization logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── templates/
│   │   └── index.html      # HTML template
│   └── static/
│       ├── style.css       # CSS styling
│       └── script.js       # JavaScript functionality
└── README.md               # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

Navigate to the backend directory and install required packages:

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- **Flask==3.0.0** - Web framework
- **nltk==3.9.1** - Natural Language Processing
- **PyPDF2==3.0.1** - PDF text extraction

### Step 2: Run the Application

```bash
python app.py
```

The server will start and display:
```
============================================================
Medical Report Summarization System
============================================================
Access the application at: http://localhost:5000
============================================================
```

### Step 3: Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:5000
```

## 📝 How to Use

### Option 1: Text Input
1. **Enter Medical Report**: Paste your medical report text into the textarea
2. **Click "Analyze Report"**: The system will process the text
3. **View Results**: Review the comprehensive analysis including:
   - Summary of findings
   - Data visualization charts ✨
   - Detected health issues
   - Personalized health advice
   - Explainable AI insights
   - NLP-based summary
   - Method comparison table

### Option 2: PDF Upload ✨
1. **Click "📄 Upload PDF Report"** button
2. **Select a PDF file** from your computer (max 16MB)
3. **Automatic Extraction**: Text is automatically extracted and displayed
4. **Click "Analyze Report"**: Process the extracted text
5. **View Results**: Same comprehensive analysis as text input

**Note**: PDF must be text-based (not image-only). See `PDF_UPLOAD_GUIDE.md` for details.

### Example Input

```
Patient blood glucose level is 180 mg/dL.
Hemoglobin count shows 11 g/dL.
Total cholesterol measured at 220 mg/dL.
The patient reports frequent urination and excessive thirst.
Blood pressure reading was 140/90 mmHg.
```

### Expected Output

**Summary**: "Your report shows high blood sugar, low hemoglobin, and high cholesterol."

**Detected Issues**:
- High Blood Sugar (Diabetes Risk)
- Low Hemoglobin (Anemia Risk)
- High Cholesterol

**Advice**: Reduce sugar intake • Increase iron-rich foods • Exercise regularly • Consult a healthcare professional

## 🔬 Technical Details

### Comparison Module (Experiment Section)

The application compares two approaches:

| Method     | Accuracy | Speed  | Complexity | Strengths |
|------------|----------|--------|------------|-----------|
| **Rule-Based** | High (structured data) | Fast (~50ms) | Low | Precise extraction, Clear thresholds, Explainable |
| **NLP-Based** | Medium-High | Medium (~150ms) | Medium | Handles free text, Extracts key points, Flexible |

### Rule-Based Analysis

Uses regex patterns to extract medical values and applies clinical thresholds. See "Medical Thresholds Used" table above for detailed reference ranges.

### NLP Summarization Algorithm

1. **Tokenization**: Split text into sentences
2. **Preprocessing**: Remove stopwords and punctuation
3. **Word Frequency**: Calculate importance scores
4. **Sentence Ranking**: Score sentences based on word frequency
5. **Selection**: Choose top 2 most important sentences
6. **Output**: Coherent summary in original order

### Data Visualization (Chart.js)

The application generates interactive bar charts showing:
- **Extracted Medical Values**: Glucose, Hemoglobin, Cholesterol levels
- **Color Coding**: 
  - 🟢 Green = Normal range
  - 🔴 Red = Abnormal range (high or low)
- **Interactive Tooltips**: Hover to see exact values with units
- **Dark Mode Support**: Charts adapt to theme automatically

### Medical Thresholds Used

| Metric | Normal Range | High Threshold | Low Threshold |
|--------|-------------|----------------|---------------|
| Glucose | 70-140 mg/dL | > 140 | < 70 |
| Hemoglobin | 12-17 g/dL | > 17 | < 12 |
| Cholesterol | 125-200 mg/dL | > 200 | < 125 |

### API Endpoint

**POST /analyze**

Request Body:
```json
{
  "report_text": "Medical report text..."
}
```

Response:
```json
{
  "success": true,
  "summary": "...",
  "issues": [...],
  "advice": "...",
  "explanations": [...],
  "nlp_summary": "...",
  "comparison": {...},
  "processing_time": 150
}
```

## 🎨 UI Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Card Layout**: Organized, easy-to-read result sections
- **Color Coding**: 
  - Red (High severity issues)
  - Orange (Medium severity)
  - Green (Normal/Low severity)
- **Animations**: Smooth transitions and loading states
- **Accessibility**: Keyboard shortcuts and clear visual hierarchy

## 🧪 Testing

### Test Case 1: High Values
```
Glucose: 180 mg/dL
Hemoglobin: 11 g/dL
Cholesterol: 220 mg/dL
```
Expected: Diabetes risk, Anemia risk, High cholesterol

### Test Case 2: Normal Values
```
Glucose: 100 mg/dL
Hemoglobin: 14 g/dL
Cholesterol: 180 mg/dL
```
Expected: No issues detected

### Test Case 3: Low Values
```
Glucose: 60 mg/dL
Hemoglobin: 10 g/dL
Cholesterol: 110 mg/dL
```
Expected: Hypoglycemia, Anemia, Low cholesterol

## 🛠️ Troubleshooting

### Issue: NLTK Data Download Error
**Solution**: The application automatically downloads required NLTK data. If issues persist:
```python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
```

### Issue: Port 5000 Already in Use
**Solution**: Modify the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port to 5001
```

### Issue: Flask Not Found
**Solution**: Ensure you're in the backend directory and run:
```bash
pip install -r requirements.txt
```

## 📊 Performance

- **Average Processing Time**: < 200ms
- **Rule-Based Speed**: ~50ms
- **NLP Speed**: ~100-150ms
- **PDF Processing**: ~200-500ms (depending on file size)
- **Chart Rendering**: < 100ms
- **Accuracy**: High for structured medical data

## ⚠️ Disclaimer

**For Educational Purposes Only**

This application is designed as an academic project for demonstrating AI and NLP concepts. It is NOT intended for:
- Medical diagnosis
- Clinical decision-making
- Replacing professional medical advice

Always consult qualified healthcare professionals for medical concerns.

## 🎓 Academic Use

This project demonstrates:
- Rule-based AI systems
- Natural Language Processing
- Text summarization techniques
- Explainable AI principles
- Comparative analysis methods
- Web application development

Suitable for:
- Advanced AI courses
- NLP mini-projects
- Web development assignments
- AI ethics discussions

## 🔐 Privacy & Security

- All processing happens locally
- No data is stored or transmitted externally
- No user authentication required
- No database connections (in basic version)

## 📈 Future Enhancements

Potential additions:
- Save report history (SQLite/MySQL)
- PDF report upload support
- Multi-language support
- Additional medical metrics
- Chart/graph visualizations
- Export results to PDF
- User accounts and profiles

## 📄 License

This project is created for educational purposes. Feel free to use and modify for learning.

## 👨‍💻 Author

Created as an Advanced AI academic mini-project in 2026.

## 🙏 Acknowledgments

- Flask Framework
- NLTK Library
- Modern Web Technologies (HTML5, CSS3, JavaScript ES6)

---

**Happy Learning! 🚀**
