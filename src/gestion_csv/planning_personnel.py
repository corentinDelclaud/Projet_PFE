import csv
import os
import sys

def generate_individual_plannings(input_csv_path, output_dir):
    """
    Reads a global planning CSV and splits it into individual CSV files per student.
    """
    student_plannings = {}
    headers = []

    print(f"Reading from: {input_csv_path}")
    
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found at {input_csv_path}")
        return

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Read and Group Data
    with open(input_csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader) # Read header
        except StopIteration:
            print("Error: Empty CSV file")
            return
            
        try:
            student_col_idx = headers.index("Eleve")
        except ValueError:
            print("Error: 'Eleve' column not found in CSV")
            return

        for row in reader:
            if not row: continue
            student_name = row[student_col_idx]
            
            if student_name not in student_plannings:
                student_plannings[student_name] = []
            
            student_plannings[student_name].append(row)

    # 2. Write Individual Files
    count = 0
    for student, rows in student_plannings.items():
        # Sanitize filename (remove characters invalid in filenames)
        safe_name = "".join([c for c in student if c.isalnum() or c in (' ', '_', '-')]).strip()
        filename = f"{safe_name}.csv"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as sout:
            writer = csv.writer(sout)
            writer.writerow(headers)
            # Sort rows by Semaine (0), then Jour index if possible
            # Here keeping original order or simple sort
            writer.writerows(rows)
        
        count += 1

    print(f"Successfully generated {count} individual planning files in: {output_dir}")

if __name__ == "__main__":
    # path navigation: src/gestion_csv/ -> .../ -> .../ -> resultat/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    input_csv = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
    output_folder = os.path.join(base_dir, 'resultat', 'planning_personnel')
    
    generate_individual_plannings(input_csv, output_folder)
