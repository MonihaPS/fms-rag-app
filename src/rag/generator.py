import os
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- UI OUTPUT SCHEMA (must match frontend expectation) ---
class ExerciseCard(BaseModel):
    name: str = Field(description="Exact exercise name from database")
    tag: str = Field(description="Short uppercase badge, e.g. 'ANKLE MOBILITY', 'KNEE TRACKING'")
    sets_reps: str = Field(description="e.g. '3 × 10-12', '3 × 30-45s hold'")
    tempo: str = Field(description="e.g. '3-1-3-0', 'Controlled'")
    coach_tip: str = Field(description="1-2 sentence fault-specific cue")

class WorkoutSession(BaseModel):
    session_title: str = Field(description="Concise title like 'Level 5 Ankle & Squat Patterning'")
    estimated_duration: str = Field(default="20-30 min", description="Approximate time")
    difficulty_color: str = Field(default="Green", description="Green, Yellow, Red")
    coach_summary: str = Field(description="2-4 sentence explanation of choices")
    exercises: List[ExerciseCard] = Field(default_factory=list, description="1-3 customized exercises")

# --- HELPER: FORMAT HIGH-SEVERITY FAULTS ---
def format_faults_for_prompt(full_data: Dict[str, Any]) -> str:
    """
    Summarizes only severe faults (≥3) with context from FMS criteria.
    """
    fault_summary = []
    pain_detected = full_data.get('pain_present', False)

    for test_name, test_data in full_data.items():
        if not isinstance(test_data, dict) or 'score' not in test_data:
            continue

        test_faults = []
        for category, details in test_data.items():
            if isinstance(details, dict):
                for fault_name, severity in details.items():
                    if isinstance(severity, int) and severity >= 3:
                        clean_name = fault_name.replace('_', ' ').title()
                        interpretation = ""
                        # Add quick FMS context
                        if 'heels_lift' in fault_name:
                            interpretation = "→ likely ankle dorsiflexion restriction (FMS score impact)"
                        elif 'knee_valgus' in fault_name:
                            interpretation = "→ knees collapse inward, poor glute control"
                        elif 'excessive_forward_lean' in fault_name:
                            interpretation = "→ torso collapses forward, poor thoracic extension"
                        elif 'loss_of_balance' in fault_name:
                            interpretation = "→ poor motor control / stability"
                        elif 'pain_reported' in fault_name and severity > 0:
                            pain_detected = True

                        test_faults.append(f"{clean_name} ({severity}/4){' ' + interpretation if interpretation else ''}")

        if test_faults:
            clean_test = test_name.replace('_', ' ').title()
            fault_summary.append(f"**{clean_test}** (manual score {test_data['score']}/3):\n  • " + "\n  • ".join(test_faults))

    if pain_detected:
        return "PAIN DETECTED – REFER TO MEDICAL PROFESSIONAL IMMEDIATELY.\n" + "\n\n".join(fault_summary)
    
    return "\n\n".join(fault_summary) if fault_summary else "No severe faults (≥3/4) detected."

# --- MAIN GENERATOR FUNCTION ---
def generate_workout_plan(analysis_context: Dict[str, Any], exercises: List[Dict[str, Any]]):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"session_title": "Configuration Error", "coach_summary": "GROQ_API_KEY missing.", "exercises": []}

    # Pain override
    if analysis_context.get('detailed_faults', {}).get('pain_present', False):
        return {
            "session_title": "Medical Referral Required",
            "coach_summary": "Pain was reported during screening. Do NOT proceed with training. Refer to a licensed medical professional for evaluation.",
            "difficulty_color": "Red",
            "exercises": []
        }

    # Sort exercises for deterministic order
    exercises = sorted(exercises, key=lambda x: x.get('name', ''))

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,           # Low for consistency
        api_key=api_key,
        model_kwargs={"seed": 42}  # Deterministic sampling
    )

    parser = JsonOutputParser(pydantic_object=WorkoutSession)

    # Format exercises for prompt
    exercise_text = "\n".join([
        f"- **{ex.get('name', 'Unknown')}** (Level {ex.get('level', '?')})\n"
        f"  Tags: {', '.join(ex.get('tags', []))}\n"
        f"  Description: {ex.get('description', 'No description')}"
        for ex in exercises
    ]) if exercises else "No corrective exercises matched at this level."

    # Format faults
    faults_text = format_faults_for_prompt(analysis_context.get('detailed_faults', {}))

    # Enhanced system prompt with FMS reference
    system_prompt = """
You are an expert FMS-certified Strength & Conditioning Coach. 
Generate a safe, targeted workout session using ONLY the provided exercises.

### ATHLETE PROFILE
- Status: {status}
- Target Level: {level} ({reason})
- Difficulty Color: Use Red for level ≤3 or pain, Yellow for 4-6, Green for ≥7

### ⚠️ CRITICAL FAULTS (Severity ≥3/4)
These are the highest priority issues — cues MUST address them directly:
{faults_text}

### OFFICIAL FMS CRITERIA REFERENCE (for context only)
- Deep Squat: Heels lift = score impact; forward lean/lumbar flexion = torso collapse
- Hurdle Step: Loss of balance, pelvic drop, toe drag = stability/hip issues
- Inline Lunge: Wobbling, knee valgus, heel lift = dynamic control problems
- Shoulder Mobility: Excessive gap, scapular winging = mobility restriction
- ASLR: <60° flexion, anterior tilt = hip/hamstring restriction
- Trunk Stability Pushup: Hips lag, sagging = core dysfunction
- Rotary Stability: Loss of balance, lumbar shift = anti-rotation weakness

### SELECTED EXERCISES (USE ONLY THESE)
{exercise_list}

### RULES
1. **Customize Cues** — Every coach_tip MUST directly reference the athlete's worst fault(s).
   Example: If "Heels Lift" ≥3 → "Drive through mid-foot, keep weight forward to avoid heel rise"
   Example: If "Knee Valgus" ≥3 → "Push knees out, engage glutes to prevent collapse"
2. **Volume & Intensity** — Low level (≤5): higher reps/holds, bodyweight focus
   High level (≥7): lower reps, add load, faster tempo
3. **Session Title** — Specific, e.g. "Level 5 Ankle Mobility & Squat Patterning"
4. **Estimated Duration** — Realistic (15-40 min)
5. **Strict JSON** — Follow the schema exactly. No extra text.

{format_instructions}
"""

    prompt = ChatPromptTemplate.from_template(
        template=system_prompt,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | llm | parser

    try:
        response = chain.invoke({
            "status": analysis_context.get('status', 'TRAINING'),
            "level": str(analysis_context.get('target_level', 1)),
            "reason": analysis_context.get('reason', 'General movement training'),
            "faults_text": faults_text,
            "exercise_list": exercise_text
        })

        # Enforce color if not set by LLM
        if 'difficulty_color' not in response or not response['difficulty_color']:
            level = analysis_context.get('target_level', 1)
            response['difficulty_color'] = 'Red' if level <= 3 else 'Yellow' if level <= 6 else 'Green'

        # Add duration if missing
        if 'estimated_duration' not in response:
            response['estimated_duration'] = '20-30 min'

        return response

    except Exception as e:
        return {
            "session_title": "Generation Error",
            "coach_summary": f"Could not generate plan: {str(e)}. Please try again or contact support.",
            "difficulty_color": "Red",
            "exercises": []
        }