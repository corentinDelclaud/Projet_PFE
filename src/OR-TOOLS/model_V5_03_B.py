# =============================================================================
# MODÈLE V5_03_B - ASSOUPLISSEMENT DES CONTRAINTES
# =============================================================================
# Ce modèle assouplit certaines contraintes dures pour permettre au solveur
# de trouver des solutions de meilleure qualité:
# - fill_requirement: Transformée en contrainte souple avec forte pénalité
# - mixite_groupes: Assouplie pour permettre plus de flexibilité
# - Grand slam bonus: Réduit pour encourager des solutions partielles
# =============================================================================

import sys
import os
import csv
import json
import collections
import argparse

# Parse arguments for batch execution
parser = argparse.ArgumentParser(description="Run optimization model.")
parser.add_argument("--time_limit", type=int, default=600, help="Max time in seconds for the solver.")
parser.add_argument("--output", type=str, default=None, help="Path to the output CSV file.")
args, unknown = parser.parse_known_args()

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
poly = discipline(1, "Polyclinique", [20,20,20,20,20,20,20,20,20,20], True, [50,50,50], [True]*10,[4,5,6])
paro = discipline(2, "Parodontologie", [0,4,4,4,4,4,4,4,4,4], False, [6,6,6], [False, True, True, True, True, True, True, True, True, True],[4,5,6])
como = discipline(3, "Comodulation", [3,3,3,3,3,3,0,0,3,3], False, [6,6,6] , [True, True, True, True, True, True, False, False, True, True],[4,5,6])
pedo_soins = discipline(4, "Pédodontie Soins", [10,0,0,0,20,20,20,0,20,0], True, [12,12,12], [True]*10,[4,5,6])
odf = discipline(5, "Orthodontie", [3] * 10, False, [4,4,4], [True]*10,[5])
occl = discipline(6, "Occlusodontie", [4,0,4,0,0,0,4,0,4,0], False, [3,0,0], [True, False, True, False, False, False, True, False, True, False],[4])
ra = discipline(7, "Radiologie", [4] * 10, False, [9,8,0], [True]*10,[4,5])
ste = discipline(8, "Stérilisation", [1] * 10, False, [3,2,0], [True]*10,[4,5,6])
pano = discipline(9, "Panoramique", [0,1,0,1,1,1,0,1,0,1,0,1] * 10, False, [0,3,3], [True]*10,[5,6])
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
poly.modif_nb_vacations_par_semaine(2)
poly.modif_paire_jours([ (0,1), (2,3), (0,4) ]) # Paires requises
poly.modif_take_jour_pref(True)

bloc.modif_fill_requirement(True)

occl.modif_repetition_continuite(1, 12)  # Pas 2 fois de suite

sp.modif_fill_requirement(True)

ste.modif_fill_requirement(True)

ra.modif_priorite_niveau([4,5,6])

odf.modif_repartition_semestrielle([2,2])  # 4 total, 2 in each semester

pedo_soins.modif_frequence_vacations(2)  # Une semaine sur deux
pedo_soins.modif_priorite_niveau([5,6,4])  # 1st prio 5A, 2nd prio 6A, 3rd prio 4A
pedo_soins.modif_meme_jour(True)

paro.modif_mixite_groupes(2) # au moins 2 niveaux différents par vacation

como.modif_mixite_groupes(3) # un élève de chaque niveau

pano.modif_priorite_niveau([6,5])

urg.modif_remplacement_niveau([(5,6,7),(5,4,5)])  # Remplacement 5A par 6A (7 élèves), 5A par 4A (5 élèves)

pedo_urg.modif_priorite_niveau([6,5])

disciplines = [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]

# Chargement Élèves
eleves: list[eleve] = []
eleves_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'eleves_with_code.csv')
with open(eleves_csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            # Convertir jour_similaire (0-9) en jour (1-5) : 0,1→1(lundi), 2,3→2(mardi), etc.
            jour_similaire_val = int(row.get("jour_similaire", 0))
            meme_jour_converted = (jour_similaire_val // 2) + 1  # Conversion en jour 1-5
            
            new_eleve = eleve(
                id_eleve=int(row["id_eleve"]),
                id_binome=int(row["id_binome"]),
                jour_preference=jour_pref[row["jour_preference"]],
                annee=niveau[row["annee"]],
                meme_jour=meme_jour_converted  # Stocker le jour similaire converti
            )
            new_eleve.periode_stage = int(row.get("periode_stage", 0))
            eleves.append(new_eleve)
        except KeyError: continue
eleve_dict = {e.id_eleve: e for e in eleves}
print(f"  {len(eleves)} élèves chargés.")

# Chargement Stages
list_periodes = [Periode(0, 34, 44), Periode(1, 45, 51), Periode(2, 1, 8), Periode(3, 9, 15), Periode(4, 16, 22), Periode(5, 23, 30)]
stages_lookup = collections.defaultdict(list)
stages_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'stages.csv') # Using copy as per working context
if os.path.exists(stages_csv_path):
    with open(stages_csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows with empty week values
            if not row.get("deb_semaine") or not row.get("fin_semaine"):
                continue
            try:
                stages_lookup[(row["pour_niveau"], int(row["periode"]))].append({
                    "nom": row["nom_stage"], 
                    "debut": int(float(row["deb_semaine"])), 
                    "fin": int(float(row["fin_semaine"])), 
                    "niveau_obj": niveau[row["pour_niveau"]]
                })
            except (ValueError, KeyError):
                continue

stages_eleves = {}
for el in eleves:
    if el.periode_stage > 0:
        key = (el.annee.name, el.periode_stage)
        if key in stages_lookup:
            stages_eleves[el.id_eleve] = [stage(d["nom"], d["debut"], d["fin"], d["niveau_obj"], el.periode_stage) for d in stages_lookup[key]]

# Chargement Calendriers (Indisponibilités Cours)
calendar_unavailability = collections.defaultdict(set)
cal_files = {niveau.DFAS01: 'calendrier_DFAS01.csv', niveau.DFAS02: 'calendrier_DFASS02.csv', niveau.DFTCC: 'calendrier_DFTCC.csv'}
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
vars_by_disc_vac_niveau = collections.defaultdict(list) # (disc_id, vac_idx, annee) -> [var]

for (e_id, d_id, v_idx), var in assignments.items():
    vars_by_student_vac[(e_id, v_idx)].append(var)
    vars_by_disc_vac[(d_id, v_idx)].append(var)
    
    el_annee = eleve_dict[e_id].annee
    vars_by_disc_vac_niveau[(d_id, v_idx, el_annee)].append(var)
    
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

max_theoretical_score = 0  # Track maximum possible score for normalization


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
        # Calculate theoretical max for pair bonus
        pair_count = 0
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            pair_count += 1
        
        # Maximum theoretical: all eligible students get pairs in all weeks
        # But we only count actual pair bonus additions (see below in loop)
        # Best case: each student-week-pair combination = 50 points
        max_theoretical_score += pair_count * 52 * len(disc.paire_jours) * 50
        
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

# FILL REQUIREMENT (Soft - Vacation Capacity Fullness) - MODÈLE B: ASSOUPLI
print("Ajout contrainte: Remplissage Obligatoire (Soft avec pénalité)...")
for disc in disciplines:
    if disc.be_filled:
        for v_idx, vac in enumerate(vacations):
            # Index du créneau dans la semaine (0-9)
            slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
            
            # Vérifier si la discipline est ouverte sur ce créneau (déjà filtré à la création variables)
            # Récupérer toutes les variables d'affectation pour cette discipline sur ce créneau
            vars_in_disc_slot = vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
            
            if vars_in_disc_slot:
                # Capacité théorique du créneau
                cap = disc.nb_eleve[slot_idx] if slot_idx < len(disc.nb_eleve) else 0
                
                # MODÈLE B: Au lieu d'une contrainte dure (==), on utilise une incitation forte
                target = min(cap, len(vars_in_disc_slot))
                if target > 0:
                    # Créer une variable d'écart pour mesurer le sous-remplissage
                    shortfall = model.NewIntVar(0, target, f"fill_shortfall_d{disc.id_discipline}_v{v_idx}")
                    model.Add(shortfall == target - sum(vars_in_disc_slot))
                    # Pénalité forte pour chaque place non remplie
                    obj_terms.append(shortfall)
                    weights.append(-5000)  # Forte pénalité pour dissuader mais pas bloquer

# BINOME (Hard) sinon avec un autre élève qui n'a pas non plus son binome
print("Ajout contrainte: Binômes...")
for disc in disciplines:
    if disc.en_binome:
        for s in range(1, 53):
            for (e1_id, e2_id) in [(e.id_eleve, e.id_binome) for e in eleves if e.id_binome > 0]:
                vars_e1 = vars_by_student_disc_semaine.get((e1_id, disc.id_discipline, s), [])
                vars_e2 = vars_by_student_disc_semaine.get((e2_id, disc.id_discipline, s), [])
                
                if not vars_e1 or not vars_e2:
                    continue
                
                for j in range(5):
                    for p in DemiJournee:
                        v_idxs_e1 = [v[0] for v in vars_e1 if vacations[v[0]].jour == j and vacations[v[0]].period == p]
                        v_idxs_e2 = [v[0] for v in vars_e2 if vacations[v[0]].jour == j and vacations[v[0]].period == p]
                        
                        if v_idxs_e1 and v_idxs_e2:
                            var_e1 = assignments.get((e1_id, disc.id_discipline, v_idxs_e1[0]))
                            var_e2 = assignments.get((e2_id, disc.id_discipline, v_idxs_e2[0]))
                            if var_e1 is not None and var_e2 is not None:
                                model.Add(var_e1 == var_e2)
                                
#fréquence_vacations : Toutes les X semaines : number input (1, 2, 3...) 1 = chaque semaine 2 = une semaine sur deux 3 = chaque semaine sur trois
print("Ajout contrainte: Fréquence des Vacations...")
for disc in disciplines:
    if disc.frequence_vacations > 1:
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            for start_week in range(1, disc.frequence_vacations + 1):
                weeks_group = list(range(start_week, 53, disc.frequence_vacations))
                for i in range(0, len(weeks_group), disc.frequence_vacations):
                    group_weeks = weeks_group[i:i + disc.frequence_vacations]
                    vars_in_group = []
                    for s in group_weeks:
                        vars_entries = vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                        vars_in_group.extend([v[1] for v in vars_entries])
                    if vars_in_group:
                        model.Add(sum(vars_in_group) <= 1)
                        
#Répartition semestrielle du total des quotas [semestre1, semestre2] semestre1 + semestre2 = total des quotas
print("Ajout contrainte: Répartition Semestrielle...")
for disc in disciplines:
    if disc.repartition_semestrielle:
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            
            # Récupération du quota pour l'année de l'élève
            try:
                adx = disc.annee.index(el.annee.value)
                quota = disc.quota[adx]
            except ValueError:
                quota = 0
            
            if quota > 0:
                sem1_target = disc.repartition_semestrielle[0]
                sem2_target = disc.repartition_semestrielle[1]
                
                vars_sem1 = []
                vars_sem2 = []
                
                for s in range(1, 53):
                    vars_entries = vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                    if vars_entries:
                        if s <= 26:
                            vars_sem1.extend([v[1] for v in vars_entries])
                        else:
                            vars_sem2.extend([v[1] for v in vars_entries])
                
                if vars_sem1:
                    model.Add(sum(vars_sem1) <= sem1_target)
                if vars_sem2:
                    model.Add(sum(vars_sem2) <= sem2_target)
# =============================================================================
#Mixité des groupes : Composition des groupes Mixité des niveaux - MODÈLE B: ASSOUPLI
print("Ajout contrainte: Mixité des Groupes (Assouplies)...")
for disc in disciplines:
    if disc.mixite_groupes > 0:
        for v_idx, vac in enumerate(vacations):
            if not vars_by_disc_vac.get((disc.id_discipline, v_idx)):
                continue

            if disc.mixite_groupes == 1:
                # MODÈLE B: Assoupli - Au moins 1 élève de chaque niveau si possible (Soft)
                for niv in niveau:
                    vars_niv = vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                    if vars_niv:
                        has_niv = model.NewBoolVar(f"has_{niv.name}_d{disc.id_discipline}_v{v_idx}")
                        model.Add(sum(vars_niv) >= 1).OnlyEnforceIf(has_niv)
                        model.Add(sum(vars_niv) == 0).OnlyEnforceIf(has_niv.Not())
                        # Bonus pour avoir ce niveau
                        obj_terms.append(has_niv)
                        weights.append(500)
            
            elif disc.mixite_groupes == 2:
                # MODÈLE B: Assoupli - Bonus pour avoir 2+ niveaux, pas d'obligation stricte
                niv_bools = []
                for niv in niveau:
                    vars_niv = vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                    if vars_niv:
                        b_niv = model.NewBoolVar(f"pres_{niv.name}_d{disc.id_discipline}_v{v_idx}")
                        model.Add(sum(vars_niv) >= 1).OnlyEnforceIf(b_niv)
                        model.Add(sum(vars_niv) == 0).OnlyEnforceIf(b_niv.Not())
                        niv_bools.append(b_niv)
                
                if niv_bools:
                    # Bonus pour avoir au moins 2 niveaux différents
                    has_diversity = model.NewBoolVar(f"diverse_d{disc.id_discipline}_v{v_idx}")
                    model.Add(sum(niv_bools) >= 2).OnlyEnforceIf(has_diversity)
                    model.Add(sum(niv_bools) < 2).OnlyEnforceIf(has_diversity.Not())
                    obj_terms.append(has_diversity)
                    weights.append(1000)  # Bonus significatif pour encourager la mixité

            elif disc.mixite_groupes == 3:
                # Tous du même niveau - Gardé en contrainte dure car simple
                niv_bools = []
                for niv in niveau:
                    vars_niv = vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                    if vars_niv:
                        b_niv = model.NewBoolVar(f"pres_{niv.name}_d{disc.id_discipline}_v{v_idx}")
                        model.Add(sum(vars_niv) >= 1).OnlyEnforceIf(b_niv)
                        model.Add(sum(vars_niv) == 0).OnlyEnforceIf(b_niv.Not())
                        niv_bools.append(b_niv)
                
                if niv_bools:
                    model.Add(sum(niv_bools) <= 1)

#Répartition continuité : Pas plus de X vacations trop proche c'est à dire ne pas avoir plus de X vacations de la même discipline à moins 3 mois d'écart (12 semaines) d'intervalles distance (ici on choisit cela car il n'y a que occlusiodontie qui a cette contrainte cependant on le fait de manière générique)
print("Ajout contrainte: Répartition de la Continuité...")
for disc in disciplines:
    if isinstance(disc.repetition_continuite, int):
        continue
    limit = disc.repetition_continuite[0]
    distance = disc.repetition_continuite[1]
    if limit > 0 and distance > 0:
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            for start_week in range(1, distance + 1):
                weeks_group = list(range(start_week, 53, distance))
                
                vars_in_group = []
                for s in weeks_group:
                    vars_entries = vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                    vars_in_group.extend([v[1] for v in vars_entries])
                
                if vars_in_group:
                    model.Add(sum(vars_in_group) <= limit)

#Remplacement de niveau : Permettre à un niveau spécifique de remplacer un autre niveau (exemple 5A par 6A)
# Si le niveau X est absent (aucune variable d'affectation disponible), le niveau Y doit remplir P% de la capacité
print("Ajout contrainte: Remplacement de Niveau (% Capacity)...")
for disc in disciplines:
    if disc.remplacement_niveau:
        for (niv_from_val, niv_to_val, percentage) in disc.remplacement_niveau:
            try:
                # Ensure we have the enum objects for key lookup
                niv_from = niveau(niv_from_val)
                niv_to = niveau(niv_to_val)
            except ValueError:
                continue

            for v_idx, vac in enumerate(vacations):
                slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
                
                # Check if From Level is present (has created variables)
                vars_from = vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv_from), [])
                
                if not vars_from:
                    # Level is absent, enforce replacement
                    vars_to = vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv_to), [])
                    capacity = disc.nb_eleve[slot_idx]
                    
                    if capacity > 0 and vars_to:
                         min_required = int(capacity * percentage / 100)
                         # Safe ceiling/floor logic? "Au moins Y%" implies floor or ceil?
                         # Usually 50% of 10 is 5. 50% of 1 is 0.5 -> 0 or 1?
                         # "Au moins" usually implies ceiling if strict, but int() floors.
                         # Let's use standard integer arithmetic (floor).
                         if min_required > 0:
                             model.Add(sum(vars_to) >= min_required)

# Même Jour : (Soft Constraint)
# Les vacations doivent être planifiées le plus possible le même jour similaire de l'élève (ou jour adjacent)
print("Ajout contrainte: Même Jour (Élève)...")
for disc in disciplines:
    if disc.meme_jour:  # Si la discipline active cette contrainte
        # Calculate theoretical max ONCE for this discipline
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            if el.meme_jour == 0: continue  # Pas de jour similaire défini
            
            # Calculer le score théorique maximum pour cet élève
            try:
                adx = disc.annee.index(el.annee.value)
                quota_disc = disc.quota[adx]
                # Best case: all assignments on target day
                max_theoretical_score += quota_disc * 20  # 20 points per assignment on target day
            except (ValueError, IndexError):
                pass
        
        for el in eleves:
            if el.annee.value not in disc.annee: continue
            if el.meme_jour == 0: continue  # Pas de jour similaire défini
            
            target_day_idx = el.meme_jour - 1  # 1=Lundi(0), 2=Mardi(1), etc.
            
            # Pour chaque vacation de cette discipline
            for v_idx, vac in enumerate(vacations):
                # Vérifier si cette vacation existe pour cet élève
                var_key = (el.id_eleve, disc.id_discipline, v_idx)
                if var_key not in assignments:
                    continue
                
                var = assignments[var_key]
                d = vac.jour
                w = 0
                
                if d == target_day_idx:
                    w = 20  # Forte préférence pour le jour similaire
                elif abs(d - target_day_idx) == 1:
                    w = 10  # Préférence pour jour adjacent
                
                if w > 0:
                    obj_terms.append(var)
                    weights.append(w)

# =============================================================================

# 4. OBJECTIFS D'OPTIMISATION
# OBJECTIF PRINCIPAL: Remplissage et Quotas
print("Configuration Objectifs...")

# Préparation des variables par (Eleve, Discipline) pour les objectifs
vars_by_student_disc_all = collections.defaultdict(list)
for (e_id, d_id, _), var in assignments.items():
    vars_by_student_disc_all[(e_id, d_id)].append(var)

# A. Maximiser le nombre d'affectations jusqu'au Quota
# (Les affectations au-delà du quota ne rapportent pas de points)

for disc in disciplines:
    # List to track individual success for this discipline for the "All Quota" bonus
    discipline_success_vars = []
    
    for el in eleves:
        if el.annee.value not in disc.annee: continue
        
        vars_list = vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
        if not vars_list: continue

        # Récupération du quota pour l'année de l'élève
        try:
            adx = disc.annee.index(el.annee.value)
            quota = disc.quota[adx]
        except ValueError:
            quota = 0
        
        if quota > 0:
            # OPTIMISATION: Fusion des logiques Bonus/Malus pour réduire le nombre de variables
            # Maximiser (Points) revient au même qu'éviter (Malus).
            # On garde uniquement les variables "positives" mais avec des poids cumulés.

            # Configuration des poids (Priorisation Polyclinique)
            w_fill = 150
            w_excess = -200
            w_success = 7000
            
            # Augmentation significative pour Polyclinique (Id=1) pour garantir l'atteinte des quotas
            if disc.nom_discipline == "Polyclinique":
                w_fill = 600      # Incitation forte au remplissage
                w_excess = -800   # Malus adapté pour éviter le dépassement malgré le fort w_fill
                w_success = 30000 # Priorité critique pour atteindre le quota global

            # Calculate theoretical max (perfect scenario: quota met, no excess)
            max_theoretical_score += quota * w_fill + w_success

            # 1. INCITATION AU REMPLISSAGE (Jusqu'au Quota)
            sat_var = model.NewIntVar(0, quota, f"sat_e{el.id_eleve}_d{disc.id_discipline}")
            model.Add(sat_var <= sum(vars_list))
            obj_terms.append(sat_var)
            weights.append(w_fill) 

            # 2. MALUS DE DÉPASSEMENT (Pour laisser la place aux autres)
            # Une assignation au-delà du quota n'apporte rien via sat_var (borné),
            # mais nous ajoutons ici un coût explicite pour "refroidir" le solveur.
            excess_var = model.NewIntVar(0, 500, f"excess_e{el.id_eleve}_d{disc.id_discipline}")
            # excess >= sum - quota
            # <=> excess + quota >= sum
            model.Add(excess_var + quota >= sum(vars_list))
            
            obj_terms.append(excess_var)
            weights.append(w_excess) # Malus doit être > w_fill pour dissuader le dépassement
            
            # 3. BONUS TERMINAISON (Gros Bonus si Quota Atteint)
            is_success = model.NewBoolVar(f"success_e{el.id_eleve}_d{disc.id_discipline}")
            model.Add(sum(vars_list) >= quota).OnlyEnforceIf(is_success)
            
            # Important: lier la variable dans les deux sens pour le bonus global
            # Si le quota n'est pas atteint, is_success DOIT être faux (pour ne pas valider le bonus global à tort)
            # Cependant, maximiser la somme pondérée poussera naturellement is_success à 1 si possible, 
            # et le bonus global require qu'ils soient TOUS à 1. 
            # Donc si un seul ne peut pas être à 1, le global est perdu.
            # On ajoute quand même la contrainte inverse pour la propreté.
            model.Add(sum(vars_list) < quota).OnlyEnforceIf(is_success.Not())
            
            discipline_success_vars.append(is_success)

            obj_terms.append(is_success)
            weights.append(w_success)

    # 4. BONUS GLOBAL DISPLINE (SUPER BONUS)
    # Si TOUS les élèves concernés ont atteint leur quota pour cette discipline
    if discipline_success_vars:
        all_success_var = model.NewBoolVar(f"all_success_d{disc.id_discipline}")
        
        # La variable est vraie SI ET SEULEMENT SI le minimum des succès individuels est 1 (donc tous à 1)
        model.AddMinEquality(all_success_var, discipline_success_vars)
        
        # MODÈLE B: Réduire le grand slam bonus pour favoriser des solutions partielles
        w_grand_slam = 200000 # 200K points (au lieu de 1M)
        if disc.nom_discipline == "Polyclinique":
             w_grand_slam = 500000 # 500K points for Poly (au lieu de 5M)

        max_theoretical_score += w_grand_slam

        obj_terms.append(all_success_var)
        weights.append(w_grand_slam)

# B. Respect des Préférences (Jour Préféré)
if poly.take_jour_pref: # Seulement pour Poly ou configurable globalement
    # Count theoretical max for preference bonus
    for el in eleves:
        if el.annee.value not in poly.annee: continue
        try:
            adx = poly.annee.index(el.annee.value)
            quota_poly = poly.quota[adx]
            # In best case, all poly assignments are on preferred day
            max_theoretical_score += quota_poly * 100
        except (ValueError, IndexError):
            pass
    
    for k, var in assignments.items():
        if k[1] == poly.id_discipline: # Si c'est poly
            el = eleve_dict[k[0]]
            v_idx = k[2]
            vac = vacations[v_idx]
            # vac.jour 0..4, pref 1..5
            if (vac.jour + 1) == el.jour_preference.value:
                obj_terms.append(var)
                weights.append(100) # Bonus significatif

# C. Priorité de Niveau (Bonus par niveau prioritaire)
print("Configuration Priorité Niveau...")
for disc in disciplines:
    if disc.priorite_niveau:
        # disc.priorite_niveau = [year_prio_1, year_prio_2, year_prio_3] ex: [5, 4, 6]
        # On donne un bonus dégressif aux affectations selon la priorité pour qu'ils soient servis en premier
        prio_map = {}
        # On vérifie la taille pour éviter les IndexErrors si la liste est incomplète
        if len(disc.priorite_niveau) > 0: prio_map[disc.priorite_niveau[0]] = 50  # Prio 1
        if len(disc.priorite_niveau) > 1: prio_map[disc.priorite_niveau[1]] = 20  # Prio 2
        if len(disc.priorite_niveau) > 2: prio_map[disc.priorite_niveau[2]] = 5   # Prio 3
        
        # Calculate theoretical max for priority bonus (all priority levels get their quotas with their weights)
        for prio_year, weight in prio_map.items():
            if prio_year in disc.annee:
                try:
                    adx = disc.annee.index(prio_year)
                    quota_prio = disc.quota[adx]
                    # Count students in this priority year
                    nb_students_prio = len([e for e in eleves if e.annee.value == prio_year])
                    max_theoretical_score += nb_students_prio * quota_prio * weight
                except (ValueError, IndexError):
                    pass
        
        # Il est plus efficace d'itérer sur les variables pré-triées par discipline si possible, 
        # C'est ce que nous faisons ici grâce au dictionnaire vars_by_student_disc_all
        for el in eleves:
            if el.annee.value in prio_map:
                vars_student = vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                w = prio_map[el.annee.value]
                for var in vars_student:
                    obj_terms.append(var)
                    weights.append(w)

model.Maximize(sum(t * w for t, w in zip(obj_terms, weights)))

# =============================================================================
# 4. RESOLUTION ET EXPORT
# =============================================================================
print("Lancement du solveur...")

solver = cp_model.CpSolver()
# Use arguments if provided, else default
solver.parameters.max_time_in_seconds = args.time_limit if args.time_limit else 3600
solver.parameters.log_search_progress = True
solver.parameters.num_workers = 8 # Réduit à 8 pour ménager le CPU et éviter les freezes

# Préparation chemin de sortie
if args.output:
    output_csv = args.output
    # Ensure dir exists
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir): 
        os.makedirs(output_dir)
else:
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resultat')
    if not os.path.exists(output_dir): 
        os.makedirs(output_dir)
    output_csv = os.path.join(output_dir, 'planning_solution.csv')

# Résolution directe
status = cp_model.UNKNOWN
try:
    status = solver.Solve(model)
except KeyboardInterrupt:
    print("\nInterruption utilisateur (Ctrl+C).")
    status = cp_model.FEASIBLE if solver.ObjectiveValue() > 0 else cp_model.UNKNOWN # Tentative de récupération

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    raw_score = solver.ObjectiveValue()
    
    # Normalize score to 0-100 scale
    normalized_score = 0.0
    if max_theoretical_score > 0:
        normalized_score = (raw_score / max_theoretical_score) * 100
        # Cap at 100 (in case bonus weights push it over)
        normalized_score = min(100.0, max(0.0, normalized_score))
    
    print("Terminé.")
    print(f"Score brut : {raw_score:,.0f}")
    print(f"Score maximum théorique : {max_theoretical_score:,.0f}")
    print(f"Score normalisé : {normalized_score:.2f}/100")
    print(f"Ecriture des résultats dans {output_csv}...")
    
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ["Semaine", "Jour", "Apres-Midi", "Discipline", "Id_Discipline", "Id_Eleve", "Id_Binome", "Annee"]
            writer.writerow(headers)
            
            rows_buffer = []
            for (e_id, d_id, v_idx), var in assignments.items():
                if solver.Value(var) == 1:
                    vac = vacations[v_idx]
                    el = eleve_dict[e_id]
                    disc = next(d for d in disciplines if d.id_discipline == d_id)
                    
                    jours_str = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
                    
                    rows_buffer.append([
                        vac.semaine,
                        jours_str[vac.jour],
                        1 if vac.period == DemiJournee.apres_midi else 0,
                        disc.nom_discipline,
                        disc.id_discipline,
                        el.id_eleve,
                        el.id_binome,
                        el.annee.name
                    ])
            writer.writerows(rows_buffer)
        print("Données sauvegardées.")
        
        # Save optimization scores to JSON file
        scores_file = os.path.join(output_dir, 'optimization_scores.json')
        try:
            with open(scores_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "raw_score": raw_score,
                    "max_theoretical_score": max_theoretical_score,
                    "normalized_score": normalized_score,
                    "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
                }, f, indent=2)
            print(f"Scores sauvegardés dans {scores_file}")
        except Exception as e:
            print(f"Erreur lors de l'écriture des scores : {e}")
            
    except Exception as e:
        print(f"Erreur lors de l'écriture du fichier : {e}")

else:
    print("Aucune solution trouvée ou arrêt avant première solution.")
