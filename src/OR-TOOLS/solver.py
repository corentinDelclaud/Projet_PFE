"""
solver.py - Configuration et exécution du solveur OR-Tools
"""
import os
import csv
from ortools.sat.python import cp_model
from Projet_PFE.src.classes.enum.demijournee import Periode


def configure_solver():
    """Configure les paramètres du solveur CP-SAT"""
    solver = cp_model.CpSolver()
    
    # Enable logging
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = True
    
    # Set a time limit of 10 minutes (600 seconds)
    solver.parameters.max_time_in_seconds = 1200
    
    # Limit workers to prevent OOM
    solver.parameters.num_search_workers = 4
    
    return solver


def solve_model(model, solver):
    """
    Résout le modèle avec le solveur configuré
    
    Args:
        model: Le modèle CP-SAT à résoudre
        solver: Le solveur CP-SAT configuré
        
    Returns:
        status: Le statut de la résolution (OPTIMAL, FEASIBLE, INFEASIBLE, etc.)
    """
    print("Lancement du solveur...")
    status = solver.Solve(model)
    print(solver.ResponseStats())
    
    return status


def export_solution_to_csv(solver, assignments, eleves, disciplines, vacations, stages_eleves):
    """
    Exporte la solution trouvée dans un fichier CSV
    
    Args:
        solver: Le solveur avec la solution
        assignments: Dict des variables d'affectation
        eleves: Liste des élèves
        disciplines: Liste des disciplines
        vacations: Liste des créneaux
        stages_eleves: Dict des stages par élève
        
    Returns:
        str: Chemin du fichier CSV créé
    """
    # Création du dictionnaire des élèves pour un accès rapide
    eleve_dict = {e.id_eleve: e for e in eleves}
    
    # Création du dossier resultat s'il n'existe pas
    result_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resultat')
    os.makedirs(result_dir, exist_ok=True)
    
    csv_file_path = os.path.join(result_dir, 'planning_solution.csv')
    
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(["Semaine", "Jour", "Periode", "Id_Eleve", "Eleve", "Discipline"])
        
        day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        
        for v_idx, vac in enumerate(vacations):
            jour_str = day_names[vac.jour]
            p_str = "Matin" if vac.period == Periode.matin else "Apres-Midi"
            
            # 1. Affectations Disciplines
            for (e_id, d_id, idx), val in assignments.items():
                if idx == v_idx and solver.Value(val) == 1:
                    e_name = eleve_dict[e_id].nom
                    d_name = next(d.nom_discipline for d in disciplines if d.id_discipline == d_id)
                    writer.writerow([vac.semaine, jour_str, p_str, e_id, e_name, d_name])

            # 2. Affectations Stages
            for e_id, s_list in stages_eleves.items():
                for s in s_list:
                    if s.debut_stage <= vac.semaine <= s.fin_stage:
                        e_name = eleve_dict[e_id].nom
                        writer.writerow([vac.semaine, jour_str, p_str, e_id, e_name, f"STAGE: {s.nom_stage}"])
    
    return csv_file_path


def print_solution_summary(status, solver):
    """
    Affiche un résumé de la solution trouvée
    
    Args:
        status: Le statut de la résolution
        solver: Le solveur avec la solution
    """
    if status == cp_model.OPTIMAL:
        print(f"\n✓ Solution OPTIMALE trouvée!")
        print(f"  Valeur objectif: {solver.ObjectiveValue()}")
    elif status == cp_model.FEASIBLE:
        print(f"\n✓ Solution RÉALISABLE trouvée!")
        print(f"  Valeur objectif: {solver.ObjectiveValue()}")
    elif status == cp_model.INFEASIBLE:
        print("\n✗ Problème INFAISABLE - Aucune solution n'existe avec les contraintes actuelles")
    elif status == cp_model.MODEL_INVALID:
        print("\n✗ Modèle INVALIDE - Erreur dans la définition du modèle")
    elif status == cp_model.UNKNOWN:
        print("\n⚠ Statut INCONNU - Le solveur n'a pas trouvé de solution dans le temps imparti")
        print(f"  Meilleure borne: {solver.BestObjectiveBound()}")
    else:
        print(f"\n? Statut: {status}")
