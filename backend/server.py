from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone
import json
import fitz  # PyMuPDF
from docx import Document
import spacy
from spacy.matcher import PhraseMatcher
import io
import subprocess

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Global variables for ontology
ontology = {}
skill_matcher = None

# Load ontology at startup
def load_ontology():
    global ontology, skill_matcher
    ontology_path = ROOT_DIR / 'ontology.json'
    with open(ontology_path, 'r') as f:
        ontology = json.load(f)
    
    # Build phrase matcher for skill extraction
    skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = []
    
    for skill_name, skill_data in ontology['skills'].items():
        # Add main skill name
        patterns.append((skill_name, [nlp(skill_name.lower())]))
        # Add aliases
        for alias in skill_data.get('aliases', []):
            patterns.append((skill_name, [nlp(alias.lower())]))
    
    for skill_name, skill_patterns in patterns:
        skill_matcher.add(skill_name, skill_patterns)
    
    logging.info(f"Loaded ontology with {len(ontology['skills'])} skills and {len(ontology['job_roles'])} job roles")

@app.on_event("startup")
async def startup_event():
    load_ontology()

# Models
class SkillAnalysis(BaseModel):
    user_skills: List[str]
    career_matches: List[Dict]
    timestamp: str

class AdminLoginRequest(BaseModel):
    password: str

class PendingUpdate(BaseModel):
    id: str
    type: str
    data: Dict
    status: str
    discovered_at: str
    discovery_reason: Optional[str] = None
    confidence: Optional[float] = None

class ReviewDecision(BaseModel):
    update_id: str
    decision: str  # "approve" or "reject"
    reviewer_name: Optional[str] = "Admin"

# Helper functions
def extract_text_from_pdf(file_bytes):
    """Extract text from PDF using PyMuPDF"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX using python-docx"""
    doc = Document(io.BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills using spaCy PhraseMatcher"""
    doc = nlp(text.lower())
    matches = skill_matcher(doc)
    
    # Get unique skill names
    found_skills = set()
    for match_id, start, end in matches:
        skill_name = nlp.vocab.strings[match_id]
        found_skills.add(skill_name)
    
    return list(found_skills)

def calculate_weighted_match(user_skills: List[str], job_role: Dict) -> Dict:
    """
    Calculate weighted match, core skill match, and total match for a job role.
    """
    user_skills_set = set(user_skills)
    
    total_score = 0
    max_possible_total_score = 0
    
    core_score = 0
    max_possible_core_score = 0
    
    matching_skills = []
    missing_skills = []
    
    for skill_weight in job_role.get('skill_weights', []):
        skill_name = skill_weight['skill']
        weight = skill_weight.get('weight', 0.5) # Default weight if missing
        is_core = skill_weight.get('is_core', False) # Default to false
        
        # Add to max possible scores
        max_possible_total_score += weight
        if is_core:
            max_possible_core_score += weight
        
        if skill_name in user_skills_set:
            # Add to user's achieved scores
            total_score += weight
            if is_core:
                core_score += weight
                
            matching_skills.append({
                "skill": skill_name,
                "weight": weight,
                "is_core": is_core
            })
        else:
            # Add to missing skills
            missing_skills.append({
                "skill": skill_name,
                "weight": weight,
                "is_core": is_core,
                "learning_resources": ontology['skills'].get(skill_name, {}).get('learning_resources', [])
            })
    
    # Calculate percentages
    total_match_percentage = (total_score / max_possible_total_score * 100) if max_possible_total_score > 0 else 0
    core_match_percentage = (core_score / max_possible_core_score * 100) if max_possible_core_score > 0 else 100 # If no core skills, 100%
    
    # Blended score to prioritize core skills
    # 70% Core Score, 30% Total Score
    final_blended_score = (core_match_percentage * 0.7) + (total_match_percentage * 0.3)
    
    return {
        "title": job_role['title'],
        "description": job_role.get('description', ''),
        "salary_range": job_role.get('salary_range', []),
        "experience_level": job_role.get('experience_level', 'mid'), # Add experience level
        "match_score": round(final_blended_score, 1), # Use the new blended score for ranking
        "core_match_score": round(core_match_percentage, 1),
        "total_match_score": round(total_match_percentage, 1),
        "matching_skills": sorted(matching_skills, key=lambda x: (x['is_core'], x['weight']), reverse=True),
        "missing_skills": sorted(missing_skills, key=lambda x: (x['is_core'], x['weight']), reverse=True)
    }
# API Routes
@api_router.get("/")
async def root():
    return {"message": "NextStepAI API - Your Future, Demystified"}

@api_router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), experience: Optional[str] = Form(None)):
    """Parse resume and analyze career paths"""
    try:
        # Read file
        file_bytes = await file.read()
        
        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file_bytes)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF or DOCX")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Extract skills
        user_skills = extract_skills_from_text(text)
        
        if not user_skills:
            raise HTTPException(status_code=400, detail="No recognizable skills found in resume")
        
        # Calculate matches for all job roles
        # Filter job roles based on experience, if provided
        job_roles_to_analyze = ontology['job_roles']
        if experience:
            job_roles_to_analyze = [
                role for role in ontology['job_roles']
                if role.get('experience_level') == experience
            ]
        
        # Calculate matches for all job roles
        career_matches = []
        for job_role in job_roles_to_analyze:
            match_data = calculate_weighted_match(user_skills, job_role)
            career_matches.append(match_data)
        
        # Sort by match score
        career_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Store analysis in DB
        analysis_doc = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "user_skills": user_skills,
            "career_matches": career_matches[:10],  # Top 10
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db.resume_analyses.insert_one(analysis_doc)
        
        return {
            "success": True,
            "user_skills": user_skills,
            "career_matches": career_matches[:10],
            "analysis_id": analysis_doc['id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error analyzing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@api_router.get("/ontology")
async def get_ontology():
    """Get current ontology"""
    return ontology

@api_router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Simple password check for admin dashboard"""
    # Simple password protection (in production, use proper auth)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'nextstep2025')
    
    if request.password == ADMIN_PASSWORD:
        return {
            "success": True,
            "message": "Login successful"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

@api_router.get("/admin/pending-updates")
async def get_pending_updates():
    """Get ALL pending ontology updates for admin review"""
    pending = await db.pending_ontology_updates.find(
        {"status": "pending"},
        {"_id": 0}  # Exclude the MongoDB _id
    ).to_list(100)
    
    # Add our string 'id' field if it's missing (for older docs)
    for item in pending:
        if 'id' not in item and '_id' in item:
            item['id'] = str(item['_id'])
        
        # Clean up _id if it's still there
        if '_id' in item:
            del item['_id']
    
    return {
        "pending_updates": pending # Return a single list
    }

@api_router.post("/admin/review")
async def review_update(review: ReviewDecision):
    """Approve or reject a pending update and update ontology.json"""
    try:
        # Find the pending update by id field (not _id)
        pending = await db.pending_ontology_updates.find_one(
            {"id": review.update_id, "status": "pending"}
        )
        
        if not pending:
            raise HTTPException(status_code=404, detail="Pending update not found")
        
        if review.decision == "approve":
            # --- BEGIN NEW LOGIC ---
            # 1. Add to the live ontology variable
            data_to_add = pending['data']
            
            if pending['type'] == 'skill':
                skill_name = data_to_add['name']
                # Add skill (without 'name' key, as 'name' is the dictionary key)
                ontology['skills'][skill_name] = {
                    "type": data_to_add['type'],
                    "aliases": data_to_add['aliases'],
                    "learning_resources": data_to_add['learning_resources']
                }
                print(f"Admin approved skill: {skill_name}")
                
            elif pending['type'] == 'role':
                # Add the full job role object
                ontology['job_roles'].append(data_to_add)
                print(f"Admin approved role: {data_to_add['title']}")

            # 2. Save updated ontology back to ontology.json file
            ontology_path = ROOT_DIR / 'ontology.json'
            with open(ontology_path, 'w', encoding='utf-8') as f:
                json.dump(ontology, f, indent=2, ensure_ascii=False)
            
            # 3. Reload the spaCy matcher with the new skills
            load_ontology()
            print(f"Ontology reloaded. Skill matcher updated.")
            # --- END NEW LOGIC ---
        
        # 4. Update status in DB
        await db.pending_ontology_updates.update_one(
            {"id": review.update_id},
            {
                "$set": {
                    "status": review.decision,
                    "reviewed_at": datetime.now(timezone.utc).isoformat(),
                    "reviewed_by": review.reviewer_name
                }
            }
        )
        
        return {
            "success": True,
            "message": f"Update {review.decision}ed successfully and ontology has been updated."
        }
        
    except Exception as e:
        logging.error(f"Error reviewing update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trigger-ontology-update")
async def trigger_ontology_update():
    """Manually trigger the simulated weekly ontology update"""
    try:
        # Run the updater script
        result = subprocess.run(
            ['python', str(ROOT_DIR / 'ontology_updater.py')],
            capture_output=True,
            text=True
        )
        
        return {
            "success": True,
            "message": "Ontology update triggered",
            "output": result.stdout
        }
    except Exception as e:
        logging.error(f"Error triggering update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
