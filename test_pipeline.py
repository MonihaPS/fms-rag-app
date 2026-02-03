import pytest
import json
import time
import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# DeepEval Imports
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, GEval

# Import Custom Judge
from groq_judge import GroqJudge

# Import RAG Logic
try:
    from src.rag.retriever import get_exercises_by_profile
    from src.rag.generator import generate_workout_plan
except ImportError:
    print("❌ ERROR: Could not find 'src' folder.")
    exit()

# 1. Setup
load_dotenv()

# Initialize Groq Judge (Llama 3.3)
# Make sure GROQ_API_KEY is in your .env file
groq_evaluator = GroqJudge(model="llama-3.3-70b-versatile")

# 2. Connect to Database (Simple Fetch)
def get_latest_inputs(limit=5):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env")
        
    # Fix for SQLAlchemy URL if needed
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    if "postgres://" in db_url:
        db_url = db_url.replace("postgres://", "postgresql://")
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Simply get the latest 'limit' records. No complex offsets.
        query = text("""
            SELECT id, raw_json_data 
            FROM assessment_inputs 
            ORDER BY created_at DESC 
            LIMIT :limit
        """)
        result = conn.execute(query, {"limit": limit})
        return result.fetchall()

# 3. Define Metric (No Pain Logic)
squat_correctness = GEval(
    name="Squat RAG Correctness",
    criteria="""Evaluate the workout plan compliance:
    1. SCORING LOGIC:
       - Score 1: Focus on "Corrective" or "Regression". Low intensity.
       - Score 2: Focus on "Progression" or moderate intensity.
       - Score 3: Focus on "Performance" or high intensity.
    2. RELEVANCE: Exercises must be relevant to the user's movement capability.
    3. SAFETY: Ensure exercises match the user's score level.
    """,
    evaluation_steps=[
        "Identify the squat score in the input.",
        "Does the workout intensity/level match that score?",
        "Are the exercises relevant?"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model=groq_evaluator, # Using Groq Judge
    async_mode=False
)

# 4. Main Test Function
async def test_all_users():
    print("🚀 Starting Evaluation (Latest 5 Users)...")

    # A. Get Data
    rows = get_latest_inputs(limit=5)
    
    if not rows:
        print("✅ No users found in database.")
        return

    # B. Process One by One
    for row in rows:
        try:
            # Parse Profile
            if isinstance(row.raw_json_data, str):
                profile = json.loads(row.raw_json_data)
            else:
                profile = row.raw_json_data
            
            print(f"\n   🔄 Processing User ID {row.id}...")

            # --- 1. Run RAG ---
            retrieval_output = await get_exercises_by_profile(profile)
            retrieved_data = retrieval_output.get('data', [])
            analysis = retrieval_output.get('analysis', {})
            
            # Format Context
            retrieval_context = [
                f"{ex.get('exercise_name', 'Unknown')}: {ex.get('description', '')}" 
                for ex in retrieved_data
            ]
            
            # Generate Plan
            if asyncio.iscoroutinefunction(generate_workout_plan):
                plan_output = await generate_workout_plan(analysis, retrieved_data)
            else:
                plan_output = generate_workout_plan(analysis, retrieved_data)
            
            actual_output_text = json.dumps(plan_output, indent=2)

            # --- 2. Create Test Case ---
            test_case = LLMTestCase(
                input=f"User Profile: {json.dumps(profile)}",
                actual_output=actual_output_text,
                retrieval_context=retrieval_context
            )

            # --- 3. Evaluate (One by One) ---
            # We explicitly recreate metrics to prevent state issues
            faithfulness = FaithfulnessMetric(
                threshold=0.9, 
                model=groq_evaluator, 
                include_reason=True, 
                async_mode=False
            )
            relevancy = AnswerRelevancyMetric(
                threshold=0.9, 
                model=groq_evaluator, 
                include_reason=True, 
                async_mode=False
            )

            # Run evaluation
            evaluate([test_case], metrics=[faithfulness, relevancy, squat_correctness])
            
            print("   ✅ Done. Moving to next user...")
            time.sleep(1) # Brief pause

        except Exception as e:
            print(f"⚠️ Error processing row {row.id}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(test_all_users())