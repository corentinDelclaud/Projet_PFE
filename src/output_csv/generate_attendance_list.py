import csv
import os
import sys

def generate_call_sheets(input_csv_path, output_dir):
    """
    Reads the global planning CSV and generates call sheets (lists of students)
    grouped by (Semaine, Jour, Periode, Discipline).
    """
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found at {input_csv_path}")
        return

    # Dictionary to store groupings
    # Key: (Semaine, Jour, Periode, Discipline)
    # Value: List of student names
    call_sheets = {}
    
    print(f"Reading from: {input_csv_path}")

    with open(input_csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Verify required headers
        required = ["Semaine", "Jour", "Periode", "Discipline", "Eleve"]
        # Basic check if headers are present (csv.DictReader reads header automatically)
        if reader.fieldnames and not all(field in reader.fieldnames for field in required):
            print(f"Error: CSV missing required columns. Found: {reader.fieldnames}")
            return

        for row in reader:
            key = (row["Semaine"], row["Jour"], row["Periode"], row["Discipline"])
            
            if key not in call_sheets:
                call_sheets[key] = []
            
            call_sheets[key].append(row["Eleve"])

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating {len(call_sheets)} call sheets in {output_dir}...")

    count = 0
    for (semaine, jour, periode, discipline), students in call_sheets.items():
        # Sanitize filename
        # Replace spaces with underscores, remove potentially unsafe chars
        safe_discipline = "".join([c if c.isalnum() else "_" for c in discipline])
        
        filename = f"Semaine{semaine}_{jour}_{periode}_{safe_discipline}.csv"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header for the call sheet
            writer.writerow(["Eleve", "Present", "Absent", "Retard", "Commentaire"])
            
            # List students
            for student in sorted(students):
                writer.writerow([student, "", "", "", ""])
        
        count += 1

    print(f"Successfully generated {count} call sheets.")

if __name__ == "__main__":
    # path navigation: src/gestion_csv/ -> .../ -> .../ -> resultat/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    input_csv = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
    output_folder = os.path.join(base_dir, 'resultat', 'fiche_appel')
    
    generate_call_sheets(input_csv, output_folder)
    