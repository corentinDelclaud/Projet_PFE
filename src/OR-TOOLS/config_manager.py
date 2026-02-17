"""
Centralized configuration management with validation
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class SolverParams:
    """Solver configuration parameters"""
    max_time_seconds: int = 18000 # 5 hours
    num_workers: int = 6
    log_progress: bool = True
    solution_limit: int = 1
    
    def to_dict(self) -> dict:
        return {
            'max_time_seconds': self.max_time_seconds,
            'num_workers': self.num_workers,
            'log_progress': self.log_progress,
            'solution_limit': self.solution_limit
        }

@dataclass
class ModelConfig:
    """Validated configuration for the optimization model"""
    disciplines: List = field(default_factory=list)
    eleves: List = field(default_factory=list)
    stages_lookup: Dict = field(default_factory=dict)
    calendar_unavailability: Dict = field(default_factory=dict)
    periodes: List = field(default_factory=list)
    output_dir: Path = None
    solver_params: SolverParams = field(default_factory=SolverParams)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration and return (is_valid, errors)
        
        Returns:
            Tuple[bool, List[str]]: (True if valid, list of error messages)
        """
        errors = []
        
        # Check disciplines
        if not self.disciplines:
            errors.append("Aucune discipline configurée")
        else:
            for disc in self.disciplines:
                if not disc.annee:
                    errors.append(f"Discipline {disc.nom_discipline}: Aucune année définie")
                if sum(disc.quota) == 0:
                    logger.warning(f"Discipline {disc.nom_discipline}: Quota total = 0")
        
        # Check students
        if not self.eleves:
            errors.append("Aucun élève chargé")
        else:
            # Check for duplicate IDs
            ids = [e.id_eleve for e in self.eleves]
            if len(ids) != len(set(ids)):
                errors.append("IDs d'élèves en double détectés")
        
        # Check output directory
        if self.output_dir is None:
            errors.append("Répertoire de sortie non défini")
        
        # Check quotas coherence
        for disc in self.disciplines:
            total_quota = sum(disc.quota)
            if total_quota > 0:
                # Count eligible students
                eligible_students = sum(1 for e in self.eleves if e.annee.value in disc.annee)
                total_capacity = sum(disc.nb_eleve) * 52  # 52 weeks
                
                if total_quota * eligible_students > total_capacity * 1.5:
                    logger.warning(
                        f"Discipline {disc.nom_discipline}: "
                        f"Quota élevé par rapport à la capacité "
                        f"(Quota total: {total_quota * eligible_students}, "
                        f"Capacité: {total_capacity})"
                    )
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """Export configuration for logging/debugging"""
        return {
            'nb_disciplines': len(self.disciplines),
            'nb_eleves': len(self.eleves),
            'disciplines': [d.nom_discipline for d in self.disciplines],
            'nb_stages': sum(len(v) for v in self.stages_lookup.values()),
            'nb_periodes': len(self.periodes),
            'solver_params': self.solver_params.to_dict()
        }
    
    def save_to_json(self, filepath: Path):
        """Save configuration summary to JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Configuration sauvegardée: {filepath}")
    
    @classmethod
    def from_csv_directory(cls, data_dir: Path, **solver_params):
        """
        Load and validate configuration from CSV directory
        
        Args:
            data_dir: Directory containing CSV files
            **solver_params: Override default solver parameters
        
        Returns:
            ModelConfig: Loaded configuration
        
        Raises:
            DataLoadError: If data loading fails
        """
        from loaders import (
            load_disciplines,
            load_eleves,
            load_stages,
            load_calendars,
            load_periodes
        )
        
        logger.info(f"Chargement configuration depuis: {data_dir}")
        
        # Create solver params
        solver_cfg = SolverParams(**solver_params) if solver_params else SolverParams()
        
        config = cls(
            disciplines=load_disciplines(data_dir / "disciplines.csv"),
            eleves=load_eleves(data_dir / "eleves_with_code.csv"),
            stages_lookup=load_stages(data_dir / "stages.csv"),
            calendar_unavailability=load_calendars(data_dir),
            periodes=load_periodes(data_dir / "periodes.csv"),
            output_dir=data_dir.parent / "resultat",
            solver_params=solver_cfg
        )
        
        logger.info(f"Configuration chargée: {config.to_dict()}")
        return config