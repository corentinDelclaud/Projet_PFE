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

# Chargement des élèves depuis le CSV
eleves: list[eleve] = []
eleves_by_niveau = {
    niveau.DFAS01: [],
    niveau.DFAS02: [],
    niveau.DFTCC: []
}

csv_path = os.path.join(os.path.dirname(__file__), '..', 'resultat', 'eleves.csv')
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
                nom=row["nom"],
                id_binome=int(row["id_binome"]),
                jour_preference=pref,
                annee=niv
            )
            eleves.append(new_eleve)
            eleves_by_niveau[niv].append(new_eleve)
            
    print(f"Chargement réussi : {len(eleves)} élèves chargés depuis {csv_path}")

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

# Configuration des stages (Groupe -> {Niveau -> (Debut, Fin)})
STAGE_CONFIG = {
    1: {niveau.DFTCC: (45, 51), niveau.DFAS01: (45, 51)},
    2: {niveau.DFTCC: (2, 8),   niveau.DFAS01: (2, 8)},
    3: {niveau.DFTCC: (9, 15),  niveau.DFAS01: (9, 15)},
    4: {niveau.DFTCC: (16, 22), niveau.DFAS01: (38, 44)}
}

# Attribution des groupes de stage
# Pour garantir que les binômes ont le même groupe, on attribue par paire.
for i in range(len(dfas01_list)):
    grp = (i % 4) + 1 
    
    # Eleve DFAS01
    e_dfas01 = dfas01_list[i]
    if niveau.DFAS01 in STAGE_CONFIG[grp]:
        debut, fin = STAGE_CONFIG[grp][niveau.DFAS01]
        stages_eleves[e_dfas01.id_eleve] = [stage(debut_stage=debut, fin_stage=fin)]
        
    # Eleve DFTCC (Son binôme)
    if i < len(dftcc_list):
        e_dftcc = dftcc_list[i]
        if niveau.DFTCC in STAGE_CONFIG[grp]:
            debut, fin = STAGE_CONFIG[grp][niveau.DFTCC]
            stages_eleves[e_dftcc.id_eleve] = [stage(debut_stage=debut, fin_stage=fin)]

# Génération des créneaux (Vacations) sur 1 semaine
vacations: list[vacation] = []
for semaine in range(1, 53): # Semaines 1 
    for jour in range(0, 5): # Lundi (0) à Vendredi (4)
        for p in Periode:
            vacations.append(vacation(semaine, jour, p))

# Mock des indisponibilités (Cours / Stages)
# Ex: Pierre (3) a cours le Mercredi matin (Semaine 1 et 2)
cours_eleves = {
    3: [cours(1, 2), cours(2, 2)] # Mercredi = jour 2
}

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
            # Vérifier les indisponibilités élèves (Base_logique.py: Availability)
            
            # 1. Stage verification
            en_stage = False
            if el.id_eleve in stages_eleves:
                for s in stages_eleves[el.id_eleve]:
                    if s.debut_stage <= vac.semaine <= s.fin_stage:
                        en_stage = True
                        break
            
            # 2. Cours verification
            en_cours = False
            if el.id_eleve in cours_eleves:
                for c in cours_eleves[el.id_eleve]:
                    if c.semaine == vac.semaine and c.jour == vac.jour:
                        # Si cours toute la journée ou spécifié (ici on simplifie: cours = jour complet ou check période?)
                        # La classe cours n'a pas de période, on suppose qu'un cours bloque la journée (ou à affiner)
                        en_cours = True
                        break
            
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
        limit = disc.nb_fauteuil * 2 if disc.en_binome else disc.nb_fauteuil
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
# Si une discipline est 'en_binome', et qu'un élève a un binome, ils doivent être ensemble.
# A <-> B équivaut à A == B
for v_idx, vac in enumerate(vacations):
    for disc in disciplines:
        if disc.en_binome:
            for el in eleves:
                if el.id_binome != 0:
                    # Trouver l'objet binome (Optimisation O(1))
                    binome_obj = eleve_dict.get(el.id_binome)
                    if binome_obj:
                        # On ne traite la contrainte qu'une fois pour la paire (id < id_binome)
                        if el.id_eleve < binome_obj.id_eleve:
                            key1 = (el.id_eleve, disc.id_discipline, v_idx)
                            key2 = (binome_obj.id_eleve, disc.id_discipline, v_idx)
                            
                            # Si les deux peuvent être affectés (variables existent)
                            if key1 in assignments and key2 in assignments:
                                model.Add(assignments[key1] == assignments[key2])
                            # Si l'un ne peut pas être là (stage/cours), l'autre ne peut pas être là non plus
                            # (Car discipline en binôme obligatoire)
                            elif key1 in assignments and key2 not in assignments:
                                model.Add(assignments[key1] == 0)
                            elif key1 not in assignments and key2 in assignments:
                                model.Add(assignments[key2] == 0)

# CONTRAINTE QUOTAS (Base_logique.py: Quotas)
# Le nombre total de vacations effectuées par un élève dans une discipline ne doit pas dépasser le quota de cette discipline
for el in eleves:
    for disc in disciplines:
        # Rassembler toutes les variables d'affectation pour ce couple (élève, discipline) sur l'ensemble des vacations
        vars_for_student_discipline = []
        for v_idx in range(len(vacations)):
            key = (el.id_eleve, disc.id_discipline, v_idx)
            if key in assignments:
                vars_for_student_discipline.append(assignments[key])
        
        # Si des variables existent, on applique la contrainte
        if vars_for_student_discipline:
            # On suppose que disc.quota est le plafond (ex: 2 pour Soins Prothétiques)
            model.Add(sum(vars_for_student_discipline) <= disc.quota)

# OBJECTIF (Base_logique.py: Preference)
# Maximiser les affectations sur les jours de préférence
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

# Maximiser la somme pondérée
model.Maximize(sum(objective_terms))

print(f"Modèle construit en {os.times().elapsed - start_time:.2f}s. Lancement du solveur...")

# --- SOLVING ---
solver = cp_model.CpSolver()
# Enable logging
solver.parameters.log_search_progress = True
# Set a time limit of 5 minutes (300 seconds)
solver.parameters.max_time_in_seconds = 300.0
# Limit workers to prevent OOM
solver.parameters.num_search_workers = 4

status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"Solution trouvée! Valeur objectif: {solver.ObjectiveValue()}")
    print("--- PLANNING ---")
    
    # Organisation de l'affichage par Semaine / Jour
    current_semaine = -1
    current_jour = -1
    
    #for v_idx, vac in enumerate(vacations):
        # Header Semaine
     #   if vac.semaine != current_semaine:
      #      print(f"\nSemaine {vac.semaine}")
       #     current_semaine = vac.semaine
            
        # Header Jour simpliste
        #day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        #jour_str = day_names[vac.jour]
        #p_str = "Matin" if vac.period == Periode.matin else "Apres-Midi"
        
        #assigned_in_slot = []
        #for (e_id, d_id, idx), val in assignments.items():
         #   if idx == v_idx and solver.Value(val) == 1:
          #      e_name = next(e.nom for e in eleves if e.id_eleve == e_id)
          #      d_name = next(d.nom_discipline for d in disciplines if d.id_discipline == d_id)
          #      assigned_in_slot.append(f"{e_name} -> {d_name}")
        
        #if assigned_in_slot:
        #    print(f"  {jour_str} {p_str}: {', '.join(assigned_in_slot)}")

    # --- CSV EXPORT ---
    import csv
    # Création du dossier resultat s'il n'existe pas
    result_dir = os.path.join(os.path.dirname(__file__), '..', 'resultat')
    os.makedirs(result_dir, exist_ok=True)
    
    csv_file_path = os.path.join(result_dir, 'planning_solution.csv')
    
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(["Semaine", "Jour", "Periode", "Eleve", "Discipline"])
        
        day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        
        for v_idx, vac in enumerate(vacations):
            jour_str = day_names[vac.jour]
            p_str = "Matin" if vac.period == Periode.matin else "Apres-Midi"
            
            for (e_id, d_id, idx), val in assignments.items():
                if idx == v_idx and solver.Value(val) == 1:
                    e_name = next(e.nom for e in eleves if e.id_eleve == e_id)
                    d_name = next(d.nom_discipline for d in disciplines if d.id_discipline == d_id)
                    writer.writerow([vac.semaine, jour_str, p_str, e_name, d_name])
                    
    print(f"\nPlanning exporté dans : {csv_file_path}")
    print(f"Solution trouvée! Valeur objectif: {solver.ObjectiveValue()}")

else:
    print("Aucune solution trouvée.")
    

