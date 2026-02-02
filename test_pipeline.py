import json
import asyncio
import os
from typing import List, Dict
import asyncpg
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# ── CONFIG ────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")  # must be in .env
API_ENDPOINT = "http://127.0.0.1:8000/generate-workout"

BATCH_SIZE = 5
SKIP_FIRST_N = 13           # <--- we skip the first 13 newest records
MAX_PROFILES_TO_TEST = 5  # safety limit after skipping

# ────────────────────────────────────────────────
# Fetch real profiles — skipping the first N newest
# ────────────────────────────────────────────────
async def fetch_real_profiles(skip: int = SKIP_FIRST_N, limit: int = MAX_PROFILES_TO_TEST) -> List[Dict]:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Skip the newest skip records, then take the next limit records
        rows = await conn.fetch("""
            SELECT id, created_at, raw_json_data
            FROM assessment_inputs
            ORDER BY created_at DESC
            OFFSET $1
            LIMIT $2
        """, skip, limit)
        
        profiles = []
        for row in rows:
            try:
                data = {
                    "id": row["id"],
                    "created_at": str(row["created_at"]),
                    "profile": json.loads(row["raw_json_data"])
                }
                profiles.append(data)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON in row {row['id']}")
                continue
                
        print(f"Fetched {len(profiles)} profiles (skipped first {skip} newest records)")
        return profiles
    finally:
        await conn.close()

# ────────────────────────────────────────────────
# Call your API
# ────────────────────────────────────────────────
def call_api(payload: Dict) -> Dict | None:
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  API call failed: {e}")
        return None

# ────────────────────────────────────────────────
# Create evaluation batch
# ────────────────────────────────────────────────
def create_evaluation_batch(profiles_batch: List[Dict]) -> List[LLMTestCase]:
    test_cases = []
    
    for entry in profiles_batch:
        profile = entry["profile"]
        profile_id = entry["id"]
        created = entry["created_at"][:19]
        
        print(f"  → Sending profile #{profile_id} ({created}) to API...")
        
        api_response = call_api(profile)
        
        if not api_response:
            print(f"    → Skipped: API failed")
            continue
            
        actual_output = json.dumps(api_response, indent=2)
        
        # Simple rule-based expected outcome
        has_pain = any(
            d.get("pain", {}).get("pain_reported", 0) == 1 or
            d.get("clearing_pain", False)
            for d in profile.values() if isinstance(d, dict)
        )
        
        squat_score = profile.get("overhead_squat", {}).get("score", 3)
        
        if has_pain:
            expected = "Medical Referral Required + empty exercises + Red"
        elif squat_score <= 1:
            expected = "Corrective squat exercises (level 1–5) + Yellow/Red color"
        elif squat_score == 2:
            expected = "Moderate squat progressions/regressions + Yellow or Green"
        else:
            expected = "Green color + higher level squat exercises or general strength"

        test_case = LLMTestCase(
            input=f"Real user profile #{profile_id} ({created}):\n{json.dumps(profile, indent=2)}",
            actual_output=actual_output,
            expected_output=expected,
            retrieval_context=[
                "This is a REAL user-submitted FMS profile from the assessment_inputs table.",
                "Current system is squat-only — all exercises must come from squat progressions.",
                "Pain → referral. Low squat score → corrective exercises."
            ]
        )
        test_cases.append(test_case)
    
    return test_cases

# ────────────────────────────────────────────────
# Metrics
# ────────────────────────────────────────────────
squat_rag_correctness = GEval(
    name="Squat RAG Correctness (Real DB Profiles)",
    criteria="""Check if the output follows correct squat FMS logic for real user data:
- Pain detected → referral message + empty list + Red
- overhead_squat ≤1 → corrective exercises (level 1–5), Yellow/Red
- overhead_squat =2 → moderate progressions, Yellow/Green
- overhead_squat =3 → higher level or general work, Green
- Summary/tips should mention squat faults when present
- No non-squat exercises allowed
""",
    evaluation_steps=[
        "Correct pain handling?",
        "Low squat score → correct level & color?",
        "Mentions relevant faults?",
        "Only squat exercises used?",
        "No hallucinated names?"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-4o-mini",
    async_mode=False
)

relevancy = AnswerRelevancyMetric(threshold=0.9)
faithfulness = FaithfulnessMetric(threshold=0.9)

# ────────────────────────────────────────────────
# MAIN - Batch processing
# ────────────────────────────────────────────────
async def main():
    print("=== Confident AI Evaluation using REAL database profiles ===\n")
    print(f"Skipping the first {SKIP_FIRST_N} newest records.\n")
    
    profiles = await fetch_real_profiles(skip=SKIP_FIRST_N)
    if not profiles:
        print("No profiles found after skipping.")
        return
    
    print(f"Processing {len(profiles)} profiles in batches of {BATCH_SIZE}...\n")
    
    for i in range(0, len(profiles), BATCH_SIZE):
        batch = profiles[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        print(f"\n{'═'*70}")
        print(f"Batch {batch_num} — {len(batch)} profiles (records {i+1+SKIP_FIRST_N} to {min(i+BATCH_SIZE, len(profiles))+SKIP_FIRST_N})")
        print(f"{'═'*70}\n")
        
        test_cases = create_evaluation_batch(batch)
        
        if test_cases:
            print(f"Evaluating batch {batch_num} ({len(test_cases)} valid cases)...")
            evaluate(
                test_cases=test_cases,
                metrics=[
                    relevancy,
                    faithfulness,
                    squat_rag_correctness
                ]
            )
        else:
            print("No valid API responses in this batch.")
        
        if i + BATCH_SIZE < len(profiles):
            input("\nPress Enter to continue to next batch... ")

if __name__ == "__main__":
    asyncio.run(main())