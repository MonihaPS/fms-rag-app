import streamlit as st
import requests
import os
import json

# ── CONFIGURATION ──
# Defaults to localhost for testing, but respects Render/Cloud env vars
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/generate-workout")

# Initialize session state for manual override
if 'use_manual_scores' not in st.session_state:
    st.session_state.use_manual_scores = False

# ── PAGE SETUP ──
st.set_page_config(page_title="FMS Smart Coach", page_icon="🏋️", layout="wide")

# ── HEADER ──
st.title("🏋️ AI Strength Coach: Detailed FMS Analyzer")
st.markdown("### From Screening to Programming (With Fault Specificity)")
st.markdown(f"**Backend Status:** Connecting to `{API_URL}`")
st.markdown("---")

# ── MAIN INPUT FORM ──
with st.form("fms_input_form"):
    st.subheader("📝 Athlete Scorecard & Fault Analysis")
    st.info("Enter Raw Scores (0-3) for Left/Right sides where applicable. Rate specific faults (0-1) to trigger corrective logic.")

    # Checkbox controls override
    use_manual_scores = st.checkbox(
        "Use manual FMS final scores (override auto-calculation logic)",
        value=st.session_state.use_manual_scores,
        key="manual_override_checkbox"
    )
    st.session_state.use_manual_scores = use_manual_scores
    
    # If manual override is OFF, we usually let backend calculate, 
    # but here we allow user to input the final score visually.
    slider_disabled = False 

    # ── 1. DEEP SQUAT (Symmetrical) ──
    with st.expander("1. Overhead Squat (Deep Squat)", expanded=True):
        col_ds_main, col_ds_faults = st.columns([1, 3])
        with col_ds_main:
            ds_score = st.number_input("Final Score", 0, 3, 0, key="ds_score")
        with col_ds_faults:
            t1, t2, t3, t4 = st.tabs(["Trunk", "Lower Limb", "Feet", "Upper Body"])
            with t1:
                ds_tu = st.number_input("Upright torso", 0, 1, key="ds_tu")
                ds_tefl = st.number_input("Excessive forward lean", 0, 1, key="ds_tefl")
                ds_trf = st.number_input("Rib flare", 0, 1, key="ds_trf")
                ds_tlf = st.number_input("Lumbar flexion", 0, 1, key="ds_tlf")
                ds_tlesb = st.number_input("Lumbar extension / sway back", 0, 1, key="ds_tlesb")
            with t2:
                ds_lktt = st.number_input("Knees track over toes", 0, 1, key="ds_lktt")
                ds_lkv = st.number_input("Knee valgus", 0, 1, key="ds_lkv")
                ds_lkvar = st.number_input("Knee varus", 0, 1, key="ds_lkvar")
                ds_lud = st.number_input("Uneven depth", 0, 1, key="ds_lud")
            with t3:
                ds_fhsd = st.number_input("Heels stay down", 0, 1, key="ds_fhsd")
                ds_fhl = st.number_input("Heels lift", 0, 1, key="ds_fhl")
                ds_fep = st.number_input("Excessive pronation", 0, 1, key="ds_fep")
                ds_fes = st.number_input("Excessive supination", 0, 1, key="ds_fes")
            with t4:
                ds_uba = st.number_input("Bar aligned over mid-foot", 0, 1, key="ds_uba")
                ds_ubdf = st.number_input("Bar drifts forward", 0, 1, key="ds_ubdf")
                ds_uaff = st.number_input("Arms fall forward", 0, 1, key="ds_uaff")
                ds_usr = st.number_input("Shoulder restriction", 0, 1, key="ds_usr")

    # ── 2. HURDLE STEP (Asymmetrical) ──
    with st.expander("2. Hurdle Step"):
        
        c1, c2, c3 = st.columns(3)
        hs_l_score = c1.number_input("Left Score", 0, 3, 0, key="hs_l_score")
        hs_r_score = c2.number_input("Right Score", 0, 3, 0, key="hs_r_score")
        hs_score = c3.number_input("Final Score", 0, 3, min(hs_l_score, hs_r_score), key="hs_score")
        
        t1, t2, t3 = st.tabs(["Pelvis/Core", "Stance Leg", "Stepping Leg"])
        with t1:
            hs_pps = st.number_input("Pelvis stable", 0, 1, key="hs_pps")
            hs_ppd = st.number_input("Pelvic drop", 0, 1, key="hs_ppd")
            hs_per = st.number_input("Excessive rotation", 0, 1, key="hs_per")
            hs_plob = st.number_input("Loss of balance", 0, 1, key="hs_plob")
        with t2:
            hs_sks = st.number_input("Knee stable", 0, 1, key="hs_sks")
            hs_skv = st.number_input("Knee valgus", 0, 1, key="hs_skv")
            hs_skvar = st.number_input("Knee varus", 0, 1, key="hs_skvar")
            hs_sai = st.number_input("Ankle instability", 0, 1, key="hs_sai")
        with t3:
            hs_stc = st.number_input("Clears hurdle", 0, 1, key="hs_stc")
            hs_sttd = st.number_input("Toe drag", 0, 1, key="hs_sttd")
            hs_sthr = st.number_input("Hip restriction", 0, 1, key="hs_sthr")
            hs_stam = st.number_input("Asymmetrical", 0, 1, key="hs_stam")

    # ── 3. INLINE LUNGE (Asymmetrical) ──
    with st.expander("3. Inline Lunge"):
        c1, c2, c3 = st.columns(3)
        il_l_score = c1.number_input("Left Score", 0, 3, 0, key="il_l_score")
        il_r_score = c2.number_input("Right Score", 0, 3, 0, key="il_r_score")
        il_score = c3.number_input("Final Score", 0, 3, min(il_l_score, il_r_score), key="il_score")

        t1, t2, t3 = st.tabs(["Alignment", "Lower Body", "Balance"])
        with t1:
            il_hn = st.number_input("Head neutral", 0, 1, key="il_hn")
            il_fh = st.number_input("Forward head", 0, 1, key="il_fh")
            il_tu = st.number_input("Trunk upright", 0, 1, key="il_tu")
            il_fl = st.number_input("Excessive lean", 0, 1, key="il_fl")
            il_ls = st.number_input("Lateral shift", 0, 1, key="il_ls")
        with t2:
            il_kt = st.number_input("Knee tracks", 0, 1, key="il_kt")
            il_kv = st.number_input("Knee valgus", 0, 1, key="il_kv")
            il_ki = st.number_input("Knee instability", 0, 1, key="il_ki")
            il_hl = st.number_input("Heel lift", 0, 1, key="il_hl")
        with t3:
            il_st = st.number_input("Stable", 0, 1, key="il_st")
            il_wb = st.number_input("Wobbling", 0, 1, key="il_wb")
            il_lob = st.number_input("Loss of balance", 0, 1, key="il_lob")
            il_uw = st.number_input("Unequal weight", 0, 1, key="il_uw")

    # ── 4. SHOULDER MOBILITY (Asymmetrical + Pain) ──
    with st.expander("4. Shoulder Mobility"):
        c1, c2, c3, c4 = st.columns(4)
        sm_l_score = c1.number_input("Left Score", 0, 3, 0, key="sm_l_score")
        sm_r_score = c2.number_input("Right Score", 0, 3, 0, key="sm_r_score")
        sm_clearing = c3.checkbox("Pain on Clearing?", key="sm_clearing")
        sm_score = c4.number_input("Final Score", 0, 3, 0 if sm_clearing else min(sm_l_score, sm_r_score), key="sm_score")

        t1, t2, t3 = st.tabs(["Reach Quality", "Compensation", "Pain Detail"])
        with t1:
            sm_fd = st.number_input("Fist distance", 0, 1, key="sm_fd")
            sm_hl = st.number_input("Hand length", 0, 1, key="sm_hl")
            sm_eg = st.number_input("Excessive gap", 0, 1, key="sm_eg")
            sm_as = st.number_input("Asymmetry", 0, 1, key="sm_as")
        with t2:
            sm_nc = st.number_input("No compensation", 0, 1, key="sm_nc")
            sm_sf = st.number_input("Spine flexion", 0, 1, key="sm_sf")
            sm_rf = st.number_input("Rib flare", 0, 1, key="sm_rf")
            sm_sw = st.number_input("Scapular winging", 0, 1, key="sm_sw")
        with t3:
            sm_np = st.number_input("No pain reported", 0, 1, key="sm_np")
            sm_pr = st.number_input("Pain reported", 0, 1, key="sm_pr")

    # ── 5. ASLR (Asymmetrical) ──
    with st.expander("5. Active Straight Leg Raise"):
        c1, c2, c3 = st.columns(3)
        aslr_l_score = c1.number_input("Left Score", 0, 3, 0, key="aslr_l_score")
        aslr_r_score = c2.number_input("Right Score", 0, 3, 0, key="aslr_r_score")
        aslr_score = c3.number_input("Final Score", 0, 3, min(aslr_l_score, aslr_r_score), key="aslr_score")

        t1, t2, t3 = st.tabs(["Non-Moving Leg", "Moving Leg", "Pelvis"])
        with t1:
            aslr_rf = st.number_input("Remains flat", 0, 1, key="aslr_rf")
            aslr_kb = st.number_input("Knee bends", 0, 1, key="aslr_kb")
            aslr_er = st.number_input("Ext rotation", 0, 1, key="aslr_er")
            aslr_fl = st.number_input("Foot lifts", 0, 1, key="aslr_fl")
        with t2:
            aslr_g80 = st.number_input(">80 flexion", 0, 1, key="aslr_g80")
            aslr_6080 = st.number_input("60-80 flexion", 0, 1, key="aslr_6080")
            aslr_l60 = st.number_input("<60 flexion", 0, 1, key="aslr_l60")
            aslr_hr = st.number_input("Hamstring restrict", 0, 1, key="aslr_hr")
        with t3:
            aslr_ps = st.number_input("Pelvis stable", 0, 1, key="aslr_ps")
            aslr_at = st.number_input("Ant tilt", 0, 1, key="aslr_at")
            aslr_pt = st.number_input("Post tilt", 0, 1, key="aslr_pt")

    # ── 6. TSPU (Symmetrical + Pain) ──
    with st.expander("6. Trunk Stability Pushup"):
        c1, c2 = st.columns(2)
        ts_clearing = c1.checkbox("Pain on Extension Clearing?", key="ts_clearing")
        tsp_score = c2.number_input("Final Score", 0, 3, 0 if ts_clearing else 0, key="tsp_score")

        t1, t2, t3 = st.tabs(["Alignment", "Core Control", "Upper Body"])
        with t1:
            tsp_ns = st.number_input("Neutral spine", 0, 1, key="tsp_ns")
            tsp_sh = st.number_input("Sagging hips", 0, 1, key="tsp_sh")
            tsp_pk = st.number_input("Pike", 0, 1, key="tsp_pk")
        with t2:
            tsp_ou = st.number_input("One unit", 0, 1, key="tsp_ou")
            tsp_hl = st.number_input("Hips lag", 0, 1, key="tsp_hl")
            tsp_le = st.number_input("Lumbar ext", 0, 1, key="tsp_le")
        with t3:
            tsp_ea = st.number_input("Elbows aligned", 0, 1, key="tsp_ea")
            tsp_up = st.number_input("Uneven push", 0, 1, key="tsp_up")
            tsp_si = st.number_input("Shoulder instab", 0, 1, key="tsp_si")

    # ── 7. ROTARY STABILITY (Asymmetrical + Pain) ──
    with st.expander("7. Rotary Stability"):
        c1, c2, c3, c4 = st.columns(4)
        rs_l_score = c1.number_input("Left Score", 0, 3, 0, key="rs_l_score")
        rs_r_score = c2.number_input("Right Score", 0, 3, 0, key="rs_r_score")
        rs_clearing = c3.checkbox("Pain on Flexion Clearing?", key="rs_clearing")
        rs_score = c4.number_input("Final Score", 0, 3, 0 if rs_clearing else min(rs_l_score, rs_r_score), key="rs_score")

        t1, t2, t3 = st.tabs(["Pattern", "Spinal Control", "Symmetry"])
        with t1:
            rs_sm = st.number_input("Smooth", 0, 1, key="rs_sm")
            rs_lob = st.number_input("Loss balance", 0, 1, key="rs_lob")
            rs_utc = st.number_input("Unable complete", 0, 1, key="rs_utc")
        with t2:
            rs_nm = st.number_input("Neutral maint", 0, 1, key="rs_nm")
            rs_er = st.number_input("Excess rot", 0, 1, key="rs_er")
            rs_ls = st.number_input("Lumbar shift", 0, 1, key="rs_ls")
        with t3:
            rs_sy = st.number_input("Symmetrical", 0, 1, key="rs_sy")
            rs_ld = st.number_input("Left deficit", 0, 1, key="rs_ld")
            rs_rd = st.number_input("Right deficit", 0, 1, key="rs_rd")

    st.markdown("---")
    submit_btn = st.form_submit_button("🚀 Generate Workout Plan", type="primary", use_container_width=True)

# ── SUBMISSION LOGIC ──
if submit_btn:
    # 1. Build Payload (Matching Backend Pydantic Models Exactly)
    payload = {
        "use_manual_scores": use_manual_scores,
        "overhead_squat": {
            "score": int(ds_score),
            "trunk_torso": {"upright_torso": int(ds_tu), "excessive_forward_lean": int(ds_tefl), "rib_flare": int(ds_trf), "lumbar_flexion": int(ds_tlf), "lumbar_extension_sway_back": int(ds_tlesb)},
            "lower_limb": {"knees_track_over_toes": int(ds_lktt), "knee_valgus": int(ds_lkv), "knee_varus": int(ds_lkvar), "uneven_depth": int(ds_lud)},
            "feet": {"heels_stay_down": int(ds_fhsd), "heels_lift": int(ds_fhl), "excessive_pronation": int(ds_fep), "excessive_supination": int(ds_fes)},
            "upper_body_bar_position": {"bar_aligned_over_mid_foot": int(ds_uba), "bar_drifts_forward": int(ds_ubdf), "arms_fall_forward": int(ds_uaff), "shoulder_mobility_restriction_suspected": int(ds_usr)}
        },
        "hurdle_step": {
            "score": int(hs_score),
            "l_score": int(hs_l_score), 
            "r_score": int(hs_r_score),
            "pelvis_core_control": {"pelvis_stable": int(hs_pps), "pelvic_drop_trendelenburg": int(hs_ppd), "excessive_rotation": int(hs_per), "loss_of_balance": int(hs_plob)},
            "stance_leg": {"knee_stable": int(hs_sks), "knee_valgus": int(hs_skv), "knee_varus": int(hs_skvar), "ankle_instability": int(hs_sai)},
            "stepping_leg": {"clears_hurdle_smoothly": int(hs_stc), "toe_drag": int(hs_sttd), "hip_flexion_restriction": int(hs_sthr), "asymmetrical_movement": int(hs_stam)}
        },
        "inline_lunge": {
            "score": int(il_score),
            "l_score": int(il_l_score),
            "r_score": int(il_r_score),
            "alignment": {"head_neutral": int(il_hn), "forward_head": int(il_fh), "trunk_upright": int(il_tu), "excessive_forward_lean": int(il_fl), "lateral_shift": int(il_ls)},
            "lower_body_control": {"knee_tracks_over_foot": int(il_kt), "knee_valgus": int(il_kv), "knee_instability": int(il_ki), "heel_lift": int(il_hl)},
            "balance_stability": {"stable_throughout": int(il_st), "wobbling": int(il_wb), "loss_of_balance": int(il_lob), "unequal_weight_distribution": int(il_uw)}
        },
        "shoulder_mobility": {
            "score": int(sm_score),
            "l_score": int(sm_l_score),
            "r_score": int(sm_r_score),
            "clearing_pain": bool(sm_clearing),
            "reach_quality": {"hands_within_fist_distance": int(sm_fd), "hands_within_hand_length": int(sm_hl), "excessive_gap": int(sm_eg), "asymmetry_present": int(sm_as)},
            "compensation": {"no_compensation": int(sm_nc), "spine_flexion": int(sm_sf), "rib_flare": int(sm_rf), "scapular_winging": int(sm_sw)},
            "pain": {"no_pain": int(sm_np), "pain_reported": int(sm_pr)}
        },
        "active_straight_leg_raise": {
            "score": int(aslr_score),
            "l_score": int(aslr_l_score),
            "r_score": int(aslr_r_score),
            "non_moving_leg": {"remains_flat": int(aslr_rf), "knee_bends": int(aslr_kb), "hip_externally_rotates": int(aslr_er), "foot_lifts_off_floor": int(aslr_fl)},
            "moving_leg": {"gt_80_hip_flexion": int(aslr_g80), "between_60_80_hip_flexion": int(aslr_6080), "lt_60_hip_flexion": int(aslr_l60), "hamstring_restriction": int(aslr_hr)},
            "pelvic_control": {"pelvis_stable": int(aslr_ps), "anterior_tilt": int(aslr_at), "posterior_tilt": int(aslr_pt)}
        },
        "trunk_stability_pushup": {
            "score": int(tsp_score),
            "clearing_pain": bool(ts_clearing),
            "body_alignment": {"neutral_spine_maintained": int(tsp_ns), "sagging_hips": int(tsp_sh), "pike_position": int(tsp_pk)},
            "core_control": {"initiates_as_one_unit": int(tsp_ou), "hips_lag": int(tsp_hl), "excessive_lumbar_extension": int(tsp_le)},
            "upper_body": {"elbows_aligned": int(tsp_ea), "uneven_arm_push": int(tsp_up), "shoulder_instability": int(tsp_si)}
        },
        "rotary_stability": {
            "score": int(rs_score),
            "l_score": int(rs_l_score),
            "r_score": int(rs_r_score),
            "clearing_pain": bool(rs_clearing),
            "diagonal_pattern": {"smooth_controlled": int(rs_sm), "loss_of_balance": int(rs_lob), "unable_to_complete": int(rs_utc)},
            "spinal_control": {"neutral_maintained": int(rs_nm), "excessive_rotation": int(rs_er), "lumbar_shift": int(rs_ls)},
            "symmetry": {"symmetrical": int(rs_sy), "left_side_deficit": int(rs_ld), "right_side_deficit": int(rs_rd)}
        }
    }

    # 2. Call API
    with st.spinner("🤖 AI Coach is analyzing faults and querying NeonDB..."):
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()

                if data.get('status') == "STOP":
                    st.error(f"🛑 MEDICAL REFERRAL REQUIRED: {data.get('reason', 'Pain detected.')}")
                
                # --- RESULTS DISPLAY ---
                color_map = {"Green": "green", "Yellow": "orange", "Red": "red"}
                ui_color = color_map.get(data.get("difficulty_color", "Green"), "blue")
                
                st.subheader(f"🎯 Target Session: :{ui_color}[{data.get('session_title', 'Workout')}]")
                st.info(f"**Coach's Logic:** {data.get('coach_summary', '')}")
                
                # --- RENDER EXERCISES ---
                st.markdown("### 📋 Prescribed Exercises")
                if data.get('exercises'):
                    grid = st.columns(3)
                    for i, exercise in enumerate(data['exercises']):
                        with grid[i % 3]:
                            tags = exercise.get('tags', [])
                            tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                            
                            st.markdown(f"""
                            <div style="padding: 20px; border: 1px solid #444; border-radius: 12px; background-color: #262730; height: 100%; display: flex; flexDirection: column; justifyContent: space-between;">
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