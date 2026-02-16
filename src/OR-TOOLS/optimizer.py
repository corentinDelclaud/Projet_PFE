"""
Optimization service with progress tracking
"""
import sys
import os
import logging
import collections
import time
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ortools.sat.python import cp_model
from classes.vacation import vacation
from classes.stage import stage
from classes.enum.demijournee import DemiJournee

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of optimization with metadata"""
    status: str  # 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'ERROR', 'TIMEOUT'
    objective_value: Optional[float] = None
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
        """Check if optimization succeeded"""
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
        """Called each time a solution is found"""
        self._solution_count += 1
        current_time = time.time()
        elapsed = int(current_time - self.start_time)
        remaining = max(0, int(self.max_time - elapsed))
        
        # Log every 2 seconds to avoid spam
        if current_time - self._last_log_time >= 2:
            # IMPORTANT: Format exact pour le parsing Streamlit
            print(f"PROGRESS|Solution #{self._solution_count}|Elapsed: {elapsed}s|Remaining: {remaining}s|Objective: {self.ObjectiveValue()}")
            sys.stdout.flush()  # Force immediate output
            self._last_log_time = current_time

class ScheduleOptimizer:
    """Clean optimizer interface with progress tracking"""
    
    def __init__(self, config):
        """
        Initialize optimizer with configuration
        
        Args:
            config: ModelConfig instance
        """
        self.config = config
        self.model = None
        self.solver = None
        self.assignments = {}
        self.vacations = []
        self.eleve_dict = {}
        self.stages_eleves = {}
        self.calendar_unavailability = {}
        self.progress_callback = None
        
        # Indexing structures
        self.vars_by_student_vac = collections.defaultdict(list)
        self.vars_by_disc_vac = collections.defaultdict(list)
        self.vars_by_student_disc_semaine = collections.defaultdict(list)
        self.vars_by_disc_vac_niveau = collections.defaultdict(list)
        self.vars_by_student_disc_all = collections.defaultdict(list)
    
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """
        Set callback for progress updates
        
        Args:
            callback: Function(message: str, progress_percent: int)
        """
        self.progress_callback = callback
    
    def prepare_data(self):
        """Prepare data structures for optimization"""
        self._notify_progress("Préparation des données", 5)
        
        # Create eleve dict
        self.eleve_dict = {e.id_eleve: e for e in self.config.eleves}
        
        # Prepare stages
        for el in self.config.eleves:
            if el.periode_stage > 0:
                key = (el.annee.name, el.periode_stage)
                if key in self.config.stages:
                    self.stages_eleves[el.id_eleve] = [
                        stage(
                            d["nom"],
                            d["debut"],
                            d["fin"],
                            d["niveau_obj"],
                            el.periode_stage
                        )
                        for d in self.config.stages[key]
                    ]
        
        # Calendar unavailability
        self.calendar_unavailability = self.config.calendriers
        
        # Generate vacations (weeks 1-52)
        self.vacations = []
        for s in range(1, 53):
            for j in range(5):  # Lundi à Vendredi
                for p in DemiJournee:
                    self.vacations.append(vacation(s, j, p))
        
        logger.info(f"✓ Données préparées: {len(self.vacations)} créneaux")
    
    def build_model(self) -> None:
        """Build the complete CP-SAT model"""
        logger.info("=" * 80)
        logger.info("CONSTRUCTION DU MODÈLE")
        logger.info("=" * 80)
        
        self.model = cp_model.CpModel()
        
        # Create variables
        self._create_variables()
        self._notify_progress("Variables créées", 20)
        
        # Build indexes
        self._build_indexes()
        self._notify_progress("Index construits", 25)
        
        # Add constraints
        self._add_capacity_constraints()
        self._notify_progress("Contraintes de capacité", 30)
        
        self._add_uniqueness_constraints()
        self._notify_progress("Contraintes d'unicité", 35)
        
        self._add_quota_constraints()
        self._notify_progress("Contraintes de quotas", 40)
        
        self._add_max_vacations_per_week()
        self._notify_progress("Contraintes hebdomadaires", 45)
        
        self._add_fill_requirements()
        self._notify_progress("Contraintes de remplissage", 50)
        
        self._add_binome_constraints()
        self._notify_progress("Contraintes de binômes", 55)
        
        self._add_advanced_constraints()
        self._notify_progress("Contraintes avancées", 65)
        
        # Set objective
        self._set_objective()
        self._notify_progress("Objectif configuré", 70)
        
        logger.info("✓ Modèle construit avec succès")
    
    def solve(self) -> OptimizationResult:
        """
        Solve the model and return results
        
        Returns:
            OptimizationResult: Optimization result with status and data
        """
        logger.info("=" * 80)
        logger.info("RÉSOLUTION")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        self._notify_progress("Résolution en cours...", 75)
        
        # Configure solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.config.solver_params.max_time_seconds
        self.solver.parameters.num_workers = self.config.solver_params.num_workers
        self.solver.parameters.log_search_progress = self.config.solver_params.log_progress
        
        # Add callback for progress tracking
        callback = SolutionCallback(self.config.solver_params.max_time_seconds)

        # Timer thread to log progress every 5 seconds
        stop_timer = threading.Event()

        def periodic_progress():
            """Log progress periodically even without new solutions"""
            while not stop_timer.is_set():
                time.sleep(5)
                if not stop_timer.is_set():
                    elapsed = int(time.time() - start_time)
                    remaining = max(0, int(self.config.solver_params.max_time_seconds - elapsed))
                    obj = callback.ObjectiveValue() if callback._solution_count > 0 else 0
                    print(f"PROGRESS|Solution #{callback._solution_count}|Elapsed: {elapsed}s|Remaining: {remaining}s|Objective: {obj}")
                    sys.stdout.flush()
        
        timer_thread = threading.Thread(target=periodic_progress, daemon=True)
        timer_thread.start()

        # Solve
        try:
            logger.info(f"Temps maximum autorisé: {self.config.solver_params.max_time_seconds}s")
            print(f"SOLVER_START|MaxTime: {self.config.solver_params.max_time_seconds}s")
            sys.stdout.flush()
            
            status = self.solver.Solve(self.model, callback)
            
            # Stop timer
            stop_timer.set()
            timer_thread.join(timeout=1)
            
            solve_time = time.time() - start_time
            
            self._notify_progress("Solution trouvée", 95)
            
            return self._build_result(status, solve_time)
        
        except Exception as e:
            stop_timer.set()
            logger.exception("Erreur lors de la résolution")
            return OptimizationResult(
                status='ERROR',
                solve_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _notify_progress(self, message: str, percent: int):
        """Notify progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(message, percent)
        logger.info(f"[{percent}%] {message}")
    
    def _create_variables(self):
        """Create decision variables"""
        logger.info("Création des variables de décision...")
        
        count_vars = 0
        for v_idx, vac in enumerate(self.vacations):
            slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
            
            for disc in self.config.disciplines:
                # Check if discipline is open at this slot
                if not (len(disc.presence) > slot_idx and disc.presence[slot_idx]):
                    continue
                
                for el in self.config.eleves:
                    # Check if student's year matches discipline
                    if el.annee.value not in disc.annee:
                        continue
                    
                    # Check calendar unavailability
                    if (vac.semaine, slot_idx) in self.calendar_unavailability.get(el.annee, set()):
                        continue
                    
                    # Check stage conflict
                    is_in_stage = False
                    if el.id_eleve in self.stages_eleves:
                        for st in self.stages_eleves[el.id_eleve]:
                            if st.debut_stage <= vac.semaine <= st.fin_stage:
                                is_in_stage = True
                                break
                    if is_in_stage:
                        continue
                    
                    # Create variable
                    var_name = f"x_e{el.id_eleve}_d{disc.id_discipline}_v{v_idx}"
                    self.assignments[(el.id_eleve, disc.id_discipline, v_idx)] = \
                        self.model.NewBoolVar(var_name)
                    count_vars += 1
        
        logger.info(f"✓ {count_vars} variables créées")
    
    def _build_indexes(self):
        """Build indexing structures for efficient constraint addition"""
        logger.info("Construction des index...")
        
        for (e_id, d_id, v_idx), var in self.assignments.items():
            # Index by student and vacation
            self.vars_by_student_vac[(e_id, v_idx)].append(var)
            
            # Index by discipline and vacation
            self.vars_by_disc_vac[(d_id, v_idx)].append(var)
            
            # Index by student and discipline (all vacations)
            self.vars_by_student_disc_all[(e_id, d_id)].append(var)
            
            # Index by student, discipline and week
            semaine = self.vacations[v_idx].semaine
            self.vars_by_student_disc_semaine[(e_id, d_id, semaine)].append((v_idx, var))
            
            # Index by discipline, vacation and student level
            el_annee = self.eleve_dict[e_id].annee
            self.vars_by_disc_vac_niveau[(d_id, v_idx, el_annee)].append(var)
        
        logger.info("✓ Index construits")
    
    def _add_capacity_constraints(self): #A modifier pour vrai modele
        """Add capacity constraints for each discipline at each slot"""
        logger.info("Ajout des contraintes de capacité...")
        
        count = 0
        for v_idx, vac in enumerate(self.vacations):
            slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
            
            for disc in self.config.disciplines:
                vars_in_disc_slot = self.vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
                
                if vars_in_disc_slot:
                    cap = disc.nb_eleve[slot_idx] if slot_idx < len(disc.nb_eleve) else 0
                    if cap > 0:
                        self.model.Add(sum(vars_in_disc_slot) <= cap)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de capacité ajoutées")
    
    def _add_uniqueness_constraints(self): #A modifier pour vrai modele
        """Ensure each student is assigned to at most one discipline per slot"""
        logger.info("Ajout des contraintes d'unicité...")
        
        count = 0
        for v_idx in range(len(self.vacations)):
            for el in self.config.eleves:
                vars_for_student = self.vars_by_student_vac.get((el.id_eleve, v_idx), [])
                
                if vars_for_student and len(vars_for_student) > 1:
                    self.model.Add(sum(vars_for_student) <= 1)
                    count += 1
        
        logger.info(f"✓ {count} contraintes d'unicité ajoutées")
    
    def _add_max_vacations_per_week(self): #A modifier pour vrai modele
        """Add maximum vacations per week constraints"""
        logger.info("Ajout des contraintes max vacations/semaine...")
        
        count = 0
        for disc in self.config.disciplines:
            if disc.nb_vacations_par_semaine <= 0:
                continue
            
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                for s in range(1, 53):
                    vars_entries = self.vars_by_student_disc_semaine.get(
                        (el.id_eleve, disc.id_discipline, s), []
                    )
                    vars_week = [v[1] for v in vars_entries]
                    
                    if vars_week:
                        self.model.Add(sum(vars_week) <= disc.nb_vacations_par_semaine)
                        count += 1
        
        logger.info(f"✓ {count} contraintes max vacations/semaine")
    
    def _add_fill_requirements(self): #A modifier pour vrai modele
        """Add constraints to fill slots to capacity"""
        logger.info("Ajout des contraintes de remplissage...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.be_filled:
                continue
            
            for v_idx, vac in enumerate(self.vacations):
                slot_idx = vac.jour * 2 + (0 if vac.period == DemiJournee.matin else 1)
                vars_in_disc_slot = self.vars_by_disc_vac.get((disc.id_discipline, v_idx), [])
                
                if vars_in_disc_slot:
                    cap = disc.nb_eleve[slot_idx] if slot_idx < len(disc.nb_eleve) else 0
                    target = min(cap, len(vars_in_disc_slot))
                    
                    if target > 0:
                        self.model.Add(sum(vars_in_disc_slot) == target)
                        count += 1
        
        logger.info(f"✓ {count} contraintes de remplissage")
    
    def _add_binome_constraints(self): #A modifier pour vrai modele
        """Add constraints for paired students (binômes)"""
        logger.info("Ajout des contraintes de binômes...")
        
        count = 0
        for disc in self.config.disciplines:
            if not disc.en_binome:
                continue
            
            # Create binome pairs
            binome_pairs = set()
            for e in self.config.eleves:
                if e.id_binome > 0 and e.id_eleve < e.id_binome:
                    if e.id_binome in self.eleve_dict:
                        binome_pairs.add((e.id_eleve, e.id_binome))
            
            for e1_id, e2_id in binome_pairs:
                for s in range(1, 53):
                    vars_e1 = self.vars_by_student_disc_semaine.get((e1_id, disc.id_discipline, s), [])
                    vars_e2 = self.vars_by_student_disc_semaine.get((e2_id, disc.id_discipline, s), [])
                    
                    if not vars_e1 or not vars_e2:
                        continue
                    
                    # For each day/period combination
                    for j in range(5):
                        for p in DemiJournee:
                            v_idxs_e1 = [v[0] for v in vars_e1 
                                        if self.vacations[v[0]].jour == j 
                                        and self.vacations[v[0]].period == p]
                            v_idxs_e2 = [v[0] for v in vars_e2 
                                        if self.vacations[v[0]].jour == j 
                                        and self.vacations[v[0]].period == p]
                            
                            if v_idxs_e1 and v_idxs_e2:
                                var_e1 = self.assignments.get((e1_id, disc.id_discipline, v_idxs_e1[0]))
                                var_e2 = self.assignments.get((e2_id, disc.id_discipline, v_idxs_e2[0]))
                                
                                if var_e1 is not None and var_e2 is not None:
                                    self.model.Add(var_e1 == var_e2)
                                    count += 1
        
        logger.info(f"✓ {count} contraintes de binômes")
    
    def _add_advanced_constraints(self): #A modifier pour vrai modele
        """Add advanced discipline-specific constraints"""
        logger.info("Ajout des contraintes avancées...")
        
        constraint_count = 0
        
        # 1. PAIRE JOURS (Soft - via objective)
        # Students should be assigned to paired days in the same week
        logger.info("  → Paires de jours...")
        obj_terms_pairs = []
        weights_pairs = []
        
        for disc in self.config.disciplines:
            if disc.paire_jours:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    for s in range(1, 53):
                        vars_entries = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                        if not vars_entries:
                            continue
                        
                        for (j1, j2) in disc.paire_jours:
                            # Get variables for each day
                            vars_j1 = [v[1] for v in vars_entries if self.vacations[v[0]].jour == j1]
                            vars_j2 = [v[1] for v in vars_entries if self.vacations[v[0]].jour == j2]
                            
                            if vars_j1 and vars_j2:
                                # Boolean for presence on j1
                                b_j1 = self.model.NewBoolVar(f"present_j{j1}_s{s}_e{el.id_eleve}_d{disc.id_discipline}")
                                self.model.Add(sum(vars_j1) >= 1).OnlyEnforceIf(b_j1)
                                self.model.Add(sum(vars_j1) == 0).OnlyEnforceIf(b_j1.Not())
                                
                                # Boolean for presence on j2
                                b_j2 = self.model.NewBoolVar(f"present_j{j2}_s{s}_e{el.id_eleve}_d{disc.id_discipline}")
                                self.model.Add(sum(vars_j2) >= 1).OnlyEnforceIf(b_j2)
                                self.model.Add(sum(vars_j2) == 0).OnlyEnforceIf(b_j2.Not())
                                
                                # If j1 then j2 (soft constraint via objective)
                                pair_ok = self.model.NewBoolVar(f"pair_ok_{j1}_{j2}_s{s}_e{el.id_eleve}_d{disc.id_discipline}")
                                self.model.AddImplication(b_j1, b_j2).OnlyEnforceIf(pair_ok)
                                
                                obj_terms_pairs.append(pair_ok)
                                weights_pairs.append(50)
                                constraint_count += 1
        
        # 2. FRÉQUENCE VACATIONS (Hard)
        # Students should have vacations every X weeks
        logger.info("  → Fréquence des vacations...")
        for disc in self.config.disciplines:
            if disc.frequence_vacations > 1:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    # For each possible starting week
                    for start_week in range(1, disc.frequence_vacations + 1):
                        weeks_group = list(range(start_week, 53, disc.frequence_vacations))
                        
                        # Split into groups of size frequence_vacations
                        for i in range(0, len(weeks_group), disc.frequence_vacations):
                            group_weeks = weeks_group[i:i + disc.frequence_vacations]
                            
                            vars_in_group = []
                            for s in group_weeks:
                                vars_entries = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                                vars_in_group.extend([v[1] for v in vars_entries])
                            
                            if vars_in_group:
                                # At most 1 vacation in this group of weeks
                                self.model.Add(sum(vars_in_group) <= 1)
                                constraint_count += 1
        
        # 3. RÉPARTITION SEMESTRIELLE (Hard)
        # Distribute quotas between semesters
        logger.info("  → Répartition semestrielle...")
        for disc in self.config.disciplines:
            if disc.repartition_semestrielle:
                for el in self.config.eleves:
                    if el.annee.value not in disc.annee:
                        continue
                    
                    # Get quota for this student's year
                    try:
                        adx = disc.annee.index(el.annee.value)
                        quota = disc.quota[adx]
                    except (ValueError, IndexError):
                        quota = 0
                    
                    if quota > 0:
                        sem1_target = disc.repartition_semestrielle[0]
                        sem2_target = disc.repartition_semestrielle[1]
                        
                        vars_sem1 = []
                        vars_sem2 = []
                        
                        for s in range(1, 53):
                            vars_entries = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                            if vars_entries:
                                if s <= 26:  # First semester
                                    vars_sem1.extend([v[1] for v in vars_entries])
                                else:  # Second semester
                                    vars_sem2.extend([v[1] for v in vars_entries])
                        
                        if vars_sem1:
                            self.model.Add(sum(vars_sem1) <= sem1_target)
                            constraint_count += 1
                        if vars_sem2:
                            self.model.Add(sum(vars_sem2) <= sem2_target)
                            constraint_count += 1
        
        # 4. MIXITÉ DES GROUPES (Hard)
        # Control year-level diversity in vacations
        logger.info("  → Mixité des groupes...")
        from classes.enum.niveaux import niveau
        
        for disc in self.config.disciplines:
            if disc.mixite_groupes > 0:
                for v_idx, vac in enumerate(self.vacations):
                    if not self.vars_by_disc_vac.get((disc.id_discipline, v_idx)):
                        continue
                    
                    if disc.mixite_groupes == 1:
                        # Exactly 1 student from each level
                        for niv in niveau:
                            vars_niv = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                            if vars_niv:
                                self.model.Add(sum(vars_niv) == 1)
                                constraint_count += 1
                    
                    elif disc.mixite_groupes == 2:
                        # At least 2 different levels (if vacation is not empty)
                        niv_bools = []
                        for niv in niveau:
                            vars_niv = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                            if vars_niv:
                                b_niv = self.model.NewBoolVar(f"pres_{niv.name}_d{disc.id_discipline}_v{v_idx}")
                                self.model.Add(sum(vars_niv) >= 1).OnlyEnforceIf(b_niv)
                                self.model.Add(sum(vars_niv) == 0).OnlyEnforceIf(b_niv.Not())
                                niv_bools.append(b_niv)
                        
                        if niv_bools:
                            # If any level present, must have at least 2 levels
                            any_present = self.model.NewBoolVar(f"any_pres_d{disc.id_discipline}_v{v_idx}")
                            self.model.Add(sum(niv_bools) >= 1).OnlyEnforceIf(any_present)
                            self.model.Add(sum(niv_bools) == 0).OnlyEnforceIf(any_present.Not())
                            self.model.Add(sum(niv_bools) >= 2).OnlyEnforceIf(any_present)
                            constraint_count += 1
                    
                    elif disc.mixite_groupes == 3:
                        # All from same level (at most 1 level present)
                        niv_bools = []
                        for niv in niveau:
                            vars_niv = self.vars_by_disc_vac_niveau.get((disc.id_discipline, v_idx, niv), [])
                            if vars_niv:
                                b_niv = self.model.NewBoolVar(f"pres_{niv.name}_d{disc.id_discipline}_v{v_idx}")
                                self.model.Add(sum(vars_niv) >= 1).OnlyEnforceIf(b_niv)
                                self.model.Add(sum(vars_niv) == 0).OnlyEnforceIf(b_niv.Not())
                                niv_bools.append(b_niv)
                        
                        if niv_bools:
                            self.model.Add(sum(niv_bools) <= 1)
                            constraint_count += 1
        
        # 5. RÉPÉTITION CONTINUITÉ (Hard)
        # No more than X vacations within Y weeks
        logger.info("  → Répétition continuité...")
        for disc in self.config.disciplines:
            if isinstance(disc.repetition_continuite, tuple):
                limit = disc.repetition_continuite[0]
                distance = disc.repetition_continuite[1]
                
                if limit > 0 and distance > 0:
                    for el in self.config.eleves:
                        if el.annee.value not in disc.annee:
                            continue
                        
                        # For each possible starting week
                        for start_week in range(1, distance + 1):
                            weeks_group = list(range(start_week, 53, distance))
                            
                            vars_in_group = []
                            for s in weeks_group:
                                vars_entries = self.vars_by_student_disc_semaine.get((el.id_eleve, disc.id_discipline, s), [])
                                vars_in_group.extend([v[1] for v in vars_entries])
                            
                            if vars_in_group:
                                self.model.Add(sum(vars_in_group) <= limit)
                                constraint_count += 1
        
        # 6. REMPLACEMENT DE NIVEAU (Hard)
        # Allow one year level to replace another
        logger.info("  → Remplacement de niveau...")
        for disc in self.config.disciplines:
            if disc.remplacement_niveau:
                for (niv_from, niv_to, nb_eleves) in disc.remplacement_niveau:
                    eleves_from = [e for e in self.config.eleves if e.annee.value == niv_from]
                    eleves_to = [e for e in self.config.eleves if e.annee.value == niv_to]
                    
                    for v_idx, vac in enumerate(self.vacations):
                        vars_from = []
                        vars_to = []
                        
                        for el in eleves_from:
                            if (el.id_eleve, disc.id_discipline, v_idx) in self.assignments:
                                vars_from.append(self.assignments[(el.id_eleve, disc.id_discipline, v_idx)])
                        
                        for el in eleves_to:
                            if (el.id_eleve, disc.id_discipline, v_idx) in self.assignments:
                                vars_to.append(self.assignments[(el.id_eleve, disc.id_discipline, v_idx)])
                        
                        if vars_from and vars_to:
                            # For every niv_from student, we need nb_eleves from niv_to
                            denom = max(1, len(eleves_from))
                            self.model.Add(sum(vars_to) * denom >= sum(vars_from) * nb_eleves)
                            constraint_count += 1
        
        # 7. PRIORITÉ NIVEAU (Soft - via objective)
        # Give priority to certain year levels
        logger.info("  → Priorité niveau...")
        obj_terms_prio = []
        weights_prio = []
        
        for disc in self.config.disciplines:
            if disc.priorite_niveau:
                # Create priority map
                prio_map = {}
                if len(disc.priorite_niveau) > 0:
                    prio_map[disc.priorite_niveau[0]] = 50  # Priority 1
                if len(disc.priorite_niveau) > 1:
                    prio_map[disc.priorite_niveau[1]] = 20  # Priority 2
                if len(disc.priorite_niveau) > 2:
                    prio_map[disc.priorite_niveau[2]] = 5   # Priority 3
                
                for el in self.config.eleves:
                    if el.annee.value in prio_map:
                        vars_student = self.vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                        w = prio_map[el.annee.value]
                        for var in vars_student:
                            obj_terms_prio.append(var)
                            weights_prio.append(w)
        
        # 8. JOUR PRÉFÉRENCE (Soft - via objective)
        # Respect student day preferences
        logger.info("  → Préférences jours...")
        obj_terms_pref = []
        weights_pref = []
        
        for disc in self.config.disciplines:
            if disc.take_jour_pref:
                for (e_id, d_id, v_idx), var in self.assignments.items():
                    if d_id == disc.id_discipline:
                        el = self.eleve_dict[e_id]
                        vac = self.vacations[v_idx]
                        
                        # Check if vacation day matches preference
                        # vac.jour: 0-4 (Mon-Fri), jour_preference.value: 1-5
                        if (vac.jour + 1) == el.jour_preference.value:
                            obj_terms_pref.append(var)
                            weights_pref.append(100)  # Significant bonus
        
        logger.info(f"✓ {constraint_count} contraintes avancées ajoutées")
        
        # Store objective terms for later use in _set_objective
        if not hasattr(self, 'advanced_obj_terms'):
            self.advanced_obj_terms = []
            self.advanced_obj_weights = []
        
        self.advanced_obj_terms.extend(obj_terms_pairs)
        self.advanced_obj_weights.extend(weights_pairs)
        self.advanced_obj_terms.extend(obj_terms_prio)
        self.advanced_obj_weights.extend(weights_prio)
        self.advanced_obj_terms.extend(obj_terms_pref)
        self.advanced_obj_weights.extend(weights_pref)
    
    def _set_objective(self): #A modifier pour vrai modele
        """Set the optimization objective"""
        logger.info("Configuration de l'objectif...")
        
        obj_terms = []
        weights = []
        
        # Main objective: Quotas
        for disc in self.config.disciplines:
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                vars_list = self.vars_by_student_disc_all.get((el.id_eleve, disc.id_discipline), [])
                if not vars_list:
                    continue
                
                try:
                    adx = disc.annee.index(el.annee.value)
                    quota = disc.quota[adx]
                except (ValueError, IndexError):
                    quota = 0
                
                if quota > 0:
                    # Weight configuration
                    w_fill = 150
                    w_excess = -200
                    w_success = 7000
                    
                    # Special weights for Polyclinique (id=1)
                    if disc.id_discipline == 1:
                        w_fill = 600
                        w_excess = -800
                        w_success = 30000
                    
                    # Satisfaction variable (how much of quota is filled)
                    sat_var = self.model.NewIntVar(
                        0, quota,
                        f"sat_e{el.id_eleve}_d{disc.id_discipline}"
                    )
                    self.model.Add(sat_var <= sum(vars_list))
                    obj_terms.append(sat_var)
                    weights.append(w_fill)
                    
                    # Excess variable (penalize going over quota)
                    excess_var = self.model.NewIntVar(
                        0, 500,
                        f"excess_e{el.id_eleve}_d{disc.id_discipline}"
                    )
                    self.model.Add(excess_var + quota >= sum(vars_list))
                    obj_terms.append(excess_var)
                    weights.append(w_excess)
                    
                    # Success variable (bonus for meeting quota exactly)
                    is_success = self.model.NewBoolVar(
                        f"success_e{el.id_eleve}_d{disc.id_discipline}"
                    )
                    self.model.Add(sum(vars_list) >= quota).OnlyEnforceIf(is_success)
                    self.model.Add(sum(vars_list) < quota).OnlyEnforceIf(is_success.Not())
                    obj_terms.append(is_success)
                    weights.append(w_success)
        
        # Add advanced constraint objectives (soft constraints)
        if hasattr(self, 'advanced_obj_terms'):
            obj_terms.extend(self.advanced_obj_terms)
            weights.extend(self.advanced_obj_weights)
            logger.info(f"  + {len(self.advanced_obj_terms)} termes de contraintes avancées")
        
        # Set objective
        self.model.Maximize(sum(t * w for t, w in zip(obj_terms, weights)))
        
        logger.info(f"✓ Objectif configuré avec {len(obj_terms)} termes")
    
    def _build_result(self, status, solve_time: float) -> OptimizationResult:
        """Build result object from solver status"""
        
        # Map status
        status_map = {
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE',
            cp_model.MODEL_INVALID: 'ERROR',
            cp_model.UNKNOWN: 'TIMEOUT'
        }
        
        status_str = status_map.get(status, 'UNKNOWN')
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.info(f"✓ Solution trouvée: {self.solver.ObjectiveValue()}")
            
            # Extract assignments
            solution_assignments = {}
            for (e_id, d_id, v_idx), var in self.assignments.items():
                if self.solver.Value(var) == 1:
                    solution_assignments[(e_id, d_id, v_idx)] = True
            
            # Compute statistics
            stats = self._compute_statistics(solution_assignments)
            
            return OptimizationResult(
                status=status_str,
                objective_value=self.solver.ObjectiveValue(),
                solve_time=solve_time,
                assignments=solution_assignments,
                statistics=stats
            )
        
        else:
            error_msg = f"Statut: {status_str}"
            if status == cp_model.INFEASIBLE:
                error_msg = "Modèle infaisable - aucune solution possible avec les contraintes actuelles"
            elif status == cp_model.UNKNOWN:
                error_msg = "Timeout atteint - aucune solution trouvée dans le temps imparti"
            
            logger.error(error_msg)
            
            return OptimizationResult(
                status=status_str,
                solve_time=solve_time,
                error_message=error_msg
            )
    
    def _compute_statistics(self, solution_assignments: Dict) -> Dict:
        """Compute solution statistics"""
        stats = {
            'total_assignments': len(solution_assignments),
            'assignments_by_discipline': collections.defaultdict(int),
            'assignments_by_student': collections.defaultdict(int),
            'quota_fulfillment': {}
        }
        
        # Count by discipline and student
        for (e_id, d_id, v_idx) in solution_assignments:
            stats['assignments_by_discipline'][d_id] += 1
            stats['assignments_by_student'][e_id] += 1
        
        # Check quota fulfillment
        for disc in self.config.disciplines:
            for el in self.config.eleves:
                if el.annee.value not in disc.annee:
                    continue
                
                try:
                    adx = disc.annee.index(el.annee.value)
                    quota = disc.quota[adx]
                except (ValueError, IndexError):
                    continue
                
                if quota > 0:
                    count = sum(1 for (e, d, v) in solution_assignments 
                              if e == el.id_eleve and d == disc.id_discipline)
                    
                    key = f"e{el.id_eleve}_d{disc.id_discipline}"
                    stats['quota_fulfillment'][key] = {
                        'quota': quota,
                        'assigned': count,
                        'fulfilled': count >= quota
                    }
        
        return stats