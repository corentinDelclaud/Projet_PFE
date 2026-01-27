import pandas as pd
import os

def generate_codes(csv_file_path : str):
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming file is in src/data/code_creation.py
    # Data is in data/mock_eleves.csv (root/data)
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    print(f"Reading CSV from: {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        print("File not found!")
        return

    # Read CSV
    df = pd.read_csv(csv_file_path)

    # Mappings
    # DFAS01: 4, DFAS02: 5, DFTCC: 6
    annee_map = {
        'DFAS01': 4,
        'DFAS02': 5,
        'DFTCC': 6
    }
    
    # Lundi: 0, Mardi: 1, Mercredi: 2, Jeudi: 3, Vendredi: 4
    jour_map = {
        'lundi': 1,
        'mardi': 2,
        'mercredi': 3,
        'jeudi': 4,
        'vendredi': 5
    }
    
    # Ensure columns exist
    if 'annee' not in df.columns or 'jour_preference' not in df.columns:
         print("Columns 'annee' or 'jour_preference' missing.")
         return

    # --- Calculation Logic ---
    
    # 1. Map Year and Day to digits
    df['digit_annee'] = df['annee'].map(annee_map)
    df['digit_jour'] = df['jour_preference'].map(lambda x: jour_map.get(x.lower() if isinstance(x, str) else x))
    
    # 2. Sort by Year, Day, ID to allow deterministic indentation count
    # Preserve original indices? We can sort back by ID later.
    df = df.sort_values(by=['digit_annee', 'digit_jour', 'id_eleve'])
    
    # 3. Calculate Indentation (start at 11)
    # Group by Year+Day and generate a cumulative count
    # cumcount() starts at 0 -> add 11
    df['indent'] = df.groupby(['digit_annee', 'digit_jour']).cumcount() + 11
    
    # 4. Create Code Column
    def create_code_str(row):
        try:
            y = int(row['digit_annee'])
            d = int(row['digit_jour'])
            i = int(row['indent'])
            # Format: Y D II (e.g. 4 0 11)
            # Indent must be 2 digits. If > 99, it grows, but user constraint says "equivalent number / 5" so ~20 per day.
            return f"{y}{d}{i}" 
        except Exception:
            return None

    df['code'] = df.apply(create_code_str, axis=1)
    
    # Check for errors
    if df['code'].isnull().any():
        print("Warning: Some codes could not be generated (invalid mapping).")
    
    # 5. Cleanup temporary columns
    df.drop(columns=['digit_annee', 'digit_jour', 'indent'], inplace=True)
    
    # 6. Restore sort order by ID
    if 'id_eleve' in df.columns:
        df = df.sort_values(by='code')

    # --- Update IDs (Code -> id_eleve) ---
    if 'id_eleve' in df.columns and 'id_binome' in df.columns:
        # Map old_id -> new_code
        id_map = dict(zip(df['id_eleve'], df['code']))
        
        # Update binome IDs using the map
        df['id_binome'] = df['id_binome'].apply(lambda x: id_map.get(x, x))
        
        # Set id_eleve to code
        df['id_eleve'] = df['code']
        
        # Drop temporary 'code' column
        df.drop(columns=['code'], inplace=True)
    
    # Save to a new CSV file
    output_file_path = os.path.join(project_root, 'data', 'eleves_with_code.csv')
    df.to_csv(output_file_path, index=False, encoding='utf-8')
    print(f"Success! Created {output_file_path} with {len(df)} rows.")
    if 'code' in df.columns:
        print(df[['id_eleve', 'annee', 'jour_preference', 'code']].head())
    else:
        print(df[['id_eleve', 'annee', 'jour_preference']].head())

if __name__ == "__main__":
    # Default execution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    default_input = os.path.join(project_root, 'data', 'mock_eleves.csv')
    generate_codes(default_input)
