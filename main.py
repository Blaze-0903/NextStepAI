import json
import spacy
from spacy.matcher import PhraseMatcher
import fitz  # PyMuPDF

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def read_pdf_resume(filepath):
    """Extracts text from a PDF file."""
    try:
        with fitz.open(filepath) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None

def load_ontology(filepath="ontology.json"):
    # ... (this function remains the same)
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None

def create_skill_matcher(skills_data):
    # ... (this function remains the same)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for skill_name, skill_info in skills_data.items():
        patterns = [nlp.make_doc(skill_name)]
        for alias in skill_info.get("aliases", []):
            patterns.append(nlp.make_doc(alias))
        matcher.add(skill_name, patterns)
    return matcher

def intelligent_skill_extractor(resume_text, matcher):
    # ... (this function remains the same)
    doc = nlp(resume_text)
    matches = matcher(doc)
    found_skills = set()
    for match_id, start, end in matches:
        skill_name = nlp.vocab.strings[match_id]
        found_skills.add(skill_name)
    return list(found_skills)

def calculate_match_scores(user_skills, job_roles):
    # ... (this function remains the same)
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

# --- Main execution block ---
if __name__ == "__main__":
    print("--- 🚀 Starting NextStepAI 🚀 ---")
    our_ontology = load_ontology()

    if our_ontology:
        skills_data = our_ontology.get('skills', {})
        job_roles_data = our_ontology.get('job_roles', [])
        skill_matcher = create_skill_matcher(skills_data)

        # --- NEW: Read from PDF instead of a string ---
        resume_text = read_pdf_resume("sample_resume.pdf")

        if resume_text:
            print(f"\n📄 Analyzing Resume: sample_resume.pdf...\n--------------------")
            extracted_skills = intelligent_skill_extractor(resume_text, skill_matcher)
            print(f"✅ Skills extracted: {extracted_skills}")

            print(f"\n🧠 Generating Job Recommendations...\n--------------------")
            job_recommendations = calculate_match_scores(extracted_skills, job_roles_data)

            for reco in job_recommendations:
                print(f"\nJob Title: {reco['title']}")
                print(f"Match Score: {reco['score']:.2f}%")
                print(f"✅ Matching Skills: {reco['matching_skills']}")
                print(f"📚 Missing Skills to Learn: {reco['missing_skills']}")

    print("\n--- ✅ Program Finished ---")