# FMS Smart Coach – Squat Pattern AI Coach 🏋️‍♂️

An AI-powered corrective exercise recommendation system based on the **Functional Movement Screen (FMS)**. 

Currently focused on the **Overhead Squat** pattern, this system uses **Retrieval-Augmented Generation (RAG)** with a custom exercise knowledge base and the Groq LLM to analyze user movement faults and generate personalized workout plans.

---

## 🚀 Project Overview

The FMS Smart Coach is designed to assist strength coaches and athletes by automating the analysis of movement screens.

It takes granular input regarding movement faults, automatically calculates official FMS scores, and uses a RAG pipeline to retrieve corrective exercises. The system then generates a cohesive, personalized workout plan using Large Language Models, ensuring the advice is grounded in verified progression logic rather than generic generation.

---

## 🧠 Architecture

The system follows a specific clinical logic combined with Generative AI:

1.  **Input Analysis:** User inputs binary sub-faults (e.g., "heels lift," "knee valgus") via the UI.
2.  **Auto-Scoring:** The system calculates the FMS score (0–3) and determines the training phase (Corrective → Strength → Power).
3.  **Retrieval:** Relevant exercises are fetched from a JSON knowledge base using tag-matching based on the specific faults.
4.  **Generation:** Groq (Llama 3.3 70B) generates a workout plan with specific "Coach Tips" addressing the user's unique biomechanical issues.
5.  **Storage:** All assessments and generated plans are persisted in PostgreSQL.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy (AsyncPG)
- **Database:** PostgreSQL (Neon)
- **AI/LLM:** Groq (Llama 3.3 70B Versatile)
- **RAG:** Custom JSON Knowledge Base, Tag-based Retrieval
- **Frontend:** Streamlit
- **Evaluation:** DeepEval + Custom Groq Judge
- **Ingestion:** Pandas + Openpyxl (Excel → JSON)

---

## 📂 Project Structure

```text
root/
├── data/
│   ├── raw/
│   │   └── SQUAT (PROGRESSION).xlsx          # Source exercise progressions
│   └── processed/
│       └── exercise_knowledge_base.json      # Ingested exercise data
├── src/
│   ├── logic/
│   │   └── fms_analyzer.py                   # FMS scoring & traffic light logic
│   ├── rag/
│   │   ├── retriever.py                      # Fault → tag → exercise retrieval
│   │   └── generator.py                      # Groq LLM plan generation
│   └── database.py                           # SQLAlchemy models & engine
├── init_db.py                                # Database initialization script
├── groq_judge.py                             # DeepEval custom judge (Groq)
├── test_pipeline.py                          # Evaluation on real DB profiles
├── main.py                                   # FastAPI backend server
├── frontend_demo.py                          # Streamlit User Interface
├── .env                                      # Secrets (DATABASE_URL, API_KEY)
├── requirements.txt                          # Project dependencies
└── README.md
```

---

## 🔑 Environment Variables Setup

This project requires external API keys to run.

**1. Create a `.env` file (local only)** inside the root directory:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CONFIDENT_API_KEY=confident_us_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **Note:** The `.env` file is excluded from version control and should never be pushed to GitHub.

---

## ▶️ Running the Project

**1. Clone the repository**
```bash
git clone [https://github.com/BluvernHQ/fitai.git](https://github.com/BluvernHQ/fitai.git)
cd fitai
```

**2. Set up virtual environment**
```bash 
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Initialize the Database**

> Run this script once to create the necessary tables in PostgreSQL (AssessmentInputs, AssessmentScores).

```base
python init_db.py
```

**5. Start the Backend Server**
```bash
uvicorn main:app --reload
```
> API Docs available at: http://127.0.0.1:8000/docs

**6. Run the Frontend**
```bash
streamlit run frontend_demo.py
```
> Access the UI at: http://localhost:8501

---

## 🧪 Evaluation

To run the evaluation pipeline on real database profiles using the custom Groq Judge:

```bash
python test_pipeline.py
```

## 🚧 Current Status & Branches

Main Branch: Stable release.

Active Development: squat-new branch (contains latest retrieval logic).

---

## 👤 Author

**Moniha P S**<br>
Bluvern</br>