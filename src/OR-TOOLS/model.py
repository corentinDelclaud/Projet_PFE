"""
model.py - Création du modèle OR-Tools avec les contraintes et les objectifs
"""
import os
from ortools.sat.python import cp_model
from classes.enum.niveaux import niveau
from Projet_PFE.src.classes.enum.demijournee import Periode


# Paramètres de contraintes
QUOTA_TOLERANCE = 1
LISSAGE_THRESHOLD = 25


def get_vac_id(vac):
    """Helper pour avoir un index unique de vacation"""
    return f"{vac.semaine}_{vac.jour}_{vac.period.name}"


def create_model(disciplines, eleves, vacations, stages_eleves, calendar_unavailability, eleves_by_niveau):
    """
    Crée et configure le modèle OR-Tools avec toutes les contraintes
    
    Args:
        disciplines: Liste des disciplines
        eleves: Liste des élèves
        vacations: Liste des créneaux horaires
        stages_eleves: Dict mapping id_eleve -> liste de stages
        calendar_unavailability: Dict mapping niveau -> set de (semaine, slot_index)
        eleves_by_niveau: Dict mapping niveau -> liste d'élèves
        
    Returns:
        tuple: (model, assignments, forced_to_zero) où model est le CpModel, 
               assignments le dict des variables et forced_to_zero les variables forcées à 0
    """
    
    print(f"Planification pour {len(eleves)} élèves, {len(disciplines)} disciplines, sur {len(vacations)} créneaux.")
    
    # Création du dictionnaire des élèves pour un accès O(1)
    eleve_dict = {e.id_eleve: e for e in eleves}
    
    # --- CRÉATION DU MODÈLE OR-TOOLS ---
    model = cp_model.CpModel()

    # Dictionnaire de variables: assignments[(id_eleve, id_discipline, index_vacation)] -> BoolVar
    assignments = {}

    print("Construction du modèle en cours...")
    start_time = os.times().elapsed

    # === CRÉATION DES VARIABLES ET CONTRAINTES DE BASE ===
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
            # Limite le nombre d'élèves par discipline et par créneau
            current_nb_eleve = disc.nb_eleve[slot_index] if isinstance(disc.nb_eleve, list) else disc.nb_eleve
            limit = current_nb_eleve
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

    # === CONTRAINTE BINOME ===
    # DÉSACTIVÉE TEMPORAIREMENT
    forced_to_zero = set() # Set vide - pas de contrainte de binôme pour le moment
    
    # === CONTRAINTE QUOTAS AVEC VARIABLES DE SLACK ===
    print("Ajout des contraintes de quotas avec pénalités...")
    
    # Dictionnaire pour stocker les variables de slack (écart au quota)
    slack_vars = {}  # (id_eleve, id_discipline) -> IntVar représentant l'écart au quota
    
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
            
            # Récupération du quota cible
            if isinstance(disc.quota, list):
                if 4 <= el.annee.value <= 6:
                    target_quota = disc.quota[el.annee.value - 4]
                else:
                    target_quota = 0
            else:
                target_quota = disc.quota
            
            if target_quota > 0 and vars_for_student_discipline:
                # Création de la variable de slack s_{e,d}
                # Elle représente le manque par rapport au quota cible
                max_possible_slack = target_quota  # Maximum = quota entièrement manqué
                slack_var = model.NewIntVar(0, max_possible_slack, f"slack_e{el.id_eleve}_d{disc.id_discipline}")
                slack_vars[(el.id_eleve, disc.id_discipline)] = slack_var
                
                # Contrainte : target_quota - somme(affectations) = slack
                # Donc : somme(affectations) + slack = target_quota
                total_assignments = sum(vars_for_student_discipline)
                model.Add(total_assignments + slack_var == target_quota)
                
                # DIAGNOSTIC
                if len(effective_vars) < target_quota:
                    print(f"AVERTISSEMENT: L'élève {el.nom} (ID {el.id_eleve}) manque de créneaux pour {disc.nom_discipline}.")
                    print(f"  - Quota requis : {target_quota}")
                    print(f"  - Créneaux disponibles : {len(effective_vars)}")
                    print(f"  -> Variable de slack créée pour pénaliser le manque dans l'objectif.")

    # === CONTRAINTE LISSAGE ===
    print("Ajout des contraintes de lissage...")

    # Pré-calcul des sommes de vacations par élève et par discipline
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
            current_quota = 0
            if isinstance(disc.quota, list):
                if 4 <= niv.value <= 6:
                    current_quota = disc.quota[niv.value - 4]
            else:
                current_quota = disc.quota
                
            if current_quota >= LISSAGE_THRESHOLD:
                delta_max = 8
            else:
                delta_max = 4
                
            # Récupération des totaux pour ce niveau/discipline
            counts = []
            for el in students_in_level:
                counts.append(student_vars_by_disc[(el.id_eleve, disc.id_discipline)])
                
            # Application de la contrainte: max(counts) - min(counts) <= delta_max
            if counts:
                # Création bornes min/max locales ce groupe
                max_possible = len(vacations)
                min_assign = model.NewIntVar(0, max_possible, f"min_assign_{niv.name}_{disc.nom_discipline}")
                max_assign = model.NewIntVar(0, max_possible, f"max_assign_{niv.name}_{disc.nom_discipline}")
                
                for c in counts:
                    model.Add(c >= min_assign)
                    model.Add(c <= max_assign)
                
                model.Add(max_assign - min_assign <= delta_max)

    # === OBJECTIF ===
    print("Ajout de la fonction objectif...")
    
    # Paramètres de poids
    PENALTY_QUOTA = 1000  # Pénalité forte pour chaque unité de quota manquant
    REWARD_PREFERRED_DAY = 10  # Bonus pour affectation sur jour préféré
    REWARD_STANDARD = 1  # Poids de base pour toute affectation
    
    objective_terms = []
    
    # Partie 1 : Récompenses pour les affectations (préférences de jour)
    for (e_id, d_id, v_idx), x_var in assignments.items():
        eleve_obj = eleve_dict[e_id]
        vac_obj = vacations[v_idx]
        
        # Jour preference check
        # vac_obj.jour: 0=Lundi, 1=Mardi...
        # jour_pref: lundi=1, mardi=2...
        # Donc mapping: vac_obj.jour + 1 == eleve_obj.jour_preference.value
        if (vac_obj.jour + 1) == eleve_obj.jour_preference.value:
            weight = REWARD_PREFERRED_DAY  # Bonus pour préférence
        else:
            weight = REWARD_STANDARD  # Poids de base
            
        objective_terms.append(weight * x_var)
    
    # Partie 2 : Pénalités pour le non-respect des quotas
    for (e_id, d_id), slack_var in slack_vars.items():
        # Soustraire PENALTY_QUOTA * slack pour pénaliser les quotas manquants
        objective_terms.append(-PENALTY_QUOTA * slack_var)
    
    # Maximiser : Récompenses - Pénalités
    # Z = Σ(w_{e,v} * x_{e,d,v}) - P * Σ(s_{e,d})
    model.Maximize(sum(objective_terms))
    
    print(f"  - Poids jour préféré : {REWARD_PREFERRED_DAY}")
    print(f"  - Poids standard : {REWARD_STANDARD}")
    print(f"  - Pénalité quota manquant : {PENALTY_QUOTA}")
    print(f"  - Variables de slack (quotas) : {len(slack_vars)}")

    print(f"Modèle construit en {os.times().elapsed - start_time:.2f}s.")
    
    return model, assignments, forced_to_zero
