import sys
import os
import csv
import collections

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ortools.sat.python import cp_model
from classes.discipline import discipline
from classes.eleve import eleve
from classes.vacation import vacation
from classes.cours import cours
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from classes.enum.demijournee import DemiJournee
from classes.periode import Periode

# =============================================================================
# 1. INITIALISATION DU MODELE ET DATALOADING
# =============================================================================
print("Initialisation du modèle et chargement des données...")

# Instanciation des disciplines (Configuration issue de new_model.py)
poly = discipline(1, "Polyclinique", [20,20,20,20,20,20,20,20,20,20], True, [52,52,52], [True]*10,[4,5,6])
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

# Configuration des présences (Ouvertures/Fermetures créneaux types)
# Format: [LunMatin, LunAprem, MarMatin, ...]
poly.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
paro.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, True, True, True, True, True, True, True, True])
como.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, False, False, True, True])
pedo_soins.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, False, False, True, True, True, False, True, False])
odf.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, True, True, False, False, False, True])
occl.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, True, False, False, False, True, False, True, False])
ra.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
ste.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pano.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, False, True, False, True, False, True])
urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pedo_urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, False, False, False, False, True, False, True])
bloc.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True,False,True,False,False,False,True,False,False,False])

# Modifications spécifiques (Contraintes avancées)
poly.modif_nb_vacations_par_semaine(4)
poly.modif_paire_jours([ (0,1), (2,3), (0,4) ]) # Paires requises
poly.modif_take_jour_pref(True)
bloc.modif_fill_requirement(True)
sp.modif_fill_requirement(True)
# paro.modif_mixite_groupes(2) # Désactivé pour stabilité initiale

disciplines = [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]

# Chargement Élèves
eleves: list[eleve] = []
eleves_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'eleves_with_code.csv')
with open(eleves_csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            new_eleve = eleve(
                id_eleve=int(row["id_eleve"]),
                nom=row["code"],
                id_binome=int(row["id_binome"]),
                jour_preference=jour_pref[row["jour_preference"]],
                annee=niveau[row["annee"]]
            )
            new_eleve.periode_stage = int(row.get("periode_stage", 0))
            eleves.append(new_eleve)
        except KeyError: continue
eleve_dict = {e.id_eleve: e for e in eleves}
print(f"  {len(eleves)} élèves chargés.")

# Chargement Stages
list_periodes = [Periode(0, 34, 44), Periode(1, 45, 51), Periode(2, 1, 8), Periode(3, 9, 15), Periode(4, 16, 22), Periode(5, 23, 30)]
stages_lookup = collections.defaultdict(list)
stages_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'mock_stages_copy.csv') # Using copy as per working context
if os.path.exists(stages_csv_path):
    with open(stages_csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stages_lookup[(row["pour_niveau"], int(row["periode"]))].append({
                 "nom": row["nom_stage"], "debut": int(row["deb_semaine"]), "fin": int(row["fin_semaine"]), "niveau_obj": niveau[row["pour_niveau"]]
            })

stages_eleves = {}
for el in eleves:
    if el.periode_stage > 0:
        key = (el.annee.name, el.periode_stage)
        if key in stages_lookup:
            stages_eleves[el.id_eleve] = [stage(d["nom"], d["debut"], d["fin"], d["niveau_obj"], el.periode_stage) for d in stages_lookup[key]]

# Chargement Calendriers (Indisponibilités Cours)
calendar_unavailability = collections.defaultdict(set)
cal_files = {niveau.DFAS01: 'calendrier_DFASO1.csv', niveau.DFAS02: 'calendrier_DFASO2.csv', niveau.DFTCC: 'calendrier_DFTCC.csv'}
for niv, fname in cal_files.items():
    fpath = os.path.join(os.path.dirname(__file__), '..', '..', 'data', fname)
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                s = int(row.get("Semaine", "0").replace("S","") or 0)
                if s == 0: continue
                for i in range(1, 11):
                    if row.get(str(i), "").strip(): calendar_unavailability[niv].add((s, i-1))

# Génération Vacations (Semaines 1-52)
vacations = []
for s in range(1, 53):
    for j in range(5):
        for p in DemiJournee:
            vacations.append(vacation(s, j, p))

# =============================================================================
# 2. DEFINITION DU MODELE OR-TOOLS
# =============================================================================
model = cp_model.CpModel()
assignments = {} # (id_eleve, id_discipline, index_vacation) -> BoolVar

print(f"Création des variables pour {len(eleves)} élèves sur {len(vacations)} créneaux...")

count_vars = 0
for v_idx, vac in enumerate(vacations):
    # Index 0-9 pour la semaine
    slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
    
    for disc in disciplines:
        # Contrainte 3 (Fermeture Discipline): O_{d,v} = 0
        if not (len(disc.presence) > slot_idx and disc.presence[slot_idx]):
            continue 

        for el in eleves:
            # Filtre année
            if el.annee.value not in disc.annee:
                continue

            # Contrainte 3 (Indisponibilité Élève): I_{e,v} = 1
            # 1. Cours
            if (vac.semaine, slot_idx) in calendar_unavailability[el.annee]:
                continue
            
            # 2. Stage
            is_in_stage = False
            if el.id_eleve in stages_eleves:
                for st in stages_eleves[el.id_eleve]:
                    if st.debut_stage <= vac.semaine <= st.fin_stage:
                        is_in_stage = True
                        break
            if is_in_stage:
                continue

            # Création variable x_{e,d,v}
            var_name = f"x_e{el.id_eleve}_d{disc.id_discipline}_v{v_idx}"
            assignments[(el.id_eleve, disc.id_discipline, v_idx)] = model.NewBoolVar(var_name)
            count_vars += 1

print(f"Modèle initialisé avec {count_vars} variables.")

# =============================================================================
# 3. OPTIMISATION ET CONTRAINTES
# =============================================================================

# Pré-calcul des groupements de variables pour accélérer la création des contraintes
print("Pré-traitement des variables (Indexation)...")
vars_by_student_vac = collections.defaultdict(list)   # (eleve_id, vac_idx) -> [var]
vars_by_disc_vac = collections.defaultdict(list)      # (disc_id, vac_idx) -> [var]
vars_by_student_disc_semaine = collections.defaultdict(list) # (eleve_id, disc_id, semaine) -> [var]

for (e_id, d_id, v_idx), var in assignments.items():
    vars_by_student_vac[(e_id, v_idx)].append(var)
    vars_by_disc_vac[(d_id, v_idx)].append(var)
    
    semaine = vacations[v_idx].semaine
    vars_by_student_disc_semaine[(e_id, d_id, semaine)].append((v_idx, var))

# 1. Capacité des Disciplines: sum(x_{e,d,v} for e) <= C_{d,v}
print("Ajout contrainte: Capacité...")
for v_idx, vac in enumerate(vacations):
    slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
    for disc in disciplines:
        vars_in_disc_slot = vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
        if vars_in_disc_slot:
            # Capacité théorique pour ce créneau (nb_eleve)
            cap = disc.nb_eleve[slot_idx] if slot_idx < len(disc.nb_eleve) else 0
            model.Add(sum(vars_in_disc_slot) <= cap)

# 2. Unicité de l'Affectation: sum(x_{e,d,v} for d) <= 1
print("Ajout contrainte: Unicité...")
for v_idx in range(len(vacations)):
    for el in eleves:
        vars_for_student = vars_by_student_vac.get((el.id_eleve, v_idx), [])
        if vars_for_student:
            model.Add(sum(vars_for_student) <= 1)

# Contraintes additionnelles
obj_terms = []
weights = []

# NB VACATIONS PAR SEMAINE (Hard)
print("Ajout contrainte: Max Vacations/Semaine...")
for disc in disciplines:
    if disc.nb_vacations_par_semaine > 0:
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            for s in range(1, 53):
                # Récupérer variables via index
                vars_entries = vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                vars_week = [v[1] for v in vars_entries]
                if vars_week:
                    model.Add(sum(vars_week) <= disc.nb_vacations_par_semaine)

# PAIRE JOURS (Soft)
print("Ajout contrainte: Paires de Jours (Soft)...")
for disc in disciplines:
    if disc.paire_jours:
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            for s in range(1, 53):
                vars_entries = vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                if not vars_entries: continue

                for (j1, j2) in disc.paire_jours:
                    # vars_entries est une liste de (v_idx, var)
                    vars_j1 = [v[1] for v in vars_entries if vacations[v[0]].jour == j1]
                    vars_j2 = [v[1] for v in vars_entries if vacations[v[0]].jour == j2]
                    
                    if vars_j1 and vars_j2:
                        b_j1 = model.NewBoolVar(f"present_j{j1}_s{s}_e{el.id_eleve}_d{disc.id_discipline}")
                        b_j2 = model.NewBoolVar(f"present_j{j2}_s{s}_e{el.id_eleve}_d{disc.id_discipline}")
                        model.Add(sum(vars_j1) >= 1).OnlyEnforceIf(b_j1)
                        model.Add(sum(vars_j1) == 0).OnlyEnforceIf(b_j1.Not())
                        model.Add(sum(vars_j2) >= 1).OnlyEnforceIf(b_j2)
                        
                        # Si b_j1 alors on VEUT b_j2. 
                        # On pénalise si b_j1 et NOT b_j2
                        # Ou bonus si b_j1 => b_j2
                        
                        pair_ok = model.NewBoolVar(f"pair_ok_{j1}_{j2}_{s}_e{el.id_eleve}_d{disc.id_discipline}")
                        model.AddImplication(b_j1, b_j2).OnlyEnforceIf(pair_ok)
                        obj_terms.append(pair_ok)
                        weights.append(50)

# OBJECTIF PRINCIPAL: Remplissage et Quotas
print("Configuration Objectifs...")

# A. Maximiser le nombre total d'affectations (Remplissage de base)
for var in assignments.values():
    obj_terms.append(var)
    weights.append(1)

# B. Respect des Préférences (Jour Préféré)
if poly.take_jour_pref: # Seulement pour Poly ou configurable globalement
    for k, var in assignments.items():
        if k[1] == poly.id_discipline: # Si c'est poly
            el = eleve_dict[k[0]]
            v_idx = k[2]
            vac = vacations[v_idx]
            # vac.jour 0..4, pref 1..5
            if (vac.jour + 1) == el.jour_preference.value:
                obj_terms.append(var)
                weights.append(20) # Bonus significatif

# C. Quotas (Version Simplifiée: Maximiser jusqu'au quota)
for disc in disciplines:
    for el in eleves:
        if el.annee.value not in disc.annee: continue
        vars_all = [assignments[k] for k in assignments if k[0] == el.id_eleve and k[1] == disc.id_discipline]
        if vars_all:
             # On veut atteindre le quota. Chaque affectation apporte des points
             # Poids adaptatif ? Non, simple somme pondérée suffit pour la maximisation
             pass

model.Maximize(sum(t * w for t, w in zip(obj_terms, weights)))

# =============================================================================
# 4. RESOLUTION ET EXPORT
# =============================================================================
print("Lancement du solveur...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300
solver.parameters.log_search_progress = True
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Solution trouvée ! Objectif: {solver.ObjectiveValue()}")
    
    # Export CSV
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resultat')
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    output_csv = os.path.join(output_dir, 'planning_solution.csv')

    print(f"Export en cours vers {output_csv}...")
    headers = ["Semaine", "Jour", "Apres-Midi", "Discipline", "Id_Discipline", "Eleve", "Id_Eleve", "Annee", "Code_Eleve"]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        count = 0
        for (e_id, d_id, v_idx), var in assignments.items():
            if solver.Value(var) == 1:
                vac = vacations[v_idx]
                el = eleve_dict[e_id]
                disc = next(d for d in disciplines if d.id_discipline == d_id)
                
                # Jour str
                jours_str = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
                # Period str
                per_str = "Matin" if vac.period == DemiJournee.matin else "Apres-Midi"
                
                writer.writerow([
                    vac.semaine,
                    jours_str[vac.jour],
                    1 if vac.period == DemiJournee.apres_midi else 0, # Apres-Midi bool/int check formatters
                    disc.nom_discipline,
                    disc.id_discipline,
                    el.nom, # Nom eleve (Code)
                    el.id_eleve,
                    el.annee.name,
                    el.nom
                ])
                count += 1
    print(f"Export terminé. {count} affectations générées.")
    
else:
    print("Aucune solution trouvée (Infeasible).")
