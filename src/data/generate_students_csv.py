import sys
import os
import csv
import random

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.eleve import eleve
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau

def generate_students_csv():
    # Génération de 100 élèves par niveau
    eleves: list[eleve] = []
    id_counter = 1

    eleves_by_niveau = {
        niveau.DFAS01: [],
        niveau.DFAS02: [],
        niveau.DFTCC: []
    }

    # 1. Création des élèves
    for niv in niveau:
        for i in range(100):
            pref = random.choice(list(jour_pref))
            new_eleve = eleve(id_counter, f"Eleve_{id_counter}_{niv.name}", 0, pref, niv)
            eleves.append(new_eleve)
            eleves_by_niveau[niv].append(new_eleve)
            id_counter += 1

    # 2. Gestion des Binômes
    # Règle : DFAS01 (4A) avec DFTCC (6A), et DFAS02 (5A) entre eux.

    # Pairing DFAS02 <-> DFAS02
    dfas02_list = eleves_by_niveau[niveau.DFAS02]
    # Independent stage assignment for DFAS02
    # 100 students / 4 periods = 25 students per period exactly.
    for i, e in enumerate(dfas02_list):
        p = (i % 4) + 1
        e.periode_stage = p
        e.periode_stage_ext = 0

    # Pairing for Binome ID only (for other purposes), but Stage is independent?
    # User said "stages are not by pairs".
    # So I will assign binome IDs as before (business rule: everyone has a binome),
    # BUT I will assign stage periods independently (round robin on the list of students).
    
    # 1. Assign Binomes DFAS02
    for i in range(0, len(dfas02_list), 2):
        if i + 1 < len(dfas02_list):
            e1 = dfas02_list[i]
            e2 = dfas02_list[i+1]
            e1.id_binome = e2.id_eleve
            e2.id_binome = e1.id_eleve
            e2.jour_preference = e1.jour_preference

    # Pairing DFAS01 <-> DFTCC
    dfas01_list = eleves_by_niveau[niveau.DFAS01]
    dftcc_list = eleves_by_niveau[niveau.DFTCC]

    # 1. Assign Binomes DFAS01 <-> DFTCC
    for i in range(min(len(dfas01_list), len(dftcc_list))):
        e1 = dfas01_list[i]
        e2 = dftcc_list[i]
        e1.id_binome = e2.id_eleve
        e2.id_binome = e1.id_eleve
        e2.jour_preference = e1.jour_preference

    # 2. Assign Stage Periods Independently
    # DFAS01: 100 students -> 25 per period
    for i, e in enumerate(dfas01_list):
        p = (i % 4) + 1
        e.periode_stage = p
        e.periode_stage_ext = 0
        
    # DFTCC: 100 students -> 25 per period
    for i, e in enumerate(dftcc_list):
        p = (i % 4) + 1
        e.periode_stage = p
        e.periode_stage_ext = 0

    # --- CSV EXPORT ---
    result_dir = os.path.dirname(os.path.abspath(__file__)) # Update to store in src/data/../../data/ if needed, but original was 'resultat'
    # Original code: result_dir = os.path.join(os.path.dirname(__file__), '..', 'resultat')
    # Actually let's put it in data/eleves.csv as per workspace structure usually expected by planning logic
    # The previous code wrote to 'resultat/eleves.csv'.
    # But `planification.py` reads `../../data/eleves.csv`.
    # I should write to `data/eleves.csv`.
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    csv_file_path = os.path.join(data_dir, 'eleves.csv')
    
    header = ["id_eleve", "nom", "id_binome", "jour_preference", "annee", "periode_stage", "periode_stage_ext"]

    try:
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            
            for el in eleves:
                writer.writerow([
                    el.id_eleve,
                    el.nom,
                    el.id_binome,
                    el.jour_preference.name,
                    el.annee.name,
                    getattr(el, 'periode_stage', 0),
                    getattr(el, 'periode_stage_ext', 0)
                ])
        print(f"Fichier élèves généré avec succès : {csv_file_path}")
        print(f"Nombre total d'élèves : {len(eleves)}")
    except Exception as e:
        print(f"Erreur lors de la génération du CSV : {e}")

if __name__ == "__main__":
    generate_students_csv()
