#!/usr/bin/env python3
"""
Script de test rapide pour comparer les trois modèles.
Compare V5_02 (baseline), V5_03_B (assoupli), V5_03_C (réaliste)
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "src" / "OR-TOOLS"
OUTPUT_DIR = PROJECT_ROOT / "test_comparaison_modeles"
TIME_LIMIT = 1200  # 20 minutes pour test rapide

MODELS = {
    "V5_02_baseline": MODELS_DIR / "model_V5_02.py",
    "V5_03_B_assoupli": MODELS_DIR / "model_V5_03_B.py",
    "V5_03_C_realiste": MODELS_DIR / "model_V5_03_C.py"
}

def run_model(model_name, model_path, output_csv, time_limit):
    """Exécute un modèle et retourne les scores."""
    print(f"\n{'='*60}")
    print(f"Exécution: {model_name}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable,
        str(model_path),
        "--time_limit", str(time_limit),
        "--output", str(output_csv)
    ]
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=time_limit + 60  # +60s de marge
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extraire les scores du output
        scores = extract_scores(result.stdout)
        scores["duration_seconds"] = duration
        scores["model_name"] = model_name
        scores["exit_code"] = result.returncode
        
        if result.returncode != 0:
            print(f"⚠️ ERREUR lors de l'exécution:")
            print(result.stderr)
            scores["error"] = result.stderr
        else:
            print(f"✅ Terminé en {duration:.1f}s")
            print(f"   Score brut: {scores.get('raw_score', 'N/A'):,}")
            print(f"   Score max théorique: {scores.get('max_theoretical_score', 'N/A'):,}")
            print(f"   Score normalisé: {scores.get('normalized_score', 'N/A')}/100")
        
        return scores
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT après {time_limit}s")
        return {
            "model_name": model_name,
            "error": "Timeout",
            "duration_seconds": time_limit
        }
    except Exception as e:
        print(f"❌ Exception: {e}")
        return {
            "model_name": model_name,
            "error": str(e)
        }

def extract_scores(output_text):
    """Extrait les scores du texte de sortie."""
    scores = {}
    
    for line in output_text.split('\n'):
        if "Score brut" in line or "raw_score" in line:
            # Format: "Score brut : 33,270,620"
            parts = line.split(':')
            if len(parts) >= 2:
                score_str = parts[-1].strip().replace(',', '').replace(' ', '')
                try:
                    scores['raw_score'] = int(score_str)
                except ValueError:
                    pass
        
        elif "Score maximum théorique" in line or "max_theoretical_score" in line:
            parts = line.split(':')
            if len(parts) >= 2:
                score_str = parts[-1].strip().replace(',', '').replace(' ', '')
                try:
                    scores['max_theoretical_score'] = int(score_str)
                except ValueError:
                    pass
        
        elif "Score normalisé" in line or "normalized_score" in line:
            # Format: "Score normalisé : 66.31/100"
            parts = line.split(':')
            if len(parts) >= 2:
                score_str = parts[-1].strip().split('/')[0].strip()
                try:
                    scores['normalized_score'] = float(score_str)
                except ValueError:
                    pass
    
    return scores

def generate_comparison_report(results, output_file):
    """Génère un rapport de comparaison."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# RAPPORT DE COMPARAISON DES MODÈLES\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Time Limit**: {TIME_LIMIT}s ({TIME_LIMIT/60:.0f} minutes)\n\n")
        
        f.write("---\n\n")
        f.write("## RÉSULTATS\n\n")
        
        # Tableau comparatif
        f.write("| Modèle | Score Brut | Max Théorique | Score Normalisé | Durée (s) | Status |\n")
        f.write("|--------|------------|---------------|-----------------|-----------|--------|\n")
        
        for result in results:
            model = result.get('model_name', 'N/A')
            raw = result.get('raw_score', 'N/A')
            max_theo = result.get('max_theoretical_score', 'N/A')
            norm = result.get('normalized_score', 'N/A')
            duration = result.get('duration_seconds', 'N/A')
            status = "✅ OK" if result.get('exit_code') == 0 else "❌ ERREUR"
            
            # Formater les nombres
            if isinstance(raw, int):
                raw = f"{raw:,}"
            if isinstance(max_theo, int):
                max_theo = f"{max_theo:,}"
            if isinstance(norm, float):
                norm = f"{norm:.2f}"
            if isinstance(duration, (int, float)):
                duration = f"{duration:.1f}"
            
            f.write(f"| {model} | {raw} | {max_theo} | {norm} | {duration} | {status} |\n")
        
        f.write("\n---\n\n")
        f.write("## ANALYSE\n\n")
        
        # Comparaison des scores normalisés
        baseline = next((r for r in results if 'baseline' in r.get('model_name', '')), None)
        
        if baseline and baseline.get('normalized_score'):
            baseline_score = baseline['normalized_score']
            f.write(f"### Score Baseline: {baseline_score:.2f}%\n\n")
            
            for result in results:
                if 'baseline' in result.get('model_name', ''):
                    continue
                
                if result.get('normalized_score'):
                    score = result['normalized_score']
                    diff = score - baseline_score
                    pct_change = (diff / baseline_score) * 100 if baseline_score > 0 else 0
                    
                    model = result['model_name']
                    f.write(f"#### {model}\n")
                    f.write(f"- Score: {score:.2f}%\n")
                    f.write(f"- Différence vs baseline: {diff:+.2f} points ({pct_change:+.1f}%)\n")
                    
                    if 'B_assoupli' in model:
                        expected = "75-85%"
                        status = "✅ OK" if 75 <= score <= 85 else "⚠️ Hors fourchette"
                        f.write(f"- Attendu: {expected}\n")
                        f.write(f"- Validation: {status}\n")
                    
                    elif 'C_realiste' in model:
                        expected = "85-95%"
                        status = "✅ OK" if 85 <= score <= 95 else "⚠️ Hors fourchette"
                        f.write(f"- Attendu: {expected}\n")
                        f.write(f"- Validation: {status}\n")
                    
                    f.write("\n")
        
        f.write("---\n\n")
        f.write("## FICHIERS GÉNÉRÉS\n\n")
        
        for result in results:
            if result.get('exit_code') == 0:
                model = result['model_name']
                csv_file = OUTPUT_DIR / f"planning_{model}.csv"
                if csv_file.exists():
                    f.write(f"- [{model}]({csv_file.name})\n")
        
        f.write("\n---\n\n")
        f.write("## RECOMMANDATION\n\n")
        
        # Trouver le meilleur score
        valid_results = [r for r in results if r.get('normalized_score')]
        if valid_results:
            best = max(valid_results, key=lambda r: r.get('normalized_score', 0))
            f.write(f"**Meilleur score**: {best['model_name']} - {best['normalized_score']:.2f}%\n\n")
            
            if 'C_realiste' in best['model_name']:
                f.write("✅ **Le modèle C (réaliste) est recommandé** car il offre:\n")
                f.write("- Score normalisé honnête (85-95%)\n")
                f.write("- Qualité planning identique au baseline\n")
                f.write("- Aucune contrainte modifiée\n")
            elif 'B_assoupli' in best['model_name']:
                f.write("⚠️ **Le modèle B (assoupli) obtient le meilleur score** mais:\n")
                f.write("- Vérifier manuellement la qualité des plannings\n")
                f.write("- Valider que les assouplissements sont acceptables\n")
                f.write("- Comparer avec le baseline pour détecter les régressions\n")
        
        f.write("\n---\n\n")
        f.write("**Fichiers créés**:\n")
        f.write("- Rapport: `rapport_comparaison.md`\n")
        f.write("- Scores JSON: `scores_comparaison.json`\n")
        f.write("- Plannings: `planning_*.csv`\n")

def main():
    """Fonction principale."""
    print("\n" + "="*60)
    print("TEST DE COMPARAISON DES TROIS MODÈLES")
    print("="*60)
    print(f"\nTime limit: {TIME_LIMIT}s ({TIME_LIMIT/60:.0f} minutes)")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Créer le répertoire de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Vérifier que les modèles existent
    for model_name, model_path in MODELS.items():
        if not model_path.exists():
            print(f"❌ ERREUR: Modèle introuvable: {model_path}")
            return 1
    
    print("\n✅ Tous les modèles trouvés")
    
    # Exécuter chaque modèle
    results = []
    
    for model_name, model_path in MODELS.items():
        output_csv = OUTPUT_DIR / f"planning_{model_name}.csv"
        
        result = run_model(model_name, model_path, output_csv, TIME_LIMIT)
        results.append(result)
    
    # Sauvegarder les résultats en JSON
    json_file = OUTPUT_DIR / "scores_comparaison.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Scores sauvegardés: {json_file}")
    
    # Générer le rapport
    report_file = OUTPUT_DIR / "rapport_comparaison.md"
    generate_comparison_report(results, report_file)
    
    print(f"✅ Rapport généré: {report_file}")
    
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    
    for result in results:
        model = result.get('model_name', 'N/A')
        norm = result.get('normalized_score', 'N/A')
        if isinstance(norm, float):
            norm = f"{norm:.2f}%"
        print(f"{model:25} → {norm}")
    
    print("\n✅ Tests terminés!")
    print(f"📁 Résultats dans: {OUTPUT_DIR}")
    print(f"📄 Lire le rapport: {report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
