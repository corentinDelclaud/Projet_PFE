import sys
import os
import csv
import collections
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Add the parent parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.classes.discipline import discipline
from src.classes.eleve import eleve
from src.classes.enum.niveaux import niveau
from src.classes.jour_preference import jour_pref

def load_data():
    # --- 1. Load Disciplines (Copied from model configuration) ---
    # Note: Use the same configuration as the model
    poly = discipline(1, "Polyclinique", [20,20,20,20,20,20,20,20,20,20], True, [50,50,50], [True]*10,[4,5,6])
    paro = discipline(2, "Parodontologie", [0,4,4,4,4,4,4,4,4,4], False, [6,6,6], [False, True, True, True, True, True, True, True, True, True],[4,5,6])
    como = discipline(3, "Comodulation", [3,3,3,3,3,3,0,0,3,3], False, [6,6,6] , [True, True, True, True, True, True, False, False, True, True],[4,5,6])
    pedo_soins = discipline(4, "Pédodontie Soins", [10,0,0,0,20,20,20,0,20,0], True, [12,12,12], [True]*10,[4,5,6])
    odf = discipline(5, "Orthodontie", [3] * 10, False, [4,4,4], [True]*10,[5])
    occl = discipline(6, "Occlusodontie", [4,0,4,0,0,0,4,0,4,0], False, [3,0,0], [True, False, True, False, False, False, True, False, True, False],[4])
    ra = discipline(7, "Radiologie", [4] * 10, False, [9,8,0], [True]*10,[4,5])
    ste = discipline(8, "Stérilisation", [1] * 10, False, [3,2,0], [True]*10,[4,5,6])
    pano = discipline(9, "Panoramique", [0,1,0,1,0,1,0,1,0,1,0,1] * 10, False, [0,3,3], [True]*10,[5,6])
    urg = discipline(10, "Urgence", [12] * 10, False, [20,20,20], [True]*10,[4,5,6])
    pedo_urg = discipline(11, "Pédodontie Urgences", [2] * 10, False, [0,1,1], [True]*10,[5,6])
    bloc = discipline(12, "BLOC", [0,0,2,0,0,0,2,0,0,0], False, [0,1,1], [False,False,True,False,False,False,True,False,False,False],[5,6])
    sp = discipline(13, "Soins spécifiques", [1,0,0,0,0,0,0,0,0,0], False, [0,0,0], [True,False,False,False,False,False,False,False,False,False],[5,6])   

    disciplines = [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]
    disc_map = {d.nom_discipline: d for d in disciplines}

    # --- 2. Load Students ---
    eleves = {}
    eleves_csv = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'eleves_with_code.csv')
    try:
        with open(eleves_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    eid = int(row["id_eleve"])
                    annee_val = niveau[row["annee"]].value
                    eleves[eid] = {
                        "id": eid,
                        "annee": annee_val,
                        "nom_annee": row["annee"]
                    }
                except KeyError: continue
    except FileNotFoundError:
        print(f"Error: {eleves_csv} not found.")
        return None, None
    
    return disc_map, eleves

def analyze_solution(solution_path, disc_map, eleves):
    if not os.path.exists(solution_path):
        print(f"Error: {solution_path} not found.")
        return

    # Data Structure: { student_id: { discipline_name: count } }
    assignments = collections.defaultdict(lambda: collections.defaultdict(int))
    
    print(f"Reading solution from {solution_path}...")
    with open(solution_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "STAGE:" in row["Discipline"]: continue
            
            try:
                sid = int(row["Id_Eleve"])
                disc_name = row["Discipline"]
                assignments[sid][disc_name] += 1
            except ValueError: continue

    # --- Stats Compilation ---
    stats_data = []
    
    # Per Student/Discipline Stats
    for sid, stud_data in eleves.items():
        annee = stud_data["annee"]
        
        for disc_name, disc_obj in disc_map.items():
            # Check if this student is concerned by this discipline
            if annee not in disc_obj.annee:
                continue
                
            # Get Quota
            try:
                # Assuming simple mapping: index in annee list = index in quota list
                # This depends on logic in model_V4_01.py: adx = disc.annee.index(el.annee.value)
                idx = disc_obj.annee.index(annee)
                quota = disc_obj.quota[idx]
            except ValueError:
                quota = 0
            
            # If quota is 0, is it still tracked?
            if quota == 0:
                # Check if they have assignments anyway
                count = assignments[sid][disc_name]
                if count > 0:
                    stats_data.append({
                        "Id_Eleve": sid,
                        "Annee": stud_data["nom_annee"],
                        "Discipline": disc_name,
                        "Attribue": count,
                        "Objectif": 0,
                        "Pourcentage": "N/A",
                        "Delta": count,
                        "Status": "Hors Quota"
                    })
                continue

            count = assignments[sid][disc_name]
            pct = count / quota * 100
            
            status = "OK"
            if count < quota: status = "Manque"
            elif count > quota: status = "Surplus"

            stats_data.append({
                "Id_Eleve": sid,
                "Annee": stud_data["nom_annee"],
                "Discipline": disc_name,
                "Attribue": count,
                "Objectif": quota,
                "Pourcentage": round(pct, 1),
                "Delta": count - quota,
                "Status": status
            })

    df = pd.DataFrame(stats_data)
    return df

def generate_report(df, output_path):
    wb = Workbook()
    
    # 1. Detailed Sheet
    ws_detail = wb.active
    ws_detail.title = "Détail par Élève"
    for r in dataframe_to_rows(df, index=False, header=True):
        ws_detail.append(r)
    
    # Style logic
    header_style = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    for cell in ws_detail[1]:
        cell.font = header_style
        cell.fill = header_fill
        
    # 2. Summary by Level (Annee) and Discipline
    if not df.empty:
        ws_summary = wb.create_sheet("Synthèse Promo")
        
        # Group by Annee, Discipline -> Sum(Attribue), Sum(Objectif), Mean(Pourcentage)
        
        # Create a cleaning copy for aggregation
        df_agg = df.copy()
        df_agg["Pourcentage"] = pd.to_numeric(df_agg["Pourcentage"], errors='coerce')
        
        summary = df_agg.groupby(["Annee", "Discipline"]).agg({
            "Attribue": "sum",
            "Objectif": "sum",
            "Pourcentage": "mean",
            "Id_Eleve": "count" # Number of students
        }).reset_index()
        
        summary["Moyenne_Vacations"] = summary["Attribue"] / summary["Id_Eleve"]
        summary["Taux_Remplissage_Global"] = (summary["Attribue"] / summary["Objectif"] * 100).round(1)
        summary["Pourcentage"] = summary["Pourcentage"].round(1)
        
        # Rename columns for clarity
        summary = summary.rename(columns={
            "Pourcentage": "Moyenne_%_Individuel",
            "Id_Eleve": "Nb_Eleves"
        })
        
        # Reorder
        cols = ["Annee", "Discipline", "Nb_Eleves", "Attribue", "Objectif", "Moyenne_Vacations", "Moyenne_%_Individuel", "Taux_Remplissage_Global"]
        summary = summary[cols]
        
        for r in dataframe_to_rows(summary, index=False, header=True):
            ws_summary.append(r)

        for cell in ws_summary[1]:
            cell.font = header_style
            cell.fill = header_fill
            
        # 3. Global Discipline Stats
        ws_disc = wb.create_sheet("Synthèse Discipline")
        disc_stats = df.groupby("Discipline").agg({
            "Attribue": "sum",
            "Objectif": "sum"
        }).reset_index()
        disc_stats["Taux_Global"] = (disc_stats["Attribue"] / disc_stats["Objectif"] * 100).round(1)
        
        for r in dataframe_to_rows(disc_stats, index=False, header=True):
            ws_disc.append(r)

        for cell in ws_disc[1]:
            cell.font = header_style
            cell.fill = header_fill

    # 4. General Statistics (Student Totals & Global)
    ws_gen = wb.create_sheet("Synthèse Générale")
    
    # A. Total per Student
    # Group by Id_Eleve, Annee -> Sum(Attribue), Sum(Objectif)
    stud_totals = df.groupby(["Id_Eleve", "Annee"]).agg({
        "Attribue": "sum",
        "Objectif": "sum"
    }).reset_index()
    
    # Calculate global fill rate per student (handle division by zero if objective is 0)
    stud_totals["Taux_Remplissage"] = stud_totals.apply(
        lambda row: round(row["Attribue"] / row["Objectif"] * 100, 1) if row["Objectif"] > 0 else 0, axis=1
    )
    
    ws_gen.append(["Statistiques par Élève (Toutes disciplines confondues)"])
    ws_gen.append(["Id_Eleve", "Annee", "Total_Vacations", "Total_Objectif", "Taux_Remplissage"])
    
    # Style header
    for col in range(1, 6):
        cell = ws_gen.cell(row=2, column=col)
        cell.font = header_style
        cell.fill = header_fill

    for r in dataframe_to_rows(stud_totals, index=False, header=False):
        ws_gen.append(r)
        
    ws_gen.append([]) # Spacer
    ws_gen.append([]) # Spacer

    # B. Total per Level (Promo)
    # Group by Annee -> Sum(Attribue), Sum(Objectif), Count(Unique Students)
    level_totals = df.groupby("Annee").agg({
        "Attribue": "sum",
        "Objectif": "sum",
        "Id_Eleve": "nunique"
    }).reset_index()
    
    level_totals["Moyenne_Vacations"] = (level_totals["Attribue"] / level_totals["Id_Eleve"]).round(1)
    level_totals["Taux_Global"] = (level_totals["Attribue"] / level_totals["Objectif"] * 100).round(1)

    start_row = ws_gen.max_row + 1
    ws_gen.append(["Statistiques par Promotion"])
    ws_gen.append(["Annee", "Total_Vacations_Promo", "Total_Objectif_Promo", "Nb_Eleves", "Moyenne_Par_Eleve", "Taux_Global"])
    
    # Style header
    for col in range(1, 7):
        cell = ws_gen.cell(row=start_row+1, column=col)
        cell.font = header_style
        cell.fill = header_fill

    for r in dataframe_to_rows(level_totals, index=False, header=False):
        ws_gen.append(r)

    ws_gen.append([]) # Spacer
    ws_gen.append([]) # Spacer

    # C. Grand Total
    grand_total_attrib = df["Attribue"].sum()
    grand_total_obj = df["Objectif"].sum()
    grand_total_pct = round(grand_total_attrib / grand_total_obj * 100, 1) if grand_total_obj > 0 else 0
    
    start_row = ws_gen.max_row + 1
    ws_gen.append(["Statistiques Globales (Tout le planning)"])
    ws_gen.append(["Total_Vacations_Affectées", "Total_Quota_Attendu", "Taux_Global"])
    
    # Style header
    for col in range(1, 4):
        cell = ws_gen.cell(row=start_row+1, column=col)
        cell.font = header_style
        cell.fill = header_fill

    ws_gen.append([grand_total_attrib, grand_total_obj, grand_total_pct])

    # Adjust column widths
    ws_gen.column_dimensions['A'].width = 25
    ws_gen.column_dimensions['B'].width = 25
    ws_gen.column_dimensions['C'].width = 25
    ws_gen.column_dimensions['D'].width = 25
    ws_gen.column_dimensions['E'].width = 25

    # Save
    wb.save(output_path)
    print(f"Report generated: {output_path}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    solution_file = os.path.join(base_dir, 'resultat', 'planning_solution.csv')
    output_file = os.path.join(base_dir, 'resultat', 'statistiques_solution.xlsx')
    
    disc_map, eleves = load_data()
    if disc_map and eleves:
        print("Analyzing solution...")
        df = analyze_solution(solution_file, disc_map, eleves)
        if df is not None:
            generate_report(df, output_file)
            print("Done.")
