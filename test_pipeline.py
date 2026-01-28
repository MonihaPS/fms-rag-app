import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan

def test_full_system():
    print("\n" + "="*60)
    print(" 🏋️‍♂️  FMS DETAILED PIPELINE TEST  🏋️‍♂️")
    print("="*60)
    
    # --- SIMULATED USER INPUT (Nested Structure) ---
    # Scenario: Squat Score 2, but with Severe Heel Lift (Ankle issue)
    
    full_data = {
        "deep_squat": {
            "score": 2,
            "feet": {"heels_lift": 5, "excessive_pronation": 0}, # <--- SEVERE FAULT
            "trunk_torso": {}, "lower_limb": {}, "upper_body": {}
        },
        "hurdle_step": {"score": 2, "pelvis_core": {}, "stance_leg": {}, "stepping_leg": {}},
        "inline_lunge": {"score": 2, "alignment": {}, "lower_body_control": {}, "balance_stability": {}},
        "shoulder_mobility": {"score": 2, "reach_quality": {}, "compensation": {}, "pain": {}},
        "active_straight_leg_raise": {"score": 2, "non_moving_leg": {}, "moving_leg": {}, "pelvic_control": {}},
        "trunk_stability_pushup": {"score": 2, "body_alignment": {}, "core_control": {}, "upper_body": {}},
        "rotary_stability": {"score": 2, "movement": {}, "spine_pelvis": {}, "balance": {}},
        "pain_present": False
    }

    print("\n1️⃣  STEP 1: PREPARING DATA...")
    
    # Extract simple scores for the Retriever
    simple_scores = {k: v['score'] for k, v in full_data.items() if isinstance(v, dict) and 'score' in v}
    print(f"   Simple Scores: {simple_scores}")

    # 1. RETRIEVER
    retrieval_result = get_exercises_by_profile(simple_scores)
    
    if retrieval_result['status'] == "STOP":
        print(f"\n🛑 STOP: {retrieval_result['message']}")
        return

    analysis = retrieval_result['analysis']
    # INJECT DETAILED FAULTS FOR GENERATOR
    analysis['detailed_faults'] = full_data 
    
    exercises = retrieval_result['data']
    
    print(f"\n✅ RETRIEVAL COMPLETE")
    print(f"   Target Level: {analysis['target_level']}")

    # 2. GENERATOR
    print("\n2️⃣  STEP 2: GENERATING COACHING UI...")
    
    try:
        ui_output = generate_workout_plan(analysis, exercises)
        
        print("\n" + "-"*20 + "  FINAL JSON OUTPUT  " + "-"*20)
        print(json.dumps(ui_output, indent=2))
        
        # Check if the AI noticed the Heel Lift
        tips = [ex['coach_tip'] for ex in ui_output['exercises']]
        print("\n🔎 CHECKING INTELLIGENCE:")
        print(f"   Fault Input: 'Heels Lift' (Level 5)")
        print(f"   Coach Tips Generated: {tips}")
        
    except Exception as e:
        print(f"\n💥 Generator Error: {e}")

if __name__ == "__main__":
    test_full_system()