import pandas as pd
import json
import os
import re

# CONFIGURATION
INPUT_EXCEL_PATH = 'data/raw/SQUAT (PROGRESSION).xlsx'
OUTPUT_JSON_PATH = 'data/processed/exercise_knowledge_base.json'

# --- 1. SMART TAGGING LOGIC ---
# This maps keywords in the Exercise Name to specific FMS Faults.
TAG_RULES = {
    # DEEP SQUAT FAULTS
    "ankle": ["fix_heels_lift", "ankle_mobility"],
    "dorsiflexion": ["fix_heels_lift", "ankle_mobility"],
    "heel": ["fix_heels_lift"],
    "wall slide": ["fix_thoracic_stiffness", "fix_forward_lean"],
    "thoracic": ["fix_forward_lean", "thoracic_mobility"],
    "band": ["fix_knee_valgus", "rnt_correction"], # Bands often fix valgus
    "valgus": ["fix_knee_valgus"],
    "glute": ["fix_knee_valgus", "glute_activation"],
    
    # CORE / STABILITY FAULTS
    "plank": ["fix_lumbar_extension", "core_stability"],
    "deadbug": ["fix_rib_flare", "core_stability"],
    "chop": ["fix_rotary_instability", "anti_rotation"],
    "lift": ["fix_rotary_instability", "anti_rotation"],
    "carry": ["fix_asymmetry", "stability"],
    
    # GENERAL PATTERNS
    "squat": ["pattern_squat"],
    "lunge": ["pattern_lunge"],
    "deadlift": ["pattern_hinge"],
    "single leg": ["fix_asymmetry", "unilateral"]
}

def generate_smart_tags(name, category, level):
    """
    Scans the exercise name and category to auto-assign correction tags.
    """
    # Base tags
    tags = [category.lower().replace(" ", "_"), f"level_{level}"]
    
    # Combine text for searching
    search_text = (name + " " + category).lower()
    
    # Keyword Matching
    for keyword, new_tags in TAG_RULES.items():
        if keyword in search_text:
            tags.extend(new_tags)
            
    # Remove duplicates
    return list(set(tags))

def run_ingestion():
    print(f"Loading data from {INPUT_EXCEL_PATH}...")
    
    if not os.path.exists(INPUT_EXCEL_PATH):
        print(f"❌ Error: File not found at {INPUT_EXCEL_PATH}")
        return

    try:
        # 1. READ THE MATRIX
        df_matrix = pd.read_excel(INPUT_EXCEL_PATH, sheet_name=0, header=2, engine='openpyxl')
        
        # 2. READ THE MANUAL DESCRIPTIONS
        try:
            df_desc = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='Descriptions', engine='openpyxl')
            desc_lookup = dict(zip(df_desc.iloc[:, 0].str.strip(), df_desc.iloc[:, 1]))
            print("✅ Found 'Descriptions' sheet. Using manual text.")
        except:
            print("⚠️ 'Descriptions' sheet not found. Using generic text.")
            desc_lookup = {}

    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return

    # Clean Matrix Columns
    df_matrix.columns = [str(c).strip() for c in df_matrix.columns]
    df_matrix = df_matrix.dropna(subset=['EXERCISE'])
    
    knowledge_base = []
    count = 0
    
    print("🔄 Processing and Tagging exercises...")

    for _, row in df_matrix.iterrows():
        category = str(row['EXERCISE']).strip()
        
        for level in range(1, 11):
            col_name = f'LEVEL {level}'
            if col_name not in df_matrix.columns: continue
            
            cell_value = row[col_name]
            if pd.isna(cell_value): continue
            
            # Handle multiple exercises in one cell
            exercises = re.split(r',\s*(?![^()]*\))', str(cell_value))
            exercises = [x.strip() for x in exercises if x.strip()]
            
            for ex_name in exercises:
                
                # Description Logic
                if ex_name in desc_lookup and pd.notna(desc_lookup[ex_name]):
                    final_description = desc_lookup[ex_name]
                    source = "Manual"
                else:
                    final_description = (
                        f"A Level {level} {category} exercise. "
                        f"Targeting specific movement patterns and corrective strategies."
                    )
                    source = "Auto"

                # --- NEW: APPLY SMART TAGS ---
                smart_tags = generate_smart_tags(ex_name, category, level)

                entry = {
                    "id": f"sq_{level}_{count}",
                    "exercise_name": ex_name,
                    "category": category,
                    "difficulty_level": level,
                    "description": final_description,
                    "description_source": source,
                    "tags": smart_tags  # <--- NOW CONTAINS 'fix_heels_lift' etc.
                }
                
                knowledge_base.append(entry)
                count += 1

    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=4)
        
    print(f"✅ Success! Processed and Auto-Tagged {count} exercises.")
    print(f"📁 Database ready at: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    run_ingestion()