def analyze_fms_profile(profile):
    """
    Input: The full nested FMS profile dictionary from the frontend.
    Output: The specific 'Squat Level' (1-10) the athlete is cleared for, along with status and reason.
    """

    def compute_test_score(test, data):
        # Extract sub-data excluding the manual score
        sub_data = {k: v for k, v in data.items() if k != 'score'}
        
        # Flatten all severities
        sevs = []
        for group, faults in sub_data.items():
            for sev in faults.values():
                sevs.append(sev)
        
        if not sevs:
            return data['score']  # No sub-faults, use manual
        
        avg = sum(sevs) / len(sevs)
        max_sev = max(sevs)
        
        # Check for pain
        pain = 0
        if 'pain' in sub_data:
            pain = sub_data['pain'].get('pain_reported', 0)
        
        if pain > 0:
            return 0
        
        # Test-specific logic
        if test == 'overhead_squat':
            score = 3
            # Feet group: heels lift implies cannot achieve without elevation
            feet = sub_data.get('feet', {})
            if feet.get('heels_lift', 0) > 1 or feet.get('heels_stay_down', 0) > 1:
                score = min(score, 2)
            # Trunk & Torso: forward lean or lumbar issues
            trunk = sub_data.get('trunk_torso', {})
            if (trunk.get('excessive_forward_lean', 0) > 1 or
                trunk.get('upright_torso', 0) > 1 or
                trunk.get('lumbar_flexion', 0) > 1 or
                trunk.get('lumbar_extension_sway_back', 0) > 1):
                score = min(score, 1)
            # Lower Limb: knee alignment
            lower = sub_data.get('lower_limb', {})
            if (lower.get('knee_valgus', 0) > 1 or
                lower.get('knee_varus', 0) > 1 or
                lower.get('knees_track_over_toes', 0) > 1):
                score = min(score, 1)
            # Upper Body
            upper = sub_data.get('upper_body_bar_position', {})
            if (upper.get('bar_drifts_forward', 0) > 1 or
                upper.get('arms_fall_forward', 0) > 1 or
                upper.get('shoulder_mobility_restriction_suspected', 0) > 1 or
                upper.get('bar_aligned_over_mid_foot', 0) > 1):
                score = min(score, 1)
            if max_sev >= 4:
                score = 1
            return score
        
        elif test == 'hurdle_step':
            score = 3
            # Pelvis & Core: loss of balance or rotation
            pelvis = sub_data.get('pelvis_core_control', {})
            if (pelvis.get('pelvic_drop_trendelenburg', 0) > 1 or
                pelvis.get('excessive_rotation', 0) > 1 or
                pelvis.get('loss_of_balance', 0) > 1 or
                pelvis.get('pelvis_stable', 0) > 1):
                score = min(score, 2)
            # Stance Leg: alignment loss
            stance = sub_data.get('stance_leg', {})
            if (stance.get('knee_valgus', 0) > 1 or
                stance.get('knee_varus', 0) > 1 or
                stance.get('ankle_instability', 0) > 1 or
                stance.get('knee_stable', 0) > 1):
                score = min(score, 2)
            # Stepping Leg: contact or restriction
            stepping = sub_data.get('stepping_leg', {})
            if (stepping.get('toe_drag', 0) > 1 or
                stepping.get('hip_flexion_restriction', 0) > 1 or
                stepping.get('asymmetrical_movement', 0) > 1 or
                stepping.get('clears_hurdle_smoothly', 0) > 1):
                score = min(score, 2)
            if pelvis.get('loss_of_balance', 0) > 2 or stepping.get('toe_drag', 0) > 2:
                score = 1
            return score
        
        elif test == 'inline_lunge':
            score = 3
            # Alignment: lean or shift
            alignment = sub_data.get('alignment', {})
            if (alignment.get('excessive_forward_lean', 0) > 1 or
                alignment.get('lateral_shift', 0) > 1 or
                alignment.get('forward_head', 0) > 1 or
                alignment.get('trunk_upright', 0) > 1):
                score = min(score, 2)
            # Lower Body Control
            lower = sub_data.get('lower_body_control', {})
            if (lower.get('knee_valgus', 0) > 1 or
                lower.get('knee_instability', 0) > 1 or
                lower.get('heel_lift', 0) > 1 or
                lower.get('knee_tracks_over_foot', 0) > 1):
                score = min(score, 2)
            # Balance & Stability
            balance = sub_data.get('balance_stability', {})
            if (balance.get('wobbling', 0) > 1 or
                balance.get('loss_of_balance', 0) > 1 or
                balance.get('unequal_weight_distribution', 0) > 1 or
                balance.get('stable_throughout', 0) > 1):
                score = min(score, 2)
            if balance.get('loss_of_balance', 0) > 2:
                score = 1
            return score
        
        elif test == 'shoulder_mobility':
            reach = sub_data.get('reach_quality', {})
            if reach.get('hands_within_fist_distance', 0) <= 1:
                score = 3
            elif reach.get('hands_within_hand_length', 0) <= 1:
                score = 2
            else:
                score = 1
            if reach.get('asymmetry_present', 0) > 1:
                score -= 1
            if reach.get('excessive_gap', 0) > 2:
                score = min(score, 1)
            comp = sub_data.get('compensation', {})
            if max(comp.values(), default=0) > 2:
                score -= 1
            score = max(0, score)
            return score
        
        elif test == 'active_straight_leg_raise':
            moving = sub_data.get('moving_leg', {})
            if moving.get('gt_80_hip_flexion', 0) <= 1:
                score = 3
            elif moving.get('60_80_hip_flexion', 0) <= 1:
                score = 2
            else:
                score = 1
            if moving.get('hamstring_restriction', 0) > 2:
                score = min(score, 2)
            non = sub_data.get('non_moving_leg', {})
            if max(non.values(), default=0) > 1:
                score -= 1
            pelvic = sub_data.get('pelvic_control', {})
            if max(pelvic.values(), default=0) > 1:
                score -= 1
            score = max(0, score)
            return score
        
        elif test == 'trunk_stability_pushup':
            score = 3
            body = sub_data.get('body_alignment', {})
            if (body.get('sagging_hips', 0) > 1 or
                body.get('pike_position', 0) > 1 or
                body.get('neutral_spine_maintained', 0) > 1):
                score = min(score, 2)
            core = sub_data.get('core_control', {})
            if (core.get('hips_lag', 0) > 1 or
                core.get('excessive_lumbar_extension', 0) > 1 or
                core.get('initiates_as_one_unit', 0) > 1):
                score = min(score, 2)
            upper = sub_data.get('upper_body', {})
            if (upper.get('uneven_arm_push', 0) > 1 or
                upper.get('shoulder_instability', 0) > 1 or
                upper.get('elbows_aligned', 0) > 1):
                score = min(score, 2)
            if avg > 2:
                score = 1
            return score
        
        elif test == 'rotary_stability':
            score = 3
            diagonal = sub_data.get('diagonal_pattern', {})
            if diagonal.get('unable_to_complete', 0) > 1:
                score = 1
            if (diagonal.get('smooth_controlled', 0) > 1 or
                diagonal.get('loss_of_balance', 0) > 1):
                score = min(score, 2)
            spinal = sub_data.get('spinal_control', {})
            if (spinal.get('excessive_rotation', 0) > 1 or
                spinal.get('lumbar_shift', 0) > 1 or
                spinal.get('neutral_maintained', 0) > 1):
                score = min(score, 2)
            symmetry = sub_data.get('symmetry', {})
            if (symmetry.get('left_side_deficit', 0) > 1 or
                symmetry.get('right_side_deficit', 0) > 1 or
                symmetry.get('symmetrical', 0) > 1):
                score = min(score, 2)
            return score
        
        # General fallback
        if max_sev >= 4:
            return 1
        if avg > 1.5:
            return 1
        elif avg > 0.5:
            return 2
        else:
            return 3

    # Compute effective scores for each test
    effective_scores = {}
    for test in profile:
        if test == 'pain_present':
            continue
        data = profile[test]
        manual_score = data.get('score', 2)
        calculated = compute_test_score(test, data)
        # Use manual if not default (2), else calculated
        effective = manual_score if manual_score != 2 else calculated
        effective_scores[test] = effective

    # -----------------------------------------------------------
    # 1. RED LIGHT: MOBILITY (ASLR & Shoulder)
    # -----------------------------------------------------------
    aslr = effective_scores.get('active_straight_leg_raise', 3)
    shoulder = effective_scores.get('shoulder_mobility', 3)

    if aslr <= 1 or shoulder <= 1:
        return {
            "status": "MOBILITY",
            "target_level": 1,
            "reason": "Mobility restriction detected (ASLR or Shoulder <= 1). Reverting to Level 1 Correctives."
        }

    # -----------------------------------------------------------
    # 2. YELLOW LIGHT: MOTOR CONTROL (Rotary & Trunk)
    # -----------------------------------------------------------
    rotary = effective_scores.get('rotary_stability', 3)
    trunk = effective_scores.get('trunk_stability_pushup', 3)

    if rotary <= 1 or trunk <= 1:
        return {
            "status": "STABILITY",
            "target_level": 3, 
            "reason": "Core Stability restriction detected. Reverting to Level 3 Static/Stability work."
        }

    # -----------------------------------------------------------
    # 3. GREEN LIGHT: SQUAT PATTERN
    # Mobility and Core are cleared. Now look at the Squat score itself.
    # Also incorporate Hurdle and Inline if low, as they affect lower body pattern
    # -----------------------------------------------------------
    hurdle = effective_scores.get('hurdle_step', 3)
    inline = effective_scores.get('inline_lunge', 3)
    squat_score = effective_scores.get('overhead_squat', 1)
    
    # Adjust squat effective if related tests low
    adjusted_squat = min(squat_score, hurdle, inline)
    
    if adjusted_squat <= 1:
        return {
            "status": "PATTERN",
            "target_level": 5,
            "reason": "Foundations cleared, but Squat pattern is dysfunctional (or related lower body tests low). Target Level 5 Patterning."
        }
    elif adjusted_squat == 2:
        return {
            "status": "STRENGTH",
            "target_level": 7,
            "reason": "Squat pattern acceptable (2). Cleared for Level 7 Loading."
        }
    elif adjusted_squat == 3:
        return {
            "status": "POWER",
            "target_level": 9,
            "reason": "Squat pattern optimal (3). Cleared for Level 9 Performance/Power."
        }

    # Fallback
    return {"status": "ERROR", "target_level": 1, "reason": "Unknown profile."}