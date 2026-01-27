import csv
import os
import argparse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

def create_header_style():
    return {
        'font': Font(bold=True, color="FFFFFF"),
        'fill': PatternFill(start_color="808080", end_color="808080", fill_type="solid"),
        'alignment': Alignment(horizontal="center", vertical="center"),
        'border': Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    }

def create_cell_style():
    return {
        'alignment': Alignment(vertical="center"),
        'border': Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    }

def generate_discipline_year_excel(input_path: str, output_dir: str):
    """
    Generates one Excel file per discipline, containing all sessions of the year ordered by week.
    """
    print(f"Generating Year Recap by Discipline from: {input_path}")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Data structure: discipline -> list of session objects
    # session object: { 'semaine': int, 'jour': str, 'periode': str, 'students': list }
    # Mapping unique session key (semaine, jour, periode) -> session index in list to merge students
    discipline_sessions = {} 

    day_map = {"Lundi": 0, "Mardi": 1, "Mercredi": 2, "Jeudi": 3, "Vendredi": 4}

    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "STAGE:" in row["Discipline"]:
                    continue

                try:
                    semaine = int(row["Semaine"])
                    jour = row["Jour"]
                    periode = row["Apres-Midi"] # "0" or "1"
                    discipline = row["Discipline"]
                    eleve = row["Id_Eleve"]
                except ValueError:
                    continue

                if discipline not in discipline_sessions:
                    discipline_sessions[discipline] = {}

                # Use (Semaine, DayIndex, Period) as key for sorting
                # Ensure periode is treated as int for consistent sorting
                p_int = int(periode) if periode.isdigit() else (0 if "Matin" in periode else 1)
                
                session_key = (semaine, day_map.get(jour, 99), p_int)
                
                if session_key not in discipline_sessions[discipline]:
                    discipline_sessions[discipline][session_key] = {
                        'semaine': semaine,
                        'jour': jour,
                        'periode': periode,
                        'students': []
                    }
                
                discipline_sessions[discipline][session_key]['students'].append(eleve)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Ensure output dir
    os.makedirs(output_dir, exist_ok=True)

    header_style = create_header_style()
    cell_style = create_cell_style()

    count = 0
    for discipline, sessions_map in discipline_sessions.items():
        # Clean filename
        safe_disc = "".join([c if c.isalnum() else "_" for c in discipline])
        out_path = os.path.join(output_dir, f"Appel_Annuel_{safe_disc}.xlsx")
        
        wb = Workbook()
        ws = wb.active
        ws.title = discipline[:31] # Excel sheet name limit
        
        # Setup columns
        ws.column_dimensions['A'].width = 30  # Nom Étudiant
        ws.column_dimensions['B'].width = 15  # Présent
        ws.column_dimensions['C'].width = 30  # Signature
        ws.column_dimensions['D'].width = 30  # Observations

        row_idx = 1
        
        # Title
        ws.cell(row=row_idx, column=1, value=f"FEUILLES D'APPEL - {discipline}").font = Font(size=16, bold=True)
        row_idx += 2

        # Sort sessions
        sorted_keys = sorted(sessions_map.keys()) # (semaine, day_idx, periode)

        for key in sorted_keys:
            session_data = sessions_map[key]
            semaine = session_data['semaine']
            jour = session_data['jour']
            # Periode display
            p_val = session_data['periode']
            p_str = "Après-Midi" if str(p_val) == "1" else "Matin"
            
            students = sorted(session_data['students'])

            # Session Header
            header_text = f"Semaine {semaine} - {jour} - {p_str}"
            ws.cell(row=row_idx, column=1, value=header_text).font = Font(size=12, bold=True, color="000080")
            row_idx += 1

            # Table Header
            headers = ['Nom Étudiant', 'Présent', 'Signature', 'Observations']
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=row_idx, column=col_num, value=header)
                cell.font = header_style['font']
                cell.fill = header_style['fill']
                cell.alignment = header_style['alignment']
                cell.border = header_style['border']
            row_idx += 1

            # Student List
            for st in students:
                ws.cell(row=row_idx, column=1, value=st).border = cell_style['border']
                ws.cell(row=row_idx, column=2).border = cell_style['border']
                ws.cell(row=row_idx, column=3).border = cell_style['border']
                ws.cell(row=row_idx, column=4).border = cell_style['border']
                row_idx += 1
            
            row_idx += 2 # Spacer
        
        try:
            wb.save(out_path)
            count += 1
            print(f"Generated {out_path}")
        except Exception as e:
            print(f"Error saving {out_path}: {e}")
    
    print(f"Finished generating {count} discipline files.")

if __name__ == "__main__":
    
    # Path navigation
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    input_csv = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
    
    # Simple argument parser for optional output dir
    parser = argparse.ArgumentParser(description="Generate annual attendance Excel files per discipline.")
    parser.add_argument("--output_dir", type=str, help="Output directory")
    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir else os.path.join(base_dir, 'resultat', 'fiche_appel_par_discipline')
    
    generate_discipline_year_excel(input_csv, output_dir)
