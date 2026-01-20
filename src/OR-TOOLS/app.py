"""
app.py - Point d'entrée principal regroupant parameter.py, model.py et solver.py
"""
import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import LogCapture
from ortools.sat.python import cp_model

# Import des modules du projet
import parameter
import model
import solver


if __name__ == "__main__":
    log_capture = LogCapture()
    log_capture.start()
    
    try:
        print("="*60)
        print("PLANIFICATION DES STAGES DENTAIRES - OR-TOOLS")
        print("="*60)
        
        # === PHASE 1 : INITIALISATION DES PARAMÈTRES ===
        print("\n[1/4] Initialisation des données...")
        
        # Initialisation des disciplines
        disciplines = parameter.initialize_disciplines()
        
        # Chargement des élèves
        eleves_csv = 'eleves_with_code.csv'
        eleves, eleves_by_niveau = parameter.load_students(eleves_csv)
        
        # Chargement des stages
        stages_csv = 'mock_stages.csv'
        stages_lookup = parameter.load_stages(stages_csv)
        stages_eleves = parameter.assign_stages_to_students(eleves, stages_lookup)
        
        # Génération des vacations (créneaux horaires)
        vacations = parameter.generate_vacations()
        
        # Chargement des calendriers d'indisponibilités
        calendrier_DFAS01_csv = 'mock_calendrier_DFAS01.csv'
        calendrier_DFAS02_csv = 'mock_calendrier_DFAS02.csv'
        calendrier_DFTCC_csv = 'mock_calendrier_DFTCC.csv'
        calendar_unavailability = parameter.load_calendars(
            calendrier_DFAS01_csv, 
            calendrier_DFAS02_csv, 
            calendrier_DFTCC_csv
        )
        
        # === PHASE 2 : CRÉATION DU MODÈLE ===
        print("\n[2/4] Création du modèle OR-Tools...")
        cp_model_obj, assignments, forced_to_zero = model.create_model(
            disciplines=disciplines,
            eleves=eleves,
            vacations=vacations,
            stages_eleves=stages_eleves,
            calendar_unavailability=calendar_unavailability,
            eleves_by_niveau=eleves_by_niveau
        )
        
        # === PHASE 3 : RÉSOLUTION ===
        print("\n[3/4] Configuration et résolution du problème...")
        solver_obj = solver.configure_solver()
        status = solver.solve_model(cp_model_obj, solver_obj)
        
        # === PHASE 4 : EXPORT DES RÉSULTATS ===
        print("\n[4/4] Export des résultats...")
        
        # Affichage du résumé
        solver.print_solution_summary(status, solver_obj)
        
        # Export si solution trouvée
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            csv_path = solver.export_solution_to_csv(
                solver_obj, 
                assignments, 
                eleves, 
                disciplines, 
                vacations, 
                stages_eleves
            )
            print(f"\n✓ Planning exporté dans : {csv_path}")
            print("\n" + "="*60)
            print("SUCCÈS - Le planning a été généré avec succès!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("ÉCHEC - Aucune solution n'a pu être trouvée")
            print("="*60)
            
    except Exception as e:
        print(f"\n✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        log_capture.stop()
        print("\nFin de l'exécution.")
