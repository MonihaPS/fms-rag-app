import json
import hashlib
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from typing import Optional, List, Dict, Any

# --- Import your modules ---
from src.logic.fms_analyzer import analyze_fms_profile
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan  # Assuming this exists; adjust path if needed

app = FastAPI(title="FMS Smart Coach API", version="3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Cache for Consistency
RESPONSE_CACHE = {}

# ==========================================
#  STEP 1: DEFINE SUB-MODELS (Aligned with Frontend)
# ==========================================

# 1. Overhead Squat (OHS)
class OS_TrunkTorso(BaseModel):
    upright_torso: int = Field(..., ge=0, le=4)
    excessive_forward_lean: int = Field(..., ge=0, le=4)
    rib_flare: int = Field(..., ge=0, le=4)
    lumbar_flexion: int = Field(..., ge=0, le=4)
    lumbar_extension_sway_back: int = Field(..., ge=0, le=4)

class OS_LowerLimb(BaseModel):
    knees_track_over_toes: int = Field(..., ge=0, le=4)
    knee_valgus: int = Field(..., ge=0, le=4)
    knee_varus: int = Field(..., ge=0, le=4)
    uneven_depth: int = Field(..., ge=0, le=4)

class OS_Feet(BaseModel):
    heels_stay_down: int = Field(..., ge=0, le=4)
    heels_lift: int = Field(..., ge=0, le=4)
    excessive_pronation: int = Field(..., ge=0, le=4)
    excessive_supination: int = Field(..., ge=0, le=4)

class OS_UpperBodyBarPosition(BaseModel):
    bar_aligned_over_mid_foot: int = Field(..., ge=0, le=4)
    bar_drifts_forward: int = Field(..., ge=0, le=4)
    arms_fall_forward: int = Field(..., ge=0, le=4)
    shoulder_mobility_restriction_suspected: int = Field(..., ge=0, le=4)

class OverheadSquatData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    trunk_torso: OS_TrunkTorso
    lower_limb: OS_LowerLimb
    feet: OS_Feet
    upper_body_bar_position: OS_UpperBodyBarPosition

# 2. Hurdle Step
class HS_PelvisCoreControl(BaseModel):
    pelvis_stable: int = Field(..., ge=0, le=4)
    pelvic_drop_trendelenburg: int = Field(..., ge=0, le=4)
    excessive_rotation: int = Field(..., ge=0, le=4)
    loss_of_balance: int = Field(..., ge=0, le=4)

class HS_StanceLeg(BaseModel):
    knee_stable: int = Field(..., ge=0, le=4)
    knee_valgus: int = Field(..., ge=0, le=4)
    knee_varus: int = Field(..., ge=0, le=4)
    ankle_instability: int = Field(..., ge=0, le=4)

class HS_SteppingLeg(BaseModel):
    clears_hurdle_smoothly: int = Field(..., ge=0, le=4)
    toe_drag: int = Field(..., ge=0, le=4)
    hip_flexion_restriction: int = Field(..., ge=0, le=4)
    asymmetrical_movement: int = Field(..., ge=0, le=4)

class HurdleStepData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    pelvis_core_control: HS_PelvisCoreControl
    stance_leg: HS_StanceLeg
    stepping_leg: HS_SteppingLeg

# 3. Inline Lunge
class IL_Alignment(BaseModel):
    head_neutral: int = Field(..., ge=0, le=4)
    forward_head: int = Field(..., ge=0, le=4)
    trunk_upright: int = Field(..., ge=0, le=4)
    excessive_forward_lean: int = Field(..., ge=0, le=4)
    lateral_shift: int = Field(..., ge=0, le=4)

class IL_LowerBodyControl(BaseModel):
    knee_tracks_over_foot: int = Field(..., ge=0, le=4)
    knee_valgus: int = Field(..., ge=0, le=4)
    knee_instability: int = Field(..., ge=0, le=4)
    heel_lift: int = Field(..., ge=0, le=4)

class IL_BalanceStability(BaseModel):
    stable_throughout: int = Field(..., ge=0, le=4)
    wobbling: int = Field(..., ge=0, le=4)
    loss_of_balance: int = Field(..., ge=0, le=4)
    unequal_weight_distribution: int = Field(..., ge=0, le=4)

class InlineLungeData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    alignment: IL_Alignment
    lower_body_control: IL_LowerBodyControl
    balance_stability: IL_BalanceStability

# 4. Shoulder Mobility
class SM_ReachQuality(BaseModel):
    hands_within_fist_distance: int = Field(..., ge=0, le=4)
    hands_within_hand_length: int = Field(..., ge=0, le=4)
    excessive_gap: int = Field(..., ge=0, le=4)
    asymmetry_present: int = Field(..., ge=0, le=4)

class SM_Compensation(BaseModel):
    no_compensation: int = Field(..., ge=0, le=4)
    spine_flexion: int = Field(..., ge=0, le=4)
    rib_flare: int = Field(..., ge=0, le=4)
    scapular_winging: int = Field(..., ge=0, le=4)

class SM_Pain(BaseModel):
    no_pain: int = Field(..., ge=0, le=4)
    pain_reported: int = Field(..., ge=0, le=4)

class ShoulderMobilityData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    reach_quality: SM_ReachQuality
    compensation: SM_Compensation
    pain: SM_Pain

# 5. Active Straight Leg Raise (ASLR)
class ASLR_NonMovingLeg(BaseModel):
    remains_flat: int = Field(..., ge=0, le=4)
    knee_bends: int = Field(..., ge=0, le=4)
    hip_externally_rotates: int = Field(..., ge=0, le=4)
    foot_lifts_off_floor: int = Field(..., ge=0, le=4)

class ASLR_MovingLeg(BaseModel):
    gt_80_hip_flexion: int = Field(..., ge=0, le=4)
    _60_80_hip_flexion: int = Field(..., ge=0, le=4)
    lt_60_hip_flexion: int = Field(..., ge=0, le=4)
    hamstring_restriction: int = Field(..., ge=0, le=4)

class ASLR_PelvicControl(BaseModel):
    pelvis_stable: int = Field(..., ge=0, le=4)
    anterior_tilt: int = Field(..., ge=0, le=4)
    posterior_tilt: int = Field(..., ge=0, le=4)

class ASLRData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    non_moving_leg: ASLR_NonMovingLeg
    moving_leg: ASLR_MovingLeg
    pelvic_control: ASLR_PelvicControl

# 6. Trunk Stability Push-Up
class TSP_BodyAlignment(BaseModel):
    neutral_spine_maintained: int = Field(..., ge=0, le=4)
    sagging_hips: int = Field(..., ge=0, le=4)
    pike_position: int = Field(..., ge=0, le=4)

class TSP_CoreControl(BaseModel):
    initiates_as_one_unit: int = Field(..., ge=0, le=4)
    hips_lag: int = Field(..., ge=0, le=4)
    excessive_lumbar_extension: int = Field(..., ge=0, le=4)

class TSP_UpperBody(BaseModel):
    elbows_aligned: int = Field(..., ge=0, le=4)
    uneven_arm_push: int = Field(..., ge=0, le=4)
    shoulder_instability: int = Field(..., ge=0, le=4)

class TSPData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    body_alignment: TSP_BodyAlignment
    core_control: TSP_CoreControl
    upper_body: TSP_UpperBody

# 7. Rotary Stability
class RS_DiagonalPattern(BaseModel):
    smooth_controlled: int = Field(..., ge=0, le=4)
    loss_of_balance: int = Field(..., ge=0, le=4)
    unable_to_complete: int = Field(..., ge=0, le=4)

class RS_SpinalControl(BaseModel):
    neutral_maintained: int = Field(..., ge=0, le=4)
    excessive_rotation: int = Field(..., ge=0, le=4)
    lumbar_shift: int = Field(..., ge=0, le=4)

class RS_Symmetry(BaseModel):
    symmetrical: int = Field(..., ge=0, le=4)
    left_side_deficit: int = Field(..., ge=0, le=4)
    right_side_deficit: int = Field(..., ge=0, le=4)

class RSData(BaseModel):
    score: int = Field(..., ge=0, le=3)
    diagonal_pattern: RS_DiagonalPattern
    spinal_control: RS_SpinalControl
    symmetry: RS_Symmetry

# MASTER REQUEST MODEL
class FMSProfileRequest(BaseModel):
    overhead_squat: OverheadSquatData
    hurdle_step: HurdleStepData
    inline_lunge: InlineLungeData
    shoulder_mobility: ShoulderMobilityData
    active_straight_leg_raise: ASLRData
    trunk_stability_pushup: TSPData
    rotary_stability: RSData
    pain_present: bool = False

# ==========================================
#  STEP 2: THE ENDPOINT
# ==========================================
@app.post("/generate-workout")
async def generate_workout(profile: FMSProfileRequest, background_tasks: BackgroundTasks):
    
    # 1. Convert complex nested model to dict
    full_data = profile.dict()

    # 2. Extract SIMPLE scores for compatibility (but analyzer uses full_data)
    simple_scores = {
        "overhead_squat": full_data['overhead_squat']['score'],
        "hurdle_step": full_data['hurdle_step']['score'],
        "inline_lunge": full_data['inline_lunge']['score'],
        "shoulder_mobility": full_data['shoulder_mobility']['score'],
        "active_straight_leg_raise": full_data['active_straight_leg_raise']['score'],
        "trunk_stability_pushup": full_data['trunk_stability_pushup']['score'],
        "rotary_stability": full_data['rotary_stability']['score']
    }

    # 3. CACHE CHECK
    cache_key = hashlib.md5(json.dumps(full_data, sort_keys=True).encode()).hexdigest()
    if cache_key in RESPONSE_CACHE:
        return RESPONSE_CACHE[cache_key]

    # 4. RUN ANALYZER (uses full profile for effective scores)
    try:
        analysis = analyze_fms_profile(full_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyzer Error: {str(e)}")

    if analysis.get('status') == "STOP":
        return {
            "session_title": "Medical Referral Recommended",
            "coach_summary": analysis.get('reason', 'Severe issues detected. Consult a professional.'),
            "exercises": [],
            "difficulty_color": "Red"
        }

    # 5. RUN RETRIEVER (pass simple_scores for legacy, full_data as detailed_faults)
    try:
        retrieval_result = get_exercises_by_profile(simple_scores, detailed_faults=full_data)
        exercises = retrieval_result['data']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retriever Error: {str(e)}")

    if not exercises:
        return {
            "session_title": "General Patterning Session",
            "coach_summary": "No specific correctives matched. Focus on foundational movement.",
            "exercises": [],
            "difficulty_color": "Yellow"
        }

    # 6. RUN GENERATOR
    try:
        # Enrich analysis with exercises and faults
        enriched_analysis = analysis.copy()
        enriched_analysis['detailed_faults'] = full_data
        enriched_analysis['selected_exercises'] = exercises

        final_plan = generate_workout_plan(enriched_analysis, exercises)

        # Add difficulty color based on level
        level_to_color = {1: "Red", 3: "Yellow", 5: "Yellow", 7: "Green", 9: "Green"}
        final_plan['difficulty_color'] = level_to_color.get(analysis['target_level'], "Yellow")

        # Cache the result
        RESPONSE_CACHE[cache_key] = final_plan
        return final_plan

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generator Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)