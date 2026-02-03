# FMS Smart Coach – Squat Pattern AI Coach

AI-powered corrective exercise recommendation system based on **Functional Movement Screen (FMS)** — currently focused on the **Overhead Squat** pattern.

Uses **Retrieval-Augmented Generation (RAG)** with a custom exercise knowledge base + Groq LLM to analyze user movement faults and generate personalized workout plans.

## Current Features

- Detailed input for Overhead Squat faults (trunk, lower limb, feet, upper body)
- Automatic FMS score calculation (0–3) from binary sub-fault checkboxes
- Traffic-light progression logic (corrective → strength → power)
- Tag-based retrieval from squat progression knowledge base (JSON)
- Groq Llama 3.3 70B-powered workout generation with fault-specific coach tips
- Stores every assessment + generated plan in PostgreSQL (Neon)
- Real-user evaluation pipeline using **DeepEval + custom Groq Judge**
- FastAPI backend + Streamlit frontend for input & visualization

## Project Structure
├── data/
│   ├── raw/
│   │   └── SQUAT (PROGRESSION).xlsx          # Source exercise progressions
│   └── processed/
│       └── exercise_knowledge_base.json      # Ingested exercise data
├── src/
│   ├── logic/
│   │   └── fms_analyzer.py                   # FMS scoring & traffic light
│   ├── rag/
│   │   ├── retriever.py                      # Fault → tag → exercise retrieval
│   │   └── generator.py                      # Groq LLM plan generation
│   └── database.py                           # SQLAlchemy models & engine
├── groq_judge.py                             # DeepEval custom judge (Groq)
├── test_pipeline.py                          # Evaluation on real DB profiles
├── init_db.py                                # One-time script to create database tables
├── main.py                                   # FastAPI backend
├── frontend_demo.py                          # Streamlit UI
├── .env                                      # Secrets (DATABASE_URL, GROQ_API_KEY, CONFIDENT_API_KEY)
├── requirements.txt
└── README.md
text### 

init_db.py – Database Initialization

This small script creates all necessary tables in your PostgreSQL database the first time you run the project.

```bash
python init_db.py
It uses your src/database.py models to automatically create:

assessment_inputs (raw user FMS profiles)
assessment_scores (calculated scores + generated workout JSON)

You only need to run it once (or whenever you add new models/tables).
The FastAPI server will not auto-create tables on startup — you must run this script manually first.
Tech Stack

Backend — FastAPI + SQLAlchemy (asyncpg) + PostgreSQL (Neon)
RAG — Custom JSON knowledge base + tag-based retrieval
LLM — Groq (Llama 3.3 70B Versatile)
Evaluation — DeepEval + Groq-powered judge
Frontend — Streamlit
Ingestion — Pandas + Openpyxl (Excel → JSON)

Quick Start
1. Clone the repo
Bashgit clone https://github.com/BluvernHQ/fitai.git
cd fitai
2. Set up virtual environment
Bashpython -m venv venv
.\venv\Scripts\activate        # Windows
# or
source venv/bin/activate       # Linux/Mac
3. Install dependencies
Bashpip install -r requirements.txt
4. Configure environment variables (.env)
Create .env file in root:
envDATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Optional: OPENAI_API_KEY=sk-... (used by some DeepEval metrics)
5. Initialize the database (run once)
Bashpython init_db.py
You should see:
text⏳ Connecting to Database...
✅ Success! Tables created.
6. Run the backend
Bashuvicorn main:app --reload
API: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs
7. Run the Streamlit frontend
Bashstreamlit run frontend_demo.py
Open: http://localhost:8501
Fill in squat faults → get personalized workout plan
8. Run evaluation on real database profiles
Bashpython test_pipeline.py
Evaluates latest user profiles from database using Groq-powered judge.
Current Status

Fully working for Overhead Squat pattern only
Automatic fault detection → tag matching → exercise retrieval
Personalized plans with fault-specific coach tips
Every assessment + plan saved in database
Real-data evaluation pipeline (batched)

Active Development Branch
All current work is happening on:
squat-new: https://github.com/BluvernHQ/fitai/tree/squat-new
main branch is kept stable and unchanged.
text