import os
import uuid
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── UI OUTPUT SCHEMA ──
class ExerciseCard(BaseModel):
    name: str = Field(description="Exact exercise name from database")
    tag: str = Field(description="Short uppercase badge, e.g. 'ANKLE MOBILITY', 'KNEE TRACKING'")
    sets_reps: str = Field(description="e.g. '3 x 10-12', '3 x 30s hold'")
    tempo: str = Field(description="e.g. '3-1-3-0', 'Controlled'")
    coach_tip: str = Field(description="1-2 sentence cue specifically addressing the athlete's high-severity faults.")

class WorkoutSession(BaseModel):
    session_title: str = Field(description="Concise title like 'Level 5 Ankle & Squat Patterning'")
    estimated_duration: str = Field(default="20-30 min", description="Approximate time")
    difficulty_color: str = Field(default="Green", description="Green, Yellow, Red")
    coach_summary: str = Field(description="2-4 sentence explanation of why these exercises were chosen.")
    exercises: List[ExerciseCard] = Field(default_factory=list, description="List of exercises")

# ── HELPER: FORMAT FAULTS ──
def format_faults_for_prompt(full_data: Dict[str, Any]) -> str:
    if not full_data:
        return "No specific faults data available."

    fault_summary = []
    
    for test_name, test_data in full_data.items():
        if not isinstance(test_data, dict):
            continue

        test_faults = []
        for category, details in test_data.items():
            if isinstance(details, dict):
                for fault_name, severity in details.items():
                    try:
                        score_val = int(severity)
                        if score_val > 0:
                            clean_name = fault_name.replace('_', ' ').title()
                            interpretation = ""
                            if 'heels_lift' in fault_name: interpretation = "→ ankle restriction"
                            elif 'knee_valgus' in fault_name: interpretation = "→ glute weakness / activation needed"
                            elif 'forward_lean' in fault_name: interpretation = "→ core / thoracic control"
                            # Kept as requested (sub-input detail), but won't block generation
                            elif 'pain_reported' in fault_name: interpretation = "→ medical referral required"
                            test_faults.append(f"{clean_name} ({score_val}) {interpretation}")
                    except (ValueError, TypeError):
                        continue

        if test_faults:
            clean_test = test_name.replace('_', ' ').title()
            fault_summary.append(f"**{clean_test}**: " + ", ".join(test_faults))

    return "\n".join(fault_summary) if fault_summary else "No severe faults detected."

# ── MAIN GENERATOR FUNCTION ──
def generate_workout_plan(analysis_context: Dict[str, Any], exercises: List[Dict[str, Any]]):
    call_id = str(uuid.uuid4())[:8]
    print(f"--- GENERATE CALL START [{call_id}] | received {len(exercises)} items ---")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(f"❌ Error [{call_id}]: GROQ_API_KEY is missing.")
        return {"session_title": "Config Error", "coach_summary": "System configuration error (API Key).", "exercises": []}

    # REMOVED: The strict "Medical Referral Required" return block.
    # The code now proceeds to generate a workout even if status was "STOP".

    if not exercises:
        return {
            "session_title": "Assessment Complete",
            "coach_summary": "No specific corrective exercises matched your profile. You may be cleared for general activity.",
            "difficulty_color": "Green",
            "exercises": []
        }

    try:
        # ── ROBUST FILTERING & SORTING ───────────────────────────────────────
        valid_exercises = []
        for item in exercises:
            if not isinstance(item, dict):
                print(f"WARNING [{call_id}]: Skipping invalid item (not dict): {item}")
                continue
            name = item.get('exercise_name') or item.get('name') or "Unnamed Exercise"
            valid_exercises.append(item)

        if len(valid_exercises) != len(exercises):
            print(f"WARNING [{call_id}]: Removed {len(exercises) - len(valid_exercises)} invalid items")

        # Sort by exercise_name (case insensitive)
        valid_exercises.sort(key=lambda x: (x.get('exercise_name') or "").lower())

        # Prepare formatted list for prompt
        formatted_exercises = []
        for ex in valid_exercises:
            name = ex.get('exercise_name', "Unknown Exercise")
            level = ex.get('difficulty_level') or "?"
            tags = ex.get('tags', [])
            tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
            formatted_exercises.append(f"- **{name}** (Level {level})\n  Tags: {tag_str}")

        exercise_text = "\n".join(formatted_exercises)

        # Format faults
        faults_text = format_faults_for_prompt(analysis_context.get('detailed_faults', {}))

        # Setup LLM
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.0,
            api_key=api_key,
            model_kwargs={"seed": 42}
        )
        parser = JsonOutputParser(pydantic_object=WorkoutSession)

        # Enhanced prompt
        system_prompt = """
        You are an expert FMS Strength Coach. Create a corrective workout plan.

        ### ATHLETE DATA
        - Status: {status}
        - Target Level: {level}
        - Key Faults: 
        {faults_text}

        ### AVAILABLE EXERCISES (STRICT CONSTRAINT)
        Use ONLY exercises from this list. Do NOT invent new ones.
        Prioritize ones that best match the specific faults shown above.
        {exercise_list}

        ### INSTRUCTIONS
        1. Select 3 top most relevant exercises that address the key faults.
        2. Create short, specific 'coach_tip' cues mentioning the actual fault.
        3. Set difficulty_color: Red if severe faults, Yellow if moderate, Green if minor/cleared.
        4. Return valid JSON matching the schema exactly.

        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_template(
            template=system_prompt,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | llm | parser

        # Invoke
        response = chain.invoke({
            # We pass the status, but the LLM will now generate a workout instead of hard-stopping
            "status": analysis_context.get('status', 'TRAINING'),
            "level": str(analysis_context.get('target_level', 1)),
            "faults_text": faults_text,
            "exercise_list": exercise_text
        })

        # Fallback for missing fields
        if 'difficulty_color' not in response:
            response['difficulty_color'] = 'Yellow'

        print(f"--- GENERATE CALL END [{call_id}] | success ---")
        return response

    except Exception as e:
        print(f"❌ GENERATION ERROR [{call_id}]: {str(e)}")
        # Safe fallback
        return {
            "session_title": "Workout Generated (Fallback)",
            "coach_summary": "AI coach encountered an issue. Here's a basic plan based on retrieved exercises.",
            "difficulty_color": "Yellow",
            "exercises": [
                {
                    "name": ex.get('exercise_name', 'Exercise'),
                    "tag": "CORRECTIVE",
                    "sets_reps": "3 x 10",
                    "tempo": "Controlled",
                    "coach_tip": "Focus on perfect form."
                }
                for ex in valid_exercises[:3]
            ]
        }