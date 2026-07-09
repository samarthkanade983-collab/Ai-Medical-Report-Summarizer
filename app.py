from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import sqlite3
import PyPDF2
import os
import io
import re
import json
import nltk
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDqpTmmd1WBYQ8e5suRNblbRqj86_IwhhE")
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=GEMINI_API_KEY)

from probabilistic_models import ProbabilisticAnalyzer
from medical_nlp import medical_extractive_summarize, structured_value_lines

app = Flask(__name__)
app.secret_key = 'super_secret_medical_key'
prob_analyzer = ProbabilisticAnalyzer()




def ensure_schema():
    """Migrate existing SQLite DBs: ensure users table exists."""
    if not os.path.exists('database.db'):
        return
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('PRAGMA table_info(users)')
    cols = [row[1] for row in c.fetchall()]
    if cols and 'email' not in cols:
        c.execute('ALTER TABLE users ADD COLUMN email TEXT')
    conn.commit()
    conn.close()


ensure_schema()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

RANGES = {
    "Glucose": (70, 140),
    "Hemoglobin": (12, 17),
    "Cholesterol": (125, 200),
    "TSH": (0.4, 4.0),
    "Vitamin D": (20, 50),
    "Heart Rate": (60, 100),
    "WBC": (4.5, 11.0),
    "Systolic BP": (90, 120),
    "Diastolic BP": (60, 80)
}

DISEASE_MAP = {
    "Glucose": "Diabetes",
    "Hemoglobin": "Anemia",
    "Cholesterol": "Heart Disease",
    "TSH": "Thyroid Disorder",
    "Vitamin D": "Vitamin Deficiency",
    "Heart Rate": "Arrhythmia",
    "WBC": "Infection",
    "Systolic BP": "Hypertension",
    "Diastolic BP": "Hypertension"
}

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS history')
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_text TEXT,
            extracted_data TEXT,
            summary TEXT,
            issues TEXT,
            diseases TEXT,
            date_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def setup_nltk():
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('tokenizers/punkt')
        # NLTK 3.8+ uses punkt_tab for sent_tokenize; without it the server returns 500
        nltk.data.find('tokenizers/punkt_tab/english/')
    except LookupError:
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('punkt_tab')

def nlp_summarize(text):
    """Legacy extractive path; prefer medical_summarize for analysis."""
    setup_nltk()
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        nltk.download('punkt_tab')
        sentences = sent_tokenize(text)
    except Exception:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip()) or [text]
    if len(sentences) <= 3:
        return text

    stop_words = set(stopwords.words('english'))
    word_freq = {}
    for word in word_tokenize(text.lower()):
        if word.isalnum() and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    sent_scores = {}
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in word_freq:
                sent_scores[sent] = sent_scores.get(sent, 0) + word_freq[word]

    top_sents = sorted(sent_scores, key=sent_scores.get, reverse=True)[:3]
    return ' '.join(top_sents)


def medical_summarize(text: str, extracted_params: dict) -> str:
    """
    Accurate summary: Gemini structured summary when configured, else TF-IDF + clinical weighting.
    Parsed lab lines are appended for transparency.
    """
    text = (text or "").strip()
    if not text:
        return "No text to summarize."
    extractive = medical_extractive_summarize(text, max_sentences=5)
    value_block = structured_value_lines(extracted_params or {})

    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY" and len(text) > 25:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = (
                "You summarize medical reports for lay readers. Rules:\n"
                "- Use ONLY information present in the report text. Do not invent labs, dates, or diagnoses.\n"
                "- If something is unclear, say it is unclear.\n"
                f"{value_block}\n\n"
                f"REPORT TEXT:\n{text[:14000]}\n\n"
                "Respond in plain text with exactly these sections:\n"
                "SUMMARY: (2-5 sentences)\n"
                "KEY FACTS: (bullet lines starting with - ; facts from the text only)\n"
                "NOTE: One sentence that this is an automated summary, not medical advice.\n"
            )
            resp = model.generate_content(prompt)
            out = (resp.text or "").strip()
            if out:
                return out
        except Exception as e:
            print(f"Gemini medical summary: {e}")

    if value_block:
        return extractive + "\n\n" + value_block
    return extractive


def _rule_based_medical_chat(user_message: str, values: dict, diseases: list, prob: dict) -> str:
    """Offline chat using probabilistic context and simple rules."""
    gmm = (prob.get("disease_risk") or {}).get("gmm_mixture") or {}
    dept = (prob.get("department") or {}).get("predicted")
    nb = (prob.get("disease_risk") or {}).get("primary_risk")
    chunks = []
    chunks.append(
        "<b>Offline medical assistant</b> (set <code>GEMINI_API_KEY</code> for full AI). "
        "This is general education only — not a diagnosis."
    )
    if gmm.get("primary_profile") and gmm.get("primary_profile") != "N/A (no structured labs)":
        chunks.append(
            f"<b>GMM profile (mixture model):</b> {gmm.get('primary_profile')} "
            f"~{gmm.get('profile_confidence_percent', 0)}% combined mixture weight."
        )
    if nb:
        chunks.append(f"<b>Gaussian NB primary risk:</b> {nb}")
    if dept:
        chunks.append(f"<b>Department model:</b> {dept}")
    if values:
        pairs = ", ".join(f"{k}={v}" for k, v in values.items())
        chunks.append(f"<b>Parsed values:</b> {pairs}")
    if diseases:
        chunks.append(f"<b>Flagged topics:</b> {', '.join(diseases)}")
    m = user_message.lower()
    if any(k in m for k in ("diet", "food", "eat", "nutrition")):
        chunks.append(
            "<b>General diet tips:</b> emphasize vegetables, fiber, lean protein; limit added sugar and ultra-processed foods. "
            "A clinician or dietitian should tailor this to you."
        )
    elif any(k in m for k in ("exercise", "workout", "activity")):
        chunks.append(
            "<b>Activity:</b> many adults aim for ~150 min/week moderate cardio plus strength training, "
            "if your doctor says it is safe."
        )
    elif any(k in m for k in ("sleep", "stress")):
        chunks.append(
            "<b>Wellbeing:</b> consistent sleep, stress management, and follow-up labs matter — discuss concerns with your provider."
        )
    elif user_message.strip():
        chunks.append(
            "Ask about <b>diet</b>, <b>exercise</b>, or how to read your <b>labs</b>. "
            "For personal medical decisions, speak with a qualified professional."
        )
    return "<br><br>".join(chunks)


def _html_to_plain(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _offline_simplify(plain: str) -> str:
    """Short plain-language fallback when Gemini is not configured."""
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    take = [s.strip() for s in sentences[:4] if len(s.strip()) > 10]
    core = " ".join(take) if take else plain[:400]
    if len(core) > 480:
        core = core[:477].rsplit(" ", 1)[0] + "…"
    return (
        "<b>Plain version</b> (offline):<br>"
        + core
        + "<br><br><span style='opacity:.85'>Add <code>GEMINI_API_KEY</code> for smarter “ELI5” rewrites.</span>"
    )


import werkzeug.utils

def extract_text_from_pdf(pdf_file):
    pdf_file.seek(0)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + " "
    return text

def extract_text_with_gemini(file_storage):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return ""
        
    filename = werkzeug.utils.secure_filename(file_storage.filename)
    if not filename:
        filename = "temp_scan.pdf"
        
    os.makedirs('uploads', exist_ok=True)
    temp_path = os.path.join('uploads', filename)
    file_storage.seek(0)
    file_storage.save(temp_path)
    
    try:
        gemini_file = genai.upload_file(temp_path)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([
            gemini_file, 
            "Extract all text from this medical report. Return ONLY the text exactly as it appears. Do NOT add markdown, explanations, or any other commentary."
        ])
        
        try:
            genai.delete_file(gemini_file.name)
        except:
            pass
            
        return response.text
    except Exception as e:
        print(f"Gemini OCR Error: {e}")
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return "__ERROR__:AI Processing Limit Exceeded. Please wait 60 seconds before uploading another image."
        return f"__ERROR__:Vision AI Error - {error_msg}"
    finally:
        try:
            os.remove(temp_path)
        except:
            pass

def extract_medical_values(text):
    values = {}
    
    # Blood Pressure parsing exception
    bp_match = re.search(r'(?:blood pressure|bp).*?(\d{2,3})\s*/\s*(\d{2,3})', text, re.IGNORECASE | re.DOTALL)
    if bp_match:
        values['Systolic BP'] = float(bp_match.group(1))
        values['Diastolic BP'] = float(bp_match.group(2))
        
    for param in RANGES.keys():
        if "BP" in param: continue # Handled above
        
        # Build dynamic regex for parameters
        pattern = rf"{param}.*?(\d+(\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            values[param] = float(match.group(1))
            
    return values

def rule_based_analysis(values):
    issues = []
    explanations = []
    diseases = set()
    abnormal_params = []
    advice = []
    
    for param, val in values.items():
        if param not in RANGES: continue
        min_v, max_v = RANGES[param]
        
        if val < min_v:
            issues.append(f"Low {param}")
            explanations.append(f"{param} is {val} (<{min_v}), so {DISEASE_MAP.get(param, 'Risk')} detected")
            diseases.add(DISEASE_MAP.get(param, "Unknown"))
            abnormal_params.append(param)
        elif val > max_v:
            issues.append(f"High {param}")
            explanations.append(f"{param} is {val} (>{max_v}), so {DISEASE_MAP.get(param, 'Risk')} detected")
            diseases.add(DISEASE_MAP.get(param, "Unknown"))
            abnormal_params.append(param)
            
    if issues:
        summary_sentence = "Your report indicates " + " and ".join([i.lower() for i in issues]) + "."
        advice = ["Consult a doctor immediately.", "Maintain a strict healthy diet.", "Exercise regularly."]
    else:
        if values:
            summary_sentence = "Your report appears completely normal."
            advice = ["Your report appears normal.", "Continue maintaining a healthy lifestyle."]
        else:
            summary_sentence = "No predefined medical parameters could be extracted from the text."
            advice = ["Ensure your report contains standard markers like Glucose, TSH, Vitamin D, etc."]
            
    return issues, explanations, list(diseases), abnormal_params, summary_sentence, advice

@app.route('/login', methods=['GET', 'POST'])
def login():
    ensure_schema()
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('welcome'))
        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    ensure_schema()
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        email = (request.form.get('email') or '').strip() or None

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), email),
            )
            conn.commit()
            conn.close()
            flash('Account created! Please sign in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already in use. Try another.')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html', username=session.get('username'))


@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html', username=session.get('username'))


@app.route('/chat')
@app.route('/consult')
@login_required
def chat_page():
    return render_template('chat.html', username=session.get('username'))


@app.route('/history')
@login_required
def history_page():
    return render_template('history.html', username=session.get('username'))


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    text = ""
    if 'pdf' in request.files and request.files['pdf'].filename != '':
        uploaded_file = request.files['pdf']
        filename = uploaded_file.filename.lower()
        
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(uploaded_file)
            
            # Fallback to Gemini OCR for scanned PDFs
            if not text.strip():
                text = extract_text_with_gemini(uploaded_file)
                
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            # Direct Gemini OCR for images
            text = extract_text_with_gemini(uploaded_file)
            
    elif 'text' in request.form:
        text = request.form['text']
        
    if text.startswith("__ERROR__:"):
        return jsonify({'error': text.split("__ERROR__:")[1]}), 400
        
    if not text.strip():
        return jsonify({'error': 'No text detected. Please upload a clear report or type manually.'}), 400
        
    extracted_params = extract_medical_values(text)
    issues, explanations, diseases, abnormal_params, rule_summary, advice = rule_based_analysis(extracted_params)
    nlp_summary = medical_summarize(text, extracted_params)
    
    # Probabilistic Models
    department_prediction = prob_analyzer.predict_department(text)
    
    # Branch Logic for Imaging Reports
    if extracted_params:
        risk_prediction = prob_analyzer.predict_disease_risk(extracted_params)
    else:
        # If no numeric blood work, it's unstructured text/imaging
        if len(text.strip()) > 30 and (GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY"):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                ner_prompt = f"Analyze this unstructured medical imaging report. Identify ONLY abnormal clinical impressions (e.g., ischemic changes, infarcts, tumors, fractures). Return ONLY a JSON list of strings representing the diseases or issues. Example: [\"Ischemic changes\", \"Mild atrophy\"]. If totally normal, return []. Text:\\n{text}"
                resp = model.generate_content(ner_prompt)
                
                cleaned = resp.text.strip()
                if cleaned.startswith("```json"): cleaned = cleaned[7:]
                if cleaned.startswith("```"): cleaned = cleaned[3:]
                if cleaned.endswith("```"): cleaned = cleaned[:-3]
                
                gemini_issues = json.loads(cleaned.strip())
                if isinstance(gemini_issues, list):
                    issues.extend(gemini_issues)
                    diseases.extend(gemini_issues)
                    
                    if gemini_issues:
                        rule_summary = "Your imaging report shows abnormal findings: " + ", ".join(gemini_issues) + "."
                        advice = ["Consult a specialist regarding your structured imaging findings immediately.", "Provide this extracted report to your primary physician."]
                    else:
                        rule_summary = "Your imaging report appears to be completely normal with no acute impressions."
                        advice = ["Keep up your healthy lifestyle.", "Follow up normally with your physician."]
                        
                    explanations.append(f"Auto-Analyzed via Gemini NLP as an Unstructured Imaging Report. Found {len(gemini_issues)} key issues.")
            except Exception as e:
                print(f"Gemini NER Error: {e}")
                
        risk_prediction = {
            "primary_risk": "Radiological / Unstructured Report",
            "max_probability": "N/A",
            "all_probabilities": [{"risk_category": "Requires Human Specialist", "probability": 100}],
            "gmm_mixture": {
                "primary_profile": "N/A (no structured labs)",
                "profile_confidence_percent": 0,
                "mixture_probabilities": [],
                "component_breakdown": [],
                "note": "Gaussian Mixture Model runs on numeric lab vectors; upload or paste labs for GMM profiling.",
            },
            "random_forest": {"top_probabilities": [], "tree_ensemble_note": ""},
            "ensemble_detail": {
                "method": "N/A",
                "naive_bayes_peak": "N/A",
                "random_forest_peak": "N/A",
            },
            "hidden_markov": {
                "available": False,
                "note": "Structured lab sequence models activate when numeric labs are present.",
                "primary_risk": None,
                "path_summary": [],
            },
        }
    
    # Store in history DB
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (user_id, report_text, extracted_data, summary, issues, diseases, date_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        text, 
        json.dumps(extracted_params), 
        rule_summary, 
        json.dumps(issues), 
        json.dumps(diseases), 
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    
    return jsonify({
        'values': extracted_params,
        'abnormal_params': abnormal_params,
        'issues': issues,
        'explanations': explanations,
        'diseases': diseases,
        'advice': advice,
        'rule_summary': rule_summary,
        'nlp_summary': nlp_summary,
        'probabilistic_analysis': {
            'department': department_prediction,
            'disease_risk': risk_prediction
        }
    })

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM history WHERE user_id=? ORDER BY id DESC', (session['user_id'],))
    rows = c.fetchall()
    conn.close()
    
    hist = []
    for r in rows:
        hist.append({
            'id': r['id'],
            'date_time': r['date_time'],
            'summary': r['summary'],
            'issues': json.loads(r['issues']) if r['issues'] else [],
            'diseases': json.loads(r['diseases']) if r['diseases'] else [],
            'text': r['report_text'],
            'data': json.loads(r['extracted_data']) if r['extracted_data'] else {}
        })
    return jsonify(hist)

@app.route('/api/history/<int:id>', methods=['DELETE'])
@login_required
def delete_history(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM history WHERE id=? AND user_id=?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/history/clear', methods=['DELETE'])
@login_required
def clear_history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM history WHERE user_id=?', (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/simplify', methods=['POST'])
@login_required
def simplify_reply():
    data = request.json or {}
    raw = data.get('text') or ''
    plain = _html_to_plain(raw)
    if len(plain) < 8:
        return jsonify({'error': 'Nothing to simplify yet. Get a reply first.'}), 400

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return jsonify({'response': _offline_simplify(plain)})

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Rewrite the text below for someone who finds medical jargon confusing (young adult friendly).
Rules:
- Keep the SAME facts; do not add new diagnoses, drugs, or numbers that were not there.
- Max 6 short sentences. Calm, supportive tone. No fear-mongering.
- Avoid heavy slang; clarity beats "cool."
- If the source is already short, still make it easier to read.

SOURCE:
{plain[:8000]}

Output plain paragraphs only (no markdown)."""
        response = model.generate_content(prompt)
        out = (response.text or '').strip() or plain[:500]
        formatted = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out, flags=re.DOTALL)
        formatted = formatted.replace("\n", "<br>")
        return jsonify({'response': f"<b>Simplified ✨</b><br><br>{formatted}"})
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            return jsonify({'response': _offline_simplify(plain)})
        return jsonify({'response': f"<b>Could not simplify.</b><br>{_offline_simplify(plain)}"})


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json or {}
    user_message = (data.get('message') or '').strip()
    history = data.get('history') or []
    v = data.get('values') or {}
    ds = data.get('diseases') or []
    prob = data.get('probabilistic_analysis') or {}
    simplify = bool(data.get('simplify'))

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        msg = _rule_based_medical_chat(user_message, v, ds, prob)
        return jsonify({'response': msg})

    conv_lines = []
    for turn in history[-10:]:
        role = (turn.get('role') or 'user').strip()
        content = (turn.get('content') or '').strip()
        if not content:
            continue
        conv_lines.append(f"{role.upper()}: {content}")
    conv_block = "\n".join(conv_lines)

    ctx = json.dumps(
        {
            'values': v,
            'diseases': ds,
            'probabilistic_analysis': prob,
        },
        indent=2,
    )

    system_instructions = f"""You are a careful medical education assistant (not a licensed clinician).

CONTEXT (JSON — includes Naive Bayes risk, GMM mixture profile if labs exist, department model):
{ctx}

PRIOR CHAT:
{conv_block if conv_block else '(none)'}

USER MESSAGE:
"{user_message if user_message else 'User sent an empty message; invite them to ask a question.'}"

RULES:
1. Give clear, empathetic, evidence-informed general education only. Do not diagnose or prescribe.
2. Reference the user's parsed values / GMM / department context when relevant.
3. Use short paragraphs or bullet points. Bold key terms with **like this** (markdown).
4. If the question is not health-related, politely decline.
5. Encourage follow-up with a qualified professional for personal decisions."""
    if simplify:
        system_instructions += """

6. SIMPLE MODE ON: Use very plain language (about 8th-grade reading level). Extra-short sentences. Friendly and direct — no slang overload."""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(system_instructions)
        raw = (response.text or '').strip() or "I could not generate a reply. Please try again."
        formatted_response = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", raw, flags=re.DOTALL)
        formatted_response = formatted_response.replace("\n", "<br>")
        msg = formatted_response
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            msg = (
                "<b><i class='fa-solid fa-clock-rotate-left text-warning'></i> Rate limited:</b><br><br>"
                "Wait 30–60 seconds and try again, or use offline tips below.<br><br>"
                + _rule_based_medical_chat(user_message, v, ds, prob)
            )
        else:
            msg = f"<b>Error:</b> {error_msg}<br><br>" + _rule_based_medical_chat(user_message, v, ds, prob)

    return jsonify({'response': msg})

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        init_db()
        
    app.run(debug=True, port=5000)
