import json
import requests
import os
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# CONFIGURATION
API_ENDPOINT = "http://127.0.0.1:8000/generate-workout"
CONFIDENT_API_KEY = os.getenv("CONFIDENT_API_KEY")

def get_base_profile():
    """Helper to generate a clean, zero-fault profile structure"""
    return {
        "overhead_squat": {
            "score": 3,
            "trunk_torso": {"upright_torso": 0, "excessive_forward_lean": 0, "rib_flare": 0, "lumbar_flexion": 0, "lumbar_extension_sway_back": 0},
            "lower_limb": {"knees_track_over_toes": 0, "knee_valgus": 0, "knee_varus": 0, "uneven_depth": 0},
            "feet": {"heels_stay_down": 0, "heels_lift": 0, "excessive_pronation": 0, "excessive_supination": 0},
            "upper_body_bar_position": {"bar_aligned_over_mid_foot": 0, "bar_drifts_forward": 0, "arms_fall_forward": 0, "shoulder_mobility_restriction_suspected": 0}
        },
        "hurdle_step": {
            "score": 3,
            "pelvis_core_control": {"pelvis_stable": 0, "pelvic_drop_trendelenburg": 0, "excessive_rotation": 0, "loss_of_balance": 0},
            "stance_leg": {"knee_stable": 0, "knee_valgus": 0, "knee_varus": 0, "ankle_instability": 0},
            "stepping_leg": {"clears_hurdle_smoothly": 0, "toe_drag": 0, "hip_flexion_restriction": 0, "asymmetrical_movement": 0}
        },
        "inline_lunge": {
            "score": 3,
            "alignment": {"head_neutral": 0, "forward_head": 0, "trunk_upright": 0, "excessive_forward_lean": 0, "lateral_shift": 0},
            "lower_body_control": {"knee_tracks_over_foot": 0, "knee_valgus": 0, "knee_instability": 0, "heel_lift": 0},
            "balance_stability": {"stable_throughout": 0, "wobbling": 0, "loss_of_balance": 0, "unequal_weight_distribution": 0}
        },
        "shoulder_mobility": {
            "score": 3,
            "reach_quality": {"hands_within_fist_distance": 0, "hands_within_hand_length": 0, "excessive_gap": 0, "asymmetry_present": 0},
            "compensation": {"no_compensation": 0, "spine_flexion": 0, "rib_flare": 0, "scapular_winging": 0},
            "pain": {"no_pain": 0, "pain_reported": 0}
        },
        "active_straight_leg_raise": {
            "score": 3,
            "non_moving_leg": {"remains_flat": 0, "knee_bends": 0, "hip_externally_rotates": 0, "foot_lifts_off_floor": 0},
            "moving_leg": {"gt_80_hip_flexion": 0, "between_60_80_hip_flexion": 0, "lt_60_hip_flexion": 0, "hamstring_restriction": 0},
            "pelvic_control": {"pelvis_stable": 0, "anterior_tilt": 0, "posterior_tilt": 0}
        },
        "trunk_stability_pushup": {
            "score": 3,
            "body_alignment": {"neutral_spine_maintained": 0, "sagging_hips": 0, "pike_position": 0},
            "core_control": {"initiates_as_one_unit": 0, "hips_lag": 0, "excessive_lumbar_extension": 0},
            "upper_body": {"elbows_aligned": 0, "uneven_arm_push": 0, "shoulder_instability": 0}
        },
        "rotary_stability": {
            "score": 3,
            "diagonal_pattern": {"smooth_controlled": 0, "loss_of_balance": 0, "unable_to_complete": 0},
            "spinal_control": {"neutral_maintained": 0, "excessive_rotation": 0, "lumbar_shift": 0},
            "symmetry": {"symmetrical": 0, "left_side_deficit": 0, "right_side_deficit": 0}
        },
        "use_manual_scores": True 
    }

def call_api(input_payload):
    try:
        response = requests.post(API_ENDPOINT, json=input_payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Call Failed: {e}")
        return None

# --- TEST CASES ---

# Case 1: Perfect Athlete
perfect_input = get_base_profile()

# Case 2: Pain Detected (Should stop)
pain_input = get_base_profile()
pain_input["shoulder_mobility"]["pain"]["pain_reported"] = 4
pain_input["shoulder_mobility"]["score"] = 0

test_cases_data = [
    {
        "name": "Perfect Athlete",
        "input": perfect_input,
        "expected_contains": "Green", 
        "context": "FMS Scoring: High scores equal Green difficulty."
    },
    {
        "name": "Pain Protocol",
        "input": pain_input,
        "expected_contains": "Medical Referral",
        "context": "FMS Protocol: Any pain detection results in immediate referral."
    }
]

# --- RUN EVALUATION ---
eval_cases = []

print("🚀 Starting Confident AI Evaluation...")

for case in test_cases_data:
    print(f"Testing: {case['name']}...")
    actual_json = call_api(case["input"])
    
    if actual_json:
        actual_output = json.dumps(actual_json)
        
        test_case = LLMTestCase(
            input=json.dumps(case["input"]),
            actual_output=actual_output,
            expected_output=case["expected_contains"],
            retrieval_context=[case["context"]]
        )
        eval_cases.append(test_case)

# Execute DeepEval
if eval_cases:
    evaluate(
        test_cases=eval_cases,
        metrics=[
            AnswerRelevancyMetric(threshold=0.5),
            FaithfulnessMetric(threshold=0.5)
        ]
    )
else:
    print("❌ No test cases generated due to API errors.")