import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# --- IMPORTANT: SET UP YOUR .env FILE ---
# Make sure your backend/.env file contains the
# correct MONGO_URL (your Atlas string) and DB_NAME.
#
# MONGO_URL="mongodb+srv://sujalrjunghare_db_user:..."
# DB_NAME="nextstep_db"
# ------------------------------------------

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# New Collection Names
SKILLS_COLLECTION = "ontology_skills"
JOBS_COLLECTION = "ontology_job_roles"
ONTOLOGY_FILE = ROOT_DIR / 'ontology.json'

async def migrate_ontology():
    """
    Uploads the contents of ontology.json to MongoDB Atlas.
    This is a one-time migration script.
    """
    print("--- Starting Ontology Migration to MongoDB Atlas ---")
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME')
    
    if not mongo_url or not db_name:
        print("❌ ERROR: MONGO_URL or DB_NAME not found in .env file.")
        return

    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        print(f"✓ Connected to MongoDB Atlas, database: '{db_name}'")
    except Exception as e:
        print(f"❌ ERROR: Could not connect to MongoDB. Check your MONGO_URL.")
        print(e)
        return

    # Load ontology.json
    try:
        with open(ONTOLOGY_FILE, 'r', encoding='utf-8') as f:
            ontology = json.load(f)
        skills = ontology.get('skills', {})
        job_roles = ontology.get('job_roles', [])
        print(f"✓ Loaded ontology.json with {len(skills)} skills and {len(job_roles)} job roles.")
    except Exception as e:
        print(f"❌ ERROR: Could not read ontology.json file.")
        print(e)
        client.close()
        return

    # --- 1. Migrate Skills ---
    try:
        skills_collection = db[SKILLS_COLLECTION]
        # Clear old data first
        await skills_collection.delete_many({})
        print(f"i Cleared old data from '{SKILLS_COLLECTION}' collection.")
        
        # We must convert the skills dictionary to a list of documents
        # We will use the skill name as the '_id' for easy lookup
        skill_documents = []
        for skill_name, data in skills.items():
            data['_id'] = skill_name # Use the skill name as the unique ID
            skill_documents.append(data)
            
        if skill_documents:
            await skills_collection.insert_many(skill_documents)
            print(f"✓ Successfully uploaded {len(skill_documents)} skills to '{SKILLS_COLLECTION}'.")
        else:
            print("! No skills found to upload.")

    except Exception as e:
        print(f"❌ ERROR: Failed to upload skills to MongoDB.")
        print(e)
        client.close()
        return

    # --- 2. Migrate Job Roles ---
    try:
        jobs_collection = db[JOBS_COLLECTION]
        # Clear old data first
        await jobs_collection.delete_many({})
        print(f"i Cleared old data from '{JOBS_COLLECTION}' collection.")
        
        if job_roles:
            await jobs_collection.insert_many(job_roles)
            print(f"✓ Successfully uploaded {len(job_roles)} job roles to '{JOBS_COLLECTION}'.")
        else:
            print("! No job roles found to upload.")

    except Exception as e:
        print(f"❌ ERROR: Failed to upload job roles to MongoDB.")
        print(e)
        client.close()
        return

    print("\n--- ✅ MIGRATION COMPLETE ---")
    print("Your ontology is now in MongoDB Atlas.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_ontology())