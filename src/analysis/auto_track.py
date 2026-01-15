from create_tracking_excel import parse_ortools_output, add_execution_to_excel
from pathlib import Path

def track_execution_from_file(log_file_path, excel_path, notes=""):
    """Lit un fichier de log et l'ajoute à l'Excel"""
    
    with open(log_file_path, 'r') as f:
        log_text = f.read()
    
    metrics = parse_ortools_output(log_text)
    add_execution_to_excel(excel_path, metrics, notes)
    
    print(f"📊 Métriques extraites:")
    print(f"  Status: {metrics['status']}")
    print(f"  Objectif: {metrics['objective']}")
    print(f"  Temps: {metrics['walltime']}s")
    print(f"  Solutions: {metrics['num_solutions']}")

if __name__ == "__main__":
    log_path = Path(__file__).parent.parent.parent / "logs" / "last_run.log"
    excel_path = Path(__file__).parent.parent.parent / "resultat" / "suivi_experimentations.xlsx"
    
    track_execution_from_file(log_path, excel_path, notes="Test avec nouveaux paramètres")