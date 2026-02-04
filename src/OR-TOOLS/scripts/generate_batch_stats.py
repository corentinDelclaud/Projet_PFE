import os
import sys
import subprocess
import re
import json
from pathlib import Path

# Add parent directories to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

STATS_SCRIPT = PROJECT_ROOT / "src" / "analysis" / "generate_statistics.py"

def parse_scores_from_log(log_file):
    """
    Extrait les scores d'optimisation depuis un fichier de log.
    
    Cherche des lignes comme:
    Score brut : 155,290,666,940
    Score maximum théorique : 290,808,782,540
    Score normalisé : 53.40/100
    
    Returns:
        dict ou None si les scores ne sont pas trouvés
    """
    if not log_file.exists():
        return None
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns pour extraire les scores
        # Score brut peut avoir des virgules comme séparateurs de milliers
        raw_pattern = r"Score brut\s*:\s*([\d,]+)"
        max_pattern = r"Score maximum théorique\s*:\s*([\d,]+)"
        norm_pattern = r"Score normalisé\s*:\s*([\d.]+)/100"
        
        raw_match = re.search(raw_pattern, content)
        max_match = re.search(max_pattern, content)
        norm_match = re.search(norm_pattern, content)
        
        if raw_match and max_match and norm_match:
            # Nettoyer les virgules des nombres
            raw_score = int(raw_match.group(1).replace(',', ''))
            max_score = int(max_match.group(1).replace(',', ''))
            norm_score = float(norm_match.group(1))
            
            # Détecter le statut (OPTIMAL ou FEASIBLE)
            status = "FEASIBLE"
            if "OPTIMAL" in content:
                status = "OPTIMAL"
            
            return {
                "raw_score": raw_score,
                "max_theoretical_score": max_score,
                "normalized_score": norm_score,
                "status": status
            }
        else:
            return None
            
    except Exception as e:
        print(f"  ⚠ Erreur lors du parsing du log : {e}")
        return None

def generate_stats_for_iterations(base_folder):
    """
    Parcourt tous les dossiers d'itérations et génère les statistiques
    pour chaque fichier CSV trouvé.
    
    Args:
        base_folder: Dossier de base contenant les sous-dossiers (ex: T1200/V5_01/)
    """
    base_path = Path(base_folder)
    
    if not base_path.exists():
        print(f"Erreur: Le dossier {base_folder} n'existe pas.")
        return
    
    # Chercher le dossier iters/
    iters_folder = base_path / "iters"
    stats_folder = base_path / "stats"
    logs_folder = base_path / "logs"
    
    if not iters_folder.exists():
        print(f"Erreur: Le dossier {iters_folder} n'existe pas.")
        return
    
    # Créer le dossier stats s'il n'existe pas
    stats_folder.mkdir(parents=True, exist_ok=True)
    
    # Trouver tous les fichiers CSV
    csv_files = sorted(iters_folder.glob("*.csv"))
    
    if not csv_files:
        print(f"Aucun fichier CSV trouvé dans {iters_folder}")
        return
    
    print(f"Trouvé {len(csv_files)} fichiers CSV dans {iters_folder}")
    print(f"Génération des statistiques dans {stats_folder}")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        # Générer le nom du fichier de sortie
        base_name = csv_file.stem  # nom sans extension
        stats_file = stats_folder / f"stats_{base_name}.xlsx"
        
        # Chercher le fichier log correspondant
        log_file = logs_folder / f"log_{base_name}.txt"
        
        print(f"\n[{success_count + failed_count + 1}/{len(csv_files)}] {csv_file.name}")
        print(f"  → CSV: {csv_file}")
        print(f"  → Stats: {stats_file.name}")
        
        # Parser les scores depuis le log
        optimization_scores = None
        if log_file.exists():
            print(f"  → Log: {log_file.name}")
            optimization_scores = parse_scores_from_log(log_file)
            if optimization_scores:
                print(f"  ✓ Scores extraits du log: {optimization_scores['normalized_score']:.2f}/100")
            else:
                print(f"  ⚠ Impossible d'extraire les scores du log")
        else:
            print(f"  ⚠ Pas de fichier log trouvé")
        
        # Créer un fichier JSON temporaire avec les scores si disponibles
        temp_json = None
        if optimization_scores:
            temp_json = csv_file.parent / f"{base_name}_scores.json"
            try:
                with open(temp_json, 'w', encoding='utf-8') as f:
                    json.dump(optimization_scores, f, indent=2)
            except Exception as e:
                print(f"  ⚠ Erreur lors de la création du JSON temporaire : {e}")
                temp_json = None
        
        try:
            # Construire la commande
            cmd = [
                sys.executable,
                str(STATS_SCRIPT),
                "--input", str(csv_file),
                "--output", str(stats_file)
            ]
            
            # Exécuter le script de statistiques
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            print(f"  ✓ Statistiques générées avec succès")
            success_count += 1
            
            # Nettoyer le fichier JSON temporaire
            if temp_json and temp_json.exists():
                try:
                    temp_json.unlink()
                except:
                    pass
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ ERREUR lors de la génération des statistiques")
            print(f"    {e.stderr if e.stderr else e.stdout}")
            failed_count += 1
            
            # Nettoyer le fichier JSON temporaire en cas d'erreur aussi
            if temp_json and temp_json.exists():
                try:
                    temp_json.unlink()
                except:
                    pass
                    
        except Exception as e:
            print(f"  ✗ ERREUR: {str(e)}")
            failed_count += 1
            
            # Nettoyer le fichier JSON temporaire en cas d'erreur aussi
            if temp_json and temp_json.exists():
                try:
                    temp_json.unlink()
                except:
                    pass
    
    print("\n" + "=" * 70)
    print(f"Terminé: {success_count} réussis, {failed_count} échoués")
    print(f"Statistiques sauvegardées dans: {stats_folder}")
    print("=" * 70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Génère les statistiques pour tous les fichiers CSV d'itérations"
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Chemin vers le dossier contenant les sous-dossiers iters/ et stats/ (ex: batch_experiments/04_02_2026/T1200/V5_01)"
    )
    
    args = parser.parse_args()
    
    generate_stats_for_iterations(args.folder)

if __name__ == "__main__":
    main()
