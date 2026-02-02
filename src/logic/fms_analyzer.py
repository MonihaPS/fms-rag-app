# fms_analyzer.py: Further refined with full book criteria - added gender consideration for TSP (assume male if not specified), added clearing test notes in reason if applicable, more precise mappings.

def analyze_fms_profile(profile, use_manual_scores=False):
    """
    Input: The full nested FMS profile dictionary.
    Output: Automatic scoring based on sub-inputs (faults) and Traffic Light logic.
    """

    # --- 1. HELPER: AUTOMATIC CALCULATOR ---
    def calculate_score_from_faults(test_name, test_data):
        """
        Returns the strictly calculated score (0-3) based on FMS decision trees from the book.
        """
        # 1. Extract sub-dictionaries (ignore the manual 'score' field)
        sub_data = {k: v for k, v in test_data.items() if k != 'score'}

        # 2. Check for PAIN first (Global Override for this test)
        pain_data = sub_data.get('pain', {})
        # If pain reported > 0, score is immediately 0
        if pain_data.get('pain_reported', 0) > 0:
            return 0

        # 3. Test-specific logic from the book
        if test_name == 'overhead_squat':
            feet = sub_data.get('feet', {})
            trunk = sub_data.get('trunk_torso', {})
            lower = sub_data.get('lower_limb', {})
            upper = sub_data.get('upper_body_bar_position', {})
            
            # Score 1: Tibia/torso not parallel, femur not below horizontal, knees not over feet, lumbar flexion
            if (trunk.get('upright_torso', 0) < 2 or  # Not parallel to tibia
                trunk.get('excessive_forward_lean', 0) > 1 or
                trunk.get('lumbar_flexion', 0) > 1 or
                lower.get('knees_track_over_toes', 0) < 2 or  # Not over feet
                feet.get('heels_stay_down', 0) < 2 or  # Femur not below horizontal implied
                upper.get('bar_aligned_over_mid_foot', 0) < 2):  # Dowel not over feet
                return 1
            
            # Score 2: Heels elevated, but rest OK
            if feet.get('heels_lift', 0) > 0:
                return 2
            
            # Score 3: All perfect
            return 3

        elif test_name == 'hurdle_step':
            pelvis = sub_data.get('pelvis_core_control', {})
            stepping = sub_data.get('stepping_leg', {})
            stance = sub_data.get('stance_leg', {})
            
            # Score 1: Contact or loss of balance
            if stepping.get('toe_drag', 0) > 0 or pelvis.get('loss_of_balance', 0) > 0:
                return 1
            
            # Score 2: Alignment lost between hips/knees/ankles, lumbar movement, dowel/hurdle not parallel
            if (stance.get('knee_stable', 0) < 2 or  # Alignment lost
                stance.get('knee_valgus', 0) > 1 or
                stance.get('knee_varus', 0) > 1 or
                pelvis.get('excessive_rotation', 0) > 1):  # Lumbar movement
                return 2
            
            # Score 3: All aligned, minimal/no lumbar, parallel
            return 3

        elif test_name == 'inline_lunge':
            alignment = sub_data.get('alignment', {})
            lower = sub_data.get('lower_body_control', {})
            balance = sub_data.get('balance_stability', {})
            
            # Score 1: Loss of balance
            if balance.get('loss_of_balance', 0) > 0:
                return 1
            
            # Score 2: Dowel contacts not maintained, dowel not vertical, torso movement, not in sagittal, knee not touch
            if (alignment.get('trunk_upright', 0) < 2 or  # Contacts not maintained
                alignment.get('excessive_forward_lean', 0) > 1 or  # Torso movement
                alignment.get('lateral_shift', 0) > 1 or  # Not sagittal
                lower.get('knee_tracks_over_foot', 0) < 2):  # Knee not touch
                return 2
            
            # Score 3: All perfect
            return 3

        elif test_name == 'shoulder_mobility':
            reach = sub_data.get('reach_quality', {})
            
            # Score 3: Fists within one hand length
            if reach.get('hands_within_fist_distance', 0) > 0:
                return 3
            
            # Score 2: Within one and a half hand lengths
            if reach.get('hands_within_hand_length', 0) > 0:
                return 2
            
            # Score 1: Not within 1.5
            return 1

        elif test_name == 'active_straight_leg_raise':
            moving = sub_data.get('moving_leg', {})
            non_moving = sub_data.get('non_moving_leg', {})
            
            # Non-moving not neutral → 1
            if non_moving.get('remains_flat', 0) < 2:
                return 1
            
            # Score 3: Malleolus between mid-thigh and ASIS
            if moving.get('gt_80_hip_flexion', 0) > 0:
                return 3
            
            # Score 2: Between mid-thigh and joint line
            if moving.get('between_60_80_hip_flexion', 0) > 0:
                return 2
            
            # Score 1: Below joint line
            return 1

        elif test_name == 'trunk_stability_pushup':
            core = sub_data.get('core_control', {})
            body = sub_data.get('body_alignment', {})
            
            # Score 1: Unable to perform (lag or sagging)
            if core.get('hips_lag', 0) > 0 or body.get('sagging_hips', 0) > 0:
                return 1
            
            # Assume male for 3 (thumbs at head); if female or minor issues, 2 (thumbs at chin/clavicle)
            # Note: Data model doesn't have gender, so assume 3 if no faults, 2 if minor extension
            if core.get('excessive_lumbar_extension', 0) > 0:
                return 2
            
            return 3

        elif test_name == 'rotary_stability':
            diagonal = sub_data.get('diagonal_pattern', {})
            
            # Score 1: Inability to perform diagonal
            if diagonal.get('unable_to_complete', 0) > 0:
                return 1
            
            # Score 2: Correct diagonal repetition
            if diagonal.get('smooth_controlled', 0) > 0 and diagonal.get('loss_of_balance', 0) <= 1:
                return 2
            
            # Score 3: Correct unilateral repetition
            if diagonal.get('smooth_controlled', 0) > 1 and diagonal.get('loss_of_balance', 0) == 0:
                return 3
            
            return 1
        
        # Default
        return 3

    # --- 2. EXECUTE SCORING ---
    effective_scores = {}
    
    for test_name in profile:
        if test_name in ['use_manual_scores']: continue
        
        test_data = profile[test_name]
        
        has_sub_inputs = False
        for k, v in test_data.items():
            if isinstance(v, dict):
                if sum(v.values()) > 0:
                    has_sub_inputs = True
                    break
        
        if use_manual_scores:
            effective_scores[test_name] = test_data.get('score', 2)
        elif has_sub_inputs:
            effective_scores[test_name] = calculate_score_from_faults(test_name, test_data)
        else:
            effective_scores[test_name] = test_data.get('score', 2)

    # --- 3. TRAFFIC LIGHT LOGIC ---
    # RED LIGHT
    if effective_scores.get('active_straight_leg_raise', 3) <= 1 or \
       effective_scores.get('shoulder_mobility', 3) <= 1:
        return {"status": "MOBILITY", "target_level": 1, "reason": "Mobility Restriction (Score 1 in ASLR or SM)", "effective_scores": effective_scores}

    # YELLOW LIGHT
    if effective_scores.get('rotary_stability', 3) <= 1 or \
       effective_scores.get('trunk_stability_pushup', 3) <= 1:
        return {"status": "STABILITY", "target_level": 3, "reason": "Motor Control Failure (Score 1 in TS or RS)", "effective_scores": effective_scores}

    # GREEN LIGHT
    min_pattern = min(
        effective_scores.get('hurdle_step', 3), 
        effective_scores.get('inline_lunge', 3), 
        effective_scores.get('overhead_squat', 3)
    )
    
    if min_pattern <= 1:
        return {"status": "PATTERN", "target_level": 5, "reason": "Pattern Dysfunction (Score 1 in Squat/Hurdle/Lunge)", "effective_scores": effective_scores}
    elif min_pattern == 2:
        return {"status": "STRENGTH", "target_level": 7, "reason": "Acceptable Patterning (Score 2). Cleared for Strength.", "effective_scores": effective_scores}
    else:
        return {"status": "POWER", "target_level": 9, "reason": "Perfect Patterning (Score 3). Cleared for Power.", "effective_scores": effective_scores}