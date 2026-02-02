# frontend_demo.py: Updated for Streamlit Community Cloud - use os.getenv for API_URL, added pain handling check in results (red warning if STOP).

import streamlit as st
import requests
import os

# CONFIGURATION
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/generate-workout")

# Initialize session state for manual override
if 'use_manual_scores' not in st.session_state:
    st.session_state.use_manual_scores = False

# PAGE SETUP
st.set_page_config(page_title="FMS Smart Coach", page_icon="🏋️", layout="wide")

# --- HEADER ---
st.title("🏋️ AI Strength Coach: Detailed FMS Analyzer")
st.markdown("### From Screening to Programming (With Fault Specificity)")
st.markdown("---")

# --- MAIN INPUT FORM (CENTERED) ---
with st.form("fms_input_form"):
    st.subheader("📝 Athlete Scorecard & Fault Analysis")
    st.info("Enter the raw scores (0-3) and rate specific faults (0-4) where 0 is no fault and 4 is severe.")

    # Checkbox controls override
    use_manual_scores = st.checkbox(
        "Use manual FMS scores (override auto-calculation)",
        value=st.session_state.use_manual_scores,
        key="manual_override_checkbox"
    )

    # Sync checkbox with session state
    st.session_state.use_manual_scores = use_manual_scores

    # When unchecked, force scores to 0 (even if previously set)
    default_score = 0 if not use_manual_scores else None

    # Sliders are disabled when override is off
    slider_disabled = not use_manual_scores

    # Create a grid layout using columns
    # Row 1: Deep Squat & Hurdle Step
    col1, col2 = st.columns(2)

    with col1:
        # UI says "Overhead Squat", but backend typically expects "deep_squat" logic
        with st.expander("1. Overhead Squat (Deep Squat)", expanded=True):
            ds_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="ds_score")
            st.markdown("---")
            # Trunk & Torso
            st.markdown("**Trunk & Torso**")
            ds_trunk_upright_torso = st.number_input("Upright torso", 0, 4, 0, key="ds_trunk_upright_torso")
            ds_trunk_excessive_forward_lean = st.number_input("Excessive forward lean", 0, 4, 0, key="ds_trunk_excessive_forward_lean")
            ds_trunk_rib_flare = st.number_input("Rib flare", 0, 4, 0, key="ds_trunk_rib_flare")
            ds_trunk_lumbar_flexion = st.number_input("Lumbar flexion", 0, 4, 0, key="ds_trunk_lumbar_flexion")
            ds_trunk_lumbar_extension_sway_back = st.number_input("Lumbar extension / sway back", 0, 4, 0, key="ds_trunk_lumbar_extension_sway_back")
            # Lower Limb
            st.markdown("**Lower Limb**")
            ds_lower_knees_track_over_toes = st.number_input("Knees track over toes", 0, 4, 0, key="ds_lower_knees_track_over_toes")
            ds_lower_knee_valgus = st.number_input("Knee valgus", 0, 4, 0, key="ds_lower_knee_valgus")
            ds_lower_knee_varus = st.number_input("Knee varus", 0, 4, 0, key="ds_lower_knee_varus")
            ds_lower_uneven_depth = st.number_input("Uneven depth", 0, 4, 0, key="ds_lower_uneven_depth")
            # Feet
            st.markdown("**Feet**")
            ds_feet_heels_stay_down = st.number_input("Heels stay down", 0, 4, 0, key="ds_feet_heels_stay_down")
            ds_feet_heels_lift = st.number_input("Heels lift", 0, 4, 0, key="ds_feet_heels_lift")
            ds_feet_excessive_pronation = st.number_input("Excessive pronation", 0, 4, 0, key="ds_feet_excessive_pronation")
            ds_feet_excessive_supination = st.number_input("Excessive supination", 0, 4, 0, key="ds_feet_excessive_supination")
            # Upper Body / Bar Position
            st.markdown("**Upper Body / Bar Position**")
            ds_upper_bar_aligned_over_mid_foot = st.number_input("Bar aligned over mid-foot", 0, 4, 0, key="ds_upper_bar_aligned_over_mid_foot")
            ds_upper_bar_drifts_forward = st.number_input("Bar drifts forward", 0, 4, 0, key="ds_upper_bar_drifts_forward")
            ds_upper_arms_fall_forward = st.number_input("Arms fall forward", 0, 4, 0, key="ds_upper_arms_fall_forward")
            ds_upper_shoulder_mobility_restriction_suspected = st.number_input("Shoulder restriction suspected", 0, 4, 0, key="ds_upper_shoulder_mobility_restriction_suspected")

    with col2:
        with st.expander("2. Hurdle Step"):
            hs_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="hs_score")
            st.markdown("---")
            # Pelvis & Core Control
            st.markdown("**Pelvis & Core Control**")
            hs_pelvis_pelvis_stable = st.number_input("Pelvis stable", 0, 4, 0, key="hs_pelvis_pelvis_stable")
            hs_pelvis_pelvic_drop_trendelenburg = st.number_input("Pelvic drop (Trendelenburg)", 0, 4, 0, key="hs_pelvis_pelvic_drop_trendelenburg")
            hs_pelvis_excessive_rotation = st.number_input("Excessive rotation", 0, 4, 0, key="hs_pelvis_excessive_rotation")
            hs_pelvis_loss_of_balance = st.number_input("Loss of balance", 0, 4, 0, key="hs_pelvis_loss_of_balance")
            # Stance Leg
            st.markdown("**Stance Leg**")
            hs_stance_knee_stable = st.number_input("Knee stable", 0, 4, 0, key="hs_stance_knee_stable")
            hs_stance_knee_valgus = st.number_input("Knee valgus", 0, 4, 0, key="hs_stance_knee_valgus")
            hs_stance_knee_varus = st.number_input("Knee varus", 0, 4, 0, key="hs_stance_knee_varus")
            hs_stance_ankle_instability = st.number_input("Ankle instability", 0, 4, 0, key="hs_stance_ankle_instability")
            # Stepping Leg
            st.markdown("**Stepping Leg**")
            hs_stepping_clears_hurdle_smoothly = st.number_input("Clears hurdle smoothly", 0, 4, 0, key="hs_stepping_clears_hurdle_smoothly")
            hs_stepping_toe_drag = st.number_input("Toe drag", 0, 4, 0, key="hs_stepping_toe_drag")
            hs_stepping_hip_flexion_restriction = st.number_input("Hip flexion restriction", 0, 4, 0, key="hs_stepping_hip_flexion_restriction")
            hs_stepping_asymmetrical_movement = st.number_input("Asymmetrical movement", 0, 4, 0, key="hs_stepping_asymmetrical_movement")

    # Row 2: Inline Lunge & Shoulder Mobility
    col3, col4 = st.columns(2)

    with col3:
        with st.expander("3. Inline Lunge"):
            il_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="il_score")
            st.markdown("---")
            # Alignment
            st.markdown("**Alignment**")
            il_alignment_head_neutral = st.number_input("Head neutral", 0, 4, 0, key="il_alignment_head_neutral")
            il_alignment_forward_head = st.number_input("Forward head", 0, 4, 0, key="il_alignment_forward_head")
            il_alignment_trunk_upright = st.number_input("Trunk upright", 0, 4, 0, key="il_alignment_trunk_upright")
            il_alignment_excessive_forward_lean = st.number_input("Excessive forward lean", 0, 4, 0, key="il_alignment_excessive_forward_lean")
            il_alignment_lateral_shift = st.number_input("Lateral shift", 0, 4, 0, key="il_alignment_lateral_shift")
            # Lower Body Control
            st.markdown("**Lower Body Control**")
            il_lower_knee_tracks_over_foot = st.number_input("Knee tracks over foot", 0, 4, 0, key="il_lower_knee_tracks_over_foot")
            il_lower_knee_valgus = st.number_input("Knee valgus", 0, 4, 0, key="il_lower_knee_valgus")
            il_lower_knee_instability = st.number_input("Knee instability", 0, 4, 0, key="il_lower_knee_instability")
            il_lower_heel_lift = st.number_input("Heel lift", 0, 4, 0, key="il_lower_heel_lift")
            # Balance & Stability
            st.markdown("**Balance & Stability**")
            il_balance_stable_throughout = st.number_input("Stable throughout", 0, 4, 0, key="il_balance_stable_throughout")
            il_balance_wobbling = st.number_input("Wobbling", 0, 4, 0, key="il_balance_wobbling")
            il_balance_loss_of_balance = st.number_input("Loss of balance", 0, 4, 0, key="il_balance_loss_of_balance")
            il_balance_unequal_weight_distribution = st.number_input("Unequal weight distribution", 0, 4, 0, key="il_balance_unequal_weight_distribution")

    with col4:
        with st.expander("4. Shoulder Mobility"):
            sm_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="sm_score")
            st.markdown("---")
            # Reach Quality
            st.markdown("**Reach Quality**")
            sm_reach_hands_within_fist_distance = st.number_input("Hands within fist distance", 0, 4, 0, key="sm_reach_hands_within_fist_distance")
            sm_reach_hands_within_hand_length = st.number_input("Hands within hand length", 0, 4, 0, key="sm_reach_hands_within_hand_length")
            sm_reach_excessive_gap = st.number_input("Excessive gap", 0, 4, 0, key="sm_reach_excessive_gap")
            sm_reach_asymmetry_present = st.number_input("Asymmetry present", 0, 4, 0, key="sm_reach_asymmetry_present")
            # Compensation
            st.markdown("**Compensation**")
            sm_comp_no_compensation = st.number_input("No compensation", 0, 4, 0, key="sm_comp_no_compensation")
            sm_comp_spine_flexion = st.number_input("Spine flexion", 0, 4, 0, key="sm_comp_spine_flexion")
            sm_comp_rib_flare = st.number_input("Rib flare", 0, 4, 0, key="sm_comp_rib_flare")
            sm_comp_scapular_winging = st.number_input("Scapular winging", 0, 4, 0, key="sm_comp_scapular_winging")
            # Pain
            st.markdown("**Pain**")
            sm_pain_no_pain = st.number_input("No pain", 0, 4, 0, key="sm_pain_no_pain")
            sm_pain_pain_reported = st.number_input("Pain reported", 0, 4, 0, key="sm_pain_pain_reported")

    # Row 3: ASLR, Trunk Stability, Rotary Stability
    col5, col6, col7 = st.columns(3)

    with col5:
        with st.expander("5. Active Straight Leg Raise (ASLR)"):
            aslr_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="aslr_score")
            st.markdown("---")
            # Non-Moving Leg
            st.markdown("**Non-Moving Leg**")
            aslr_non_remains_flat = st.number_input("Remains flat", 0, 4, 0, key="aslr_non_remains_flat")
            aslr_non_knee_bends = st.number_input("Knee bends", 0, 4, 0, key="aslr_non_knee_bends")
            aslr_non_hip_externally_rotates = st.number_input("Hip externally rotates", 0, 4, 0, key="aslr_non_hip_externally_rotates")
            aslr_non_foot_lifts_off_floor = st.number_input("Foot lifts off floor", 0, 4, 0, key="aslr_non_foot_lifts_off_floor")
            # Moving Leg
            st.markdown("**Moving Leg**")
            aslr_moving_gt_80_hip_flexion = st.number_input(">80° hip flexion", 0, 4, 0, key="aslr_moving_gt_80_hip_flexion")
            aslr_moving_60_to_80_deg = st.number_input("60–80° hip flexion", 0, 4, 0, key="aslr_moving_60_to_80_deg")
            aslr_moving_lt_60_hip_flexion = st.number_input("<60° hip flexion", 0, 4, 0, key="aslr_moving_lt_60_hip_flexion")
            aslr_moving_hamstring_restriction = st.number_input("Hamstring restriction", 0, 4, 0, key="aslr_moving_hamstring_restriction")
            # Pelvic Control
            st.markdown("**Pelvic Control**")
            aslr_pelvic_pelvis_stable = st.number_input("Pelvis stable", 0, 4, 0, key="aslr_pelvic_pelvis_stable")
            aslr_pelvic_anterior_tilt = st.number_input("Anterior tilt", 0, 4, 0, key="aslr_pelvic_anterior_tilt")
            aslr_pelvic_posterior_tilt = st.number_input("Posterior tilt", 0, 4, 0, key="aslr_pelvic_posterior_tilt")

    with col6:
        with st.expander("6. Trunk Stability Push-Up"):
            tsp_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="tsp_score")
            st.markdown("---")
            # Body Alignment
            st.markdown("**Body Alignment**")
            tsp_body_neutral_spine_maintained = st.number_input("Neutral spine maintained", 0, 4, 0, key="tsp_body_neutral_spine_maintained")
            tsp_body_sagging_hips = st.number_input("Sagging hips", 0, 4, 0, key="tsp_body_sagging_hips")
            tsp_body_pike_position = st.number_input("Pike position", 0, 4, 0, key="tsp_body_pike_position")
            # Core Control
            st.markdown("**Core Control**")
            tsp_core_initiates_as_one_unit = st.number_input("Initiates as one unit", 0, 4, 0, key="tsp_core_initiates_as_one_unit")
            tsp_core_hips_lag = st.number_input("Hips lag", 0, 4, 0, key="tsp_core_hips_lag")
            tsp_core_excessive_lumbar_extension = st.number_input("Excessive lumbar extension", 0, 4, 0, key="tsp_core_excessive_lumbar_extension")
            # Upper Body
            st.markdown("**Upper Body**")
            tsp_upper_elbows_aligned = st.number_input("Elbows aligned", 0, 4, 0, key="tsp_upper_elbows_aligned")
            tsp_upper_uneven_arm_push = st.number_input("Uneven arm push", 0, 4, 0, key="tsp_upper_uneven_arm_push")
            tsp_upper_shoulder_instability = st.number_input("Shoulder instability", 0, 4, 0, key="tsp_upper_shoulder_instability")

    with col7:
        with st.expander("7. Rotary Stability"):
            rs_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="rs_score")
            st.markdown("---")
            # Diagonal Pattern
            st.markdown("**Diagonal Pattern**")
            rs_diagonal_smooth_controlled = st.number_input("Smooth & controlled", 0, 4, 0, key="rs_diagonal_smooth_controlled")
            rs_diagonal_loss_of_balance = st.number_input("Loss of balance", 0, 4, 0, key="rs_diagonal_loss_of_balance")
            rs_diagonal_unable_to_complete = st.number_input("Unable to complete", 0, 4, 0, key="rs_diagonal_unable_to_complete")
            # Spinal Control
            st.markdown("**Spinal Control**")
            rs_spinal_neutral_maintained = st.number_input("Neutral maintained", 0, 4, 0, key="rs_spinal_neutral_maintained")
            rs_spinal_excessive_rotation = st.number_input("Excessive rotation", 0, 4, 0, key="rs_spinal_excessive_rotation")
            rs_spinal_lumbar_shift = st.number_input("Lumbar shift", 0, 4, 0, key="rs_spinal_lumbar_shift")
            # Symmetry
            st.markdown("**Symmetry**")
            rs_symmetry_symmetrical = st.number_input("Symmetrical", 0, 4, 0, key="rs_symmetry_symmetrical")
            rs_symmetry_left_side_deficit = st.number_input("Left-side deficit", 0, 4, 0, key="rs_symmetry_left_side_deficit")
            rs_symmetry_right_side_deficit = st.number_input("Right-side deficit", 0, 4, 0, key="rs_symmetry_right_side_deficit")

    st.markdown("---")
    submit_btn = st.form_submit_button("🚀 Generate Workout Plan", type="primary", use_container_width=True)

# --- RESULTS SECTION ---
if submit_btn:
    # Construct the Nested JSON Payload
    payload = {
        "overhead_squat": {
            "score": ds_score,
            "trunk_torso": {
                "upright_torso": ds_trunk_upright_torso,
                "excessive_forward_lean": ds_trunk_excessive_forward_lean,
                "rib_flare": ds_trunk_rib_flare,
                "lumbar_flexion": ds_trunk_lumbar_flexion,
                "lumbar_extension_sway_back": ds_trunk_lumbar_extension_sway_back
            },
            "lower_limb": {
                "knees_track_over_toes": ds_lower_knees_track_over_toes,
                "knee_valgus": ds_lower_knee_valgus,
                "knee_varus": ds_lower_knee_varus,
                "uneven_depth": ds_lower_uneven_depth
            },
            "feet": {
                "heels_stay_down": ds_feet_heels_stay_down,
                "heels_lift": ds_feet_heels_lift,
                "excessive_pronation": ds_feet_excessive_pronation,
                "excessive_supination": ds_feet_excessive_supination
            },
            "upper_body_bar_position": {
                "bar_aligned_over_mid_foot": ds_upper_bar_aligned_over_mid_foot,
                "bar_drifts_forward": ds_upper_bar_drifts_forward,
                "arms_fall_forward": ds_upper_arms_fall_forward,
                "shoulder_mobility_restriction_suspected": ds_upper_shoulder_mobility_restriction_suspected
            }
        },
        "hurdle_step": {
            "score": hs_score,
            "pelvis_core_control": {
                "pelvis_stable": hs_pelvis_pelvis_stable,
                "pelvic_drop_trendelenburg": hs_pelvis_pelvic_drop_trendelenburg,
                "excessive_rotation": hs_pelvis_excessive_rotation,
                "loss_of_balance": hs_pelvis_loss_of_balance
            },
            "stance_leg": {
                "knee_stable": hs_stance_knee_stable,
                "knee_valgus": hs_stance_knee_valgus,
                "knee_varus": hs_stance_knee_varus,
                "ankle_instability": hs_stance_ankle_instability
            },
            "stepping_leg": {
                "clears_hurdle_smoothly": hs_stepping_clears_hurdle_smoothly,
                "toe_drag": hs_stepping_toe_drag,
                "hip_flexion_restriction": hs_stepping_hip_flexion_restriction,
                "asymmetrical_movement": hs_stepping_asymmetrical_movement
            }
        },
        "inline_lunge": {
            "score": il_score,
            "alignment": {
                "head_neutral": il_alignment_head_neutral,
                "forward_head": il_alignment_forward_head,
                "trunk_upright": il_alignment_trunk_upright,
                "excessive_forward_lean": il_alignment_excessive_forward_lean,
                "lateral_shift": il_alignment_lateral_shift
            },
            "lower_body_control": {
                "knee_tracks_over_foot": il_lower_knee_tracks_over_foot,
                "knee_valgus": il_lower_knee_valgus,
                "knee_instability": il_lower_knee_instability,
                "heel_lift": il_lower_heel_lift
            },
            "balance_stability": {
                "stable_throughout": il_balance_stable_throughout,
                "wobbling": il_balance_wobbling,
                "loss_of_balance": il_balance_loss_of_balance,
                "unequal_weight_distribution": il_balance_unequal_weight_distribution
            }
        },
        "shoulder_mobility": {
            "score": sm_score,
            "reach_quality": {
                "hands_within_fist_distance": sm_reach_hands_within_fist_distance,
                "hands_within_hand_length": sm_reach_hands_within_hand_length,
                "excessive_gap": sm_reach_excessive_gap,
                "asymmetry_present": sm_reach_asymmetry_present
            },
            "compensation": {
                "no_compensation": sm_comp_no_compensation,
                "spine_flexion": sm_comp_spine_flexion,
                "rib_flare": sm_comp_rib_flare,
                "scapular_winging": sm_comp_scapular_winging
            },
            "pain": {
                "no_pain": sm_pain_no_pain,
                "pain_reported": sm_pain_pain_reported
            }
        },
        "active_straight_leg_raise": {
            "score": aslr_score,
            "non_moving_leg": {
                "remains_flat": aslr_non_remains_flat,
                "knee_bends": aslr_non_knee_bends,
                "hip_externally_rotates": aslr_non_hip_externally_rotates,
                "foot_lifts_off_floor": aslr_non_foot_lifts_off_floor
            },
            "moving_leg": {
                "gt_80_hip_flexion": aslr_moving_gt_80_hip_flexion,
                "between_60_80_hip_flexion": aslr_moving_60_to_80_deg,
                "lt_60_hip_flexion": aslr_moving_lt_60_hip_flexion,
                "hamstring_restriction": aslr_moving_hamstring_restriction
            },
            "pelvic_control": {
                "pelvis_stable": aslr_pelvic_pelvis_stable,
                "anterior_tilt": aslr_pelvic_anterior_tilt,
                "posterior_tilt": aslr_pelvic_posterior_tilt
            }
        },
        "trunk_stability_pushup": {
            "score": tsp_score,
            "body_alignment": {
                "neutral_spine_maintained": tsp_body_neutral_spine_maintained,
                "sagging_hips": tsp_body_sagging_hips,
                "pike_position": tsp_body_pike_position
            },
            "core_control": {
                "initiates_as_one_unit": tsp_core_initiates_as_one_unit,
                "hips_lag": tsp_core_hips_lag,
                "excessive_lumbar_extension": tsp_core_excessive_lumbar_extension
            },
            "upper_body": {
                "elbows_aligned": tsp_upper_elbows_aligned,
                "uneven_arm_push": tsp_upper_uneven_arm_push,
                "shoulder_instability": tsp_upper_shoulder_instability
            }
        },
        "rotary_stability": {
            "score": rs_score,
            "diagonal_pattern": {
                "smooth_controlled": rs_diagonal_smooth_controlled,
                "loss_of_balance": rs_diagonal_loss_of_balance,
                "unable_to_complete": rs_diagonal_unable_to_complete
            },
            "spinal_control": {
                "neutral_maintained": rs_spinal_neutral_maintained,
                "excessive_rotation": rs_spinal_excessive_rotation,
                "lumbar_shift": rs_spinal_lumbar_shift
            },
            "symmetry": {
                "symmetrical": rs_symmetry_symmetrical,
                "left_side_deficit": rs_symmetry_left_side_deficit,
                "right_side_deficit": rs_symmetry_right_side_deficit
            }
        }
    }

    st.divider()
    
    with st.spinner("🤖 AI Coach is analyzing faults and retrieving corrective strategies..."):
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                
                # Check for STOP (pain)
                if data.get('status') == "STOP":
                    st.error(data.get('reason', "Pain detected — Medical referral recommended. No exercises generated."))
                
                
                # Display effective scores if available
                if 'effective_scores' in data:
                    st.subheader("Calculated Effective FMS Scores (Based on Faults)")
                    st.json(data['effective_scores'])
                
                # --- RESULTS DISPLAY ---
                color_map = {"Green": "green", "Yellow": "orange", "Red": "red"}
                ui_color = color_map.get(data.get("difficulty_color", "Green"), "blue")
                
                st.subheader(f"🎯 Target Session: :{ui_color}[{data['session_title']}]")
                st.info(f"**Coach's Logic:** {data['coach_summary']}")
                
                st.markdown("### 📋 Prescribed Exercises")
                
                if data['exercises']:
                    grid = st.columns(3)
                    for i, exercise in enumerate(data['exercises']):
                        with grid[i % 3]:
                            st.markdown(f"""
                            <div style="
                                padding: 20px;
                                border: 1px solid #444;
                                border-radius: 12px;
                                background-color: #262730;
                                height: 100%;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                            ">
                                <div>
                                    <h4 style="color: #FF4B4B; margin-top: 0;">{exercise['name']}</h4>
                                    <span style="background: #333; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; letter-spacing: 0.5px;">{exercise['tag'].upper()}</span>
                                    <p style="margin-top: 15px; font-weight: bold; font-size: 1.1em;">{exercise['sets_reps']}</p>
                                    <p style="color: #bbb; font-size: 0.9em;">Tempo: {exercise['tempo']}</p>
                                </div>
                                <div>
                                    <hr style="border-color: #444;">
                                    <p style="font-style: italic; color: #ddd; font-size: 0.95em;">💡 "{exercise['coach_tip']}"</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No specific exercises generated. Please check your inputs.")

                with st.expander("🔍 View Raw API Data (Debug)"):
                    st.json(data)

            else:
                st.error(f"API Error: {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to Backend. Is the backend running?")