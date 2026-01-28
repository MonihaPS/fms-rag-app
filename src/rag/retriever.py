import json
import os
from src.logic.fms_analyzer import analyze_fms_profile

DB_PATH = 'data/processed/exercise_knowledge_base.json'

# --- 1. DEFINE TAG MAPPING ---
# This links the Frontend Input ID (negative faults) to the Database Smart Tag
FAULT_TO_TAG_MAP = {
    # Overhead Squat
    "excessive_forward_lean": "fix_posture",
    "rib_flare": "fix_core_stability",
    "lumbar_flexion": "fix_core_stability",
    "lumbar_extension_sway_back": "fix_core_stability",
    "knee_valgus": "fix_knee_tracking",
    "knee_varus": "fix_knee_tracking",
    "uneven_depth": "fix_asymmetry",
    "heels_lift": "fix_ankle_mobility",
    "excessive_pronation": "fix_ankle_mobility",
    "excessive_supination": "fix_ankle_mobility",
    "bar_drifts_forward": "fix_balance",
    "arms_fall_forward": "fix_shoulder_mobility",
    "shoulder_mobility_restriction_suspected": "fix_shoulder_mobility",
    
    # Hurdle Step
    "pelvic_drop_trendelenburg": "fix_balance",
    "excessive_rotation": "fix_core_stability",
    "loss_of_balance": "fix_balance",
    "ankle_instability": "fix_balance",
    "toe_drag": "fix_hip_mobility",
    "hip_flexion_restriction": "fix_hip_mobility",
    "asymmetrical_movement": "fix_asymmetry",
    
    # Inline Lunge
    "forward_head": "fix_posture",
    "excessive_forward_lean": "fix_posture",
    "lateral_shift": "fix_balance",
    "knee_instability": "fix_knee_tracking",
    "heel_lift": "fix_ankle_mobility",
    "wobbling": "fix_balance",
    "unequal_weight_distribution": "fix_asymmetry",
    
    # Shoulder Mobility
    "excessive_gap": "fix_shoulder_mobility",
    "asymmetry_present": "fix_asymmetry",
    "spine_flexion": "fix_core_stability",
    "scapular_winging": "fix_shoulder_mobility",
    "pain_reported": "fix_pain",  # Special handling perhaps
    
    # Active Straight Leg Raise
    "knee_bends": "fix_knee_tracking",
    "hip_externally_rotates": "fix_hip_mobility",
    "foot_lifts_off_floor": "fix_core_stability",
    "lt_60_hip_flexion": "fix_hip_mobility",
    "hamstring_restriction": "fix_hip_mobility",
    "anterior_tilt": "fix_core_stability",
    "posterior_tilt": "fix_core_stability",
    
    # Trunk Stability Push-Up
    "sagging_hips": "fix_core_stability",
    "pike_position": "fix_core_stability",
    "hips_lag": "fix_core_stability",
    "excessive_lumbar_extension": "fix_core_stability",
    "uneven_arm_push": "fix_asymmetry",
    "shoulder_instability": "fix_shoulder_mobility",
    
    # Rotary Stability
    "unable_to_complete": "fix_balance",
    "lumbar_shift": "fix_core_stability",
    "left_side_deficit": "fix_asymmetry",
    "right_side_deficit": "fix_asymmetry",
    
    # Add more as needed
}

def load_knowledge_base():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['exercises']  # Assuming top-level 'exercises' list

def get_exercises_by_profile(simple_scores, detailed_faults=None):
    """
    1. Analyzes FMS Level.
    2. Scans Detailed Faults to find 'Priority Tags'.
    3. Scores exercises: +50 pts for Tag Match, +10 pts for Level Match.
    4. Returns the highest scoring exercises.
    No random fallback; return empty if no matches.
    """
    
    # --- 1. ANALYZE LEVEL ---
    analysis = analyze_fms_profile(simple_scores)
    
    if analysis['status'] == "STOP":
        return {"status": "STOP", "message": analysis['reason'], "data": []}
    
    target_level = analysis['target_level']
    kb = load_knowledge_base()

    # --- 2. IDENTIFY PRIORITY TAGS ---
    # We look through the detailed_faults for anything rated 3 or higher (severe faults).
    priority_tags = set()  # Use set to avoid duplicates
    
    if detailed_faults:
        for test_name, data in detailed_faults.items():
            if isinstance(data, dict):
                for category, details in data.items():
                    if isinstance(details, dict):
                        for fault_name, severity in details.items():
                            # If Fault is Severe (3 or 4)
                            if isinstance(severity, int) and severity >= 3:
                                # Find the matching DB tag (only for negative faults in map)
                                if fault_name in FAULT_TO_TAG_MAP:
                                    priority_tags.add(FAULT_TO_TAG_MAP[fault_name])

    # --- 3. SCORING ALGORITHM ---
    scored_exercises = []

    for ex in kb:
        score = 0
        ex_level = ex.get('level', 1)
        ex_tags = ex.get('tags', [])

        # Rule A: Must be close to Target Level (Strict Safety)
        level_diff = abs(ex_level - target_level)
        if level_diff > 1:
            continue  # Skip exercises that are too hard or too easy
        
        # Rule B: Exact Level Match (+10 pts)
        if ex_level == target_level:
            score += 10
        
        # Rule C: Corrective Tag Match (+50 pts per match)
        # This forces the corrective exercises to the top
        for p_tag in priority_tags:
            if p_tag in ex_tags:
                score += 50
                # Bonus for match
                score += 5 

        # Only add if score > 0 (i.e., at least level close)
        if score > 0:
            scored_exercises.append({
                "exercise": ex,
                "score": score
            })

    # --- 4. SELECT TOP 3 ---
    # Sort by Score (Desc), then by Name (for consistency)
    scored_exercises.sort(key=lambda x: (-x['score'], x['exercise']['name']))
    
    # Take top 3 highest scoring exercises
    top_picks = [item['exercise'] for item in scored_exercises[:3]]

    # No fallback; if empty, return empty

    return {
        "status": "SUCCESS" if top_picks else "NO_MATCH",
        "analysis": analysis,
        "data": top_picks
    }