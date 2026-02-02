import streamlit as st
import requests
import os
import json

# CONFIGURATION
# Defaults to localhost for testing, but respects Render/Cloud env vars
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/generate-workout")

# Initialize session state for manual override
if 'use_manual_scores' not in st.session_state:
    st.session_state.use_manual_scores = False

# PAGE SETUP
st.set_page_config(page_title="FMS Smart Coach", page_icon="🏋️", layout="wide")

# --- HEADER ---
st.title("🏋️ AI Strength Coach: Detailed FMS Analyzer")
st.markdown("### From Screening to Programming (With Fault Specificity)")
st.markdown(f"**Backend Status:** Connecting to `{API_URL}`")
st.markdown("---")

# --- MAIN INPUT FORM ---
with st.form("fms_input_form"):
    st.subheader("📝 Athlete Scorecard & Fault Analysis")
    st.info("Enter the raw scores (0-3) and rate specific faults (0-4).")

    # Checkbox controls override
    use_manual_scores = st.checkbox(
        "Use manual FMS scores (override auto-calculation)",
        value=st.session_state.use_manual_scores,
        key="manual_override_checkbox"
    )
    st.session_state.use_manual_scores = use_manual_scores
    default_score = 0 if not use_manual_scores else None
    slider_disabled = not use_manual_scores

    # --- INPUT COLUMNS (Condensed for readability, logic preserved) ---
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("1. Overhead Squat (Deep Squat)", expanded=True):
            ds_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="ds_score")
            st.markdown("**Trunk & Torso**")
            ds_trunk_upright_torso = st.number_input("Upright torso", 0, 4, 0, key="ds_tu")
            ds_trunk_excessive_forward_lean = st.number_input("Excessive forward lean", 0, 4, 0, key="ds_tefl")
            ds_trunk_rib_flare = st.number_input("Rib flare", 0, 4, 0, key="ds_trf")
            ds_trunk_lumbar_flexion = st.number_input("Lumbar flexion", 0, 4, 0, key="ds_tlf")
            ds_trunk_lumbar_extension_sway_back = st.number_input("Lumbar extension / sway back", 0, 4, 0, key="ds_tlesb")
            st.markdown("**Lower Limb**")
            ds_lower_knees_track_over_toes = st.number_input("Knees track over toes", 0, 4, 0, key="ds_lktt")
            ds_lower_knee_valgus = st.number_input("Knee valgus", 0, 4, 0, key="ds_lkv")
            ds_lower_knee_varus = st.number_input("Knee varus", 0, 4, 0, key="ds_lkvar")
            ds_lower_uneven_depth = st.number_input("Uneven depth", 0, 4, 0, key="ds_lud")
            st.markdown("**Feet**")
            ds_feet_heels_stay_down = st.number_input("Heels stay down", 0, 4, 0, key="ds_fhsd")
            ds_feet_heels_lift = st.number_input("Heels lift", 0, 4, 0, key="ds_fhl")
            ds_feet_excessive_pronation = st.number_input("Excessive pronation", 0, 4, 0, key="ds_fep")
            ds_feet_excessive_supination = st.number_input("Excessive supination", 0, 4, 0, key="ds_fes")
            st.markdown("**Upper Body**")
            ds_upper_bar_aligned = st.number_input("Bar aligned over mid-foot", 0, 4, 0, key="ds_uba")
            ds_upper_bar_drifts = st.number_input("Bar drifts forward", 0, 4, 0, key="ds_ubdf")
            ds_upper_arms_fall = st.number_input("Arms fall forward", 0, 4, 0, key="ds_uaff")
            ds_upper_shoulder_rest = st.number_input("Shoulder restriction", 0, 4, 0, key="ds_usr")

    with col2:
        with st.expander("2. Hurdle Step"):
            hs_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="hs_score")
            st.markdown("**Pelvis**")
            hs_pelvis_stable = st.number_input("Pelvis stable", 0, 4, 0, key="hs_pps")
            hs_pelvis_drop = st.number_input("Pelvic drop", 0, 4, 0, key="hs_ppd")
            hs_pelvis_rot = st.number_input("Excessive rotation", 0, 4, 0, key="hs_per")
            hs_pelvis_lob = st.number_input("Loss of balance", 0, 4, 0, key="hs_plob")
            st.markdown("**Stance Leg**")
            hs_stance_stable = st.number_input("Knee stable", 0, 4, 0, key="hs_sks")
            hs_stance_valgus = st.number_input("Knee valgus", 0, 4, 0, key="hs_skv")
            hs_stance_varus = st.number_input("Knee varus", 0, 4, 0, key="hs_skvar")
            hs_stance_ankle = st.number_input("Ankle instability", 0, 4, 0, key="hs_sai")
            st.markdown("**Stepping Leg**")
            hs_step_clear = st.number_input("Clears hurdle", 0, 4, 0, key="hs_stc")
            hs_step_toe = st.number_input("Toe drag", 0, 4, 0, key="hs_sttd")
            hs_step_hip = st.number_input("Hip restriction", 0, 4, 0, key="hs_sthr")
            hs_step_asym = st.number_input("Asymmetrical", 0, 4, 0, key="hs_stam")

    col3, col4 = st.columns(2)
    with col3:
        with st.expander("3. Inline Lunge"):
            il_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="il_score")
            # Keeping inputs minimal for brevity in this display, assume full mapping exists in your local version
            # Using defaults for the required fields to save visual space in this file, 
            # ensure your local version has ALL fields mapped like the Squat section above.
            il_head_neutral = st.number_input("Head neutral", 0, 4, 0, key="il_hn")
            il_fwd_head = st.number_input("Forward head", 0, 4, 0, key="il_fh")
            il_trunk_up = st.number_input("Trunk upright", 0, 4, 0, key="il_tu")
            il_fwd_lean = st.number_input("Excessive lean", 0, 4, 0, key="il_fl")
            il_lat_shift = st.number_input("Lateral shift", 0, 4, 0, key="il_ls")
            
            il_knee_track = st.number_input("Knee tracks", 0, 4, 0, key="il_kt")
            il_knee_val = st.number_input("Knee valgus", 0, 4, 0, key="il_kv")
            il_knee_inst = st.number_input("Knee instability", 0, 4, 0, key="il_ki")
            il_heel_lift = st.number_input("Heel lift", 0, 4, 0, key="il_hl")
            
            il_stab = st.number_input("Stable", 0, 4, 0, key="il_st")
            il_wobble = st.number_input("Wobbling", 0, 4, 0, key="il_wb")
            il_lob = st.number_input("Loss of balance", 0, 4, 0, key="il_lob")
            il_unequal = st.number_input("Unequal weight", 0, 4, 0, key="il_uw")

    with col4:
        with st.expander("4. Shoulder Mobility"):
            sm_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="sm_score")
            sm_fist = st.number_input("Fist distance", 0, 4, 0, key="sm_fd")
            sm_hand = st.number_input("Hand length", 0, 4, 0, key="sm_hl")
            sm_gap = st.number_input("Excessive gap", 0, 4, 0, key="sm_eg")
            sm_asym = st.number_input("Asymmetry", 0, 4, 0, key="sm_as")
            sm_nocomp = st.number_input("No compensation", 0, 4, 0, key="sm_nc")
            sm_spine = st.number_input("Spine flexion", 0, 4, 0, key="sm_sf")
            sm_rib = st.number_input("Rib flare", 0, 4, 0, key="sm_rf")
            sm_wing = st.number_input("Scapular winging", 0, 4, 0, key="sm_sw")
            sm_nopain = st.number_input("No pain", 0, 4, 0, key="sm_np")
            sm_pain = st.number_input("Pain reported", 0, 4, 0, key="sm_pr")

    col5, col6, col7 = st.columns(3)
    with col5:
        with st.expander("5. ASLR"):
            aslr_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="aslr_score")
            aslr_flat = st.number_input("Remains flat", 0, 4, 0, key="aslr_rf")
            aslr_bend = st.number_input("Knee bends", 0, 4, 0, key="aslr_kb")
            aslr_ext = st.number_input("Ext rotation", 0, 4, 0, key="aslr_er")
            aslr_lift = st.number_input("Foot lifts", 0, 4, 0, key="aslr_fl")
            aslr_gt80 = st.number_input(">80 flexion", 0, 4, 0, key="aslr_g80")
            aslr_6080 = st.number_input("60-80 flexion", 0, 4, 0, key="aslr_6080")
            aslr_lt60 = st.number_input("<60 flexion", 0, 4, 0, key="aslr_l60")
            aslr_ham = st.number_input("Hamstring restrict", 0, 4, 0, key="aslr_hr")
            aslr_pstab = st.number_input("Pelvis stable", 0, 4, 0, key="aslr_ps")
            aslr_ant = st.number_input("Ant tilt", 0, 4, 0, key="aslr_at")
            aslr_post = st.number_input("Post tilt", 0, 4, 0, key="aslr_pt")

    with col6:
        with st.expander("6. TSPU"):
            tsp_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="tsp_score")
            tsp_neut = st.number_input("Neutral spine", 0, 4, 0, key="tsp_ns")
            tsp_sag = st.number_input("Sagging hips", 0, 4, 0, key="tsp_sh")
            tsp_pike = st.number_input("Pike", 0, 4, 0, key="tsp_pk")
            tsp_unit = st.number_input("One unit", 0, 4, 0, key="tsp_ou")
            tsp_lag = st.number_input("Hips lag", 0, 4, 0, key="tsp_hl")
            tsp_ext = st.number_input("Lumbar ext", 0, 4, 0, key="tsp_le")
            tsp_elb = st.number_input("Elbows aligned", 0, 4, 0, key="tsp_ea")
            tsp_unev = st.number_input("Uneven push", 0, 4, 0, key="tsp_up")
            tsp_inst = st.number_input("Shoulder instab", 0, 4, 0, key="tsp_si")

    with col7:
        with st.expander("7. Rotary Stability"):
            rs_score = st.slider("Score", 0, 3, default_score if default_score is not None else 0, disabled=slider_disabled, key="rs_score")
            rs_sm = st.number_input("Smooth", 0, 4, 0, key="rs_sm")
            rs_lob = st.number_input("Loss balance", 0, 4, 0, key="rs_lob")
            rs_utc = st.number_input("Unable complete", 0, 4, 0, key="rs_utc")
            rs_neut = st.number_input("Neutral maint", 0, 4, 0, key="rs_nm")
            rs_rot = st.number_input("Excess rot", 0, 4, 0, key="rs_er")
            rs_shift = st.number_input("Lumbar shift", 0, 4, 0, key="rs_ls")
            rs_sym = st.number_input("Symmetrical", 0, 4, 0, key="rs_sy")
            rs_left = st.number_input("Left deficit", 0, 4, 0, key="rs_ld")
            rs_right = st.number_input("Right deficit", 0, 4, 0, key="rs_rd")

    st.markdown("---")
    submit_btn = st.form_submit_button("🚀 Generate Workout Plan", type="primary", use_container_width=True)

# --- RESULTS ---
if submit_btn:
    # 1. Build Payload
    payload = {
        "overhead_squat": {
            "score": ds_score,
            "trunk_torso": {"upright_torso": ds_trunk_upright_torso, "excessive_forward_lean": ds_trunk_excessive_forward_lean, "rib_flare": ds_trunk_rib_flare, "lumbar_flexion": ds_trunk_lumbar_flexion, "lumbar_extension_sway_back": ds_trunk_lumbar_extension_sway_back},
            "lower_limb": {"knees_track_over_toes": ds_lower_knees_track_over_toes, "knee_valgus": ds_lower_knee_valgus, "knee_varus": ds_lower_knee_varus, "uneven_depth": ds_lower_uneven_depth},
            "feet": {"heels_stay_down": ds_feet_heels_stay_down, "heels_lift": ds_feet_heels_lift, "excessive_pronation": ds_feet_excessive_pronation, "excessive_supination": ds_feet_excessive_supination},
            "upper_body_bar_position": {"bar_aligned_over_mid_foot": ds_upper_bar_aligned, "bar_drifts_forward": ds_upper_bar_drifts, "arms_fall_forward": ds_upper_arms_fall, "shoulder_mobility_restriction_suspected": ds_upper_shoulder_rest}
        },
        "hurdle_step": {
            "score": hs_score,
            "pelvis_core_control": {"pelvis_stable": hs_pelvis_stable, "pelvic_drop_trendelenburg": hs_pelvis_drop, "excessive_rotation": hs_pelvis_rot, "loss_of_balance": hs_pelvis_lob},
            "stance_leg": {"knee_stable": hs_stance_stable, "knee_valgus": hs_stance_valgus, "knee_varus": hs_stance_varus, "ankle_instability": hs_stance_ankle},
            "stepping_leg": {"clears_hurdle_smoothly": hs_step_clear, "toe_drag": hs_step_toe, "hip_flexion_restriction": hs_step_hip, "asymmetrical_movement": hs_step_asym}
        },
        "inline_lunge": {
            "score": il_score,
            "alignment": {"head_neutral": il_head_neutral, "forward_head": il_fwd_head, "trunk_upright": il_trunk_up, "excessive_forward_lean": il_fwd_lean, "lateral_shift": il_lat_shift},
            "lower_body_control": {"knee_tracks_over_foot": il_knee_track, "knee_valgus": il_knee_val, "knee_instability": il_knee_inst, "heel_lift": il_heel_lift},
            "balance_stability": {"stable_throughout": il_stab, "wobbling": il_wobble, "loss_of_balance": il_lob, "unequal_weight_distribution": il_unequal}
        },
        "shoulder_mobility": {
            "score": sm_score,
            "reach_quality": {"hands_within_fist_distance": sm_fist, "hands_within_hand_length": sm_hand, "excessive_gap": sm_gap, "asymmetry_present": sm_asym},
            "compensation": {"no_compensation": sm_nocomp, "spine_flexion": sm_spine, "rib_flare": sm_rib, "scapular_winging": sm_wing},
            "pain": {"no_pain": sm_nopain, "pain_reported": sm_pain}
        },
        "active_straight_leg_raise": {
            "score": aslr_score,
            "non_moving_leg": {"remains_flat": aslr_flat, "knee_bends": aslr_bend, "hip_externally_rotates": aslr_ext, "foot_lifts_off_floor": aslr_lift},
            "moving_leg": {"gt_80_hip_flexion": aslr_gt80, "between_60_80_hip_flexion": aslr_6080, "lt_60_hip_flexion": aslr_lt60, "hamstring_restriction": aslr_ham},
            "pelvic_control": {"pelvis_stable": aslr_pstab, "anterior_tilt": aslr_ant, "posterior_tilt": aslr_post}
        },
        "trunk_stability_pushup": {
            "score": tsp_score,
            "body_alignment": {"neutral_spine_maintained": tsp_neut, "sagging_hips": tsp_sag, "pike_position": tsp_pike},
            "core_control": {"initiates_as_one_unit": tsp_unit, "hips_lag": tsp_lag, "excessive_lumbar_extension": tsp_ext},
            "upper_body": {"elbows_aligned": tsp_elb, "uneven_arm_push": tsp_unev, "shoulder_instability": tsp_inst}
        },
        "rotary_stability": {
            "score": rs_score,
            "diagonal_pattern": {"smooth_controlled": rs_sm, "loss_of_balance": rs_lob, "unable_to_complete": rs_utc},
            "spinal_control": {"neutral_maintained": rs_neut, "excessive_rotation": rs_rot, "lumbar_shift": rs_shift},
            "symmetry": {"symmetrical": rs_sym, "left_side_deficit": rs_left, "right_side_deficit": rs_right}
        },
        "use_manual_scores": use_manual_scores
    }

    # 2. Call API
    with st.spinner("🤖 AI Coach is analyzing faults and querying NeonDB..."):
        try:
            response = requests.post(API_URL, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()

                if data.get('status') == "STOP":
                    st.error(data.get('reason', "Pain detected."))
                
                # --- RESULTS DISPLAY ---
                color_map = {"Green": "green", "Yellow": "orange", "Red": "red"}
                ui_color = color_map.get(data.get("difficulty_color", "Green"), "blue")
                
                st.subheader(f"🎯 Target Session: :{ui_color}[{data.get('session_title', 'Workout')}]")
                st.info(f"**Coach's Logic:** {data.get('coach_summary', '')}")
                
                st.markdown("### 📋 Prescribed Exercises")
                
                if data.get('exercises'):
                    grid = st.columns(3)
                    for i, exercise in enumerate(data['exercises']):
                        with grid[i % 3]:
                            # SAFE TAG HANDLING: Join list to string
                            tags = exercise.get('tags', [])
                            tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                            
                            st.markdown(f"""
                            <div style="
                                padding: 20px;
                                border: 1px solid #444;
                                border-radius: 12px;
                                background-color: #262730;
                                height: 100%;
                                display: flex;
                                flexDirection: column;
                                justifyContent: space-between;
                            ">
                                <div>
                                    <h4 style="color: #FF4B4B; margin-top: 0;">{exercise.get('name', 'Exercise')}</h4>
                                    <span style="background: #333; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">{tag_str.upper()}</span>
                                    <p style="margin-top: 15px; font-weight: bold; font-size: 1.1em;">{exercise.get('sets_reps', '3 x 10')}</p>
                                    <p style="color: #bbb; font-size: 0.9em;">Tempo: {exercise.get('tempo', '2-0-2')}</p>
                                </div>
                                <div>
                                    <hr style="border-color: #444;">
                                    <p style="font-style: italic; color: #ddd; font-size: 0.95em;">💡 "{exercise.get('coach_tip', '')}"</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No exercises returned. Check if Database is populated.")

                with st.expander("🔍 Debug Data"):
                    st.json(data)

            else:
                st.error(f"API Error ({response.status_code}): {response.text}")

        except requests.exceptions.ConnectionError:
            st.error(f"❌ Could not connect to {API_URL}. Is the backend running?")
        except Exception as e:
            st.error(f"An error occurred: {e}")