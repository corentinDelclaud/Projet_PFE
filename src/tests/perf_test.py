import sys
import os
import time
import csv
from ortools.sat.python import cp_model

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.discipline import discipline
from classes.eleve import eleve
from classes.vacation import vacation
from classes.cours import cours
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from Projet_PFE.src.classes.enum.demijournee import Periode

# --- SETUP COMMON DATA ---

# 1. Disciplines
poly = discipline(1, "Polyclinique", "A101", 1, True, 3)
paro = discipline(2, "Parodontologie", "A102", 1, True, 8)
como = discipline(3, "Comodulation", "A103", 1, True, 6)
pedo = discipline(4, "Pédodontie", "A104", 5, True, 4)
odf = discipline(5, "Orthodontie", "A105", 8, True, 5)
occl = discipline(6, "Occlusodontie", "A106", 12, True, 7)
ra = discipline(7, "Radiologie", "A107", 1, False, 0)
ste = discipline(8, "Stomatologie", "A108", 18, True, 0)
pano = discipline(9, "Panoramique", "A109", 1, False, 1)
cs_urg = discipline(10, "Consultation d'urgence", "A110", 1, False, 1)
sp = discipline(11, "Soins Prothétiques", "A111", 1, True, 1)
urg_op = discipline(12, "Urgences Opératoires", "A112", 1, False, 2)

# Presence setup (mocked like in planification.py)
for d in [poly, paro, como, pedo, odf, occl, ra, ste, pano, cs_urg, sp, urg_op]:
    # Simple mock presence
    d.presence = [True] * 10

disciplines = [poly, paro, como, pedo, odf, occl, ra, ste, pano, cs_urg, sp, urg_op]

# 2. Eleves (Load from CSV)
eleves: list[eleve] = []
csv_path = os.path.join(os.path.dirname(__file__), '..', 'resultat', 'eleves.csv')
if not os.path.exists(csv_path):
    print("CSV not found, run generate_students_csv.py first")
    sys.exit(1)

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pref = jour_pref[row["jour_preference"]] 
        niv = niveau[row["annee"]]
        new_eleve = eleve(
            id_eleve=int(row["id_eleve"]),
            nom=row["nom"],
            id_binome=int(row["id_binome"]),
            jour_preference=pref,
            annee=niv
        )
        eleves.append(new_eleve)

# 3. Vacations (5 weeks)
vacations: list[vacation] = []
for semaine in range(1, 52): # 5 Semaines
    for jour in range(0, 5):
        for p in Periode:
            vacations.append(vacation(semaine, jour, p))

print(f"--- PERFORMANCE TEST ---")
print(f"Data: {len(eleves)} Studdents, {len(disciplines)} Disciplines, {len(vacations)} Vacations (5 weeks)")
print(f"Total Variables approx: {len(eleves) * len(disciplines) * len(vacations)}")

# --- TEST FUNCTION ---

def run_construction_test(use_optimization: bool):
    start_time = time.time()
    
    model = cp_model.CpModel()
    assignments = {}

    # Optimization: Dict lookup
    eleve_dict = {}
    if use_optimization:
        eleve_dict = {e.id_eleve: e for e in eleves}

    # 1. Variables & Capacity & Uniqueness
    for v_idx, vac in enumerate(vacations):
        vac_id = f"{vac.semaine}_{vac.jour}_{vac.period.name}"
        jour_idx = vac.jour 
        periode_offset = 0 if vac.period == Periode.matin else 1
        slot_index = jour_idx * 2 + periode_offset
        
        for disc in disciplines:
            is_open = True # Simplified for test
            if not is_open: continue
                
            vars_in_discipline_slot = []
            
            for el in eleves:
                # Simplified availability checks (skipping stages/cours for pure algo perf)
                var_name = f"assign_e{el.id_eleve}_d{disc.id_discipline}_{vac_id}"
                x_var = model.NewBoolVar(var_name)
                assignments[(el.id_eleve, disc.id_discipline, v_idx)] = x_var
                vars_in_discipline_slot.append(x_var)
            
            # Capacity
            limit = disc.nb_fauteuil * 2 if disc.en_binome else disc.nb_fauteuil
            if vars_in_discipline_slot:
                model.Add(sum(vars_in_discipline_slot) <= limit)

        # Uniqueness
        for el in eleves:
            vars_for_student_in_slot = []
            for disc in disciplines:
                key = (el.id_eleve, disc.id_discipline, v_idx)
                if key in assignments:
                    vars_for_student_in_slot.append(assignments[key])
            if vars_for_student_in_slot:
                model.Add(sum(vars_for_student_in_slot) <= 1)

    # 2. Binome Constraint
    for v_idx, vac in enumerate(vacations):
        for disc in disciplines:
            if disc.en_binome:
                for el in eleves:
                    if el.id_binome != 0:
                        
                        # --- DIFF IS HERE ---
                        binome_obj = None
                        if use_optimization:
                            binome_obj = eleve_dict.get(el.id_binome) # O(1)
                        else:
                            # O(E) Linear scan inside loop
                            binome_obj = next((e for e in eleves if e.id_eleve == el.id_binome), None)
                        # --------------------

                        if binome_obj:
                            if el.id_eleve < binome_obj.id_eleve:
                                key1 = (el.id_eleve, disc.id_discipline, v_idx)
                                key2 = (binome_obj.id_eleve, disc.id_discipline, v_idx)
                                if key1 in assignments and key2 in assignments:
                                    model.Add(assignments[key1] == assignments[key2])

    # 3. Quotas (Same for both)
    for el in eleves:
        for disc in disciplines:
            vars_for_student_discipline = []
            for v_idx in range(len(vacations)):
                key = (el.id_eleve, disc.id_discipline, v_idx)
                if key in assignments:
                    vars_for_student_discipline.append(assignments[key])
            if vars_for_student_discipline:
                 model.Add(sum(vars_for_student_discipline) <= disc.quota)

    # 4. Objective
    objective_terms = []
    for (e_id, d_id, v_idx), x_var in assignments.items():
        
        # --- DIFF IS HERE ---
        eleve_obj = None
        if use_optimization:
            eleve_obj = eleve_dict[e_id] # O(1)
        else:
             # O(E) Linear scan inside loop
            eleve_obj = next(e for e in eleves if e.id_eleve == e_id)
        # --------------------
        
        vac_obj = vacations[v_idx]
        weight = 1
        if (vac_obj.jour + 1) == eleve_obj.jour_preference.value:
            weight = 10
        objective_terms.append(weight * x_var)

    model.Maximize(sum(objective_terms))
    
    end_time = time.time()
    return end_time - start_time

# --- RUN EXECUTION ---

print("\nRunning OLD method (O(N^2))... please wait...")
time_old = run_construction_test(use_optimization=False)
print(f"OLD Method Construction Time: {time_old:.4f} seconds")

print("\nRunning NEW method (O(N))...")
time_new = run_construction_test(use_optimization=True)
print(f"NEW Method Construction Time: {time_new:.4f} seconds")

ratio = time_old / time_new if time_new > 0 else 0
print(f"\nSpeedup Factor: {ratio:.2f}x faster")
