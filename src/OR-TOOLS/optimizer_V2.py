""" 
OPTIMIZER V2 - Adapté pour Model V5_03_C
Optimization service with progress tracking
"""
import sys
import os
import logging
import collections
import time
import csv
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ortools.sat.python import cp_model
from classes.vacation import vacation
from classes.stage import stage
from classes.enum.demijournee import DemiJournee
from classes.enum.niveaux import niveau

logger = logging.getLogger(__name__)


# result & callback classes


@dataclass
class OptimizationResult:
    """Résultat d'optimisation avec métadonnées"""
    status: str  # 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'ERROR', 'TIMEOUT'
    objective_value: Optional[float] = None
    normalized_score: Optional[float] = None  # Score normalisé /100
    max_theoretical_score: Optional[float] = None  # Score max théorique
    solve_time: float = 0.0
    assignments: Optional[Dict] = None
    statistics: Optional[Dict] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.assignments is None:
            self.assignments = {}
        if self.statistics is None:
            self.statistics = {}
    
    def is_success(self) -> bool:
        """Vérifie si l'optimisation a réussi"""
        return self.status in ['OPTIMAL', 'FEASIBLE']

class SolutionCallback(cp_model.CpSolverSolutionCallback):
    """Callback pour suivre la progression de la résolution"""
    
    def __init__(self, max_time_seconds):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.max_time = max_time_seconds
        self.start_time = time.time()
        self._solution_count = 0
        self._last_log_time = 0
    
    def on_solution_callback(self):
        """Appelé à chaque nouvelle solution trouvée"""
        self._solution_count += 1
        current_time = time.time()
        elapsed = int(current_time - self.start_time)
        remaining = max(0, int(self.max_time - elapsed))
        
        # Log toutes les 2 secondes pour éviter le spam
        if current_time - self._last_log_time >= 2:
            # Format exact pour le parsing Streamlit
            print(f"PROGRESS|Solution #{self._solution_count}|Elapsed: {elapsed}s|Remaining: {remaining}s|Objective: {self.ObjectiveValue()}")
            sys.stdout.flush()  # Force l'affichage immédiat
            self._last_log_time = current_time


# main optimizer class


class ScheduleOptimizerV2:
    """
    Optimizer adapté au model V5_03_C avec scoring réaliste.
    
    Architecture:
    - prepare_data(): Charge données (élèves, stages, calendriers, vacations)
    - build_model(): Construit le modèle CP-SAT complet
    - solve(): Lance la résolution avec tracking progression
    - export_solution(): Exporte la solution en CSV
    """
    
    def __init__(self, config):
        """
        Initialize optimizer avec configuration
        
        Args:
            config: ModelConfig instance contenant:
                - disciplines: Liste des disciplines
                - eleves: Liste des élèves
                - calendriers: Dict des indisponibilités
                - solver_params: Paramètres du solver
        """
        self.config = config
        self.model = None
        self.solver = None
        self.assignments = {}  # (eleve_id, disc_id, vac_idx) -> BoolVar
        self.vacations = []
        self.eleve_dict = {}
        self.stages_eleves = {}
        self.calendar_unavailability = {}
        self.progress_callback = None
        
        # Structures d'indexation pour accélération
        self.vars_by_student_vac = collections.defaultdict(list)
        self.vars_by_disc_vac = collections.defaultdict(list)
        self.vars_by_student_disc_semaine = collections.defaultdict(list)
        self.vars_by_disc_vac_niveau = collections.defaultdict(list)
        self.vars_by_student_disc_all = collections.defaultdict(list)
        
        # Variables pour l'objectif (V5_03_C logic)
        self.obj_terms = []
        self.weights = []
        self.max_theoretical_score = 0  # Score max théorique réaliste
        
        # Variables de quota (sat_var, excess_var, is_success, all_success_var)
        self.sat_vars = {}  # (eleve_id, disc_id) -> IntVar (affectations dans quota)
        self.excess_vars = {}  # (eleve_id, disc_id) -> IntVar (affectations au-delà quota)
        self.success_vars = {}  # (eleve_id, disc_id) -> BoolVar (quota atteint?)
        self.all_success_vars = {}  # disc_id -> BoolVar (tous élèves quota atteint?)
    
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """
        Configure callback pour les mises à jour de progression
        
        Args:
            callback: Function(message: str, progress_percent: int)
        """
        self.progress_callback = callback
    
    # data preparation
    
    def prepare_data(self):
        """Prépare les structures de données pour l'optimisation"""
        self._notify_progress("Préparation des données", 5)
        
        # Create eleve dict
        self.eleve_dict = {e.id_eleve: e for e in self.config.eleves}
        logger.info(f"  {len(self.config.eleves)} élèves chargés.")
        
        # Prepare stages
        for el in self.config.eleves:
            if el.periode_stage > 0:
                key = (el.annee.name, el.periode_stage)
                if key in self.config.stages_lookup:
                    # Créer objets stage à partir des dicts dans stages_lookup
                    self.stages_eleves[el.id_eleve] = [
                        stage(
                            d["nom"],
                            d["debut"],
                            d["fin"],
                            d["niveau_obj"],
                            el.periode_stage
                        )
                        for d in self.config.stages_lookup[key]
                    ]
        
        # Calendar unavailability
        self.calendar_unavailability = self.config.calendar_unavailability
        
        # Générer vacations (semaines 1-52)
        self.vacations = []
        for s in range(1, 53):
            for j in range(5):  # Lundi à Vendredi
                for p in DemiJournee:
                    self.vacations.append(vacation(s, j, p))
        
        logger.info(f"✓ Données préparées: {len(self.vacations)} créneaux")
    
    
    # model construction
    
    
    def build_model(self) -> None:
        """Construit le modèle CP-SAT complet"""
        logger.info("=" * 80)
        logger.info("CONSTRUCTION DU MODÈLE V5_03_C")
        logger.info("=" * 80)
        
        self.model = cp_model.CpModel()
        
        # Créer variables
        self._create_variables()
        self._notify_progress("Variables créées", 20)
        
        # Construire index
        self._build_indexes()
        self._notify_progress("Index construits", 25)
        
        # Ajouter contraintes
        self._add_capacity_constraints()
        self._notify_progress("Contraintes de capacité", 30)
        
        self._add_uniqueness_constraints()
        self._notify_progress("Contraintes d'unicité", 35)
        
        self._add_max_vacations_per_week()
        self._notify_progress("Contraintes hebdomadaires", 40)
        
        self._add_pair_days_constraints()
        self._notify_progress("Contraintes paires de jours", 42)
        
        self._add_fill_requirements()
        self._notify_progress("Contraintes de remplissage", 45)
        
        self._add_binome_constraints()
        self._notify_progress("Contraintes de binômes", 48)
        
        self._add_frequency_constraints()
        self._notify_progress("Contraintes de fréquence", 50)
        
        self._add_semester_distribution()
        self._notify_progress("Répartition semestrielle", 52)
        
        self._add_group_diversity()
        self._notify_progress("Mixité des groupes", 55)
        
        self._add_continuity_constraints()
        self._notify_progress("Contraintes de continuité", 58)
        
        self._add_level_replacement()
        self._notify_progress("Remplacement de niveau", 60)
        
        self._add_same_day_constraints()
        self._notify_progress("Contraintes même jour", 62)
        
        # Configurer objectif
        self._set_objective()
        self._notify_progress("Objectif configuré", 70)
        
        logger.info("✓ Modèle construit avec succès")
        logger.info(f"  Variables: {len(self.assignments)}")
        logger.info(f"  Score max théorique: {self.max_theoretical_score:,.0f}")
    
    
    # variable creation
    
    
    def _create_variables(self):
        """Crée les variables de décision x_{e,d,v}"""
        logger.info("Création des variables de décision...")
        
        count_vars = 0
        for v_idx, vac in enumerate(self.vacations):
            slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
            
            for disc in self.config.disciplines:
                # Contrainte 3 (Fermeture Discipline): O_{d,v} = 0
                if not (len(disc.presence) > slot_idx and disc.presence[slot_idx]):
                    continue
                
                for el in self.config.eleves:
                    # Contrainte 2 (Éligibilité Niveau): E_{e,d} = 0
                    if el.annee.value not in disc.annee:
                        continue
                    
                    # Contrainte 4 (Indisponibilité Élève - Stage): I_{e,v} = 1
                    is_in_stage = False
                    if el.id_eleve in self.stages_eleves:
                        for st in self.stages_eleves[el.id_eleve]:
                            if st.debut_stage <= vac.semaine <= st.fin_stage:
                                is_in_stage = True
                                break
                    if is_in_stage:
                        continue
                    
                    # Contrainte 5 (Indisponibilité Cours - Calendrier): C_{a,v} = 1
                    if el.annee in self.calendar_unavailability:
                        if vac in self.calendar_unavailability[el.annee]:
                            continue
                    
                    # Créer variable
                    var_name = f"x_e{el.id_eleve}_d{disc.id_discipline}_v{v_idx}"
                    var = self.model.NewBoolVar(var_name)
                    self.assignments[(el.id_eleve, disc.id_discipline, v_idx)] = var
                    count_vars += 1
        
        logger.info(f"✓ {count_vars} variables créées")
    
    def _build_indexes(self):
        """Construit les structures d'indexation pour accélération"""
        logger.info("Construction des index...")
        
        for (e_id, d_id, v_idx), var in self.assignments.items():
            # Index par (élève, vacation)
            self.vars_by_student_vac[(e_id, v_idx)].append(var)
            
            # Index par (discipline, vacation)
            self.vars_by_disc_vac[(d_id, v_idx)].append(var)
            
            # Index par (élève, discipline) - toutes vacations
            self.vars_by_student_disc_all[(e_id, d_id)].append(var)
            
            # Index par (élève, discipline, semaine)
            semaine = self.vacations[v_idx].semaine
            self.vars_by_student_disc_semaine[(e_id, d_id, semaine)].append((v_idx, var))
            
            # Index par (discipline, vacation, niveau)
            el_annee = self.eleve_dict[e_id].annee
            self.vars_by_disc_vac_niveau[(d_id, v_idx, el_annee)].append(var)
        
        logger.info("✓ Index construits")
    # CONSTRAINTS
    def _add_capacity_constraints(self):
        """Contrainte 1: Capacité des disciplines par créneau"""
        logger.info("Ajout contraintes: Capacité...")
        
        count = 0
        for v_idx, vac in enumerate(self.vacations):
            slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
            
            for disc in self.config.disciplines:
                vars_in_disc_slot = self.vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
                if vars_in_disc_slot:
                    cap = disc.capacite[slot_idx] if len(disc.capacite) > slot_idx else 0
                    if cap > 0:
                        self.model.Add(sum(vars_in_disc_slot) <= cap)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de capacité ajoutées")
    
    def _add_uniqueness_constraints(self):
        """Contrainte 2: Un élève sur au plus une vacation par créneau"""
        logger.info("Ajout contraintes: Unicité...")
        
        count = 0
        for v_idx in range(len(self.vacations)):
            for el in self.config.eleves:
                vars_for_student = self.vars_by_student_vac.get((el.id_eleve, v_idx), [])
                if vars_for_student:
                    self.model.Add(sum(vars_for_student) <= 1)
                    count += 1
        
        logger.info(f"✓ {count} contraintes d'unicité ajoutées")
    
    def _add_max_vacations_per_week(self):
        """Contrainte: Maximum de vacations par semaine par discipline"""
        logger.info("Ajout contraintes: Max vacations/semaine...")
        
        count = 0
        for disc in self.config.disciplines:
            if disc.nb_vacations_par_semaine <= 0:
                continue
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                for s in range(1, 53):
                    vars_semaine = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                    if vars_semaine:
                        vars_only = [v for (_, v) in vars_semaine]
                        self.model.Add(sum(vars_only) <= disc.nb_vacations_par_semaine)
                        count += 1
        
        logger.info(f"✓ {count} contraintes max vacations/semaine ajoutées")
    
    def _add_pair_days_constraints(self):
        """Contrainte soft: Paires de jours (bonus dans objectif)"""
        logger.info("Ajout contraintes: Paires de jours (soft)...")
        
        # Cette contrainte est gérée dans l'objectif (bonus)
        # Calcul du score max théorique pour les paires
        for disc in self.config.disciplines:
            if disc.paire_jours:
                pair_count = 0
                for el in self.config.eleves:
                    if el.annee.value in disc.annee:
                        pair_count += 1
                
                # Maximum: chaque élève obtient toutes les paires dans toutes les semaines
                self.max_theoretical_score += pair_count * 52 * len(disc.paire_jours) * 50
        
        logger.info("✓ Paires de jours configurées (soft)")
    
    def _add_fill_requirements(self):
        """Contrainte hard: Vacations doivent être remplies à capacité"""
        logger.info("Ajout contraintes: Remplissage obligatoire...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.be_filled:
                continue
            
            for v_idx, vac in enumerate(self.vacations):
                slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
                
                if len(disc.capacite) > slot_idx and disc.presence[slot_idx]:
                    cap = disc.capacite[slot_idx]
                    vars_in_slot = self.vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
                    
                    if cap > 0 and vars_in_slot:
                        self.model.Add(sum(vars_in_slot) == cap)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de remplissage ajoutées")
    
    def _add_binome_constraints(self):
        """Contrainte: Binômes doivent être affectés ensemble"""
        logger.info("Ajout contraintes: Binômes...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.en_binome:
                continue
            
            # Créer paires de binômes
            binome_pairs = set()
            for e in self.config.eleves:
                if e.annee.value in disc.annee and e.binome:
                    binome_id_1 = min(e.id_eleve, e.binome.id_eleve)
                    binome_id_2 = max(e.id_eleve, e.binome.id_eleve)
                    binome_pairs.add((binome_id_1, binome_id_2))
            
            for e1_id, e2_id in binome_pairs:
                for s in range(1, 53):
                    vars_e1 = self.vars_by_student_disc_semaine.get((e1_id, disc.id_discipline, s), [])
                    vars_e2 = self.vars_by_student_disc_semaine.get((e2_id, disc.id_discipline, s), [])
                    
                    if vars_e1 and vars_e2:
                        # Même nombre d'affectations dans la semaine
                        sum_e1 = sum(v for (_, v) in vars_e1)
                        sum_e2 = sum(v for (_, v) in vars_e2)
                        self.model.Add(sum_e1 == sum_e2)
                        
                        # Même créneaux
                        for (v_idx1, var1) in vars_e1:
                            for (v_idx2, var2) in vars_e2:
                                if v_idx1 == v_idx2:
                                    self.model.Add(var1 == var2)
                        
                        count += 1
        
        logger.info(f"✓ {count} contraintes de binômes ajoutées")
    
    def _add_frequency_constraints(self):
        """Contrainte: Fréquence des vacations (toutes les X semaines)"""
        logger.info("Ajout contraintes: Fréquence...")
        
        count = 0
        for disc in self.config.disciplines:
            if disc.frequence_vacations <= 1:
                continue
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                # Vérifier qu'entre deux semaines consécutives avec affectation,
                # il y a au moins frequence_vacations semaines d'écart
                for s1 in range(1, 53):
                    vars_s1 = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s1), [])
                    if not vars_s1:
                        continue
                    
                    # Si affectation en s1, pas d'affectation dans les (freq-1) semaines suivantes
                    for offset in range(1, disc.frequence_vacations):
                        s2 = s1 + offset
                        if s2 > 52:
                            break
                        
                        vars_s2 = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s2), [])
                        if vars_s2:
                            sum_s1 = sum(v for (_, v) in vars_s1)
                            sum_s2 = sum(v for (_, v) in vars_s2)
                            # Si sum_s1 > 0, alors sum_s2 == 0
                            has_s1 = self.model.NewBoolVar(f"has_e{el.id_eleve}_d{disc.id_discipline}_s{s1}")
                            self.model.Add(sum_s1 > 0).OnlyEnforceIf(has_s1)
                            self.model.Add(sum_s1 == 0).OnlyEnforceIf(has_s1.Not())
                            self.model.Add(sum_s2 == 0).OnlyEnforceIf(has_s1)
                            count += 1
        
        logger.info(f"✓ {count} contraintes de fréquence ajoutées")
    
    def _add_semester_distribution(self):
        """Contrainte: Répartition semestrielle des quotas"""
        logger.info("Ajout contraintes: Répartition semestrielle...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.repartition_semestrielle:
                continue
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                # Semestre 1: semaines 1-26, Semestre 2: semaines 27-52
                vars_sem1 = []
                vars_sem2 = []
                
                for s in range(1, 27):
                    vars_s = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                    vars_sem1.extend([v for (_, v) in vars_s])
                
                for s in range(27, 53):
                    vars_s = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                    vars_sem2.extend([v for (_, v) in vars_s])
                
                if vars_sem1 and vars_sem2:
                    quota_sem1 = disc.repartition_semestrielle[0]
                    quota_sem2 = disc.repartition_semestrielle[1]
                    
                    self.model.Add(sum(vars_sem1) <= quota_sem1)
                    self.model.Add(sum(vars_sem2) <= quota_sem2)
                    count += 2
        
        logger.info(f"✓ {count} contraintes de répartition semestrielle ajoutées")
    
    def _add_group_diversity(self):
        """Contrainte: Mixité des groupes (niveaux)"""
        logger.info("Ajout contraintes: Mixité des groupes...")
        
        count = 0
        for disc in self.config.disciplines:
            if disc.mixite_groupes == 0:
                continue
            
            for v_idx, vac in enumerate(self.vacations):
                slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
                
                if not (len(disc.presence) > slot_idx and disc.presence[slot_idx]):
                    continue
                
                # Récupérer toutes les années éligibles
                niveaux_eligibles = [niv for niv in niveau if niv.value in disc.annee]
                
                if disc.mixite_groupes == 1:
                    # Exactement 1 élève de chaque niveau
                    for niv in niveaux_eligibles:
                        vars_niveau = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                        if vars_niveau:
                            self.model.Add(sum(vars_niveau) == 1)
                            count += 1
                
                elif disc.mixite_groupes == 2:
                    # Au moins 2 niveaux différents
                    niveau_present_vars = []
                    for niv in niveaux_eligibles:
                        vars_niveau = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                        if vars_niveau:
                            niv_present = self.model.NewBoolVar(f"niv{niv.value}_d{disc.id_discipline}_v{v_idx}")
                            self.model.Add(sum(vars_niveau) > 0).OnlyEnforceIf(niv_present)
                            self.model.Add(sum(vars_niveau) == 0).OnlyEnforceIf(niv_present.Not())
                            niveau_present_vars.append(niv_present)
                    
                    if len(niveau_present_vars) >= 2:
                        self.model.Add(sum(niveau_present_vars) >= 2)
                        count += 1
                
                elif disc.mixite_groupes == 3:
                    # Tous du même niveau
                    niveau_present_vars = []
                    for niv in niveaux_eligibles:
                        vars_niveau = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                        if vars_niveau:
                            niv_present = self.model.NewBoolVar(f"niv{niv.value}_d{disc.id_discipline}_v{v_idx}")
                            self.model.Add(sum(vars_niveau) > 0).OnlyEnforceIf(niv_present)
                            self.model.Add(sum(vars_niveau) == 0).OnlyEnforceIf(niv_present.Not())
                            niveau_present_vars.append(niv_present)
                    
                    if niveau_present_vars:
                        self.model.Add(sum(niveau_present_vars) <= 1)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de mixité ajoutées")
    
    def _add_continuity_constraints(self):
        """Contrainte: Pas plus de X vacations dans Y semaines"""
        logger.info("Ajout contraintes: Continuité...")
        
        count = 0
        for disc in self.config.disciplines:
            if not isinstance(disc.repetition_continuite, (list, tuple)):
                continue
            
            limit = disc.repetition_continuite[0]
            distance = disc.repetition_continuite[1]
            
            if limit <= 0 or distance <= 0:
                continue
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                # Fenêtre glissante de 'distance' semaines
                for s_start in range(1, 53):
                    s_end = min(s_start + distance - 1, 52)
                    
                    vars_window = []
                    for s in range(s_start, s_end + 1):
                        vars_s = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                        vars_window.extend([v for (_, v) in vars_s])
                    
                    if vars_window:
                        self.model.Add(sum(vars_window) <= limit)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de continuité ajoutées")
    
    def _add_level_replacement(self):
        """Contrainte: Remplacement de niveau (% de capacité)"""
        logger.info("Ajout contraintes: Remplacement de niveau...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.remplacement_niveau:
                continue
            
            for (niv_from_val, niv_to_val, percentage) in disc.remplacement_niveau:
                # Trouver les objets niveau
                niv_from = None
                niv_to = None
                for n in niveau:
                    if n.value == niv_from_val:
                        niv_from = n
                    if n.value == niv_to_val:
                        niv_to = n
                
                if not niv_from or not niv_to:
                    continue
                
                # Pour chaque vacation, si niveau FROM absent, niveau TO doit remplir X%
                for v_idx, vac in enumerate(self.vacations):
                    slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
                    
                    if not (len(disc.presence) > slot_idx and disc.presence[slot_idx]):
                        continue
                    
                    vars_from = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv_from), [])
                    vars_to = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv_to), [])
                    
                    if not vars_to:
                        continue
                    
                    cap = disc.capacite[slot_idx] if len(disc.capacite) > slot_idx else 0
                    required = int((percentage / 100.0) * cap)
                    
                    if required > 0:
                        # Si aucun élève FROM présent, alors TO >= required
                        from_absent = self.model.NewBoolVar(f"from_absent_d{disc.id_discipline}_v{v_idx}")
                        
                        if vars_from:
                            self.model.Add(sum(vars_from) == 0).OnlyEnforceIf(from_absent)
                            self.model.Add(sum(vars_from) > 0).OnlyEnforceIf(from_absent.Not())
                        else:
                            # Pas de variables FROM disponibles, donc toujours absent
                            self.model.Add(from_absent == 1)
                        
                        self.model.Add(sum(vars_to) >= required).OnlyEnforceIf(from_absent)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de remplacement ajoutées")
    
    def _add_same_day_constraints(self):
        """Contrainte soft: Même jour (bonus dans objectif)"""
        logger.info("Ajout contraintes: Même jour (soft)...")
        
        # Cette contrainte est gérée dans l'objectif (bonus)
        # Calcul du score max théorique
        for disc in self.config.disciplines:
            if disc.meme_jour:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    try:
                        idx_annee = disc.annee.index(el.annee.value)
                        quota = disc.quotas[idx_annee] if len(disc.quotas) > idx_annee else 0
                    except (ValueError, IndexError):
                        quota = 0
                    
                    if quota > 1:
                        # Chaque paire d'affectations peut rapporter 30 points max
                        max_pairs = quota * (quota - 1) // 2
                        self.max_theoretical_score += max_pairs * 30
        
        logger.info("✓ Même jour configuré (soft)")
    
    # objective configuration
        
    def _set_objective(self):
        """Configure la fonction objectif (logique V5_03_C)"""
        logger.info("Configuration de l'objectif...")
        
        # Poids configuration (identique à V5_03_C)
        w_fill = 600         # Points par affectation dans le quota
        w_excess = -900      # Pénalité par affectation au-delà du quota
        w_success = 30000    # Bonus si élève atteint son quota pour une discipline
        w_grand_slam = 5000000  # Super bonus si TOUS les élèves atteignent quota
        
        w_preference = 50    # Bonus préférence jour
        w_priority_1 = 30    # Bonus priorité niveau 1
        w_priority_2 = 15    # Bonus priorité niveau 2
        w_priority_3 = 5     # Bonus priorité niveau 3
        
        w_pair = 50          # Bonus paire de jours
        w_same_day = 30      # Bonus même jour
        
        # A. MAXIMISER REMPLISSAGE JUSQU'AU QUOTA
        logger.info("  → Configuration quotas...")
        
        for disc in self.config.disciplines:
            discipline_success_vars = []
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                vars_list = self.vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                if not vars_list:
                    continue
                
                # Récupérer quota
                try:
                    idx_annee = disc.annee.index(el.annee.value)
                    quota = disc.quotas[idx_annee] if len(disc.quotas) > idx_annee else 0
                except (ValueError, IndexError):
                    quota = 0
                
                if quota > 0:
                    # 1. Variable sat_var: affectations DANS le quota
                    sat_var = self.model.NewIntVar(0, quota, f"sat_e{el.id_eleve}_d{disc.id_discipline}")
                    self.sat_vars[(el.id_eleve, disc.id_discipline)] = sat_var
                    
                    # 2. Variable excess_var: affectations AU-DELÀ du quota
                    max_possible = len(vars_list)
                    excess_var = self.model.NewIntVar(0, max_possible, f"excess_e{el.id_eleve}_d{disc.id_discipline}")
                    self.excess_vars[(el.id_eleve, disc.id_discipline)] = excess_var
                    
                    # 3. Relation: sum(vars) = sat_var + excess_var
                    self.model.Add(sum(vars_list) == sat_var + excess_var)
                    
                    # 4. Contrainte: sat_var <= quota
                    self.model.Add(sat_var <= quota)
                    
                    # 5. Contribution objectif: w_fill * sat_var + w_excess * excess_var
                    self.obj_terms.append(sat_var)
                    self.weights.append(w_fill)
                    self.obj_terms.append(excess_var)
                    self.weights.append(w_excess)
                    
                    # Score max théorique: tous atteignent quota sans dépassement
                    self.max_theoretical_score += w_fill * quota
                    
                    # 6. Variable is_success: True si quota atteint
                    is_success = self.model.NewBoolVar(f"success_e{el.id_eleve}_d{disc.id_discipline}")
                    self.success_vars[(el.id_eleve, disc.id_discipline)] = is_success
                    
                    self.model.Add(sat_var >= quota).OnlyEnforceIf(is_success)
                    self.model.Add(sat_var < quota).OnlyEnforceIf(is_success.Not())
                    
                    # 7. Bonus si succès individuel
                    self.obj_terms.append(is_success)
                    self.weights.append(w_success)
                    
                    # Score max théorique: tous les élèves réussissent
                    self.max_theoretical_score += w_success
                    
                    discipline_success_vars.append(is_success)
            
            # 8. SUPER BONUS: Tous les élèves de la discipline atteignent quota
            if discipline_success_vars:
                all_success_var = self.model.NewBoolVar(f"all_success_d{disc.id_discipline}")
                self.all_success_vars[disc.id_discipline] = all_success_var
                
                # all_success = min(discipline_success_vars)
                self.model.AddMinEquality(all_success_var, discipline_success_vars)
                
                # Bonus si tous réussissent
                # NOTE: On ne l'inclut PAS dans max_theoretical_score (logique V5_03_C)
                # car trop difficile à atteindre avec toutes les contraintes
                # self.obj_terms.append(all_success_var)
                # self.weights.append(w_grand_slam)
        
        # B. PRÉFÉRENCES JOURS
        logger.info("  → Préférences jours...")
        poly = None
        for disc in self.config.disciplines:
            if disc.id_discipline == 1:  # Polyclinique
                poly = disc
                break
        
        if poly and poly.take_jour_pref:
            # Calcul max théorique
            pref_count = 0
            for el in self.config.eleves:
                if el.annee.value in poly.annee and el.jour_pref:
                    try:
                        idx_annee = poly.annee.index(el.annee.value)
                        quota = poly.quotas[idx_annee] if len(poly.quotas) > idx_annee else 0
                        pref_count += quota
                    except (ValueError, IndexError):
                        pass
            
            self.max_theoretical_score += pref_count * w_preference
            
            # Ajouter bonus
            for (e_id, d_id, v_idx), var in self.assignments.items():
                if d_id == poly.id_discipline:
                    el = self.eleve_dict[e_id]
                    if el.jour_pref:
                        vac = self.vacations[v_idx]
                        if vac.jour == el.jour_pref.jour and vac.period == el.jour_pref.period:
                            self.obj_terms.append(var)
                            self.weights.append(w_preference)
        
        # C. PRIORITÉ NIVEAU
        logger.info("  → Priorité niveau...")
        for disc in self.config.disciplines:
            if disc.priorite_niveau:
                # Calcul max théorique
                for priority_idx, niv_val in enumerate(disc.priorite_niveau):
                    niv = None
                    for n in niveau:
                        if n.value == niv_val:
                            niv = n
                            break
                    
                    if niv:
                        # Compter élèves de ce niveau
                        count_niv = sum(1 for el in self.config.eleves if el.annee == niv)
                        
                        try:
                            idx_annee = disc.annee.index(niv_val)
                            quota = disc.quotas[idx_annee] if len(disc.quotas) > idx_annee else 0
                        except (ValueError, IndexError):
                            quota = 0
                        
                        if priority_idx == 0:
                            self.max_theoretical_score += count_niv * quota * w_priority_1
                        elif priority_idx == 1:
                            self.max_theoretical_score += count_niv * quota * w_priority_2
                        elif priority_idx == 2:
                            self.max_theoretical_score += count_niv * quota * w_priority_3
                
                # Ajouter bonus
                for priority_idx, niv_val in enumerate(disc.priorite_niveau):
                    niv = None
                    for n in niveau:
                        if n.value == niv_val:
                            niv = n
                            break
                    
                    if not niv:
                        continue
                    
                    for el in self.config.eleves:
                        if el.annee != niv:
                            continue
                        
                        vars_list = self.vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                        if not vars_list:
                            continue
                        
                        bonus = 0
                        if priority_idx == 0:
                            bonus = w_priority_1
                        elif priority_idx == 1:
                            bonus = w_priority_2
                        elif priority_idx == 2:
                            bonus = w_priority_3
                        
                        if bonus > 0:
                            for var in vars_list:
                                self.obj_terms.append(var)
                                self.weights.append(bonus)
        
        # D. PAIRES DE JOURS (Soft)
        logger.info("  → Paires de jours...")
        for disc in self.config.disciplines:
            if disc.paire_jours:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    for s in range(1, 53):
                        vars_semaine = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                        if not vars_semaine:
                            continue
                        
                        # Grouper par jour
                        vars_by_day = collections.defaultdict(list)
                        for (v_idx, var) in vars_semaine:
                            day = self.vacations[v_idx].jour
                            vars_by_day[day].append(var)
                        
                        # Vérifier paires
                        for (day1, day2) in disc.paire_jours:
                            if day1 in vars_by_day and day2 in vars_by_day:
                                # Bonus si les deux jours ont au moins une affectation
                                pair_bonus = self.model.NewBoolVar(f"pair_e{el.id_eleve}_d{disc.id_discipline}_s{s}_d{day1}d{day2}")
                                
                                has_day1 = self.model.NewBoolVar(f"has_d{day1}_e{el.id_eleve}_d{disc.id_discipline}_s{s}")
                                has_day2 = self.model.NewBoolVar(f"has_d{day2}_e{el.id_eleve}_d{disc.id_discipline}_s{s}")
                                
                                self.model.Add(sum(vars_by_day[day1]) > 0).OnlyEnforceIf(has_day1)
                                self.model.Add(sum(vars_by_day[day1]) == 0).OnlyEnforceIf(has_day1.Not())
                                self.model.Add(sum(vars_by_day[day2]) > 0).OnlyEnforceIf(has_day2)
                                self.model.Add(sum(vars_by_day[day2]) == 0).OnlyEnforceIf(has_day2.Not())
                                
                                # pair_bonus = has_day1 AND has_day2
                                self.model.AddBoolAnd([has_day1, has_day2]).OnlyEnforceIf(pair_bonus)
                                self.model.AddBoolOr([has_day1.Not(), has_day2.Not()]).OnlyEnforceIf(pair_bonus.Not())
                                
                                self.obj_terms.append(pair_bonus)
                                self.weights.append(w_pair)
        
        # E. MÊME JOUR (Soft)
        logger.info("  → Même jour...")
        for disc in self.config.disciplines:
            if disc.meme_jour:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    # Pour chaque paire d'affectations de l'élève dans cette discipline
                    vars_list = self.vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                    if len(vars_list) < 2:
                        continue
                    
                    # Récupérer v_idx pour chaque variable
                    var_to_vidx = {}
                    for (e_id, d_id, v_idx), var in self.assignments.items():
                        if e_id == el.id_eleve and d_id == disc.id_discipline:
                            var_to_vidx[id(var)] = v_idx
                    
                    # Pour chaque paire
                    for i in range(len(vars_list)):
                        for j in range(i + 1, len(vars_list)):
                            var_i = vars_list[i]
                            var_j = vars_list[j]
                            
                            v_idx_i = var_to_vidx.get(id(var_i))
                            v_idx_j = var_to_vidx.get(id(var_j))
                            
                            if v_idx_i is None or v_idx_j is None:
                                continue
                            
                            day_i = self.vacations[v_idx_i].jour
                            day_j = self.vacations[v_idx_j].jour
                            
                            # Bonus si même jour ou jour adjacent
                            if abs(day_i - day_j) <= 1:
                                same_day_bonus = self.model.NewBoolVar(f"sameday_e{el.id_eleve}_d{disc.id_discipline}_v{v_idx_i}v{v_idx_j}")
                                
                                # bonus actif si les deux variables sont à 1
                                self.model.AddBoolAnd([var_i, var_j]).OnlyEnforceIf(same_day_bonus)
                                self.model.AddBoolOr([var_i.Not(), var_j.Not()]).OnlyEnforceIf(same_day_bonus.Not())
                                
                                self.obj_terms.append(same_day_bonus)
                                self.weights.append(w_same_day)
        
        # Définir objectif
        self.model.Maximize(sum(t * w for t, w in zip(self.obj_terms, self.weights)))
        
        logger.info(f"✓ Objectif configuré avec {len(self.obj_terms)} termes")
        logger.info(f"  Score max théorique: {self.max_theoretical_score:,.0f}")
    
    # resolution
    
    def solve(self) -> OptimizationResult:
        """
        Résout le modèle et retourne les résultats
        
        Returns:
            OptimizationResult: Résultat avec statut et données
        """
        logger.info("=" * 80)
        logger.info("RÉSOLUTION")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        self._notify_progress("Résolution en cours...", 75)
        
        # Configurer solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.config.solver_params.max_time_seconds
        self.solver.parameters.num_workers = self.config.solver_params.num_workers
        self.solver.parameters.log_search_progress = self.config.solver_params.log_progress
        
        # Callback pour suivi progression
        callback = SolutionCallback(self.config.solver_params.max_time_seconds)
        
        # Thread timer pour log périodique
        stop_timer = threading.Event()
        
        def periodic_progress():
            """Log progression périodique même sans nouvelle solution"""
            last_log = time.time()
            while not stop_timer.is_set():
                time.sleep(1)
                current = time.time()
                if current - last_log >= 5:
                    elapsed = int(current - start_time)
                    remaining = max(0, int(self.config.solver_params.max_time_seconds - elapsed))
                    print(f"STATUS|Elapsed: {elapsed}s|Remaining: {remaining}s")
                    sys.stdout.flush()
                    last_log = current
        
        timer_thread = threading.Thread(target=periodic_progress, daemon=True)
        timer_thread.start()
        
        # Résolution
        try:
            logger.info(f"Temps maximum: {self.config.solver_params.max_time_seconds}s")
            print(f"SOLVER_START|MaxTime: {self.config.solver_params.max_time_seconds}s")
            sys.stdout.flush()
            
            status = self.solver.Solve(self.model, callback)
            
            # Arrêter timer
            stop_timer.set()
            timer_thread.join(timeout=1)
            
            solve_time = time.time() - start_time
            
            self._notify_progress("Solution trouvée", 95)
            
            return self._build_result(status, solve_time)
        
        except KeyboardInterrupt:
            stop_timer.set()
            logger.warning("Interruption utilisateur (Ctrl+C)")
            
            # Tenter récupération solution partielle
            if self.solver.ObjectiveValue() > 0:
                solve_time = time.time() - start_time
                return self._build_result(cp_model.FEASIBLE, solve_time)
            else:
                return OptimizationResult(
                    status='ERROR',
                    solve_time=time.time() - start_time,
                    error_message="Interruption utilisateur sans solution"
                )
        
        except Exception as e:
            stop_timer.set()
            logger.exception("Erreur lors de la résolution")
            return OptimizationResult(
                status='ERROR',
                solve_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _build_result(self, status, solve_time: float) -> OptimizationResult:
        """Construit l'objet résultat depuis le statut du solver"""
        
        # Mapping statuts
        status_map = {
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE',
            cp_model.MODEL_INVALID: 'ERROR',
            cp_model.UNKNOWN: 'TIMEOUT'
        }
        
        status_str = status_map.get(status, 'UNKNOWN')
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raw_score = self.solver.ObjectiveValue()
            
            # Normaliser score
            normalized_score = 0.0
            if self.max_theoretical_score > 0:
                normalized_score = (raw_score / self.max_theoretical_score) * 100
                normalized_score = min(100.0, max(0.0, normalized_score))
            
            logger.info(f"✓ Solution trouvée!")
            logger.info(f"  Score brut: {raw_score:,.0f}")
            logger.info(f"  Score max théorique: {self.max_theoretical_score:,.0f}")
            logger.info(f"  Score normalisé: {normalized_score:.2f}/100")
            
            # Extraire affectations
            solution_assignments = {}
            for (e_id, d_id, v_idx), var in self.assignments.items():
                if self.solver.Value(var) == 1:
                    solution_assignments[(e_id, d_id, v_idx)] = 1
            
            # Calculer statistiques
            stats = self._compute_statistics(solution_assignments)
            
            return OptimizationResult(
                status=status_str,
                objective_value=raw_score,
                normalized_score=normalized_score,
                max_theoretical_score=self.max_theoretical_score,
                solve_time=solve_time,
                assignments=solution_assignments,
                statistics=stats
            )
        
        else:
            logger.error(f"✗ Aucune solution trouvée: {status_str}")
            return OptimizationResult(
                status=status_str,
                solve_time=solve_time,
                error_message=f"Solver status: {status_str}"
            )
    
    def _compute_statistics(self, solution_assignments: Dict) -> Dict:
        """Calcule les statistiques de la solution"""
        stats = {
            'total_assignments': len(solution_assignments),
            'assignments_by_discipline': collections.defaultdict(int),
            'assignments_by_student': collections.defaultdict(int),
            'assignments_by_level': collections.defaultdict(int),
            'quota_fulfillment': {},
            'success_count': 0,
            'grand_slam_disciplines': []
        }
        
        # Compter par discipline, élève, niveau
        for (e_id, d_id, v_idx) in solution_assignments:
            stats['assignments_by_discipline'][d_id] += 1
            stats['assignments_by_student'][e_id] += 1
            
            el = self.eleve_dict[e_id]
            stats['assignments_by_level'][el.annee.name] += 1
        
        # Vérifier quotas
        for disc in self.config.disciplines:
            disc_stats = {
                'students_checked': 0,
                'students_success': 0,
                'grand_slam': False
            }
            
            success_count = 0
            total_count = 0
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                total_count += 1
                
                # Compter affectations
                count = sum(1 for (e_id, d_id, v_idx) in solution_assignments 
                           if e_id == el.id_eleve and d_id == disc.id_discipline)
                
                # Récupérer quota
                try:
                    idx_annee = disc.annee.index(el.annee.value)
                    quota = disc.quotas[idx_annee] if len(disc.quotas) > idx_annee else 0
                except (ValueError, IndexError):
                    quota = 0
                
                if count >= quota and quota > 0:
                    success_count += 1
            
            disc_stats['students_checked'] = total_count
            disc_stats['students_success'] = success_count
            
            if total_count > 0 and success_count == total_count:
                disc_stats['grand_slam'] = True
                stats['grand_slam_disciplines'].append(disc.id_discipline)
            
            stats['quota_fulfillment'][disc.id_discipline] = disc_stats
            stats['success_count'] += success_count
        
        return stats
    
    
    # export solution
    
    
    def export_solution(self, result: OptimizationResult, output_path: str):
        """
        Exporte la solution en CSV
        
        Args:
            result: OptimizationResult avec les affectations
            output_path: Chemin du fichier CSV de sortie
        """
        if not result.is_success():
            logger.error("Impossible d'exporter: pas de solution valide")
            return
        
        logger.info(f"Export de la solution vers {output_path}...")
        
        # Créer répertoire si nécessaire
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Préparer données
        rows = []
        for (e_id, d_id, v_idx) in sorted(result.assignments.keys()):
            el = self.eleve_dict[e_id]
            disc = None
            for d in self.config.disciplines:
                if d.id_discipline == d_id:
                    disc = d
                    break
            
            if not disc:
                continue
            
            vac = self.vacations[v_idx]
            
            rows.append({
                'eleve_id': e_id,
                'eleve_nom': el.nom,
                'eleve_prenom': el.prenom,
                'eleve_annee': el.annee.name,
                'discipline_id': d_id,
                'discipline_nom': disc.nom,
                'semaine': vac.semaine,
                'jour': vac.jour,
                'jour_nom': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'][vac.jour],
                'period': vac.period.name,
                'vacation_index': v_idx
            })
        
        # Écrire CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['eleve_id', 'eleve_nom', 'eleve_prenom', 'eleve_annee',
                         'discipline_id', 'discipline_nom', 'semaine', 'jour',
                         'jour_nom', 'period', 'vacation_index']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"✓ Solution exportée: {len(rows)} affectations")
    
    # utilities
     
    def _notify_progress(self, message: str, percent: int):
        """Notifie la progression si callback configuré"""
        if self.progress_callback:
            self.progress_callback(message, percent)
        logger.info(f"[{percent}%] {message}")
