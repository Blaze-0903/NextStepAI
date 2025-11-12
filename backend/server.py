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

# --- NEW: MongoDB Collection Names ---
SKILLS_COLLECTION = "ontology_skills"
JOBS_COLLECTION = "ontology_job_roles"
PENDING_COLLECTION = "pending_ontology_updates"
ANALYSIS_COLLECTION = "resume_analyses"

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
ontology = {"skills": {}, "job_roles": []} # Will be populated from DB
skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER") # Will be populated from DB

# --- NEW: Load ontology from MongoDB at startup ---
async def load_ontology_from_db():
    """
    Loads skills and job roles from MongoDB into the global 'ontology' var
    and builds the spaCy PhraseMatcher.
    """
    global ontology, skill_matcher
    print("Loading ontology from MongoDB Atlas...")
    
    # 1. Load Skills
    skills_cursor = db[SKILLS_COLLECTION].find({}, {"_id": 1}) # _id is the skill name
    skills_data = {}
    async for skill_doc in skills_cursor:
        # The document itself is the skill data, _id is the name
        skill_name = skill_doc['_id']
        # Fetch the full skill data (excluding _id)
        full_skill_data = await db[SKILLS_COLLECTION].find_one({"_id": skill_name}, {"_id": 0})
        skills_data[skill_name] = full_skill_data
        
    ontology['skills'] = skills_data
    
    # 2. Load Job Roles
    job_roles_cursor = db[JOBS_COLLECTION].find({}, {"_id": 0}) # Exclude mongo _id
    job_roles_list = await job_roles_cursor.to_list(length=1000)
    ontology['job_roles'] = job_roles_list

    # 3. Build Phrase Matcher
    skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = []
    
    for skill_name, skill_data in ontology['skills'].items():
        patterns.append((skill_name, [nlp(skill_name.lower())]))
        for alias in skill_data.get('aliases', []):
            patterns.append((skill_name, [nlp(alias.lower())]))
    
    for skill_name, skill_patterns in patterns:
        skill_matcher.add(skill_name, skill_patterns)
    
    logging.info(f"Loaded ontology from DB: {len(ontology['skills'])} skills and {len(ontology['job_roles'])} job roles")

@app.on_event("startup")
async def startup_event():
    """
    On server startup, load the ontology from MongoDB.
    """
    await load_ontology_from_db()

# Models (No change)
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
    decision: str
    reviewer_name: Optional[str] = "Admin"

# Helper functions (No change)
def extract_text_from_pdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_skills_from_text(text: str) -> List[str]:
    doc = nlp(text.lower())
    matches = skill_matcher(doc)
    found_skills = set()
    for match_id, start, end in matches:
        skill_name = nlp.vocab.strings[match_id]
        found_skills.add(skill_name)
    return list(found_skills)

# Scoring function (No change)
def calculate_weighted_match(user_skills: List[str], job_role: Dict) -> Dict:
    user_skills_set = set(user_skills)
    total_score = 0
    max_possible_total_score = 0
    core_score = 0
    max_possible_core_score = 0
    matching_skills = []
    missing_skills = []
    
    for skill_weight in job_role.get('skill_weights', []):
        skill_name = skill_weight['skill']
        weight = skill_weight.get('weight', 0.5)
        is_core = skill_weight.get('is_core', False)
        
        max_possible_total_score += weight
        if is_core:
            max_possible_core_score += weight
        
        if skill_name in user_skills_set:
            total_score += weight
            if is_core:
                core_score += weight
            matching_skills.append({
                "skill": skill_name,
                "weight": weight,
                "is_core": is_core
            })
        else:
            missing_skills.append({
                "skill": skill_name,
                "weight": weight,
                "is_core": is_core,
                "learning_resources": ontology['skills'].get(skill_name, {}).get('learning_resources', [])
            })
    
    total_match_percentage = (total_score / max_possible_total_score * 100) if max_possible_total_score > 0 else 0
    core_match_percentage = (core_score / max_possible_core_score * 100) if max_possible_core_score > 0 else 100
    final_blended_score = (core_match_percentage * 0.7) + (total_match_percentage * 0.3)
    
    return {
        "title": job_role['title'],
        "description": job_role.get('description', ''),
        "salary_range": job_role.get('salary_range', []),
        "experience_level": job_role.get('experience_level', 'mid'),
        "match_score": round(final_blended_score, 1),
        "core_match_score": round(core_match_percentage, 1),
        "total_match_score": round(total_match_percentage, 1),
        "matching_skills": sorted(matching_skills, key=lambda x: (x['is_core'], x['weight']), reverse=True),
        "missing_skills": sorted(missing_skills, key=lambda x: (x['is_core'], x['weight']), reverse=True)
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "NextStepAI API - Your Future, Demystified"}

# --- UPDATED: No longer needs Form(...) for experience ---
@api_router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), experience: Optional[str] = Form(None)):
    """Parse resume and analyze career paths"""
    try:
        file_bytes = await file.read()
        
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file_bytes)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF or DOCX")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        user_skills = extract_skills_from_text(text)
        
        if not user_skills:
            raise HTTPException(status_code=400, detail="No recognizable skills found in resume")
        
        # --- UPDATED: Filter logic uses in-memory ontology ---
        job_roles_to_analyze = ontology['job_roles']
        if experience:
            job_roles_to_analyze = [
                role for role in ontology['job_roles']
                if role.get('experience_level') == experience
            ]
        
        career_matches = []
        for job_role in job_roles_to_analyze:
            match_data = calculate_weighted_match(user_skills, job_role)
            career_matches.append(match_data)
        
        career_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        analysis_doc = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "user_skills": user_skills,
            "career_matches": career_matches[:10],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db[ANALYSIS_COLLECTION].insert_one(analysis_doc)
        
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
    """Get current in-memory ontology"""
    return ontology # Returns the global variable populated from DB

# Admin Login (No change)
@api_router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'nextstep2025')
    if request.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

# --- UPDATED: get_pending_updates (Simpler) ---
@api_router.get("/admin/pending-updates")
async def get_pending_updates():
    """Get ALL pending ontology updates for admin review"""
    pending = await db[PENDING_COLLECTION].find(
        {"status": "pending"},
        {"_id": 0}  # Exclude the MongoDB _id
    ).to_list(1000)
    
    return {
        "pending_updates": pending # Return a single list
    }

# --- UPDATED: review_update (Writes to DB, not file) ---
@api_router.post("/admin/review")
async def review_update(review: ReviewDecision):
    """Approve or reject a pending update and update ontology in DB"""
    try:
        pending = await db[PENDING_COLLECTION].find_one(
            {"id": review.update_id, "status": "pending"}
        )
        
        if not pending:
            raise HTTPException(status_code=404, detail="Pending update not found")
        
        if review.decision == "approve":
            data_to_add = pending['data']
            
            if pending['type'] == 'skill':
                skill_name = data_to_add['name']
                skill_data_to_insert = {
                    "_id": skill_name, # Use name as _id
                    "type": data_to_add['type'],
                    "aliases": data_to_add['aliases'],
                    "learning_resources": data_to_add['learning_resources'],
                    "mention_frequency": data_to_add.get('confidence', 0.9) * 1000, # Initial freq
                    "last_seen_in_market": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                }
                # Add to MongoDB
                await db[SKILLS_COLLECTION].replace_one(
                    {"_id": skill_name}, 
                    skill_data_to_insert, 
                    upsert=True
                )
                print(f"Admin approved skill: {skill_name}")
                
            elif pending['type'] == 'role':
                # Add to MongoDB
                await db[JOBS_COLLECTION].insert_one(data_to_add)
                print(f"Admin approved role: {data_to_add['title']}")
            
            # 3. Reload ontology and matcher from DB
            await load_ontology_from_db()
            print(f"Ontology reloaded from DB. Skill matcher updated.")
        
        # 4. Update status in DB
        await db[PENDING_COLLECTION].update_one(
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

# Trigger Updater (No change)
@api_router.post("/trigger-ontology-update")
async def trigger_ontology_update():
    try:
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

# CORS Middleware (No change)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging (No change)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()