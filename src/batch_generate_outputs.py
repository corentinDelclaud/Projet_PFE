"""
batch_generate_outputs.py
--------------------------
Pour chaque sous-dossier d'itération dans un répertoire de batch, ce script :
  1. Trouve le fichier CSV de planning (planning_solution ou model_V5_*)
  2. Génère les emplois du temps individuels + fichier Excel compilé
     → <dossier_iteration>/emplois_du_temps/
  3. Génère les fiches d'appel par discipline
     → <dossier_iteration>/fiches_appel/

Usage :
  python batch_generate_outputs.py --batch_dir "..." [--start_date YYYY-MM-DD]

Exemple :
  python batch_generate_outputs.py \
    --batch_dir "C:/Users/coren/Desktop/PFE/Projet_PFE/batch_experiments/2026_02_13/T18000/V5_03_C - Copie" \
    --start_date 2025-09-01
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# ── Ajouter src/ au path pour importer les formatters ──────────────────────────
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from formatters.generate_formatted_student_TT_custom import (
    generate_individual_plannings,
    create_timetable_excel,
)
from formatters.generate_formatted_fiche_appel_custom import (
    generate_discipline_year_excel,
)


def process_iteration(csv_path: str, output_root: str, start_date: datetime):
    """
    Traite un fichier CSV d'itération :
      - génère les emplois du temps (student TT)
      - génère les fiches d'appel (discipline attendance)
    """
    csv_basename = Path(csv_path).stem
    print(f"\n{'='*70}")
    print(f"  Traitement : {csv_basename}")
    print(f"{'='*70}")

    # ── ÉTAPE 1 : Emplois du temps ──────────────────────────────────────────────
    tt_dir       = os.path.join(output_root, "emplois_du_temps")
    planning_dir = os.path.join(tt_dir, "planning_personnel")

    print("\n[1/2] Génération des emplois du temps...")
    count = generate_individual_plannings(csv_path, planning_dir)

    if count > 0:
        excel_filename = f"emplois_du_temps_{csv_basename}.xlsx"
        excel_path     = os.path.join(tt_dir, excel_filename)
        create_timetable_excel(planning_dir, excel_path, start_date)
        print(f"  ✓ {count} emplois du temps → {tt_dir}")
    else:
        print("  ✗ Aucun emploi du temps généré.")

    # ── ÉTAPE 2 : Fiches d'appel ────────────────────────────────────────────────
    fiche_dir = os.path.join(output_root, "fiches_appel")

    print("\n[2/2] Génération des fiches d'appel par discipline...")
    n = generate_discipline_year_excel(csv_path, fiche_dir, csv_basename)
    if n > 0:
        print(f"  ✓ {n} fiches d'appel → {fiche_dir}")
    else:
        print("  ✗ Aucune fiche d'appel générée.")


def main():
    parser = argparse.ArgumentParser(
        description="Génère emplois du temps + fiches d'appel pour chaque itération d'un batch."
    )
    parser.add_argument(
        "--batch_dir",
        type=str,
        required=True,
        help="Dossier racine contenant les sous-dossiers d'itération (1, 2, 3, ...)",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default="2025-09-01",
        help="Date de début de l'année universitaire (YYYY-MM-DD). Défaut : 2025-09-01",
    )
    args = parser.parse_args()

    batch_dir = args.batch_dir
    if not os.path.isdir(batch_dir):
        print(f"Erreur : le dossier '{batch_dir}' n'existe pas.")
        sys.exit(1)

    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        print(f"Erreur : format de date invalide '{args.start_date}'. Utilisez YYYY-MM-DD.")
        sys.exit(1)

    # ── Parcourir les sous-dossiers triés (1, 2, 3 …) ─────────────────────────
    subdirs = sorted(
        [d for d in Path(batch_dir).iterdir() if d.is_dir()],
        key=lambda p: (p.name.isdigit(), int(p.name) if p.name.isdigit() else p.name),
    )

    if not subdirs:
        print(f"Aucun sous-dossier trouvé dans : {batch_dir}")
        sys.exit(0)

    print(f"\nBatch directory  : {batch_dir}")
    print(f"Date de début    : {start_date.strftime('%d/%m/%Y')}")
    print(f"Itérations trouvées : {len(subdirs)}")

    total_ok  = 0
    total_err = 0

    for subdir in subdirs:
        # Chercher UN fichier CSV dans le sous-dossier
        csv_files = list(subdir.glob("*.csv"))

        if not csv_files:
            print(f"\n[SKIP] Aucun CSV dans {subdir.name}/")
            continue

        if len(csv_files) > 1:
            print(f"\n[WARN] Plusieurs CSV dans {subdir.name}/, seul le premier sera utilisé.")

        csv_path = str(csv_files[0])

        try:
            process_iteration(
                csv_path=csv_path,
                output_root=str(subdir),   # ← sauvegarde dans le même dossier
                start_date=start_date,
            )
            total_ok += 1
        except Exception as exc:
            print(f"\n  ✗ Erreur sur l'itération {subdir.name} : {exc}")
            import traceback
            traceback.print_exc()
            total_err += 1

    print(f"\n{'='*70}")
    print(f"TERMINÉ  —  {total_ok} itération(s) traitées, {total_err} erreur(s).")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
