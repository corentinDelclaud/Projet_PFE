import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Add your planning code here using the OR-Tools CP-SAT solver
# For example, define variables, constraints, and the objective function

from classes.discipline import discipline
num_disciplines = 12

poly : discipline
paro : discipline
como : discipline
pedo : discipline
odf : discipline
occl : discipline
ra : discipline
ste : discipline
pano : discipline
cs_urg : discipline
sp : discipline
urg_op : discipline

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

# spécific modifications for poly
poly.modif_nb_vacations_par_semaine(4)
poly.modif_paire_jours([ (0,1), (2,3), (0,4) ]) # Lundi-Mardi et Mercredi-Jeudi et Lundi-Vendredi
poly.modif_take_jour_pref(True)
print("Discipline reels charges avec succes.")

x = [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]
disciplines = x

# --- DATA MOCKING (Pour tester l'algo sans BDD) ---
from classes.eleve import eleve
from classes.vacation import vacation
from classes.cours import cours
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from classes.enum.demijournee import DemiJournee
from classes.periode import Periode
import random
import csv

list_periodes = [Periode(0, 34, 44), Periode(1, 45, 51), Periode(2, 1, 8), Periode(3, 9, 15), Periode(4, 16, 22), Periode(5, 23, 30)] # Represente les periodes de stage possibles sauf 0 = pas de stage


# --- Chargement des documents depuis streamlit ---
eleves_csv = 'eleves_with_code.csv'
stages_csv = 'mock_stages.csv'
calendrier_DFAS01_csv = 'calendrier_DFASO1.csv'
calendrier_DFAS02_csv = 'calendrier_DFASO2.csv'
calendrier_DFTCC_csv = 'calendrier_DFTCC.csv'

# Chargement des élèves depuis le CSV
eleves: list[eleve] = []
eleves_by_niveau = {
    niveau.DFAS01: [],
    niveau.DFAS02: [],
    niveau.DFTCC: []
}

csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', eleves_csv)
try:
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Conversion des données CSV
            # Note: Assurez-vous que les noms dans le CSV correspondent exactement aux membres de l'Enum
            pref = jour_pref[row["jour_preference"]] 
            niv = niveau[row["annee"]]
            
            new_eleve = eleve(
                id_eleve=int(row["id_eleve"]),
                nom=row["code"],
                id_binome=int(row["id_binome"]),
                jour_preference=pref,
                annee=niv
            )
            # Chargement des périodes de stage
            new_eleve.periode_stage = int(row.get("periode_stage", 0))
            new_eleve.periode_stage_ext = int(row.get("periode_stage_ext", 0))
            
            eleves.append(new_eleve)
            eleves_by_niveau[niv].append(new_eleve)
            
    print(f"Chargement réussi : {len(eleves)} élèves chargés depuis {csv_path}")

    # --- CHARGEMENT DES STAGES ---
    stages_lookup = {} # Key: (niveau_name, periode_id) -> List of stage dicts
    stages_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', stages_csv)
    try:
        with open(stages_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # id_stage,nom_stage,deb_semaine,fin_semaine,pour_niveau,periode
                key = (row["pour_niveau"], int(row["periode"]))
                if key not in stages_lookup:
                    stages_lookup[key] = []
                stages_lookup[key].append({
                     "nom": row["nom_stage"],
                     "debut": int(row["deb_semaine"]),
                     "fin": int(row["fin_semaine"]),
                     "niveau_obj": niveau[row["pour_niveau"]]
                })
        print("Configuration des stages chargée avec succès.")
    except FileNotFoundError:
        print(f"Attention: Fichier stages.csv introuvable ({stages_csv_path}).")

except FileNotFoundError:
    print(f"Erreur : Le fichier {csv_path} est introuvable. Veuillez exécuter generate_students_csv.py d'abord.")
    sys.exit(1)
except KeyError as e:
    print(f"Erreur de format dans le CSV (Enum inconnu) : {e}")
    sys.exit(1)

# --- OPTIMISATION ---
# Création d'un dictionnaire pour un accès O(1) aux élèves par leur ID
eleve_dict = {e.id_eleve: e for e in eleves}

# Récupération des listes pour la gestion des stages (étape 3)
dfas01_list = eleves_by_niveau[niveau.DFAS01]
dftcc_list = eleves_by_niveau[niveau.DFTCC]
dfas02_list = eleves_by_niveau[niveau.DFAS02]

# 3. Gestion des Stages
stages_eleves = {}

# Créer un dictionnaire pour accès O(1) aux périodes
periode_dict = {p.id: p for p in list_periodes}

# Attribution des stages via le fichier de config et l'attribut éleve
for el in eleves:
    p_id = getattr(el, 'periode_stage', 0)
    if p_id > 0:
        # Chercher les stages correspondant au niveau de l'élève et sa période
        key = (el.annee.name, p_id)
        if key in stages_lookup:
            stage_data_list = stages_lookup[key]
            user_stages = []
            for sd in stage_data_list:
                # Création de l'objet stage
                # __init__(self, nom_stage: str, debut_stage: int, fin_stage: int, pour_niveau: niveau, periode: int)
                new_st = stage(sd["nom"], sd["debut"], sd["fin"], sd["niveau_obj"], p_id)
                user_stages.append(new_st)
            
            stages_eleves[el.id_eleve] = user_stages


# Génération des créneaux (Vacations) sur 1 semaine
vacations: list[vacation] = []
for semaine in range(1, 53): # Semaines 1 
    for jour in range(0, 5): # Lundi (0) à Vendredi (4)
        for p in DemiJournee:
            vacations.append(vacation(semaine, jour, p))

# --- CHARGEMENT DES CALENDRIERS (EMPLOIS DU TEMPS) ---
# Format: Semaine (lignes) x Créneaux[1-10] (colonnes)
# Contenu non vide = Indisponible (Cours)
calendar_unavailability = {
    niveau.DFAS01: set(),
    niveau.DFAS02: set(),
    niveau.DFTCC: set()
}

calendar_files = {
    niveau.DFAS01: calendrier_DFAS01_csv,
    niveau.DFAS02: calendrier_DFAS02_csv,
    niveau.DFTCC: calendrier_DFTCC_csv
}

print("Chargement des calendriers...")
for niv, filename in calendar_files.items():
    cal_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', filename)
    try:
        with open(cal_path, mode='r', encoding='utf-8') as f:
            # Le CSV a pour header: Semaine,1,2,3,4,5,6,7,8,9,10
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    s_val = row.get("Semaine")
                    if not s_val:
                        continue
                    # Correction: Le CSV contient "S34", "S35"... il faut retirer le "S"
                    if s_val.upper().startswith("S"):
                        s_val = s_val[1:]
                    semaine = int(s_val)
                    
                    # Parcours des créneaux 1 à 10
                    for i in range(1, 11):
                        col_k = str(i)
                        val = (row.get(col_k) or "").strip()
                        # Si non vide, c'est occupé
                        if val:
                            calendar_unavailability[niv].add((semaine, i - 1))
                except ValueError:
                    continue
        print(f"  - Calendrier {niv.name} chargé ({len(calendar_unavailability[niv])} indisponibilités).")

    except FileNotFoundError:
        print(f"Attention: Calendrier introuvable {cal_path}")

print(f"Planification pour {len(eleves)} élèves, {len(disciplines)} disciplines, sur {len(vacations)} créneaux.")

# --- OR-TOOLS MODEL ---
model = cp_model.CpModel()

# Dictionnaire de variables: assignments[(id_eleve, id_discipline, index_vacation)] -> BoolVar
assignments = {}

# Helper pour avoir un index unique de vacation pour le dict
def get_vac_id(v: vacation):
    return f"{v.semaine}_{v.jour}_{v.period.name}"

print("Construction du modèle en cours...")
start_time = os.times().elapsed

# Variables pour suivre les vacations complètes
vacation_fullness_vars = []

for v_idx, vac in enumerate(vacations):
    if v_idx % 50 == 0:
        print(f"  Traitement créneau {v_idx}/{len(vacations)}...")

    vac_id = get_vac_id(vac)
    
    # Index pour la disponibilité des disciplines (presence[0..9])
    # 0=LunMatin, 1=LunApMidi, 2=MarMatin...
    jour_idx = vac.jour 
    periode_offset = 0 if vac.period == DemiJournee.matin else 1
    slot_index = jour_idx * 2 + periode_offset
    
    # Variables d'affectation pour ce créneau
    vars_in_this_slot = []
    
    for disc in disciplines:
        # Vérifier si la discipline est ouverte sur ce créneau (Base_logique.py: Availability)
        # Note: disc.presence est list[bool]
        is_open = True
        if hasattr(disc, 'presence') and len(disc.presence) > slot_index:
             is_open = disc.presence[slot_index]
        
        if not is_open:
            # Discipline fermée: IMPOSSIBLE d'affecter
            continue
            
        vars_in_discipline_slot = []
        
        for el in eleves:
            # Vérifier si la discipline concerne l'année de l'élève
            if el.annee.value not in disc.annee:
                continue
                
            # Vérifier les indisponibilités élèves (Base_logique.py: Availability)
            
            # 1. Stage verification
            en_stage = False
            if el.id_eleve in stages_eleves:
                for s in stages_eleves[el.id_eleve]:
                    # Si le stage a des dates spécifiques, les utiliser
                    if s.debut_stage is not None and s.fin_stage is not None:
                        if s.debut_stage <= vac.semaine <= s.fin_stage:
                            en_stage = True
                            break
                    # Sinon, utiliser les dates de la période
                    elif s.periode in periode_dict:
                        periode = periode_dict[s.periode]
                        if periode.semaine_debut <= vac.semaine <= periode.semaine_fin:
                            en_stage = True
                            break
            
            # 2. Cours verification (Priorité 2: Calendrier commun)
            # Vérifie si le calendrier du niveau de l'élève marque ce créneau comme occupé
            en_cours = False
            if (vac.semaine, slot_index) in calendar_unavailability.get(el.annee, set()):
                en_cours = True
            
            if en_stage or en_cours:
                continue # Pas de variable créée = pas d'affectation possible

            # Création de la variable de décision
            var_name = f"assign_e{el.id_eleve}_d{disc.id_discipline}_{vac_id}"
            x_var = model.NewBoolVar(var_name)
            assignments[(el.id_eleve, disc.id_discipline, v_idx)] = x_var
            vars_in_this_slot.append(x_var)
            vars_in_discipline_slot.append(x_var)
        
        # CONTRAINTE CAPACITÉ (Base_logique.py: Capacity)
        current_nb_fauteuil = disc.nb_eleve[slot_index] if isinstance(disc.nb_eleve, list) else disc.nb_eleve
        limit = current_nb_fauteuil
        if vars_in_discipline_slot and limit > 0:
            model.Add(sum(vars_in_discipline_slot) <= limit)
            
            # Variable booléenne: vacation complète si on atteint la capacité max
            is_full_var = model.NewBoolVar(f"full_d{disc.id_discipline}_{vac_id}")
            model.Add(sum(vars_in_discipline_slot) == limit).OnlyEnforceIf(is_full_var)
            model.Add(sum(vars_in_discipline_slot) < limit).OnlyEnforceIf(is_full_var.Not())
            vacation_fullness_vars.append(is_full_var)

    # CONTRAINTE UNICITÉ (Un élève ne peut être qu'à un seul endroit par créneau)
    for el in eleves:
        vars_for_student_in_slot = []
        for disc in disciplines:
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_in_slot.append(assignments[key])
        
        if vars_for_student_in_slot:
            model.Add(sum(vars_for_student_in_slot) <= 1)

# CONTRAINTE QUOTAS (Base_logique.py: Quotas) - SOFT VERSION
# Le nombre total de vacations effectuées par un élève dans une discipline ne doit pas dépasser le quota de cette discipline
quota_fulfillment_vars = []
for el in eleves:
    for disc in disciplines:
        # Vérifier si la discipline concerne l'année de l'élève
        if el.annee.value not in disc.annee:
            continue
            
        # Rassembler toutes les variables d'affectation pour ce couple (élève, discipline) sur l'ensemble des vacations
        vars_for_student_discipline = []
        for v_idx in range(len(vacations)):
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_discipline.append(assignments[key])
        
        # Si des variables existent, on applique la contrainte (avec variable d'ecart)
        if vars_for_student_discipline:
            # Récupération du quota cible
            if isinstance(disc.quota, list):
                if 4 <= el.annee.value <= 6:
                    target_quota = disc.quota[el.annee.value - 4]
                else:
                    target_quota = 0
            else:
                target_quota = disc.quota
                
            if target_quota > 0:
                # Variable binaire: quota atteint si sum >= target
                quota_met_var = model.NewBoolVar(f"quota_met_e{el.id_eleve}_d{disc.id_discipline}")
                model.Add(sum(vars_for_student_discipline) >= target_quota).OnlyEnforceIf(quota_met_var)
                model.Add(sum(vars_for_student_discipline) < target_quota).OnlyEnforceIf(quota_met_var.Not())
                quota_fulfillment_vars.append(quota_met_var)

# CONTRAINTE NB_VACATIONS_PAR_SEMAINE
# Limiter le nombre de vacations par semaine pour chaque discipline qui a cette contrainte
print("Ajout des contraintes nb_vacations_par_semaine...")
for disc in disciplines:
    if disc.nb_vacations_par_semaine > 0:
        # Pour chaque élève et chaque semaine, limiter le nombre de vacations
        for el in eleves:
            if el.annee.value not in disc.annee:
                continue
                
            for semaine in range(1, 53):
                # Collecter toutes les variables pour cette semaine/élève/discipline
                vars_week = []
                for v_idx, vac in enumerate(vacations):
                    if vac.semaine == semaine:
                        key = (el.id_eleve, disc.id_discipline, v_idx)
                        if key in assignments:
                            vars_week.append(assignments[key])
                
                if vars_week:
                    model.Add(sum(vars_week) <= disc.nb_vacations_par_semaine)

# CONTRAINTE PAIRE_JOURS
# Si un élève est affecté un jour d'une paire, il doit l'être aussi l'autre jour
print("Ajout des contraintes paire_jours...")
for disc in disciplines:
    if disc.paire_jours is not None and len(disc.paire_jours) > 0:
        for el in eleves:
            if el.annee.value not in disc.annee:
                continue
                
            # Pour chaque semaine
            for semaine in range(1, 53):
                # Pour chaque paire de jours
                for (jour1, jour2) in disc.paire_jours:
                    # Collecter les variables pour jour1 et jour2 dans cette semaine
                    vars_jour1 = []
                    vars_jour2 = []
                    
                    for v_idx, vac in enumerate(vacations):
                        if vac.semaine == semaine:
                            key = (el.id_eleve, disc.id_discipline, v_idx)
                            if key in assignments:
                                if vac.jour == jour1:
                                    vars_jour1.append(assignments[key])
                                elif vac.jour == jour2:
                                    vars_jour2.append(assignments[key])
                    
                    # Si affecté au moins une fois sur jour1, doit l'être au moins une fois sur jour2
                    if vars_jour1 and vars_jour2:
                        # Créer variables indicatrices
                        has_jour1 = model.NewBoolVar(f"has_j{jour1}_e{el.id_eleve}_d{disc.id_discipline}_s{semaine}")
                        has_jour2 = model.NewBoolVar(f"has_j{jour2}_e{el.id_eleve}_d{disc.id_discipline}_s{semaine}")
                        
                        # has_jour1 = 1 si au moins une vacation sur jour1
                        model.Add(sum(vars_jour1) >= 1).OnlyEnforceIf(has_jour1)
                        model.Add(sum(vars_jour1) == 0).OnlyEnforceIf(has_jour1.Not())
                        
                        # has_jour2 = 1 si au moins une vacation sur jour2
                        model.Add(sum(vars_jour2) >= 1).OnlyEnforceIf(has_jour2)
                        model.Add(sum(vars_jour2) == 0).OnlyEnforceIf(has_jour2.Not())
                        
                        # Si has_jour1, alors has_jour2 (et vice-versa)
                        model.Add(has_jour1 == has_jour2)

# OBJECTIF: Maximiser quotas remplis + vacations complètes + préférences de jours
# Poids pour équilibrer les objectifs
QUOTA_WEIGHT = 1000      # Priorité forte sur les quotas
VACATION_WEIGHT = 1      # Bonus pour remplir les vacations
PREFERENCE_WEIGHT = 10   # Bonus pour respecter les préférences de jours

# Calculer les bonus de préférence pour les disciplines qui le demandent
preference_bonus = []
for (e_id, d_id, v_idx), x_var in assignments.items():
    disc = next((d for d in disciplines if d.id_discipline == d_id), None)
    if disc and disc.take_jour_pref:
        eleve_obj = eleve_dict[e_id]
        vac_obj = vacations[v_idx]
        
        # vac_obj.jour: 0=Lundi, 1=Mardi, 2=Mercredi, 3=Jeudi, 4=Vendredi
        # eleve_obj.jour_preference.value: 1=lundi, 2=mardi, 3=mercredi, 4=jeudi, 5=vendredi
        if (vac_obj.jour + 1) == eleve_obj.jour_preference.value:
            preference_bonus.append(x_var)

model.Maximize(
    QUOTA_WEIGHT * sum(quota_fulfillment_vars) +
    VACATION_WEIGHT * sum(vacation_fullness_vars) +
    PREFERENCE_WEIGHT * sum(preference_bonus)
)

print(f"Modèle construit en {os.times().elapsed - start_time:.2f}s. Lancement du solveur...")

# --- SOLVING ---
solver = cp_model.CpSolver()
# Enable logging
solver.parameters.log_search_progress = True
# Set a time limit of 10 minutes (600 seconds)
solver.parameters.max_time_in_seconds = 300
# Limit workers to prevent OOM
solver.parameters.num_search_workers = 4

status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"Solution trouvée! Valeur objectif: {solver.ObjectiveValue()}")
    print("--- PLANNING ---")

    # --- CSV EXPORT ---
    import csv
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
            p_str = "Matin" if vac.period == DemiJournee.matin else "Apres-Midi"
            
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
                    
    print(f"\nPlanning exporté dans : {csv_file_path}")
    print(f"Solution trouvée! Valeur objectif: {solver.ObjectiveValue()}")

else:
    print("Aucune solution trouvée.")
    

