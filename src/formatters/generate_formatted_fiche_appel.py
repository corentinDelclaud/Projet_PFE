import csv
import os
import argparse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

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

def generate_appel_pdf(input_path: str, output_path: str, target_semaine: int = None, target_jour: str = None, target_periode: str = None, target_discipline: str = None):
    """
    Generates a PDF attendance sheet from the planning CSV file.
    Groups entries by Discipline, Day, and Period.
    Can filter by specific Week, Day, Period, or Discipline.
    """
    print(f"Generating PDF from: {input_path}")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # 1. Read CSV Data and Organize by Session
    # Structure: sessions[Week][Day][Period][Discipline] = [List of Students]
    sessions = {}
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Row keys: Semaine, Jour, Periode, Id_Eleve, Eleve, Discipline
                # Skip STAGE entries for attendance sheets (usually separate) or include them if needed
                if "STAGE:" in row["Discipline"]:
                    continue

                semaine = int(row["Semaine"])
                jour = row["Jour"]
                periode = row["Periode"]
                discipline = row["Discipline"]
                eleve = row["Eleve"]

                if semaine not in sessions:
                    sessions[semaine] = {}
                if jour not in sessions[semaine]:
                    sessions[semaine][jour] = {}
                if periode not in sessions[semaine][jour]:
                    sessions[semaine][jour][periode] = {}
                if discipline not in sessions[semaine][jour][periode]:
                    sessions[semaine][jour][periode][discipline] = []
                
                sessions[semaine][jour][periode][discipline].append(eleve)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Build PDF Document
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # Sort keys for consistent order
    sorted_semaines = sorted(sessions.keys())
    day_order = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    period_order = ["Matin", "Apres-Midi"]

    found_any = False

    for semaine in sorted_semaines:
        if semaine not in sessions: continue
        # Filter by Week
        if target_semaine is not None and semaine != target_semaine: continue
        
        # Week Header
        elements.append(Paragraph(f"Semaine {semaine} - Feuille d'Appel", title_style))
        elements.append(Spacer(1, 12))

        for jour in day_order:
            if jour not in sessions[semaine]: continue
            # Filter by Day
            if target_jour is not None and jour != target_jour: continue
            
            for periode in period_order:
                if periode not in sessions[semaine][jour]: continue
                # Filter by Period
                if target_periode is not None and periode != target_periode: continue
                
                # Check if there are disciplines in this slot
                disciplines_dict = sessions[semaine][jour][periode]
                if not disciplines_dict: continue

                # Filter disciplines
                active_disciplines = [d for d in disciplines_dict if target_discipline is None or d == target_discipline]
                if not active_disciplines: continue

                found_any = True

                # Section Header: Day - Period
                elements.append(Paragraph(f"{jour} - {periode}", heading_style))
                elements.append(Spacer(1, 6))

                # Iterate through disciplines
                for discipline in active_disciplines:
                    students = disciplines_dict[discipline]
                    elements.append(Paragraph(f"<b>{discipline}</b>", normal_style))
                    
                    # Create Table Data
                    # Header row
                    data = [['Nom Étudiant', 'Présent', 'Signature', 'Observations']]
                    
                    # Sort students alphabetically
                    for student in sorted(students):
                        data.append([student, '', '', ''])
                    
                    # Table Style
                    t = Table(data, colWidths=[200, 50, 150, 150])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    
                    elements.append(t)
                    elements.append(Spacer(1, 12))
                
                # Page break only if we are not restricted to a single slot, or just to keep clean
                if target_semaine is None or target_jour is None or target_periode is None or target_discipline is None:
                    elements.append(PageBreak())

    if not found_any:
        print("Warning: No sessions found matching criteria.")
        return

    # Build
    try:
        doc.build(elements)
        print(f"PDF successfully generated at: {output_path}")
    except Exception as e:
        print(f"Error building PDF: {e}")

def generate_all_discipline_appel_pdfs_for_one_day(input_dir: str, output_dir: str, target_semaine: int, target_jour: str, target_periode: str = None):
    """
    Scans input_dir for CSV files matching the criteria (Week/Day) and generates one PDF per file.
    Assumes individual attendance CSVs with format: Semaine{S}_{Jour}_{Periode}_{Discipline}.csv
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    print(f"Scanning {input_dir} for Semaine {target_semaine}, Jour {target_jour}...")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        return

    found_any = False

    for filename in os.listdir(input_dir):
        if not filename.endswith(".csv"): continue
        
        # Check matching
        # Expected Format: Semaine1_Jeudi_Apres-Midi_Comodulation.csv
        parts = filename.replace(".csv", "").split("_")
        
        # Safety check on parts length: needs at least SemaineX, Jour, Periode, Discipline
        if len(parts) < 4: continue 
        
        file_semaine_str = parts[0]
        file_jour = parts[1]
        file_periode = parts[2]
        file_discipline = "_".join(parts[3:])
        
        try:
            file_semaine = int(file_semaine_str.replace("Semaine", ""))
        except:
            continue
            
        if file_semaine != target_semaine: continue
        if file_jour != target_jour: continue
        if target_periode and file_periode != target_periode: continue
        
        # Found a match!
        found_any = True
        
        # Read students from the small CSV
        students = []
        csv_full_path = os.path.join(input_dir, filename)
        try:
            with open(csv_full_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Small CSV has "Eleve"
                    if "Eleve" in row and row["Eleve"]:
                        students.append(row["Eleve"])
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            continue

        if not students:
            print(f"Skipping empty session: {filename}")
            continue

        # Generate PDF
        output_pdf_name = f"feuille_appel_{filename.replace('.csv', '.pdf')}"
        output_pdf_path = os.path.join(output_dir, output_pdf_name)
        
        print(f"Generating PDF for {file_discipline}...")
        
        # ReportLab generation (copied from main function to be standalone)
        doc = SimpleDocTemplate(output_pdf_path, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph(f"Feuille d'Appel - {file_discipline.replace('_', ' ')}", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Semaine {file_semaine} - {file_jour} - {file_periode}", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Table
        data = [['Nom Étudiant', 'Présent', 'Signature', 'Observations']]
        for student in sorted(students):
            data.append([student, '', '', ''])
            
        t = Table(data, colWidths=[200, 50, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        
        try:
            doc.build(elements)
            print(f"Created: {output_pdf_path}")
        except Exception as e:
            print(f"Error building PDF for {filename}: {e}")

    if not found_any:
        print("No matching files found.")

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

def generate_appel_excel(input_path: str, output_path: str, target_semaine: int = None, target_jour: str = None, target_periode: str = None, target_discipline: str = None):
    """
    Generates an Excel attendance sheet from the planning CSV file.
    Groups entries by Discipline, Day, and Period.
    Can filter by specific Week, Day, Period, or Discipline.
    """
    print(f"Generating Excel from: {input_path}")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # 1. Read CSV Data and Organize by Session
    sessions = {}
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "STAGE:" in row["Discipline"]:
                    continue

                semaine = int(row["Semaine"])
                jour = row["Jour"]
                periode = row["Periode"]
                discipline = row["Discipline"]
                eleve = row["Eleve"]

                if semaine not in sessions:
                    sessions[semaine] = {}
                if jour not in sessions[semaine]:
                    sessions[semaine][jour] = {}
                if periode not in sessions[semaine][jour]:
                    sessions[semaine][jour][periode] = {}
                if discipline not in sessions[semaine][jour][periode]:
                    sessions[semaine][jour][periode][discipline] = []
                
                sessions[semaine][jour][periode][discipline].append(eleve)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Build Excel Document
    wb = Workbook()
    ws = wb.active
    ws.title = "Feuilles d'Appel"
    
    # Set Column Widths
    ws.column_dimensions['A'].width = 30  # Nom Étudiant
    ws.column_dimensions['B'].width = 15  # Présent
    ws.column_dimensions['C'].width = 30  # Signature
    ws.column_dimensions['D'].width = 30  # Observations

    header_style = create_header_style()
    cell_style = create_cell_style()

    row_idx = 1

    sorted_semaines = sorted(sessions.keys())
    day_order = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    period_order = ["Matin", "Apres-Midi"]

    found_any = False

    for semaine in sorted_semaines:
        if semaine not in sessions: continue
        if target_semaine is not None and semaine != target_semaine: continue
        
        # Week Header (Optional, looks nice to separate)
        ws.cell(row=row_idx, column=1, value=f"SEMAINE {semaine}").font = Font(size=14, bold=True)
        row_idx += 2

        for jour in day_order:
            if jour not in sessions[semaine]: continue
            if target_jour is not None and jour != target_jour: continue
            
            for periode in period_order:
                if periode not in sessions[semaine][jour]: continue
                if target_periode is not None and periode != target_periode: continue
                
                disciplines_dict = sessions[semaine][jour][periode]
                if not disciplines_dict: continue

                active_disciplines = [d for d in disciplines_dict if target_discipline is None or d == target_discipline]
                if not active_disciplines: continue

                found_any = True
                
                # Section Header
                ws.cell(row=row_idx, column=1, value=f"{jour} - {periode}").font = Font(size=12, bold=True)
                row_idx += 2

                for discipline in active_disciplines:
                    students = disciplines_dict[discipline]
                    
                    # Discipline Header
                    ws.cell(row=row_idx, column=1, value=discipline).font = Font(bold=True)
                    row_idx += 1
                    
                    # Table Headers
                    headers = ['Nom Étudiant', 'Présent', 'Signature', 'Observations']
                    for col_num, header in enumerate(headers, 1):
                        cell = ws.cell(row=row_idx, column=col_num, value=header)
                        cell.font = header_style['font']
                        cell.fill = header_style['fill']
                        cell.alignment = header_style['alignment']
                        cell.border = header_style['border']
                    row_idx += 1
                    
                    # Student Rows
                    for student in sorted(students):
                        ws.cell(row=row_idx, column=1, value=student).border = cell_style['border']
                        ws.cell(row=row_idx, column=2).border = cell_style['border']
                        ws.cell(row=row_idx, column=3).border = cell_style['border']
                        ws.cell(row=row_idx, column=4).border = cell_style['border']
                        row_idx += 1
                    
                    row_idx += 2 # Space between tables

    if not found_any:
        print("Warning: No sessions found matching criteria.")
        return

    try:
        wb.save(output_path)
        print(f"Excel successfully generated at: {output_path}")
    except Exception as e:
        print(f"Error saving Excel: {e}")

def generate_all_discipline_appel_excels_for_one_day(input_dir: str, output_dir: str, target_semaine: int, target_jour: str, target_periode: str = None):
    """
    Scans input_dir for CSV files matching the criteria (Week/Day) and generates one Excel file per CSV.
    Assumes filename format: Semaine{S}_{Jour}_{Periode}_{Discipline}.csv
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    print(f"Scanning {input_dir} for Semaine {target_semaine}, Jour {target_jour}...")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        return

    found_any = False
    header_style = create_header_style()
    cell_style = create_cell_style()

    for filename in os.listdir(input_dir):
        if not filename.endswith(".csv"): continue
        
        parts = filename.replace(".csv", "").split("_")
        if len(parts) < 4: continue 
        
        file_semaine_str = parts[0]
        file_jour = parts[1]
        file_periode = parts[2]
        file_discipline = "_".join(parts[3:])
        
        try:
            file_semaine = int(file_semaine_str.replace("Semaine", ""))
        except:
            continue
            
        if file_semaine != target_semaine: continue
        if file_jour != target_jour: continue
        if target_periode and file_periode != target_periode: continue
        
        found_any = True
        
        students = []
        csv_full_path = os.path.join(input_dir, filename)
        try:
            with open(csv_full_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "Eleve" in row and row["Eleve"]:
                        students.append(row["Eleve"])
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            continue

        if not students:
            continue

        # Generate Excel
        output_excel_name = f"feuille_appel_{filename.replace('.csv', '.xlsx')}"
        output_excel_path = os.path.join(output_dir, output_excel_name)
        
        print(f"Generating Excel for {file_discipline}...")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Appel" 
        
        # Setup Page Layout for printing
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 30

        row_idx = 1
        
        # Title
        title_cell = ws.cell(row=row_idx, column=1, value=f"Feuille d'Appel - {file_discipline.replace('_', ' ')}")
        title_cell.font = Font(size=14, bold=True)
        row_idx += 1
        
        subtitle_cell = ws.cell(row=row_idx, column=1, value=f"Semaine {file_semaine} - {file_jour} - {file_periode}")
        subtitle_cell.font = Font(size=12, bold=True)
        row_idx += 2
        
        # Headers
        headers = ['Nom Étudiant', 'Présent', 'Signature', 'Observations']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_num, value=header)
            cell.font = header_style['font']
            cell.fill = header_style['fill']
            cell.alignment = header_style['alignment']
            cell.border = header_style['border']
        row_idx += 1
        
        # Rows
        for student in sorted(students):
            ws.cell(row=row_idx, column=1, value=student).border = cell_style['border']
            ws.cell(row=row_idx, column=2).border = cell_style['border']
            ws.cell(row=row_idx, column=3).border = cell_style['border']
            ws.cell(row=row_idx, column=4).border = cell_style['border']
            row_idx += 1
            
        try:
            wb.save(output_excel_path)
            print(f"Created: {output_excel_path}")
        except Exception as e:
            print(f"Error saving Excel {output_excel_path}: {e}")

    if not found_any:
        print("No matching files found.")

if __name__ == "__main__":

    # path navigation: src/gestion_csv/ -> .../ -> .../ -> resultat/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    input_csv = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
    output_folder = os.path.join(base_dir, 'resultat', 'fiche_appel')
    
    generate_call_sheets(input_csv, output_folder)

    
    parser = argparse.ArgumentParser(description="Generate attendance Excel files.")
    parser.add_argument("--semaine", type=int, help="Target week number")
    parser.add_argument("--jour", type=str, help="Target day")
    parser.add_argument("--periode", type=str, help="Target period (optional)")
    parser.add_argument("--discipline", type=str, help="Target discipline (optional)")
    parser.add_argument("--input_dir", type=str, help="Input directory containing CSVs (for batch mode)")
    parser.add_argument("--output_dir", type=str, help="Output directory")
    parser.add_argument("--batch", action="store_true", help="Run in batch mode from individual CSVs (fiches_dir)")
    parser.add_argument("--mode", choices=['single', 'batch'], default='single', help="Operation mode: single (from global planning) or batch (from fiches_dir)")

    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Defaults
    if args.batch or args.input_dir:
        # Batch mode
        input_dir = args.input_dir if args.input_dir else os.path.join(base_dir, "resultat", "fiche_appel")
        if not os.path.isabs(input_dir):
            input_dir = os.path.join(base_dir, input_dir)
            
        if not args.semaine or not args.jour:
            print("Error: --semaine and --jour are required for batch mode.")
        else:
            if args.output_dir:
                output_dir = args.output_dir
            else:
                output_dir = os.path.join(base_dir, "resultat", f"feuilles_appel_excel_S{args.semaine}_{args.jour}")
            
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(base_dir, output_dir)
                
            generate_all_discipline_appel_excels_for_one_day(input_dir, output_dir, args.semaine, args.jour, args.periode)
            
    else:
        # Single file mode (from global solution)
        input_csv = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
        
        # Build output filename
        suffix_parts = []
        if args.semaine: suffix_parts.append(f"S{args.semaine}")
        if args.jour: suffix_parts.append(f"{args.jour}")
        if args.periode: suffix_parts.append(f"{args.periode}")
        if args.discipline: suffix_parts.append(f"{args.discipline}")
        
        suffix = "_" + "_".join(suffix_parts) if suffix_parts else ""
        output_name = f'feuilles_appel{suffix}.xlsx'
        
        if args.output_dir:
            output_dir = args.output_dir
        else:
            output_dir = os.path.join(base_dir, 'resultat')
            
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(base_dir, output_dir)
            
        output_excel = os.path.join(output_dir, output_name)
        
        generate_appel_excel(input_csv, output_excel, args.semaine, args.jour, args.periode, args.discipline)
