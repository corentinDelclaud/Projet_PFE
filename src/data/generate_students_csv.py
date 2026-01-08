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
    for i in range(0, len(dfas02_list), 2):
        if i + 1 < len(dfas02_list):
            e1 = dfas02_list[i]
            e2 = dfas02_list[i+1]
            
            e1.id_binome = e2.id_eleve
            e2.id_binome = e1.id_eleve
            e2.jour_preference = e1.jour_preference # Harmonisation

    # Pairing DFAS01 <-> DFTCC
    dfas01_list = eleves_by_niveau[niveau.DFAS01]
    dftcc_list = eleves_by_niveau[niveau.DFTCC]

    for i in range(min(len(dfas01_list), len(dftcc_list))):
        e1 = dfas01_list[i]
        e2 = dftcc_list[i]
        
        e1.id_binome = e2.id_eleve
        e2.id_binome = e1.id_eleve
        e2.jour_preference = e1.jour_preference # Harmonisation

    # --- CSV EXPORT ---
    result_dir = os.path.join(os.path.dirname(__file__), '..', 'resultat')
    os.makedirs(result_dir, exist_ok=True)
    
    csv_file_path = os.path.join(result_dir, 'eleves.csv')
    
    header = ["id_eleve", "nom", "id_binome", "jour_preference", "annee"]

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
                    el.annee.name
                ])
        print(f"Fichier élèves généré avec succès : {csv_file_path}")
        print(f"Nombre total d'élèves : {len(eleves)}")
    except Exception as e:
        print(f"Erreur lors de la génération du CSV : {e}")

if __name__ == "__main__":
    generate_students_csv()
