import csv
import os
import sys

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.stage import stage
from classes.enum.niveaux import niveau

SERVICE_SANITAIRE = "SERVICE SANITAIRE"
STAGE_ACTIF = "Stage Actif"

def generate_stages_csv():
    # Reset static counter just in case (though script runs once)
    stage.id_stage = 0
    
    stages_objects = []

    # Definition based on user requirements
    
    def add_stage(nom, niv_enum, debut, fin, p_id):
        # __init__(self, nom_stage: str, debut_stage: int, fin_stage: int, pour_niveau: niveau, periode: int)
        # Note the order in __init__ from the file I read:
        # nom_stage, debut_stage, fin_stage, pour_niveau, periode
        new_stage = stage(nom, debut, fin, niv_enum, p_id)
        stages_objects.append(new_stage)

    # Period 1
    add_stage(STAGE_ACTIF, niveau.DFTCC, 45, 51, 1)
    add_stage(SERVICE_SANITAIRE, niveau.DFAS01, 45, 51, 1)
    
    # Period 2
    add_stage(STAGE_ACTIF, niveau.DFTCC, 2, 8, 2)
    add_stage(SERVICE_SANITAIRE, niveau.DFAS01, 2, 8, 2)
    
    # Period 3
    add_stage(STAGE_ACTIF, niveau.DFTCC, 9, 15, 3)
    add_stage(SERVICE_SANITAIRE, niveau.DFAS01, 9, 15, 3)
    
    # Period 4
    add_stage(STAGE_ACTIF, niveau.DFTCC, 16, 22, 4)
    add_stage(SERVICE_SANITAIRE, niveau.DFAS01, 38, 44, 4)

    # Path setup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, '..', '..', 'data', 'mock_stages.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Fields to export
    # The class has: id_stage, nom_stage, periode, pour_niveau, debut_stage, fin_stage
    header = ["id_stage", "nom_stage", "deb_semaine", "fin_semaine", "pour_niveau", "periode"]

    try:
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            for s in stages_objects:
                writer.writerow([
                    s.id_stage,
                    s.nom_stage,
                    s.debut_stage,
                    s.fin_stage,
                    s.pour_niveau.name, # Export name of Enum
                    s.periode
                ])
        print(f"Fichier stages.csv généré avec succès : {output_path}")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    generate_stages_csv()
