import json
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any

# ── IMPORTS ──
from src.logic.fms_analyzer import analyze_fms_profile
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan
from src.database import AsyncSessionLocal, AssessmentInput, AssessmentScore, User, engine, Base

# ────────────────────────────────────────────────
# Lifecycle (Startup)
# ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up: Connecting to NeonDB...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Neon DB Connection Verified & Tables Ready.")
    yield

app = FastAPI(title="FMS Smart Coach API", version="3.3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────
# Pydantic Models (Validation)
# ────────────────────────────────────────────────

# --- 1. DEEP SQUAT ---
class OS_TrunkTorso(BaseModel):
    upright_torso: int = 0
    excessive_forward_lean: int = 0
    rib_flare: int = 0
    lumbar_flexion: int = 0
    lumbar_extension_sway_back: int = 0

class OS_LowerLimb(BaseModel):
    knees_track_over_toes: int = 0
    knee_valgus: int = 0
    knee_varus: int = 0
    uneven_depth: int = 0

class OS_Feet(BaseModel):
    heels_stay_down: int = 0
    heels_lift: int = 0
    excessive_pronation: int = 0
    excessive_supination: int = 0

class OS_UpperBodyBarPosition(BaseModel):
    bar_aligned_over_mid_foot: int = 0
    bar_drifts_forward: int = 0
    arms_fall_forward: int = 0
    shoulder_mobility_restriction_suspected: int = 0

class OverheadSquatData(BaseModel):
    score: int
    trunk_torso: OS_TrunkTorso
    lower_limb: OS_LowerLimb
    feet: OS_Feet
    upper_body_bar_position: OS_UpperBodyBarPosition

# --- 2. HURDLE STEP ---
class HS_PelvisCoreControl(BaseModel):
    pelvis_stable: int = 0
    pelvic_drop_trendelenburg: int = 0
    excessive_rotation: int = 0
    loss_of_balance: int = 0

class HS_StanceLeg(BaseModel):
    knee_stable: int = 0
    knee_valgus: int = 0
    knee_varus: int = 0
    ankle_instability: int = 0

class HS_SteppingLeg(BaseModel):
    clears_hurdle_smoothly: int = 0
    toe_drag: int = 0
    hip_flexion_restriction: int = 0
    asymmetrical_movement: int = 0

class HurdleStepData(BaseModel):
    score: int
    l_score: int = 0
    r_score: int = 0
    pelvis_core_control: HS_PelvisCoreControl
    stance_leg: HS_StanceLeg
    stepping_leg: HS_SteppingLeg

# --- 3. INLINE LUNGE ---
class IL_Alignment(BaseModel):
    head_neutral: int = 0
    forward_head: int = 0
    trunk_upright: int = 0
    excessive_forward_lean: int = 0
    lateral_shift: int = 0

class IL_LowerBodyControl(BaseModel):
    knee_tracks_over_foot: int = 0
    knee_valgus: int = 0
    knee_instability: int = 0
    heel_lift: int = 0

class IL_BalanceStability(BaseModel):
    stable_throughout: int = 0
    wobbling: int = 0
    loss_of_balance: int = 0
    unequal_weight_distribution: int = 0

class InlineLungeData(BaseModel):
    score: int
    l_score: int = 0
    r_score: int = 0
    alignment: IL_Alignment
    lower_body_control: IL_LowerBodyControl
    balance_stability: IL_BalanceStability

# --- 4. SHOULDER MOBILITY ---
class SM_ReachQuality(BaseModel):
    hands_within_fist_distance: int = 0
    hands_within_hand_length: int = 0
    excessive_gap: int = 0
    asymmetry_present: int = 0

class SM_Compensation(BaseModel):
    no_compensation: int = 0
    spine_flexion: int = 0
    rib_flare: int = 0
    scapular_winging: int = 0

class SM_Pain(BaseModel):
    no_pain: int = 0
    pain_reported: int = 0

class ShoulderMobilityData(BaseModel):
    score: int
    l_score: int = 0
    r_score: int = 0
    clearing_pain: bool = False
    reach_quality: SM_ReachQuality
    compensation: SM_Compensation
    pain: SM_Pain

# --- 5. ASLR ---
class ASLR_NonMovingLeg(BaseModel):
    remains_flat: int = 0
    knee_bends: int = 0
    hip_externally_rotates: int = 0
    foot_lifts_off_floor: int = 0

class ASLR_MovingLeg(BaseModel):
    gt_80_hip_flexion: int = 0
    between_60_80_hip_flexion: int = 0
    lt_60_hip_flexion: int = 0
    hamstring_restriction: int = 0

class ASLR_PelvicControl(BaseModel):
    pelvis_stable: int = 0
    anterior_tilt: int = 0
    posterior_tilt: int = 0

class ASLRData(BaseModel):
    score: int
    l_score: int = 0
    r_score: int = 0
    non_moving_leg: ASLR_NonMovingLeg
    moving_leg: ASLR_MovingLeg
    pelvic_control: ASLR_PelvicControl

# --- 6. TRUNK STABILITY ---
class TSP_BodyAlignment(BaseModel):
    neutral_spine_maintained: int = 0
    sagging_hips: int = 0
    pike_position: int = 0

class TSP_CoreControl(BaseModel):
    initiates_as_one_unit: int = 0
    hips_lag: int = 0
    excessive_lumbar_extension: int = 0

class TSP_UpperBody(BaseModel):
    elbows_aligned: int = 0
    uneven_arm_push: int = 0
    shoulder_instability: int = 0

class TSPData(BaseModel):
    score: int
    clearing_pain: bool = False
    body_alignment: TSP_BodyAlignment
    core_control: TSP_CoreControl
    upper_body: TSP_UpperBody

# --- 7. ROTARY STABILITY ---
class RS_DiagonalPattern(BaseModel):
    smooth_controlled: int = 0
    loss_of_balance: int = 0
    unable_to_complete: int = 0

class RS_SpinalControl(BaseModel):
    neutral_maintained: int = 0
    excessive_rotation: int = 0
    lumbar_shift: int = 0

class RS_Symmetry(BaseModel):
    symmetrical: int = 0
    left_side_deficit: int = 0
    right_side_deficit: int = 0

class RSData(BaseModel):
    score: int
    l_score: int = 0
    r_score: int = 0
    clearing_pain: bool = False
    diagonal_pattern: RS_DiagonalPattern
    spinal_control: RS_SpinalControl
    symmetry: RS_Symmetry

class FMSProfileRequest(BaseModel):
    overhead_squat: OverheadSquatData
    hurdle_step: HurdleStepData
    inline_lunge: InlineLungeData
    shoulder_mobility: ShoulderMobilityData
    active_straight_leg_raise: ASLRData
    trunk_stability_pushup: TSPData
    rotary_stability: RSData
    use_manual_scores: bool = False

# ────────────────────────────────────────────────
# API Endpoints
# ────────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ────────────────────────────────────────────────
# MAIN ENDPOINT - Cleaned & Fixed
# ────────────────────────────────────────────────
@app.post("/generate-workout")
async def generate_workout(
    profile: FMSProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    full_data = profile.dict()

    # ─────────────────────────────────────────────────
    # 1. Analyze FMS profile
    # ─────────────────────────────────────────────────
    try:
        analysis = analyze_fms_profile(
            full_data,
            use_manual_scores=full_data.get('use_manual_scores', False)
        )
        
        effective_scores = analysis.get("effective_scores", {})
        print("\n" + "="*40)
        print(f"🧐 DEBUG: CALCULATED SCORES: {effective_scores}")
        print(f"🧐 DEBUG: ANALYSIS STATUS: {analysis.get('status')}")
        print("="*40 + "\n")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyzer Error: {str(e)}")

    # Early return if pain detected
    if analysis.get("status") == "STOP":
        return {
            "session_title": "Medical Referral Required",
            "coach_summary": f"Pain detected: {analysis.get('reason', 'Pain reported during screening')}",
            "exercises": [],
            "difficulty_color": "Red"
        }

    # ─────────────────────────────────────────────────
    # 2. Retrieve relevant exercises
    # ─────────────────────────────────────────────────
    try:
        retrieval_result = await get_exercises_by_profile(
            simple_scores=effective_scores,
            detailed_faults=full_data
        )
        
        exercises = retrieval_result.get("data", [])
        
        print(f"🧐 DEBUG: RETRIEVED {len(exercises)} EXERCISES")
        if exercises:
            names = [ex.get('exercise_name', 'MISSING_NAME') for ex in exercises]
            print(f"Top exercises: {names[:5]}")
        else:
            print("⚠️ WARNING: No exercises found for this profile!")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval Error: {str(e)}")

    # ─────────────────────────────────────────────────
    # 3. Generate workout plan
    # ─────────────────────────────────────────────────
    try:
        final_plan = generate_workout_plan(analysis, exercises)
        final_plan["calculated_scores"] = effective_scores

        # ─────────────────────────────────────────────────
        # 4. Save to database (non-blocking)
        # ─────────────────────────────────────────────────
        try:
            input_entry = AssessmentInput(raw_json_data=full_data)
            db.add(input_entry)
            await db.flush()

            score_entry = AssessmentScore(
                input_id=input_entry.id,
                overhead_squat=effective_scores.get('overhead_squat', 0),
                hurdle_step=effective_scores.get('hurdle_step', 0),
                inline_lunge=effective_scores.get('inline_lunge', 0),
                shoulder_mobility=effective_scores.get('shoulder_mobility', 0),
                active_straight_leg_raise=effective_scores.get('active_straight_leg_raise', 0),
                trunk_stability_pushup=effective_scores.get('trunk_stability_pushup', 0),
                rotary_stability=effective_scores.get('rotary_stability', 0),
                total_score=analysis.get("total_score", 0),
                generated_workout=final_plan
            )
            db.add(score_entry)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"❌ DB Save Error (non-blocking): {str(e)}")

        return final_plan

    except Exception as e:
        print(f"Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation Error: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)