# NextStepAI: AI-Powered Career Roadmap 🚀

[![Frontend Deployment](https://img.shields.io/badge/Frontend-Live%20on%20Vercel-black?style=for-the-badge&logo=vercel)](https://next-step-ai-tan.vercel.app)
[![Backend Deployment](https://img.shields.io/badge/Backend-Live%20on%20Render-blue?style=for-the-badge&logo=render)](https://nextstepai-backend.onrender.com)
[![Tech Stack](https://img.shields.io/badge/Stack-Full%20Stack-brightgreen?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiA3djEwbDEwIDV6IiBmaWxsPSIjMDBCN0IwIi8+PHBhdGggZD0iTTEyIDJMMjIgN3YxMGwtMTAgNXoiIGZpbGw9IiMwMEQzODUiLz48cGF0aCBkPSJNMjIgN0wxMiAxMmwyLTMtMi0zIDEwLTZ6IiBmaWxsPSIjMDBCN0IwIi8+PHBhdGggZD0iTTIgN2wxMCA1bC0yIDMtMiAzTDIgN3oiIGZpbGw9IiMwMEQzODUiLz48cGF0aCBkPSJNMiAxN2wxMCA1IDEwLTUgMi0zLTIgM3YtN2wtMTAgNS0xMC01eiIgZmlsbD0iIzAwNUI2MSIvPjxwYXRoIGQ9Ik0xMiAxMmwxMCA1djIuOWwtMiAxLjFMMTIgMTJ6IiBmaWxsPSIjMDBCN0IwIi8+PHBhdGggZD0iTTEyIDEybC0xMC01di0yLjlsMi0xLjFMMTIgMTJ6IiBmaWxsPSIjMDBCN0IwIi8+PC9zdmc+)](httpsax://github.com/Blaze-0903/NextStepAI)

**NextStepAI** is an intelligent, full-stack application that transforms a user's resume into a personalized, actionable career roadmap. It moves beyond simple keyword matching to provide a deep, weighted skill-gap analysis, targeting early-career professionals and "freshers."

**Live Links:**
* **Frontend App:** [**https://next-step-ai-tan.vercel.app**](https://next-step-ai-tan.vercel.app)
* **Backend API:** [**https://nextstepai-backend.onrender.com**](https://nextstepai-backend.onrender.com)

---

### 🌟 Core Features

This project provides a complete, end-to-end solution for modern career guidance.

[--- PASTE A SCREENSHOT OF YOUR 'RESULTSDASHBOARD.JS' PAGE HERE ---]
*(Placeholder: A screenshot showing the Career Roadmap graph and the Job Cards with "Learn Now" links.)*

* **Multi-Format Resume Parsing:** Accepts and parses both `.pdf` (using PyMuPDF) and `.docx` (using `python-docx`) files.
* **Advanced NLP Skill Extraction:** Uses `spaCy`'s `PhraseMatcher` to read unstructured text and accurately identify a user's skills from a knowledge base of 39+ skills and their aliases.
* **Weighted, Core-Skill Scoring:** Our main innovation. The system doesn't just *count* skills; it *weighs* them. It calculates a blended score based on "Core" (must-have) vs. "Complementary" (nice-to-have) skills, providing a far more accurate match for freshers.
* **Actionable Upskilling:** Automatically provides direct "Learn Now" links for every skill a user is missing for a recommended job.
* **Dynamic "Ever-Learning" Ontology:**
    * A backend script (`ontology_updater.py`) simulates market analysis to find new, trending skills and flag obsolete ones.
    * These suggestions are stored in a MongoDB "pending" queue.
* **Human-in-the-Loop Admin Dashboard:** A secure `/admin` route where an administrator can log in, view pending skills, and "Approve" or "Reject" them, which instantly updates the live ontology in the cloud.

[--- PASTE A SCREENSHOT OF YOUR 'ADMINDASHBOARD.JS' PAGE HERE ---]
*(Placeholder: A screenshot showing the Admin Dashboard with "Pending Skills," "Pending Roles," and "Obsolete Skills" cards.)*

---

### 🛠️ Tech Stack

This project is a "stateless" full-stack application deployed on modern cloud platforms.

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React | Building the interactive user interface. |
| | `shadcn/ui` & Tailwind | For a professional, aesthetic, and responsive component-based design. |
| | React Flow | For the interactive "Career Roadmap" visualizer. |
| | Vercel | For continuous deployment and hosting of the frontend. |
| **Backend** | Python 3.11 | Core programming language. |
| | FastAPI & Uvicorn | For a high-performance, asynchronous API server. |
| | `spaCy` | For fast and accurate NLP `PhraseMatcher` skill extraction. |
| | Render | For hosting the "stateless" backend web service. |
| **Database** | MongoDB Atlas | Cloud-hosted NoSQL database for the *entire* ontology (skills, jobs, pending updates). |
| **Parsing** | PyMuPDF, `python-docx`| For reading `.pdf` and `.docx` files. |

---

### 🏃‍♂️ How to Run This Project Locally

To get this project running on your local machine, you need to run three separate services: **MongoDB**, the **Backend**, and the **Frontend**.

#### 1. Database (MongoDB)
* **Local:** Install [MongoDB Community Server](https://www.mongodb.com/try/download/community) and have it running in the background on its default port (`mongodb://localhost:27017`).
* **Recommended (Cloud):** You can also use a free MongoDB Atlas cluster. Just create one and get the connection string (URI).

#### 2. Backend (Python/FastAPI)
```bash
# 1. Navigate to the 'backend' folder
cd backend

# 2. Create a Python virtual environment
python -m venv venv

# 3. Activate it
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Set up your Environment Variables
# Create a file named '.env' in the 'backend' folder
# Add your database URI and a password
MONGO_URL="mongodb://localhost:27017"
DB_NAME="nextstep_db"
ADMIN_PASSWORD="your_secret_password"
CORS_ORIGINS="*"

# 6. (One-Time Setup) Upload the ontology to your database
# This script reads 'ontology.json' and uploads it to your MongoDB
python upload_ontology.py

# 7. Run the server
uvicorn server:app --reload
