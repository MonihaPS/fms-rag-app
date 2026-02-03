import json
import os
import uuid
from typing import Dict, Any, List, Optional
from src.logic.fms_analyzer import analyze_fms_profile

# --- CONFIGURATION ---
JSON_KB_PATH = 'data/processed/exercise_knowledge_base.json'

FAULT_TO_TAG_MAP = {
    "heels_lift": "fix_heels_lift",
    "knee_valgus": "fix_knee_valgus",
    "knee_varus": "pattern_squat",
    "excessive_forward_lean": "fix_forward_lean",
    "lumbar_flexion": "fix_lumbar_flexion",
    "uneven_depth": "fix_asymmetry",
    "pelvic_drop_trendelenburg": "fix_pelvic_drop",
    "loss_of_balance": "level_1",
    "default_squat": "pattern_squat",
    "rib_flare": "fix_rib_flare",
    "lumbar_extension_sway_back": "fix_lumbar_extension",
    "excessive_pronation": "fix_heels_lift",
    "excessive_supination": "fix_heels_lift",
    "bar_drifts_forward": "fix_forward_lean",
    "arms_fall_forward": "fix_shoulder_mobility",
    "shoulder_mobility_restriction_suspected": "pattern_shoulder",
    "excessive_rotation": "fix_rotary_instability",
    "ankle_instability": "fix_heels_lift",
    "toe_drag": "pattern_step",
    "hip_flexion_restriction": "pattern_leg_raise",
    "asymmetrical_movement": "fix_asymmetry",
    "forward_head": "fix_forward_lean",
    "lateral_shift": "fix_lateral_shift",
    "knee_instability": "fix_knee_valgus",
    "heel_lift": "fix_heels_lift",
    "wobbling": "level_1",
    "unequal_weight_distribution": "fix_asymmetry",
    "excessive_gap": "pattern_shoulder",
    "asymmetry_present": "fix_asymmetry",
    "spine_flexion": "fix_lumbar_flexion",
    "scapular_winging": "pattern_shoulder",
    # REMOVED: "pain_reported": "stop" 
    "knee_bends": "fix_knee_instability",
    "hip_externally_rotates": "fix_hip_rotation",
    "foot_lifts_off_floor": "fix_heels_lift",
    "lt_60_hip_flexion": "pattern_leg_raise",
    "hamstring_restriction": "pattern_leg_raise",
    "anterior_tilt": "fix_pelvic_tilt",
    "posterior_tilt": "fix_pelvic_tilt",
    "sagging_hips": "fix_core_stability",
    "pike_position": "fix_core_stability",
    "hips_lag": "fix_core_stability",
    "excessive_lumbar_extension": "fix_lumbar_extension",
    "uneven_arm_push": "fix_asymmetry",
    "shoulder_instability": "pattern_shoulder",
    "unable_to_complete": "level_1",
    "lumbar_shift": "fix_lumbar_flexion",
    "left_side_deficit": "fix_asymmetry",
    "right_side_deficit": "fix_asymmetry"
}

def fetch_exercises_from_json():
    """Fetch all exercises from the local JSON Knowledge Base"""
    print(f"--- DEBUG: Loading exercises from {JSON_KB_PATH}... ---")
    
    if not os.path.exists(JSON_KB_PATH):
        print(f"❌ ERROR: JSON file not found at {JSON_KB_PATH}")
        return []
        
    try:
        with open(JSON_KB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ SUCCESS: Loaded {len(data)} exercises from JSON.")
            return data
    except Exception as e:
        print(f"❌ ERROR reading JSON: {e}")
        return []

async def get_exercises_by_profile(
    simple_scores: Dict[str, int],
    detailed_faults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    call_id = str(uuid.uuid4())[:8]
    print(f"--- RETRIEVAL CALL START [{call_id}] ---")

    # 1. Analyze
    if detailed_faults:
        analysis = analyze_fms_profile(detailed_faults, use_manual_scores=detailed_faults.get('use_manual_scores', False))
    else:
        analysis = analyze_fms_profile(simple_scores)

    target_level = analysis.get('target_level', 1)
    print(f"--- DEBUG [{call_id}]: Target Level is {target_level} ---")

    # 2. Load Data
    kb = fetch_exercises_from_json()
    
    if not kb:
        print(f"--- RETRIEVAL CALL END [{call_id}] | ERROR: No data ---")
        return {"status": "ERROR_NO_DATA", "analysis": analysis, "data": []}

    # 3. Build Search Tags
    search_tags = set()
    search_tags.add(f"level_{target_level}")

    if detailed_faults:
        for test, data in detailed_faults.items():
            if test == 'use_manual_scores': continue
            if not isinstance(data, dict): continue
            
            # Add pattern tags for low scores in each major test
            if test == 'overhead_squat' and data.get('score', 3) <= 2:
                search_tags.add("pattern_squat")
            elif test == 'hurdle_step' and data.get('score', 3) <= 2:
                search_tags.add("pattern_step")
            elif test == 'inline_lunge' and data.get('score', 3) <= 2:
                search_tags.add("pattern_lunge")
            elif test == 'shoulder_mobility' and data.get('score', 3) <= 2:
                search_tags.add("pattern_shoulder")
            elif test == 'active_straight_leg_raise' and data.get('score', 3) <= 2:
                search_tags.add("pattern_leg_raise")
            elif test == 'trunk_stability_pushup' and data.get('score', 3) <= 2:
                search_tags.add("pattern_pushup")
            elif test == 'rotary_stability' and data.get('score', 3) <= 2:
                search_tags.add("pattern_rotary")

            # Fault-specific tags (binary > 0)
            for category in data.values():
                if isinstance(category, dict):
                    for fault, severity in category.items():
                        if isinstance(severity, (int, float)) and severity > 0:
                            if fault in FAULT_TO_TAG_MAP:
                                search_tags.add(FAULT_TO_TAG_MAP[fault])
    
    print(f"--- DEBUG [{call_id}]: Searching for tags: {search_tags} ---")

    # 4. Filter & Score exercises
    scored_exercises = []
    for ex in kb:
        ex_tags = [str(t).lower() for t in ex.get('tags', [])]
        ex_level = ex.get('difficulty_level', 1)
        
        # Strict level matching
        if ex_level == target_level:
            match_count = sum(1 for t in search_tags if t.lower() in ex_tags)
            
            # Boost for specific corrective tags
            if match_count > 0:
                if any("fix_" in t for t in search_tags if t.lower() in ex_tags):
                    match_count += 5
            scored_exercises.append({"ex": ex, "score": match_count})

    # 5. Sort by relevance
    scored_exercises.sort(key=lambda x: x['score'], reverse=True)
    top_exercises = [x['ex'] for x in scored_exercises[:6]]  # increased to 6 for better selection pool

    # Fallback if no matches
    if not top_exercises:
        print(f"--- DEBUG [{call_id}]: No specific matches → using general level fallback ---")
        fallback = [ex for ex in kb if ex.get('difficulty_level') == target_level]
        top_exercises = fallback[:6]

    # Final debug of returned items
    print(f"--- DEBUG [{call_id}]: RETRIEVED {len(top_exercises)} EXERCISES ---")
    for i, ex in enumerate(top_exercises):
        name = ex.get('exercise_name', 'MISSING_NAME')
        print(f"  [{i}] {name}")

    print(f"--- RETRIEVAL CALL END [{call_id}] | returning {len(top_exercises)} items ---")

    return {
        "status": "SUCCESS",
        "analysis": analysis,
        "data": top_exercises
    }