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

poly = discipline(1, "Polyclinique", ["A101"] * 10, [20] * 10, True, 20, [True]*10,[4,5,6])
paro = discipline(2, "Parodontologie", ["A102"] * 10, [15] * 10, True, 15, [True]*10,[4,5,6])
como = discipline(3, "Comodulation", ["A103"] * 10, [10] * 10, True, 10, [True]*10,[4,5,6])
pedo = discipline(4, "Pédodontie", ["A104"] * 10, [5] * 10, True, 5, [True]*10,[4,5,6])
odf = discipline(5, "Orthodontie", ["A105"] * 10, [8] * 10, True, 5, [True]*10,[4,5,6])
occl = discipline(6, "Occlusodontie", ["A106"] * 10, [12] * 10, True, 10, [True]*10,[4,5,6])
ra = discipline(7, "Radiologie", ["A107"] * 10, [0] * 10, False, 0, [True]*10,[4,5,6])
ste = discipline(8, "Stomatologie", ["A108"] * 10, [18] * 10, True, 15, [True]*10,[5])
pano = discipline(9, "Panoramique", ["A109"] * 10, [0] * 10, False, 0, [True]*10,[4,5,6])
cs_urg = discipline(10, "Consultation d'urgence", ["A110"] * 10, [0] * 10, False, 0, [True]*10,[4,5,6])
sp = discipline(11, "Soins Prothétiques", ["A111"] * 10, [14] * 10, True, 15, [True]*10,[4,5,6])
urg_op = discipline(12, "Urgences Opératoires", ["A112"] * 10, [2] * 10, False, 0, [True]*10,[4,5,6])  

poly.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
paro.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, True, True, True, True, True, True, True, True])
como.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pedo.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, False, False, False, True, True, True, False, True, False])
odf.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, True, True, False, True, False, True])
occl.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, True, False, False, False, True, False, True, False])
ra.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
ste.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
pano.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, False, True, False, True, False, True])
cs_urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
sp.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
urg_op.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, False, False, False, False, False, True, False, True])

print("Discipline reels charges avec succes.")

x = [poly, paro, como, pedo, odf, occl, ra, ste, pano, cs_urg, sp, urg_op]
disciplines = x

# --- DATA MOCKING (Pour tester l'algo sans BDD) ---
from classes.eleve import eleve
from classes.vacation import vacation
from classes.cours import cours
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from classes.enum.periode import Periode
import random
import csv


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





# Génération des créneaux (Vacations)
vacations: list[vacation] = []
# L'année universitaire commence semaine 34 et finit semaine 33 l'année suivante
weeks_range = list(range(34, 53)) + list(range(1, 34))

for semaine in weeks_range: 
    for jour in range(0, 5): # Lundi (0) à Vendredi (4)
        for p in Periode:
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
            # Le CSV a pour header: Semaine,1,2,3,4,5,6,7,8,9,10,période
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    s_val = row.get("Semaine")
                    if not s_val:
                        continue                    # Correction: Le CSV contient "S34", "S35"... il faut retirer le "S"
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

for v_idx, vac in enumerate(vacations):
    if v_idx % 50 == 0:
        print(f"  Traitement créneau {v_idx}/{len(vacations)}...")

    vac_id = get_vac_id(vac)
    
    # Index pour la disponibilité des disciplines (presence[0..9])
    # 0=LunMatin, 1=LunApMidi, 2=MarMatin...
    jour_idx = vac.jour 
    periode_offset = 0 if vac.period == Periode.matin else 1
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
            # el.annee est une Enum (niveau), .value donne l'entier (4, 5, 6)
            if el.annee.value not in disc.annee:
                continue

            # Vérifier les indisponibilités élèves (Base_logique.py: Availability)
            
            # 1. Stage verification
            en_stage = False
            if el.id_eleve in stages_eleves:
                for s in stages_eleves[el.id_eleve]:
                    if s.debut_stage <= vac.semaine <= s.fin_stage:
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
        # Si matière en binôme : 1 fauteuil accueille 2 élèves (le binôme).
        # Sinon : 1 fauteuil accueille 1 élève.
        current_nb_fauteuil = disc.nb_fauteuil[slot_index] if isinstance(disc.nb_fauteuil, list) else disc.nb_fauteuil
        limit = current_nb_fauteuil * 2 if disc.en_binome else current_nb_fauteuil
        if vars_in_discipline_slot:
            model.Add(sum(vars_in_discipline_slot) <= limit)

    # CONTRAINTE UNICITÉ (Un élève ne peut être qu'à un seul endroit par créneau)
    for el in eleves:
        vars_for_student_in_slot = []
        for disc in disciplines:
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_in_slot.append(assignments[key])
        
        if vars_for_student_in_slot:
            model.Add(sum(vars_for_student_in_slot) <= 1)

# CONTRAINTE BINOME (Base_logique.py: Binome)
forced_to_zero = set() # Set of (id_eleve, id_discipline, v_idx) forced to 0

for v_idx, vac in enumerate(vacations):
    for disc in disciplines:
        if disc.en_binome:
            for el in eleves:
                if el.id_binome != 0:
                    binome_obj = eleve_dict.get(el.id_binome)
                    if binome_obj:
                        if el.id_eleve < binome_obj.id_eleve:
                            key1 = (el.id_eleve, disc.id_discipline, v_idx)
                            key2 = (binome_obj.id_eleve, disc.id_discipline, v_idx)
                            
                            if key1 in assignments and key2 in assignments:
                                model.Add(assignments[key1] == assignments[key2])
                            elif key1 in assignments and key2 not in assignments:
                                # Le binôme (key2/binome_obj) est indisponible.
                                # Vérifions si c'est à cause d'un stage.
                                binome_en_stage = False
                                if binome_obj.id_eleve in stages_eleves:
                                    for s in stages_eleves[binome_obj.id_eleve]:
                                        if s.debut_stage <= vac.semaine <= s.fin_stage:
                                            binome_en_stage = True
                                            break
                                
                                if binome_en_stage:
                                    # EXCEPTION "Binôme Exceptionnel":
                                    # Si le binôme est en stage, l'élève présent (A) N'EST PAS BLOQUÉ.
                                    # Il pourra travailler seul ou avec un autre orphelin (C).
                                    pass
                                else:
                                    # Sinon (ex: cours), on maintient la contrainte stricte
                                    model.Add(assignments[key1] == 0)
                                    forced_to_zero.add(key1)

                            elif key1 not in assignments and key2 in assignments:
                                # Même logique symétrique pour key2 (si A est absent)
                                eleve_en_stage = False
                                if el.id_eleve in stages_eleves:
                                    for s in stages_eleves[el.id_eleve]:
                                        if s.debut_stage <= vac.semaine <= s.fin_stage:
                                            eleve_en_stage = True
                                            break
                                
                                if eleve_en_stage:
                                    pass
                                else:
                                    model.Add(assignments[key2] == 0)
                                    forced_to_zero.add(key2)

# CONTRAINTE QUOTAS (HARD MINIMUM VERSION)
for el in eleves:
    for disc in disciplines:
        if el.annee.value not in disc.annee:
            continue
            
        vars_for_student_discipline = []
        effective_vars = [] # Variables not forced to zero
        
        for v_idx in range(len(vacations)):
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_discipline.append(assignments[key])
                if key not in forced_to_zero:
                    effective_vars.append(assignments[key])
        
        target_quota = disc.quota
        if target_quota > 0:
            # DIAGNOSTIC AMELIORE
            # On vérifie sur les "effective_vars" (celles qui ne sont pas tuées par le binôme)
            if len(effective_vars) < target_quota:
                 print(f"ERREUR FATALE: L'élève {el.nom} (ID {el.id_eleve}) manque de créneaux pour {disc.nom_discipline}.")
                 print(f"  - Quota requis : {target_quota}")
                 print(f"  - Créneaux théoriques : {len(vars_for_student_discipline)}")
                 print(f"  - Créneaux effectifs (hors blocage binôme) : {len(effective_vars)}")
                 print(f"  -> L'élève (ou son binôme) a trop d'indisponibilités (Stages/Cours).")
            
            if vars_for_student_discipline:
                 model.Add(sum(vars_for_student_discipline) >= target_quota)
            else:
                 # Si l'élève doit faire un quota mais n'a aucune disponibilité/créneau possible -> Infeasible
                 # On force le modèle à échouer pour signaler le problème de données
                 print(f"Warning: Impossible d'atteindre le quota {target_quota} pour {el.nom} en {disc.nom_discipline} (indisponibilités totales)")
                 # model.Add(0 >= target_quota) # Uncomment to force failure

# CONTRAINTE LISSAGE (Lissage par niveau des vacations entre élèves par discipline)
# Les élèves d'un même niveau ne doivent pas avoir un nombre de vacations trop différent.
# Si Quota > LISSAGE_THRESHOLD -> écart max [-5; 5]
# Sinon -> écart max [-2; 2]
LISSAGE_THRESHOLD = 25
print("Ajout des contraintes de lissage...")

# Pré-calcul des sommes de vacations par élève et par discipline pour éviter de refaire les boucles
# (id_eleve, id_discipline) -> sum(vars)
student_vars_by_disc = {} 

for el in eleves:
    for disc in disciplines:
        vars_for_student_discipline = []
        for v_idx in range(len(vacations)):
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_discipline.append(assignments[key])
        
        # On stocke la somme (expression lineaire) ou 0 si vide
        if vars_for_student_discipline:
            student_vars_by_disc[(el.id_eleve, disc.id_discipline)] = sum(vars_for_student_discipline)
        else:
            student_vars_by_disc[(el.id_eleve, disc.id_discipline)] = 0

for niv, students_in_level in eleves_by_niveau.items():
    if not students_in_level:
        continue
    
    for disc in disciplines:
        # Détermination de l'écart autorisé (delta)
        if disc.quota >= LISSAGE_THRESHOLD:
            delta_max = 5
        else:
            delta_max = 2
            
        # Récupération des totaux pour ce niveau/discipline
        counts = []
        for el in students_in_level:
            counts.append(student_vars_by_disc[(el.id_eleve, disc.id_discipline)])
            
        # Application de la contrainte: max(counts) - min(counts) <= delta_max
        if counts:
            # Création bornes min/max locales ce groupe
            # Borne sup théorique = nombre total de créneaux
            max_possible = len(vacations)
            min_assign = model.NewIntVar(0, max_possible, f"min_assign_{niv.name}_{disc.nom_discipline}")
            max_assign = model.NewIntVar(0, max_possible, f"max_assign_{niv.name}_{disc.nom_discipline}")
            
            for c in counts:
                model.Add(c >= min_assign)
                model.Add(c <= max_assign)
            
            model.Add(max_assign - min_assign <= delta_max)

# OBJECTIF (Base_logique.py: Preference)
# Maximiser les affectations sur les jours de préférence tout en minimisant les pénalités de quota
objective_terms = []
for (e_id, d_id, v_idx), x_var in assignments.items():
    # Optimisation O(1)
    eleve_obj = eleve_dict[e_id]
    vac_obj = vacations[v_idx]
    
    # Jour preference check
    # vac_obj.jour: 0=Lundi, 1=Mardi...
    # jour_pref: lundi=1, mardi=2...
    # Donc mapping: vac_obj.jour + 1 == eleve_obj.jour_preference.value
    weight = 1 # Poids de base pour toute affectation
    if (vac_obj.jour + 1) == eleve_obj.jour_preference.value:
        weight = 10 # Bonus pour préférence
        
    objective_terms.append(weight * x_var)

# Maximiser la somme pondérée (Préférences uniquement)
model.Maximize(sum(objective_terms))

print(f"Modèle construit en {os.times().elapsed - start_time:.2f}s. Lancement du solveur...")

# --- SOLVING ---
solver = cp_model.CpSolver()
# Enable logging
solver.parameters.log_search_progress = True
# Set a time limit of 10 minutes (600 seconds)
solver.parameters.max_time_in_seconds = 600
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
                    
    print(f"\nPlanning exporté dans : {csv_file_path}")
    print(f"Solution trouvée! Valeur objectif: {solver.ObjectiveValue()}")

else:
    print("Aucune solution trouvée.")
    

