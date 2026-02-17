"""
Main application entry point for schedule optimization
"""
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager import ModelConfig
from optimizer import ScheduleOptimizer
from exporter import export_planning, export_statistics
from loaders import DataLoadError

def resolve_data_path():
    """Resolve data directory path for both normal and PyInstaller frozen mode"""
    if getattr(sys, 'frozen', False):
        # Mode compilé (PyInstaller) - data est à côté de l'exécutable
        base_dir = Path(sys.executable).parent
    else:
        # Mode script Python normal
        base_dir = Path(__file__).parent.parent.parent
    return base_dir / "data"

def main():
    """Main execution function"""
    try:
        logger.info("=" * 80)
        logger.info("OPTIMISATION DU PLANNING - DÉMARRAGE")
        logger.info("=" * 80)
        
        # Load configuration
        data_dir = resolve_data_path()
        logger.info(f"Répertoire de données: {data_dir}")
        
        # Utilise les valeurs par défaut de SolverParams (3h, 6 workers)
        config = ModelConfig.from_csv_directory(data_dir)
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            logger.error("Configuration invalide:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("✓ Configuration validée")
        
        # Save configuration
        config.save_to_json(config.output_dir / "config_used.json")
        
        # Create optimizer
        optimizer = ScheduleOptimizer(config)
        
        # Prepare data
        optimizer.prepare_data()
        
        # Build model
        optimizer.build_model()
        
        # Solve
        result = optimizer.solve()
        
        # Export results
        if result.is_success():
            logger.info("=" * 80)
            logger.info("EXPORT DES RÉSULTATS")
            logger.info("=" * 80)
            
            # Export planning
            export_planning(
                result,
                config.output_dir / "planning_solution.csv",
                config,
                optimizer
            )
            
            # Export statistics
            export_statistics(
                result,
                config.output_dir / "statistics.json"
            )
            
            logger.info("=" * 80)
            logger.info("✓ OPTIMISATION TERMINÉE AVEC SUCCÈS")
            logger.info("=" * 80)
            return True
        
        else:
            logger.error("=" * 80)
            logger.error("✗ OPTIMISATION ÉCHOUÉE")
            logger.error(f"Statut: {result.status}")
            if result.error_message:
                logger.error(f"Message: {result.error_message}")
            logger.error("=" * 80)
            return False
    
    except DataLoadError as e:
        logger.error(f"Erreur de chargement des données: {e}")
        return False
    
    except Exception as e:
        logger.exception("Erreur inattendue:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)