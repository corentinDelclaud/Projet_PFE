#!/usr/bin/env python3
"""
Script de récupération des scores depuis les logs pour les anciennes runs.
Utilisé pour corriger les runs où tous les CSVs lisaient le même optimization_scores.json.
"""

import json
import re
import sys
from pathlib import Path
import argparse

def parse_scores_from_log(log_file):
    """
    Extrait les scores d'optimisation depuis un fichier de log.
    
    Returns:
        dict ou None si les scores ne sont pas trouvés
    """
    if not log_file.exists():
        return None
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns pour extraire les scores
        raw_pattern = r"Score brut\s*:\s*([\d,]+)"
        max_pattern = r"Score maximum théorique\s*:\s*([\d,]+)"
        norm_pattern = r"Score normalisé\s*:\s*([\d.]+)/100"
        status_pattern = r"status:\s*(OPTIMAL|FEASIBLE)"
        
        raw_match = re.search(raw_pattern, content)
        max_match = re.search(max_pattern, content)
        norm_match = re.search(norm_pattern, content)
        status_match = re.search(status_pattern, content)
        
        if raw_match and max_match and norm_match:
            raw_score = int(raw_match.group(1).replace(',', ''))
            max_theoretical = int(max_match.group(1).replace(',', ''))
            normalized = float(norm_match.group(1))
            status = status_match.group(1) if status_match else "FEASIBLE"
            
            return {
                "raw_score": float(raw_score),
                "max_theoretical_score": max_theoretical,
                "normalized_score": normalized,
                "status": status
            }
        else:
            print(f"  ⚠ Impossible d'extraire tous les scores depuis {log_file.name}")
            return None
            
    except Exception as e:
        print(f"  ⚠ Erreur lors du parsing de {log_file.name}: {e}")
        return None

def recover_scores(base_folder):
    """
    Récupère les scores depuis les logs et regénère les fichiers JSON dans stats/.
    
    Args:
        base_folder: Dossier de base (ex: batch_experiments/2026_02_07/T7200/V5_03_C/)
    """
    base_path = Path(base_folder)
    
    if not base_path.exists():
        print(f"❌ Erreur: Le dossier {base_folder} n'existe pas.")
        return 1
    
    logs_folder = base_path / "logs"
    stats_folder = base_path / "stats"
    
    if not logs_folder.exists():
        print(f"❌ Erreur: Le dossier logs n'existe pas dans {base_folder}")
        return 1
    
    # Créer le dossier stats s'il n'existe pas
    stats_folder.mkdir(parents=True, exist_ok=True)
    
    # Trouver tous les fichiers logs
    log_files = sorted(logs_folder.glob("log_*.txt"))
    
    if not log_files:
        print(f"❌ Aucun fichier log trouvé dans {logs_folder}")
        return 1
    
    print(f"\n{'='*70}")
    print(f"RÉCUPÉRATION DES SCORES DEPUIS LES LOGS")
    print(f"{'='*70}")
    print(f"Dossier: {base_folder}")
    print(f"Logs trouvés: {len(log_files)}")
    print(f"{'='*70}\n")
    
    success_count = 0
    failed_count = 0
    recovered_scores = []
    
    for log_file in log_files:
        # Extraire le nom de base pour générer le nom du JSON
        # log_model_V5_03_C_t7200_iter01_20260208_061009.txt
        # → stats_model_V5_03_C_t7200_iter01_20260208_061009_scores.json
        base_name = log_file.stem.replace('log_', '')
        json_file = stats_folder / f"stats_{base_name}_scores.json"
        
        print(f"[{success_count + failed_count + 1}/{len(log_files)}] {log_file.name}")
        
        # Parser les scores depuis le log
        scores = parse_scores_from_log(log_file)
        
        if scores:
            # Sauvegarder le JSON
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(scores, f, indent=2)
                print(f"  ✓ Scores récupérés: {scores['raw_score']:,.0f} / {scores['max_theoretical_score']:,.0f} = {scores['normalized_score']:.2f}%")
                print(f"  ✓ Sauvegardé: {json_file.name}")
                success_count += 1
                recovered_scores.append(scores)
            except Exception as e:
                print(f"  ✗ Erreur lors de la sauvegarde: {e}")
                failed_count += 1
        else:
            print(f"  ✗ Impossible de récupérer les scores")
            failed_count += 1
        
        print()
    
    print(f"{'='*70}")
    print(f"RÉSUMÉ")
    print(f"{'='*70}")
    print(f"Succès: {success_count}/{len(log_files)}")
    print(f"Échecs: {failed_count}/{len(log_files)}")
    
    if recovered_scores:
        print(f"\n📊 Statistiques des scores récupérés:")
        raw_scores = [s['raw_score'] for s in recovered_scores]
        norm_scores = [s['normalized_score'] for s in recovered_scores]
        
        print(f"  Raw score:")
        print(f"    Min:  {min(raw_scores):,.0f}")
        print(f"    Max:  {max(raw_scores):,.0f}")
        print(f"    Moy:  {sum(raw_scores)/len(raw_scores):,.0f}")
        
        print(f"  Normalized score:")
        print(f"    Min:  {min(norm_scores):.2f}%")
        print(f"    Max:  {max(norm_scores):.2f}%")
        print(f"    Moy:  {sum(norm_scores)/len(norm_scores):.2f}%")
    
    print(f"\n💡 Prochaine étape:")
    print(f"   Regénérer le scores_summary.json avec:")
    print(f"   python src/OR-TOOLS/scripts/generate_batch_stats.py \"{base_folder}\"")
    print(f"{'='*70}\n")
    
    return 0 if failed_count == 0 else 1

def main():
    parser = argparse.ArgumentParser(
        description="Récupère les scores depuis les logs et regénère les fichiers JSON dans stats/"
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Chemin vers le dossier contenant logs/ et stats/ (ex: batch_experiments/2026_02_07/T7200/V5_03_C)"
    )
    
    args = parser.parse_args()
    
    return recover_scores(args.folder)

if __name__ == "__main__":
    sys.exit(main())
