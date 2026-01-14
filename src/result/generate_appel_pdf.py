import csv
import os
import argparse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate attendance PDFs.")
    parser.add_argument("--semaine", type=int, required=True, help="Target week number")
    parser.add_argument("--jour", type=str, required=True, help="Target day")
    parser.add_argument("--periode", type=str, help="Target period (optional)")
    parser.add_argument("--input_dir", type=str, default=os.path.join("resultat", "fiche_appel"), help="Input directory containing CSVs")
    parser.add_argument("--output_dir", type=str, help="Output directory for PDFs")

    args = parser.parse_args()
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Resolve input dir relative to base if not absolute
    if not os.path.isabs(args.input_dir):
        input_dir = os.path.join(base_dir, args.input_dir)
    else:
        input_dir = args.input_dir
        
    # Resolve output dir
    if args.output_dir:
        if not os.path.isabs(args.output_dir):
            output_dir = os.path.join(base_dir, args.output_dir)
        else:
            output_dir = args.output_dir
    else:
        output_dir = os.path.join(base_dir, "resultat", f"feuilles_appel_S{args.semaine}_{args.jour}")

    generate_all_discipline_appel_pdfs_for_one_day(input_dir, output_dir, args.semaine, args.jour, args.periode)
    
    
    #& "C:/Program Files/Python313/python.exe" c:/Users/coren/Desktop/PFE/Projet_PFE/src/result/generate_appel_pdf.py --semaine 6 --jour Jeudi --periode "Matin"