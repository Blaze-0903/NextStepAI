import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid # Import uuid at the top

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# --- CONFIGURATION FOR SKILL DEPRECIATION ---
SKILL_DEPRECIATION_RATE = 10  # How much to lower frequency if not seen
SKILL_FLAG_THRESHOLD = 100   # Frequency below which a skill is flagged for review
DATE_FLAG_THRESHOLD_DAYS = 180 # Days old after which a skill is flagged

class OntologyUpdater:
    def __init__(self):
        self.ontology_path = ROOT_DIR / 'ontology.json'
        # MongoDB connection for pending updates
        mongo_url = os.environ.get('MONGO_URL', "mongodb://localhost:27017")
        db_name = os.environ.get('DB_NAME', "test_database")
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
    def load_ontology(self):
        """Load current ontology"""
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_ontology(self, ontology):
        """Save updated ontology"""
        with open(self.ontology_path, 'w', encoding='utf-8') as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)
    
    async def simulate_job_market_scraping(self, current_ontology):
        """
        Simulates scraping job portals.
        - Discovers new skills/roles.
        - Updates frequencies of existing skills.
        - Reduces frequency of unseen skills.
        """
        print("[SIMULATED] Scraping LinkedIn, Indeed for 'Junior', 'Entry-Level' roles...")
        
        # --- 1. SIMULATE DISCOVERY OF NEW ITEMS ---
        potential_skills = [
            {
                "name": "GraphQL", "type": "Technology", "aliases": ["graph ql", "gql"],
                "learning_resources": ["https://graphql.org/learn/"],
                "discovery_reason": "Trending in 1,250 'Junior Web Developer' postings", "confidence": 0.92
            },
            {
                "name": "Terraform", "type": "Tool", "aliases": ["infrastructure as code", "iac"],
                "learning_resources": ["https://learn.hashicorp.com/terraform"],
                "discovery_reason": "Required in 68% of 'Junior DevOps' positions", "confidence": 0.95
            }
        ]
        
        potential_roles = [
            {
                "title": "Junior Data Scientist",
                "description": "Assists senior data scientists in analyzing data and building models.",
                "salary_range": [85000, 115000], "experience_level": "entry",
                "skill_weights": [
                    {"skill": "Python", "weight": 1.0, "is_core": True},
                    {"skill": "Data Analysis", "weight": 1.0, "is_core": True},
                    {"skill": "SQL", "weight": 0.7, "is_core": True}
                ],
                "discovery_reason": "High volume of 'Graduate Data Scientist' postings", "confidence": 0.91
            }
        ]
        
        # --- 2. SIMULATE MARKET FREQUENCY FOR EXISTING SKILLS ---
        # We "see" most skills, so their frequency goes up and date is updated.
        simulated_seen_skills = [
            "Python", "JavaScript", "React", "Machine Learning", "Data Analysis", "SQL",
            "Git", "Docker", "AWS", "Node.js", "TypeScript", "HTML", "CSS", "REST API",
            "MongoDB", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Kubernetes", "Java",
            "C++", "Django", "Flask", "FastAPI", "Vue.js", "Tableau", "Power BI", "Agile",
            "Communication", "Leadership", "Problem Solving", "Linux", "Network Firewalls",
            "SIEM Tools", "Intrusion Detection", "Statistics", "Excel"
        ]
        
        # We deliberately "don't see" our obsolete test skill: "Angular"
        
        print("\n--- Updating Skill Frequencies ---")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        updated_skills = current_ontology['skills']
        
        for skill_name, skill_data in updated_skills.items():
            if skill_name in simulated_seen_skills:
                # Skill was seen, increase frequency and update date
                skill_data["mention_frequency"] = skill_data.get("mention_frequency", 900) + random.randint(50, 150)
                skill_data["last_seen_in_market"] = today
            else:
                # Skill was NOT seen, depreciate its frequency
                skill_data["mention_frequency"] = max(0, skill_data.get("mention_frequency", 100) - SKILL_DEPRECIATION_RATE)
                print(f"-> Depreciating unseen skill: {skill_name}")

        # --- 3. DECIDE WHAT NEW ITEMS TO PROPOSE ---
        selected_skills = random.sample(potential_skills, 1)
        selected_roles = random.sample(potential_roles, 1)
        
        return {
            "new_skills": selected_skills,
            "new_roles": selected_roles,
            "updated_skills_ontology": updated_skills # Return the entire updated skills block
        }
    
    async def store_pending_updates(self, discoveries):
        """
        Store discovered skills/roles in DB as pending (awaiting admin approval)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for skill in discoveries['new_skills']:
            # Check if skill already exists or is pending
            existing = await self.db.pending_ontology_updates.find_one({"data.name": skill['name']})
            if not existing and skill['name'] not in self.current_ontology['skills']:
                await self.db.pending_ontology_updates.insert_one({
                    "id": str(uuid.uuid4()),
                    "type": "skill",
                    "data": skill,
                    "status": "pending",
                    "discovered_at": timestamp,
                    "reviewed_at": None,
                    "reviewed_by": None
                })
                print(f"✓ Added pending skill: {skill['name']}")
            else:
                print(f"i Skill '{skill['name']}' already exists or is pending review.")

        
        for role in discoveries['new_roles']:
            # Check if role already exists or is pending
            existing = await self.db.pending_ontology_updates.find_one({"data.title": role['title']})
            existing_in_ontology = any(r['title'] == role['title'] for r in self.current_ontology['job_roles'])
            
            if not existing and not existing_in_ontology:
                await self.db.pending_ontology_updates.insert_one({
                    "id": str(uuid.uuid4()),
                    "type": "role",
                    "data": role,
                    "status": "pending",
                    "discovered_at": timestamp,
                    "reviewed_at": None,
                    "reviewed_by": None
                })
                print(f"✓ Added pending role: {role['title']}")
            else:
                print(f"i Role '{role['title']}' already exists or is pending review.")

    async def check_for_obsolete_skills(self, updated_skills_ontology):
        """
        Check for obsolete skills and flag them for review in MongoDB.
        """
        print("\n--- Checking for Obsolete Skills ---")
        today = datetime.now(timezone.utc)
        
        for skill_name, skill_data in updated_skills_ontology.items():
            # Check 1: Low mention frequency
            if skill_data.get("mention_frequency", 1000) < SKILL_FLAG_THRESHOLD:
                flag_reason = f"Mention frequency ({skill_data.get('mention_frequency')}) is below threshold ({SKILL_FLAG_THRESHOLD})."
                print(f"! FLAGGING Obsolete Skill (Frequency): {skill_name}")
                await self.flag_skill_for_review(skill_name, flag_reason)

            # Check 2: Not seen recently
            last_seen_str = skill_data.get("last_seen_in_market", today.strftime("%Y-%m-%d"))
            last_seen_date = datetime.strptime(last_seen_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_since_seen = (today - last_seen_date).days
            
            if days_since_seen > DATE_FLAG_THRESHOLD_DAYS:
                flag_reason = f"Not seen in market for {days_since_seen} days (Threshold: {DATE_FLAG_THRESHOLD_DAYS})."
                print(f"! FLAGGING Obsolete Skill (Date): {skill_name}")
                await self.flag_skill_for_review(skill_name, flag_reason)

    async def flag_skill_for_review(self, skill_name, reason):
        """
        Adds a skill to the pending updates list for 'review_obsolete'
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check if already pending review
        existing = await self.db.pending_ontology_updates.find_one({
            "type": "review_obsolete",
            "data.name": skill_name,
            "status": "pending"
        })
        
        if not existing:
            await self.db.pending_ontology_updates.insert_one({
                "id": str(uuid.uuid4()),
                "type": "review_obsolete",
                "data": {"name": skill_name},
                "status": "pending",
                "discovery_reason": reason,
                "discovered_at": timestamp,
                "reviewed_at": None,
                "reviewed_by": None
            })
    
    async def run_weekly_update(self):
        """
        Main function to run weekly ontology update
        """
        print("\n" + "="*60)
        print("NEXTSTEAI ONTOLOGY UPDATER (v2 - Depreciation Update) - Weekly Run")
        print(f"Timestamp: {datetime.now(timezone.utc)}")
        print("="*60 + "\n")
        
        try:
            # Load current ontology
            self.current_ontology = self.load_ontology()
            
            # Simulate scraping
            discoveries = await self.simulate_job_market_scraping(self.current_ontology)
            
            # Save the updated skill frequencies back to the file
            self.current_ontology['skills'] = discoveries['updated_skills_ontology']
            self.save_ontology(self.current_ontology)
            print("\n✓ Updated skill frequencies saved to ontology.json.")
            
            # Store NEWLY discovered items for admin review
            await self.store_pending_updates(discoveries)
            
            # Check for any skills that are now obsolete
            await self.check_for_obsolete_skills(discoveries['updated_skills_ontology'])
            
            print("\n" + "="*60)
            print("✓ Update complete! Pending admin review in dashboard.")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n✗ Error during update: {str(e)}")
        finally:
            self.client.close()

if __name__ == "__main__":
    updater = OntologyUpdater()
    asyncio.run(updater.run_weekly_update())