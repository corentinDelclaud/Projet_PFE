"""
Export optimization results to various formats
"""
import csv
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

def export_planning(result, output_path: Path, config, optimizer):
    """
    Export planning solution to CSV
    
    Args:
        result: OptimizationResult instance
        output_path: Path to output CSV file
        config: ModelConfig instance
        optimizer: ScheduleOptimizer instance (for accessing vacations, eleve_dict, etc.)
    """
    if not result.is_success():
        logger.error("Cannot export: optimization was not successful")
        return False
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Semaine", "Jour", "Apres-Midi", "Discipline",
                "Id_Discipline", "Id_Eleve", "Id_Binome", "Annee"
            ])
            
            jours_str = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
            
            for (e_id, d_id, v_idx) in result.assignments:
                vac = optimizer.vacations[v_idx]
                el = optimizer.eleve_dict[e_id]
                disc = next(d for d in config.disciplines if d.id_discipline == d_id)
                
                from classes.enum.demijournee import DemiJournee
                
                writer.writerow([
                    vac.semaine,
                    jours_str[vac.jour],
                    1 if vac.period == DemiJournee.apres_midi else 0,
                    disc.nom_discipline,
                    disc.id_discipline,
                    el.id_eleve,
                    el.id_binome,
                    el.annee.name
                ])
        
        logger.info(f"✓ Planning exporté: {output_path}")
        return True
    
    except Exception as e:
        logger.exception(f"Erreur export planning: {e}")
        return False

def export_statistics(result, output_path: Path):
    """Export solution statistics to JSON"""
    import json
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.statistics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Statistiques exportées: {output_path}")
        return True
    
    except Exception as e:
        logger.exception(f"Erreur export statistiques: {e}")
        return False