from flask import Flask, render_template, request
import json
import spacy
from spacy.matcher import PhraseMatcher
import fitz  # PyMuPDF
import os

# --- Initialize Flask App and spaCy Model ---
app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# --- All our backend functions from main.py ---
def read_pdf_resume(file_stream):
    try:
        text = ""
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def load_ontology(filepath="ontology.json"):
    with open(filepath, 'r') as file:
        return json.load(file)

def create_skill_matcher(skills_data):
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for skill_name, skill_info in skills_data.items():
        patterns = [nlp.make_doc(skill_name)]
        for alias in skill_info.get("aliases", []):
            patterns.append(nlp.make_doc(alias))
        matcher.add(skill_name, patterns)
    return matcher

def intelligent_skill_extractor(resume_text, matcher):
    doc = nlp(resume_text)
    matches = matcher(doc)
    found_skills = set()
    for match_id, start, end in matches:
        skill_name = nlp.vocab.strings[match_id]
        found_skills.add(skill_name)
    return list(found_skills)

def calculate_match_scores(user_skills, job_roles):
    recommendations = []
    user_skills_set = set(s.lower() for s in user_skills)
    for role in job_roles:
        required_skills_set = set(s.lower() for s in role['required_skills'])
        matching_skills = user_skills_set.intersection(required_skills_set)
        missing_skills = required_skills_set - user_skills_set
        score = (len(matching_skills) / len(required_skills_set)) * 100 if required_skills_set else 0
        recommendations.append({
            "title": role['title'], "score": score,
            "matching_skills": list(matching_skills), "missing_skills": list(missing_skills)
        })
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations

# --- Load Ontology and create Matcher on startup ---
our_ontology = load_ontology()
skills_data = our_ontology.get('skills', {})
job_roles_data = our_ontology.get('job_roles', [])
skill_matcher = create_skill_matcher(skills_data)


# --- Flask Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return "No file part"
    
    resume_file = request.files['resume']
    
    if resume_file.filename == '':
        return "No selected file"

    if resume_file:
        resume_text = read_pdf_resume(resume_file)
        extracted_skills = intelligent_skill_extractor(resume_text, skill_matcher)
        job_recommendations = calculate_match_scores(extracted_skills, job_roles_data)
        
        return render_template('results.html', skills=extracted_skills, recommendations=job_recommendations)

if __name__ == '__main__':
    app.run(debug=True)