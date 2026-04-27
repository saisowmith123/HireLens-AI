from flask import Flask, render_template, request, jsonify, session
from resume_parser import extract_text
from gemini_utils import analyze_resume_jobdesc, gemini_chat
import uuid
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        resume_file = request.files['resume']
        jd_file = request.files['jobdesc']

        resume_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
        jd_path = os.path.join(UPLOAD_FOLDER, jd_file.filename)

        resume_file.save(resume_path)
        jd_file.save(jd_path)

        resume_text = extract_text(resume_path)
        jd_text = extract_text(jd_path)

        result = analyze_resume_jobdesc(resume_text, jd_text)

        session['chat_id'] = str(uuid.uuid4())
        session['resume_text'] = resume_text
        session['jd_text'] = jd_text

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "score": 0,
            "resume_skills": [],
            "jd_skills": [],
            "missing_skills": [],
            "improvements": [],
            "summary": f"Server error: {str(e)}"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        response = gemini_chat(session.get('resume_text', ''), session.get('jd_text', ''), user_message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f"Chat error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
