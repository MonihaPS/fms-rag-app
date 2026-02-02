from typing import Dict, Any, List, Optional
from sqlalchemy import select
from src.logic.fms_analyzer import analyze_fms_profile
from src.database import AsyncSessionLocal, Exercise
import asyncio

# --- CONFIGURATION ---
# FAULT_TO_TAG_MAP remains exactly the same as your version
FAULT_TO_TAG_MAP = {
    "heels_lift": "fix_heels_lift",
    "knee_valgus": "fix_knee_valgus",
    "knee_varus": "pattern_squat",
    "excessive_forward_lean": "pattern_squat",
    "lumbar_flexion": "pattern_squat",
    "uneven_depth": "pattern_squat",
    "pelvic_drop_trendelenburg": "pattern_squat",
    "loss_of_balance": "level_1",
    "default_squat": "pattern_squat",
    "rib_flare": "pattern_squat",
    "lumbar_extension_sway_back": "pattern_squat",
    "excessive_pronation": "fix_heels_lift",
    "excessive_supination": "fix_heels_lift",
    "bar_drifts_forward": "pattern_squat",
    "arms_fall_forward": "pattern_squat",
    "shoulder_mobility_restriction_suspected": "pattern_squat",
    "excessive_rotation": "pattern_squat",
    "ankle_instability": "fix_heels_lift",
    "toe_drag": "pattern_squat",
    "hip_flexion_restriction": "pattern_squat",
    "asymmetrical_movement": "pattern_squat",
    "forward_head": "pattern_squat",
    "lateral_shift": "pattern_squat",
    "knee_instability": "fix_knee_valgus",
    "heel_lift": "fix_heels_lift",
    "wobbling": "level_1",
    "unequal_weight_distribution": "pattern_squat",
    "excessive_gap": "pattern_squat",
    "asymmetry_present": "pattern_squat",
    "spine_flexion": "pattern_squat",
    "scapular_winging": "pattern_squat",
    "pain_reported": "stop",
    "knee_bends": "pattern_squat",
    "hip_externally_rotates": "pattern_squat",
    "foot_lifts_off_floor": "pattern_squat",
    "lt_60_hip_flexion": "pattern_squat",
    "hamstring_restriction": "pattern_squat",
    "anterior_tilt": "pattern_squat",
    "posterior_tilt": "pattern_squat",
    "sagging_hips": "pattern_squat",
    "pike_position": "pattern_squat",
    "hips_lag": "pattern_squat",
    "excessive_lumbar_extension": "pattern_squat",
    "uneven_arm_push": "pattern_squat",
    "shoulder_instability": "pattern_squat",
    "unable_to_complete": "level_1",
    "lumbar_shift": "pattern_squat",
    "left_side_deficit": "pattern_squat",
    "right_side_deficit": "pattern_squat"
}

async def fetch_exercises_from_db():
    """Fetch all exercises from NeonDB"""
    try:
        async with AsyncSessionLocal() as session:
            print("--- DEBUG: Connecting to NeonDB to fetch exercises... ---")
            result = await session.execute(select(Exercise))
            exercises = result.scalars().all()
            
            # Convert SQLAlchemy objects to Dictionary format
            data = []
            for ex in exercises:
                data.append({
                    "name": ex.name,
                    "difficulty_level": ex.difficulty_level,
                    "tags": ex.tags if ex.tags else [],
                    "description": ex.description,
                    "coach_tip": ex.meta_data.get("coach_tip", "") if ex.meta_data else ""
                })
            print(f"✅ SUCCESS: Loaded {len(data)} exercises from NeonDB.")
            return data
    except Exception as e:
        print(f"❌ ERROR loading from DB: {e}")
        return []

async def get_exercises_by_profile(
    simple_scores: Dict[str, int],
    detailed_faults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    
    # 1. Analyze
    if detailed_faults:
        analysis = analyze_fms_profile(detailed_faults, use_manual_scores=detailed_faults.get('use_manual_scores', False))
    else:
        analysis = analyze_fms_profile(simple_scores)

    target_level = analysis.get('target_level', 1)
    print(f"--- DEBUG: Target Level is {target_level} ---")

    # 2. Load Data (FROM DB NOW)
    kb = await fetch_exercises_from_db()
    
    if not kb:
        return {"status": "ERROR_NO_DB", "analysis": analysis, "data": []}

    # 3. Build Search Tags
    search_tags = set()
    search_tags.add(f"level_{target_level}")

    if detailed_faults:
        for test, data in detailed_faults.items():
            if test == 'use_manual_scores': continue
            if not isinstance(data, dict): continue
            
            # Special Logic for Squat Score
            if test == 'overhead_squat' and data.get('score', 3) <= 2:
                search_tags.add("pattern_squat")

            for category in data.values():
                if isinstance(category, dict):
                    for fault, severity in category.items():
                        if isinstance(severity, (int, float)) and severity > 1:
                            if fault in FAULT_TO_TAG_MAP:
                                search_tags.add(FAULT_TO_TAG_MAP[fault])
    
    print(f"--- DEBUG: Searching for tags: {search_tags} ---")

    # 4. Filter
    scored_exercises = []
    for ex in kb:
        ex_tags = [str(t).lower() for t in ex['tags']]
        ex_level = ex.get('difficulty_level', 1)
        
        if ex_level == target_level:
            match_count = sum(1 for t in search_tags if t.lower() in ex_tags)
            if match_count > 0:
                if any("fix" in t for t in search_tags if t.lower() in ex_tags):
                    match_count += 5
                scored_exercises.append({"ex": ex, "score": match_count})

    # 5. Sort
    scored_exercises.sort(key=lambda x: x['score'], reverse=True)
    top_exercises = [x['ex'] for x in scored_exercises[:3]]

    # Fallback
    if not top_exercises:
        print("--- DEBUG: No matches found. Using Fallback logic. ---")
        fallback = [ex for ex in kb if ex.get('difficulty_level') == target_level and 'pattern_squat' in [t.lower() for t in ex.get('tags', [])]]
        top_exercises = fallback[:3]

    return {
        "status": "SUCCESS",
        "analysis": analysis,
        "data": top_exercises
    }